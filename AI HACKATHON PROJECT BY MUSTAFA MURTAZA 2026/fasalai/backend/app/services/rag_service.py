"""
📚 Advanced RAG Service — Fast In-Memory Knowledge Base
TF-IDF scoring, synonym expansion, category filtering, caching
Zero external dependencies — blazing fast!
"""
import math
import re
from typing import Optional, List, Dict, Tuple
from collections import defaultdict
from functools import lru_cache
from loguru import logger


class Document:
    __slots__ = ("text", "category", "crops", "tokens", "token_set")

    def __init__(self, text: str, category: str, crops: List[str]):
        self.text = text
        self.category = category
        self.crops = crops
        self.tokens = tokenize(text)
        self.token_set = set(self.tokens)


# ═══════════════════════════════════════════
# TOKENIZER + SYNONYMS
# ═══════════════════════════════════════════

_STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
    "to", "for", "of", "and", "or", "ka", "ki", "ke", "ko", "se",
    "me", "hai", "hain", "kya", "ya", "aur", "ye", "wo", "mein",
    "par", "ne", "with", "how", "what", "when", "which", "can",
})

SYNONYMS: Dict[str, List[str]] = {
    "wheat": ["gandum", "gandom", "گندم", "gehun"],
    "rice": ["chawal", "dhan", "چاول"],
    "cotton": ["kapas", "کپاس", "narma"],
    "sugarcane": ["ganna", "ganna", "گنا"],
    "potato": ["aloo", "آلو"],
    "tomato": ["tamatar", "ٹماٹر"],
    "maize": ["corn", "makki", "makai", "مکئی"],
    "onion": ["pyaz", "پیاز"],
    "mango": ["aam", "آم"],
    "citrus": ["malta", "kinno", "sangtara"],
    "banana": ["kela", "کیلا"],
    "rust": ["zang", "زنگ"],
    "blight": ["jhulsa", "جھلسا"],
    "whitefly": ["safed_makhi", "سفید_مکھی", "bemisia"],
    "fertilizer": ["khad", "کھاد", "urea", "dap"],
    "irrigation": ["pani", "sinchai", "آبپاشی", "water"],
    "disease": ["bimari", "بیماری", "rog", "مرض"],
    "pest": ["keera", "کیڑا", "bug", "insect"],
    "sowing": ["bijai", "بجائی", "planting", "kasht"],
    "harvest": ["katai", "کٹائی", "harvesting"],
    "price": ["qeemat", "قیمت", "rate", "bhav"],
    "treatment": ["ilaj", "علاج", "dawai", "spray"],
    "fungicide": ["곰팡이", "곰팡이약", "anti_fungal"],
    "pesticide": ["keera_mar", "کیڑے_مار"],
    "virus": ["وائرس"],
    "worm": ["sundi", "سنڈی"],
    "aphid": ["tela", "تیلا"],
    "mildew": ["phoondhi", "پھوندھی"],
    "rot": ["gallan", "گلن"],
}

# Build reverse lookup: synonym → canonical
_SYNONYM_MAP: Dict[str, str] = {}
for canonical, syns in SYNONYMS.items():
    for syn in syns:
        _SYNONYM_MAP[syn.lower()] = canonical
    _SYNONYM_MAP[canonical] = canonical


def tokenize(text: str) -> List[str]:
    """Lowercase, split, remove stopwords, expand synonyms"""
    raw = re.sub(r"[^\w\s]", " ", text.lower())
    tokens = [t for t in raw.split() if t not in _STOP_WORDS and len(t) > 1]
    return tokens


def expand_query(tokens: List[str]) -> set:
    """Expand tokens with synonyms for better matching"""
    expanded = set(tokens)
    for token in tokens:
        # Add canonical form
        if token in _SYNONYM_MAP:
            canonical = _SYNONYM_MAP[token]
            expanded.add(canonical)
            # Add all synonyms of canonical
            if canonical in SYNONYMS:
                expanded.update(SYNONYMS[canonical])
        # Check if token is a canonical key
        if token in SYNONYMS:
            expanded.update(SYNONYMS[token])
    return expanded


# ═══════════════════════════════════════════
# KNOWLEDGE BASE DOCUMENTS
# ═══════════════════════════════════════════

RAW_KNOWLEDGE = [
    # ── Wheat ──
    {
        "text": "Wheat leaf rust (Puccinia triticina) is the most common wheat disease in Punjab Pakistan. Symptoms: Orange-brown pustules on upper leaf surface. Appears in Feb-March when temp is 15-25°C with humidity >60%. Treatment: Tilt 250EC (Propiconazole) 200ml/acre or Nativo 75WG (Trifloxystrobin + Tebuconazole) 100g/acre. Cost 800-1200 PKR. Apply at first sign of pustules. Repeat after 15 days if needed.",
        "category": "disease", "crops": ["wheat"],
    },
    {
        "text": "Wheat yellow rust (Puccinia striiformis): Yellow stripe-like pustules along leaf veins. Common in cooler areas — KPK, northern Punjab, Balochistan highlands. Appears when temp 10-15°C with moisture. Treatment: Tilt 250EC 200ml/acre. Resistant varieties: Ujala-2016, Zincol-2016, Pakistan-2013. More aggressive than leaf rust, spreads rapidly.",
        "category": "disease", "crops": ["wheat"],
    },
    {
        "text": "Wheat powdery mildew (Blumeria graminis): White powdery patches on leaves, stems, and heads. Favored by high humidity, moderate temperatures. Treatment: Sulfur dust 10kg/acre or Score 250EC (Difenoconazole) 300ml/acre. Ensure good air circulation. Avoid excess nitrogen.",
        "category": "disease", "crops": ["wheat"],
    },
    {
        "text": "Wheat loose smut (Ustilago tritici): Black powdery spores replace grain heads. Seed-borne disease. Prevention: Treat seed with Vitavax 200 (Carboxin + Thiram) 2.5g/kg seed before sowing. No field spray effective. Use certified disease-free seed.",
        "category": "disease", "crops": ["wheat"],
    },
    {
        "text": "Wheat aphid (Sitobion avenae): Small green-yellow insects on leaves and heads, cause yellowing and honeydew. Peak: February-March. Treatment: Imidacloprid 200SL 250ml/acre or Confidor 200SL 200ml/acre. Spray when 10+ aphids per tiller. Ladybird beetles are natural predators.",
        "category": "pest", "crops": ["wheat"],
    },
    {
        "text": "Wheat fertilizer schedule Punjab: At sowing — DAP 50kg/acre (or NP 18-46-0). Urea splits — 50kg at sowing + 50kg at first irrigation (crown root stage, 21 days) + 25kg at booting (65 days). Total Urea 125kg/acre. SOP (Potash) 25kg/acre if soil deficient. DAP price ~13500 PKR/bag, Urea ~2500 PKR/bag.",
        "category": "fertilizer", "crops": ["wheat"],
    },
    {
        "text": "Wheat irrigation schedule Punjab: 4-5 irrigations total. 1st: Crown root stage (21 days after sowing). 2nd: Tillering (45 days). 3rd: Heading/flowering (65 days). 4th: Grain filling (85 days). 5th: Dough stage if available. Each irrigation 3-4 inches. Skip if rain >25mm. Deficit at flowering reduces yield most (up to 50%).",
        "category": "irrigation", "crops": ["wheat"],
    },
    {
        "text": "Punjab wheat sowing calendar: Optimal sowing Oct 15 - Nov 30. Best: Nov 1-20. Late sowing after Dec 15 reduces yield 30-40%. Varieties: Early — Faisalabad-2008 (Nov 1-15); Normal — Galaxy-2013, Akbar-2019 (Nov 1-30); Late — Ujala-2016 (Dec 1-15). Seed rate: 50-60kg/acre. Row spacing: 9 inches.",
        "category": "calendar", "crops": ["wheat"],
    },
    {
        "text": "Wheat support price 2024-25 season: PKR 3900/40kg set by government. PASSCO and provincial food departments purchase at this rate. Farmers should ensure gunny bags meet quality standards. Market open price usually PKR 3500-3800/40kg before support price kicks in.",
        "category": "market", "crops": ["wheat"],
    },

    # ── Rice ──
    {
        "text": "Rice blast (Magnaporthe oryzae): Most damaging rice disease in Pakistan. Diamond-shaped lesions with gray centers on leaves. Also attacks neck causing empty grains. Favored by high humidity, 25-28°C. Treatment: Score 250EC 300ml/acre or Nativo 75WG 100g/acre. Apply preventively at booting stage. Resistant varieties: KSK-133, IRRI-6.",
        "category": "disease", "crops": ["rice"],
    },
    {
        "text": "Rice brown spot (Bipolaris oryzae): Brown oval spots on leaves, often due to nutritional deficiency especially zinc. Treatment: Apply Zinc Sulphate 5kg/acre at transplanting + fungicide spray Antracol 70WP 500g/acre. Ensure balanced fertilization.",
        "category": "disease", "crops": ["rice"],
    },
    {
        "text": "Rice bacterial leaf blight (BLB): Water-soaked lesions that turn yellow, starting from leaf tips. Spreads in warm, wet conditions. No effective chemical cure. Prevention: Resistant varieties (IRRI-6), balanced fertilizer (reduce excess Nitrogen), drain flooded fields.",
        "category": "disease", "crops": ["rice"],
    },
    {
        "text": "Rice stem borer: Dead heart in vegetative stage, white head at reproductive stage. Treatment: Virtako 40WG 30g/acre or Cartap Hydrochloride 4G granules 8kg/acre in standing water. Light traps for monitoring moth activity. Two generations per season.",
        "category": "pest", "crops": ["rice"],
    },
    {
        "text": "Sindh rice calendar: Nursery sowing May 15 - June 15. Transplanting June 15 - July 31. Harvesting October - November. Super Basmati: Nursery June 1-15, transplant July 1-15. IRRI-6/IRRI-9 can be transplanted till August 15. Seed rate: 5kg/acre nursery for 1 acre field.",
        "category": "calendar", "crops": ["rice"],
    },
    {
        "text": "Rice fertilizer schedule: DAP 50kg/acre at transplanting. Urea: 35kg at transplanting + 35kg at tillering (25 days) + 30kg at panicle initiation (55 days). Total 100kg/acre. Zinc Sulphate 5kg/acre at transplanting. SOP 25kg/acre for grain quality.",
        "category": "fertilizer", "crops": ["rice"],
    },
    {
        "text": "Rice support price 2024-25: PKR 4000/40kg (IRRI varieties), Super Basmati PKR 6500-8000/40kg in open market. Sindh Rice Research Institute recommends IRRI-6 for yield, Super Basmati for premium price.",
        "category": "market", "crops": ["rice"],
    },

    # ── Cotton ──
    {
        "text": "Cotton Leaf Curl Virus (CLCuV) is the most devastating cotton disease in Punjab Pakistan. Symptoms: Upward or downward leaf curling, thickened veins, enations (leaf-like outgrowths). Spread by whitefly (Bemisia tabaci). No direct cure — control whitefly. Spray: Confidor 200SL (Imidacloprid) 250ml/acre or Movento 150OD (Spirotetramat) 400ml/acre. Resistant varieties: FH-142, MNH-886, CIM-595. Destroy infected plant residues.",
        "category": "disease", "crops": ["cotton"],
    },
    {
        "text": "Cotton whitefly (Bemisia tabaci): Tiny white insects on leaf undersides. Suck sap causing yellowing, transmit CLCuV. Economic threshold: 5 whiteflies per leaf. Treatment: Confidor 200SL 250ml/acre, Movento 150OD 400ml/acre, or Siren 25EC (Thiamethoxam) 200ml/acre. Spray early morning or evening. Rotate insecticides to prevent resistance. Yellow sticky traps for monitoring.",
        "category": "pest", "crops": ["cotton"],
    },
    {
        "text": "Cotton bollworm (Helicoverpa armigera): Larvae feed inside bolls causing major yield loss. Scout twice weekly during flowering. Treatment: Coragen 20SC (Chlorantraniliprole) 60ml/acre or Match 50EC (Lufenuron) 300ml/acre. Pheromone traps for monitoring. IPM: Release Trichogramma wasps.",
        "category": "pest", "crops": ["cotton"],
    },
    {
        "text": "Cotton jassid/leafhopper (Amrasca biguttula): Leaves curl downward, yellowing from margins. Economic threshold: 1-2 per leaf. Treatment: Imidacloprid 200SL 250ml/acre. Keep field clean of weeds. Okra-leaf varieties (e.g., CIM-595) have some tolerance.",
        "category": "pest", "crops": ["cotton"],
    },
    {
        "text": "Cotton pink bollworm: Rosetted flowers, damaged bolls with pink larvae inside. Treatment: Emamectin Benzoate 1.9EC 200ml/acre at square/flower stage. Destroy crop residues after picking. Short-duration varieties escape late attack.",
        "category": "pest", "crops": ["cotton"],
    },
    {
        "text": "Cotton fertilizer: DAP 50kg/acre + Urea 75-100kg/acre (split: 25kg at sowing, 50kg at first irrigation, 25kg at flowering). SOP 25-50kg/acre for boll quality. Foliar spray Boron 0.5kg/acre at flowering reduces boll drop.",
        "category": "fertilizer", "crops": ["cotton"],
    },
    {
        "text": "Cotton calendar Punjab: Sowing April 15 - May 31. Optimal May 1-15. First picking August, continues through November. Varieties: FH-142 (virus tolerant), MNH-886, CIM-602. Seed rate 8-10kg/acre. Row spacing 30 inches, plant spacing 9 inches.",
        "category": "calendar", "crops": ["cotton"],
    },

    # ── Sugarcane ──
    {
        "text": "Sugarcane red rot (Colletotrichum falcatum): Internal red discoloration of cane with interrupted white patches. Sour smell when split. No effective chemical cure. Management: Remove and burn infected canes, use resistant varieties CPF-246, CPF-247, HSF-240. Avoid flood irrigation. Seed treatment with Carbendazim 2g/liter soak for 30 minutes.",
        "category": "disease", "crops": ["sugarcane"],
    },
    {
        "text": "Sugarcane smut (Ustilago scitaminea): Black whip-like structure from growing point. Remove infected plants immediately and burn. Use resistant varieties HSF-240. Do not use infected canes as seed. Treatment: Hot water treatment of seed cane at 52°C for 30 minutes.",
        "category": "disease", "crops": ["sugarcane"],
    },
    {
        "text": "Sugarcane borers (top borer, stem borer): Dead hearts, bore holes in stem. Treatment: Furadan 3G granules 12kg/acre in leaf whorl. Or Virtako 40WG 30g/acre spray. Release Trichogramma parasitoid wasps. Trash mulching reduces borer survival.",
        "category": "pest", "crops": ["sugarcane"],
    },
    {
        "text": "Sugarcane support price: PKR 425/40kg (2024-25). Mills should pay promptly. Punjab Cane Commissioner handles payment disputes. Average yield 250-300 maunds/acre. Revenue potential 100,000-125,000 PKR/acre.",
        "category": "market", "crops": ["sugarcane"],
    },
    {
        "text": "Sugarcane calendar: Spring planting Feb-March. Autumn planting September-October. Harvest December-March. Varieties: CPF-246, HSF-240, CP-77-400. Seed rate: 100-120 maunds/acre. Trench planting gives 20% more yield than flat planting.",
        "category": "calendar", "crops": ["sugarcane"],
    },

    # ── Potato ──
    {
        "text": "Potato late blight (Phytophthora infestans): Most destructive potato disease. Brown-black water-soaked lesions on leaves, white mold underneath in humid conditions. Can destroy entire crop in 7-10 days. Treatment: Antracol 70WP (Propineb) 500g/acre or Ridomil Gold 68WG (Metalaxyl + Mancozeb) 500g/acre every 7-10 days. Start preventive sprays when humidity >80%.",
        "category": "disease", "crops": ["potato"],
    },
    {
        "text": "Potato common scab (Streptomyces scabies): Rough corky patches on tuber skin, reduces market value. Management: Maintain soil pH below 5.5, irrigate regularly during tuber formation (critical period 4-6 weeks after emergence), avoid fresh manure, use acid-forming fertilizers.",
        "category": "disease", "crops": ["potato"],
    },
    {
        "text": "Potato black leg (Pectobacterium): Stem base turns black, slimy, plant wilts. Seed-borne. Use certified seed only. Treat seed with Mancozeb before planting. Avoid waterlogging. Remove infected plants immediately.",
        "category": "disease", "crops": ["potato"],
    },
    {
        "text": "Potato calendar Punjab: Autumn crop sowing Sep 15 - Oct 31. Spring crop Jan 15 - Feb 28. Harvest after 90-100 days. Varieties: Desiree (red skin, popular), Cardinal, Diamant, Sante. Seed rate: 600-800kg/acre (whole seed) or 400-500kg (cut seed).",
        "category": "calendar", "crops": ["potato"],
    },
    {
        "text": "Potato fertilizer: DAP 75kg/acre at planting + Urea 75kg/acre (split: 50kg at planting, 25kg at earthing up). SOP 50kg/acre for tuber quality. Farmyard manure 2-3 trolleys/acre mixed 2 weeks before planting.",
        "category": "fertilizer", "crops": ["potato"],
    },

    # ── Tomato ──
    {
        "text": "Tomato leaf curl virus (ToLCV): Upward curling of leaves, stunted growth, no fruit. Spread by whitefly. No chemical cure once infected. Prevention: Use virus-free seedlings, yellow sticky traps (20/acre), control whitefly with Confidor 200SL 200ml/acre, resistant varieties Roma, Sahil.",
        "category": "disease", "crops": ["tomato"],
    },
    {
        "text": "Tomato early blight (Alternaria solani): Concentric ring-shaped brown spots (target board pattern) on lower leaves, moves upward. Treatment: Antracol 70WP 500g/acre or Score 250EC 300ml/acre every 10-14 days. Remove and destroy infected lower leaves. Stake plants for air circulation.",
        "category": "disease", "crops": ["tomato"],
    },
    {
        "text": "Tomato fruit borer (Helicoverpa): Larvae bore into fruits causing direct loss. Treatment: Coragen 20SC 60ml/acre or Emamectin Benzoate 200ml/acre. Pheromone traps 5/acre for monitoring. Neem oil 5ml/liter as deterrent.",
        "category": "pest", "crops": ["tomato"],
    },
    {
        "text": "Tomato calendar: Nursery sowing Punjab — Autumn July-Aug, transplant Aug-Sep. Spring nursery Dec-Jan, transplant Feb-March. Seed rate: 100-150g for 1 acre nursery. Harvest starts 60-70 days after transplanting.",
        "category": "calendar", "crops": ["tomato"],
    },

    # ── Maize ──
    {
        "text": "Maize fall armyworm (Spodoptera frugiperda): Invasive pest devastating maize. Larvae eat leaves leaving ragged holes, feed in whorl. Treatment: Emamectin Benzoate 1.9EC 200ml/acre or Chlorantraniliprole 18.5SC (Coragen) 60ml/acre. Scout when plants 2-4 weeks old. Apply in evening when larvae are active.",
        "category": "pest", "crops": ["maize"],
    },
    {
        "text": "Maize stem borer (Chilo partellus): Dead heart in young plants (central leaf wilts and dies). Treatment: Furadan 3G granules 8kg/acre applied in leaf whorl. Or Chlorpyrifos 20EC 500ml/acre drench. Critical period: 2-5 weeks after emergence.",
        "category": "pest", "crops": ["maize"],
    },
    {
        "text": "Maize calendar Punjab: Spring sowing Jan 15 - Feb 28 (fodder + grain). Autumn/Kharif sowing July 1 - Aug 15. Hybrid varieties: Pioneer 30Y87, Syngenta NK-6240, DK-919. Seed rate: 8-10kg/acre. Row spacing 30 inches.",
        "category": "calendar", "crops": ["maize"],
    },

    # ── General / Cross-crop ──
    {
        "text": "Neem oil organic pesticide: Effective against aphids, whitefly, mealybugs, jassids, and mites. Dosage: 5ml per liter water, spray every 7-10 days. Acts as repellent and growth regulator. Cost 500-800 PKR/liter. Safe for beneficial insects after 24 hours. USDA organic certified.",
        "category": "general", "crops": [],
    },
    {
        "text": "Soil testing services Pakistan: Free via Kissan Card at government labs in Lahore (AARI), Faisalabad (UAF), Multan, Rawalpindi, Tandojam (Sindh). Also private labs: FMC, Engro. Test for NPK, pH, EC, Zinc, Boron. Take samples from 6-8 inches depth, 10 spots per field, mix well.",
        "category": "general", "crops": [],
    },
    {
        "text": "Drip irrigation benefits: Saves 40-60% water compared to flood irrigation. 20-30% yield increase. Ideal for vegetables, orchards, cotton. Punjab government provides 60% subsidy through agriculture department. Contact district agriculture office. Cost: 60,000-80,000 PKR/acre (before subsidy).",
        "category": "irrigation", "crops": [],
    },
    {
        "text": "DAP fertilizer (18-46-0): Primary phosphorus source. Apply at sowing time — phosphorus doesn't move in soil. Current price ~13500 PKR/50kg bag. Subsidized via Kissan Card — subsidy amount varies. Store in dry place. Check for adulteration: genuine DAP dissolves in water leaving no residue.",
        "category": "fertilizer", "crops": [],
    },
    {
        "text": "Urea fertilizer (46-0-0): Primary nitrogen source. Always split-apply — never apply full dose at once. Store away from moisture. Current price ~2500 PKR/50kg bag. Apply when soil is moist. Do not broadcast on dry soil — nitrogen lost to atmosphere. Deep placement increases efficiency 20%.",
        "category": "fertilizer", "crops": [],
    },
    {
        "text": "SOP (Sulphate of Potash 0-0-50): Essential for fruit quality, disease resistance, and drought tolerance. Critical for cotton (boll quality), potato (tuber firmness), fruits. Dose: 25-50kg/acre depending on crop. Price ~9000 PKR/50kg bag. Apply at planting or first irrigation.",
        "category": "fertilizer", "crops": [],
    },
    {
        "text": "Onion price trends Pakistan: Prices peak March-April (gap between Rabi harvest ending and new crop) and July-August (between seasons). Best selling time for stored onion: April-May. Storage in ventilated sheds (mutti system) keeps onion 2-3 months. Major mandis: Lahore, Faisalabad, Multan, Hyderabad.",
        "category": "market", "crops": ["onion"],
    },
    {
        "text": "Mango malformation disease: Bunchy top of inflorescence, no normal flowering/fruiting. Caused by Fusarium mango. No complete cure. Cut affected panicles/branches 15cm below infection point and burn. Spray NAA (Naphthalene Acetic Acid) 200ppm in October. Deblossom affected trees one season.",
        "category": "disease", "crops": ["mango"],
    },
    {
        "text": "Citrus canker (Xanthomonas citri): Raised corky lesions surrounded by oily halo on leaves, fruit, and twigs. Spread by wind-driven rain. Treatment: Copper Oxychloride 50WP 500g per 100L water. Prune and burn infected branches. Spray after every rain during monsoon. Windbreaks reduce spread.",
        "category": "disease", "crops": ["citrus"],
    },
    {
        "text": "Banana bunchy top virus (BBTV): Leaves bunch at top, dark green streaks on petioles, plant stunted, no fruit. Spread by banana aphid (Pentalonia nigronervosa). No cure — uproot entire plant including corm, bury or burn. Control aphids with Imidacloprid. Use tissue culture virus-free planting material.",
        "category": "disease", "crops": ["banana"],
    },
    {
        "text": "Kissan Card Pakistan: Government subsidy card for farmers. Benefits: subsidized fertilizer (up to 50% off), free soil testing, market price SMS alerts, tractor subsidy program, crop insurance. Apply at local agriculture office with CNIC and land documents (Fard). Processing time 2-4 weeks.",
        "category": "general", "crops": [],
    },
    {
        "text": "Crop insurance Pakistan (Fasal Beema): Government-backed crop insurance against natural disasters (flood, drought, hailstorm, pest attack). Premium subsidized 50% by government. Available through State Bank partner banks. Coverage: Rs 20,000-50,000 per acre depending on crop. Register via Kissan Card.",
        "category": "general", "crops": [],
    },
    {
        "text": "Seed treatment importance: Treating seeds before sowing prevents soil-borne and seed-borne diseases. Common treatments: Vitavax (Carboxin + Thiram) 2.5g/kg for wheat smut; Mancozeb 3g/kg for general protection; Imidacloprid 5ml/kg for early pest protection. Mix seed thoroughly, dry in shade.",
        "category": "general", "crops": [],
    },
    {
        "text": "Zinc deficiency is widespread in Pakistani soils. Symptoms: Yellowing between leaf veins, stunted growth, small leaves (khaira disease in rice). Treatment: Zinc Sulphate 33% at 5kg/acre soil application or 0.5% foliar spray (500g in 100L water). Critical for rice, wheat, maize, cotton.",
        "category": "fertilizer", "crops": [],
    },
    {
        "text": "Boron deficiency causes hollow stem in wheat, boll drop in cotton, cracked fruits in tomato. Treatment: Borax 2-3kg/acre soil application or Solubor 0.5kg/acre foliar spray at flowering. Cost effective — prevents significant yield loss.",
        "category": "fertilizer", "crops": [],
    },
]


# ═══════════════════════════════════════════
# TF-IDF ENGINE
# ═══════════════════════════════════════════

class TFIDFEngine:
    """Lightweight TF-IDF scoring without any ML libraries"""

    def __init__(self, documents: List[Document]):
        self.docs = documents
        self.N = len(documents)
        self.idf: Dict[str, float] = {}
        self._build_idf()

    def _build_idf(self):
        """Pre-compute IDF for all terms"""
        df: Dict[str, int] = defaultdict(int)
        for doc in self.docs:
            for token in doc.token_set:
                df[token] += 1
        for term, count in df.items():
            self.idf[term] = math.log((self.N + 1) / (count + 1)) + 1.0

    def score(self, query_tokens: set, doc: Document) -> float:
        """BM25-inspired scoring"""
        k1 = 1.5
        b = 0.75
        avg_dl = sum(len(d.tokens) for d in self.docs) / max(self.N, 1)
        dl = len(doc.tokens)

        score = 0.0
        token_counts = defaultdict(int)
        for t in doc.tokens:
            token_counts[t] += 1

        for term in query_tokens:
            if term not in doc.token_set:
                continue
            tf = token_counts[term]
            idf = self.idf.get(term, 1.0)
            tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / max(avg_dl, 1)))
            score += idf * tf_norm

        return score


# ═══════════════════════════════════════════
# RAG SERVICE
# ═══════════════════════════════════════════

class RAGService:
    def __init__(self):
        self._initialized = False
        self._docs: List[Document] = []
        self._engine: Optional[TFIDFEngine] = None
        self._cache: Dict[str, str] = {}  # query hash → result
        self._max_cache = 200

    async def initialize(self):
        if self._initialized:
            return

        logger.info("📚 Building advanced knowledge base...")

        for entry in RAW_KNOWLEDGE:
            self._docs.append(Document(
                text=entry["text"],
                category=entry["category"],
                crops=entry["crops"],
            ))

        self._engine = TFIDFEngine(self._docs)

        logger.info(
            f"✅ Knowledge base ready — {len(self._docs)} documents, "
            f"{len(self._engine.idf)} unique terms, "
            f"TF-IDF indexed (instant!)"
        )
        self._initialized = True

    async def query(
        self,
        query: str,
        top_k: int = 5,
        filter_category: Optional[str] = None,
        filter_crop: Optional[str] = None,
    ) -> str:
        if not self._initialized:
            await self.initialize()

        # ── Cache check ──
        cache_key = f"{query}|{filter_category}|{filter_crop}|{top_k}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # ── Tokenize + expand query ──
        raw_tokens = tokenize(query)
        expanded = expand_query(raw_tokens)

        # ── Filter documents ──
        candidates = self._docs
        if filter_category:
            cat = filter_category.lower()
            candidates = [d for d in candidates if d.category == cat]
        if filter_crop:
            crop_lower = filter_crop.lower()
            # Expand crop name via synonyms
            crop_terms = {crop_lower}
            if crop_lower in _SYNONYM_MAP:
                crop_terms.add(_SYNONYM_MAP[crop_lower])
            if crop_lower in SYNONYMS:
                crop_terms.update(SYNONYMS[crop_lower])
            candidates = [
                d for d in candidates
                if not d.crops or any(c in crop_terms for c in d.crops)
            ]
            # If too few after filtering, include general docs
            if len(candidates) < 3:
                general = [d for d in self._docs if not d.crops]
                candidates = candidates + general

        # If no candidates after filtering, use all
        if not candidates:
            candidates = self._docs

        # ── Score with TF-IDF ──
        scored: List[Tuple[float, Document]] = []
        for doc in candidates:
            base_score = self._engine.score(expanded, doc) if self._engine else 0

            # ── Bonus: crop match ──
            if filter_crop:
                crop_lower = filter_crop.lower()
                if crop_lower in doc.token_set or any(c == crop_lower for c in doc.crops):
                    base_score *= 1.5

            # ── Bonus: category match ──
            if filter_category and doc.category == filter_category.lower():
                base_score *= 1.3

            # ── Bonus: multi-word phrase match ──
            query_lower = query.lower()
            if len(raw_tokens) >= 2:
                bigrams = [f"{raw_tokens[i]} {raw_tokens[i+1]}" for i in range(len(raw_tokens)-1)]
                for bg in bigrams:
                    if bg in doc.text.lower():
                        base_score += 2.0

            if base_score > 0:
                scored.append((base_score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_docs = [doc.text for _, doc in scored[:top_k]]

        # Fallback if nothing matched
        if not top_docs:
            top_docs = [d.text for d in self._docs[:3]]

        result = "\n---\n".join(top_docs)

        # ── Cache result ──
        if len(self._cache) >= self._max_cache:
            # Evict oldest
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[cache_key] = result

        return result

    def get_stats(self) -> Dict:
        return {
            "total_documents": len(self._docs),
            "unique_terms": len(self._engine.idf) if self._engine else 0,
            "cache_size": len(self._cache),
            "categories": list(set(d.category for d in self._docs)),
            "crops_covered": list(set(c for d in self._docs for c in d.crops)),
        }


rag_service = RAGService()