import io
from typing import Dict
from loguru import logger

TORCH_AVAILABLE = False
try:
    import torch
    import torch.nn as nn
    from torchvision import models, transforms
    from PIL import Image
    TORCH_AVAILABLE = True
    logger.info("✅ PyTorch available")
except ImportError:
    logger.warning("⚠️ PyTorch not available — Vision AI fallback")
    try:
        from PIL import Image
    except ImportError:
        pass


class CropDiseaseClassifier:
    DISEASE_CLASSES = [
        "wheat_leaf_rust", "wheat_stem_rust", "wheat_yellow_rust",
        "wheat_powdery_mildew", "wheat_septoria", "wheat_healthy",
        "rice_blast", "rice_brown_spot", "rice_leaf_blight", "rice_healthy",
        "cotton_bacterial_blight", "cotton_curl_virus",
        "cotton_fusarium_wilt", "cotton_healthy",
        "sugarcane_red_rot", "sugarcane_smut", "sugarcane_healthy",
        "maize_northern_leaf_blight", "maize_common_rust",
        "maize_gray_leaf_spot", "maize_healthy",
        "potato_early_blight", "potato_late_blight", "potato_healthy",
        "tomato_bacterial_spot", "tomato_early_blight",
        "tomato_late_blight", "tomato_leaf_mold",
        "tomato_septoria_leaf_spot", "tomato_target_spot",
        "tomato_yellow_leaf_curl", "tomato_mosaic_virus", "tomato_healthy",
    ]

    URDU_NAMES = {
        "wheat_leaf_rust": "گندم کی پتی کا زنگ",
        "wheat_stem_rust": "گندم کے تنے کا زنگ",
        "wheat_yellow_rust": "گندم کا پیلا زنگ",
        "wheat_powdery_mildew": "گندم کی سفید پھپھوندی",
        "wheat_septoria": "گندم کا سیپٹوریا",
        "wheat_healthy": "صحت مند گندم",
        "rice_blast": "چاول کا بلاسٹ",
        "rice_brown_spot": "چاول کا بھورا دھبہ",
        "rice_leaf_blight": "چاول کی پتی کا جھلساؤ",
        "rice_healthy": "صحت مند چاول",
        "cotton_bacterial_blight": "کپاس کا بیکٹیریل بلائٹ",
        "cotton_curl_virus": "کپاس کا پتا مروڑ وائرس",
        "cotton_fusarium_wilt": "کپاس کا مرجھاؤ",
        "cotton_healthy": "صحت مند کپاس",
        "sugarcane_red_rot": "گنے کی لال سڑاند",
        "sugarcane_smut": "گنے کا کنگیارا",
        "sugarcane_healthy": "صحت مند گنا",
        "maize_northern_leaf_blight": "مکئی کا پتی جھلساؤ",
        "maize_common_rust": "مکئی کا زنگ",
        "maize_gray_leaf_spot": "مکئی کا سرمئی دھبہ",
        "maize_healthy": "صحت مند مکئی",
        "potato_early_blight": "آلو کا اگیتا جھلساؤ",
        "potato_late_blight": "آلو کا پچھیتا جھلساؤ",
        "potato_healthy": "صحت مند آلو",
        "tomato_bacterial_spot": "ٹماٹر کا بیکٹیریل دھبہ",
        "tomato_early_blight": "ٹماٹر کا اگیتا جھلساؤ",
        "tomato_late_blight": "ٹماٹر کا پچھیتا جھلساؤ",
        "tomato_leaf_mold": "ٹماٹر کی پھپھوندی",
        "tomato_septoria_leaf_spot": "ٹماٹر کا سیپٹوریا",
        "tomato_target_spot": "ٹماٹر کا ٹارگٹ اسپاٹ",
        "tomato_yellow_leaf_curl": "ٹماٹر کا پیلا مروڑ",
        "tomato_mosaic_virus": "ٹماٹر کا موزیک وائرس",
        "tomato_healthy": "صحت مند ٹماٹر",
        "unknown": "نامعلوم",
    }

    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.use_torch = TORCH_AVAILABLE
        if self.use_torch:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ])

    def load_model(self):
        if not self.use_torch:
            return
        try:
            n = len(self.DISEASE_CLASSES)
            self.model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
            self.model.fc = nn.Sequential(
                nn.Dropout(0.3), nn.Linear(self.model.fc.in_features, 512),
                nn.ReLU(), nn.Dropout(0.2), nn.Linear(512, n),
            )
            try:
                sd = torch.load(self.model_path, map_location=self.device, weights_only=True)
                self.model.load_state_dict(sd)
                logger.info("✅ Trained model loaded")
            except FileNotFoundError:
                logger.warning("⚠️ No trained weights — demo mode")
            self.model.to(self.device)
            self.model.eval()
        except Exception as e:
            logger.error(f"Model load failed: {e}")
            self.use_torch = False

    def predict(self, image_bytes: bytes) -> Dict:
        if not self.use_torch:
            return {
                "predicted_class": "unknown", "confidence": 0.0,
                "top_3_predictions": [{"disease": "unknown", "disease_urdu": "نامعلوم", "confidence": 0.0}],
                "urdu_name": "Vision AI سے تشخیص ہوگی", "method": "vision_ai_pending",
            }
        if self.model is None:
            self.load_model()
        if not self.use_torch:
            return self.predict(image_bytes)  # Will hit fallback above
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            tensor = self.transform(image).unsqueeze(0).to(self.device)
            with torch.no_grad():
                outputs = self.model(tensor)
                probs = torch.nn.functional.softmax(outputs, dim=1)
                top_probs, top_idx = torch.topk(probs, k=3)
            top_probs = top_probs.cpu().numpy()[0]
            top_idx = top_idx.cpu().numpy()[0]
            predicted = self.DISEASE_CLASSES[top_idx[0]]
            top_3 = [
                {"disease": self.DISEASE_CLASSES[idx],
                 "disease_urdu": self.URDU_NAMES.get(self.DISEASE_CLASSES[idx], ""),
                 "confidence": round(float(p), 4)}
                for idx, p in zip(top_idx, top_probs)
            ]
            return {
                "predicted_class": predicted, "confidence": round(float(top_probs[0]), 4),
                "top_3_predictions": top_3,
                "urdu_name": self.URDU_NAMES.get(predicted, predicted),
                "method": "ResNet50_CNN",
            }
        except Exception as e:
            logger.error(f"CNN predict failed: {e}")
            return {
                "predicted_class": "unknown", "confidence": 0.0,
                "top_3_predictions": [{"disease": "unknown", "disease_urdu": "نامعلوم", "confidence": 0.0}],
                "urdu_name": "نامعلوم", "method": "vision_ai_pending",
            }


classifier = CropDiseaseClassifier("app/data/trained_models/disease_classifier_v1.pth")