"""
📈 Market Prediction Service — Pakistani Crop Market Intelligence
All prices in PKR per 40kg (1 maund) — the standard Pakistani unit
Integrated with LLM client for AI-powered analysis
"""
import random
import math
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from loguru import logger
from app.ai.llm_client import llm_client, ModelTier
from app.ai.prompt_templates import SYSTEM_PROMPT, MARKET_ANALYSIS_PROMPT
from app.models.schemas import (
    PricePredictionResponse,
    PricePrediction,
    MarketTrendResponse,
)


class MarketPredictionService:
    """AI-powered market predictions for Pakistani crops"""

    # Base prices in PKR per 40kg (maund) — 2024-25 season
    BASE_PRICES: Dict[str, Dict[str, Any]] = {
        "wheat": {
            "price_pkr": 3900,
            "support_price": 3900,
            "unit": "40 kg",
            "season": "Rabi",
            "peak_months": [3, 4],
            "low_months": [10, 11],
            "volatility": 0.03,
        },
        "rice": {
            "price_pkr": 4500,
            "support_price": 4000,
            "unit": "40 kg",
            "season": "Kharif",
            "peak_months": [5, 6],
            "low_months": [11, 12],
            "volatility": 0.05,
        },
        "cotton": {
            "price_pkr": 9000,
            "support_price": 8000,
            "unit": "40 kg",
            "season": "Kharif",
            "peak_months": [3, 4],
            "low_months": [10, 11],
            "volatility": 0.07,
        },
        "sugarcane": {
            "price_pkr": 425,
            "support_price": 425,
            "unit": "40 kg",
            "season": "Annual",
            "peak_months": [9, 10],
            "low_months": [1, 2],
            "volatility": 0.02,
        },
        "maize": {
            "price_pkr": 2200,
            "support_price": None,
            "unit": "40 kg",
            "season": "Both",
            "peak_months": [5, 6],
            "low_months": [10, 11],
            "volatility": 0.04,
        },
        "potato": {
            "price_pkr": 2000,
            "support_price": None,
            "unit": "40 kg",
            "season": "Rabi",
            "peak_months": [6, 7, 8],
            "low_months": [1, 2, 3],
            "volatility": 0.10,
        },
        "onion": {
            "price_pkr": 3500,
            "support_price": None,
            "unit": "40 kg",
            "season": "Rabi",
            "peak_months": [3, 4, 7, 8],
            "low_months": [5, 6],
            "volatility": 0.15,
        },
        "tomato": {
            "price_pkr": 4000,
            "support_price": None,
            "unit": "40 kg",
            "season": "Both",
            "peak_months": [7, 8],
            "low_months": [12, 1],
            "volatility": 0.12,
        },
    }

    # ─── Mandi price adjustments ───────────────────────────────
    MANDI_ADJUSTMENTS: Dict[str, float] = {
        "lahore": 1.02,
        "faisalabad": 1.00,
        "multan": 0.98,
        "karachi": 1.05,
        "rawalpindi": 1.01,
        "peshawar": 0.97,
        "hyderabad": 0.96,
        "quetta": 0.95,
        "bahawalpur": 0.97,
        "sahiwal": 0.99,
    }

    # ─── Seasonal Factor ───────────────────────────────────────
    def _get_seasonal_factor(self, crop_info: Dict, month: int) -> float:
        """Calculate seasonal price adjustment"""
        if month in crop_info.get("peak_months", []):
            return 1.0 + random.uniform(0.05, 0.15)
        elif month in crop_info.get("low_months", []):
            return 1.0 - random.uniform(0.05, 0.12)
        return 1.0 + random.uniform(-0.03, 0.03)

    # ─── Trend Generator ──────────────────────────────────────
    def _generate_predictions(
        self,
        base_price: float,
        days: int,
        volatility: float,
        crop_info: Dict,
    ) -> List[PricePrediction]:
        """Generate realistic price predictions using PricePrediction schema"""
        predictions: List[PricePrediction] = []
        current = base_price
        today = datetime.now()

        # Overall trend factor
        trend_factor = random.uniform(-0.02, 0.04)

        for i in range(1, days + 1):
            future_date = today + timedelta(days=i)
            future_month = future_date.month

            # Seasonal adjustment
            seasonal = self._get_seasonal_factor(crop_info, future_month)

            # Daily random walk with mean reversion
            daily_change = random.gauss(0, volatility * base_price * 0.01)
            mean_pull = (base_price * seasonal - current) * 0.05
            trend_pull = trend_factor * i * base_price / days

            current = current + daily_change + mean_pull + trend_pull * 0.01

            # Clamp to reasonable range
            current = max(base_price * 0.5, min(base_price * 2.0, current))

            confidence_pct = max(0.60, 0.95 - (i * 0.01))

            predictions.append(
                PricePrediction(
                    date=future_date.strftime("%Y-%m-%d"),
                    predicted_price_pkr=round(current),
                    confidence_interval_low=round(current * (1 - 0.08)),
                    confidence_interval_high=round(current * (1 + 0.08)),
                    confidence=round(confidence_pct, 2),
                )
            )

        return predictions

    # ─── Trend Determination ──────────────────────────────────
    def _determine_trend(self, predictions: List[PricePrediction]) -> str:
        if len(predictions) < 2:
            return "stable"
        first_3 = sum(p.predicted_price_pkr for p in predictions[:3]) / min(
            3, len(predictions)
        )
        last_3 = sum(p.predicted_price_pkr for p in predictions[-3:]) / min(
            3, len(predictions)
        )
        if last_3 > first_3 * 1.02:
            return "increasing"
        elif last_3 < first_3 * 0.98:
            return "decreasing"
        return "stable"

    # ─── Best Sell Window ─────────────────────────────────────
    def _get_best_sell_window(self, predictions: List[PricePrediction]) -> str:
        if not predictions:
            return "No prediction available"
        best = max(predictions, key=lambda x: x.predicted_price_pkr)
        return (
            f"{best.date} (Expected: PKR {best.predicted_price_pkr:,}/40kg)"
        )

    # ─── Fallback Analysis ────────────────────────────────────
    def _generate_fallback_analysis(
        self,
        crop: str,
        trend: str,
        current_price: float,
        predictions: List[PricePrediction],
        crop_info: Dict,
    ) -> str:
        """Generate analysis when LLM is unavailable"""
        current_month = datetime.now().month
        crop_title = crop.capitalize()

        # Trend text
        if trend == "increasing":
            trend_text = f"**{crop_title}** prices show an **upward trend** over the forecast period."
        elif trend == "decreasing":
            trend_text = f"**{crop_title}** prices are expected to **decline slightly** in the coming days."
        else:
            trend_text = f"**{crop_title}** prices are expected to remain **relatively stable**."

        # Seasonal context
        if current_month in crop_info.get("peak_months", []):
            season_text = f"Currently in **peak price season** for {crop_title}. Good time to sell if you have stock."
        elif current_month in crop_info.get("low_months", []):
            season_text = f"Currently in **low season** for {crop_title}. Consider storing if you can — prices typically improve later."
        else:
            season_text = f"Currently in a **normal pricing period** for {crop_title}."

        # Support price context
        support = crop_info.get("support_price")
        support_text = ""
        if support:
            if current_price < support:
                support_text = (
                    f"\n\n**Government support price** is PKR {support:,}/40kg — "
                    f"market price is below support price. Consider selling through PASSCO/government channels."
                )
            else:
                support_text = (
                    f"\n\n**Government support price** is PKR {support:,}/40kg — "
                    f"market price is above this level."
                )

        # Price range
        if predictions:
            prices = [p.predicted_price_pkr for p in predictions]
            range_text = (
                f"\n\n**Expected price range:** PKR {min(prices):,} — PKR {max(prices):,} "
                f"per 40kg over the forecast period."
            )
        else:
            range_text = ""

        # Recommendation
        is_peak = current_month in crop_info.get("peak_months", [])
        if trend == "increasing" or is_peak:
            rec = "Sell now or within the next few days while prices are favorable."
        else:
            rec = "Consider holding stock if storage conditions are good — prices may improve."

        return (
            f"{trend_text}\n\n{season_text}{support_text}{range_text}\n\n"
            f"**Recommendation:** {rec}"
        )

    # ═══════════════════════════════════════════════════════════
    #  MAIN: predict_price
    # ═══════════════════════════════════════════════════════════
    async def predict_price(
        self,
        crop: str,
        days_ahead: int = 7,
        mandi: Optional[str] = None,
    ) -> PricePredictionResponse:
        """Main prediction endpoint — returns PricePredictionResponse"""
        crop = crop.lower().strip()

        if crop not in self.BASE_PRICES:
            raise ValueError(
                f"'{crop}' not supported. Available: {list(self.BASE_PRICES.keys())}"
            )

        crop_info = self.BASE_PRICES[crop]
        base_price = crop_info["price_pkr"]
        volatility = crop_info["volatility"]

        # Apply seasonal factor to current price
        current_month = datetime.now().month
        seasonal = self._get_seasonal_factor(crop_info, current_month)
        current_price = round(base_price * seasonal)

        # Mandi adjustment
        if mandi:
            mandi_factor = self.MANDI_ADJUSTMENTS.get(mandi.lower(), 1.0)
            current_price = round(current_price * mandi_factor)

        # Generate predictions
        predictions = self._generate_predictions(
            current_price, days_ahead, volatility, crop_info
        )

        # Determine trend
        trend = self._determine_trend(predictions)

        # Best sell window
        best_sell = self._get_best_sell_window(predictions)

        # ── AI Analysis (with LLM fallback) ──
        try:
            pd_data = [
                {"date": p.date, "price": p.predicted_price_pkr}
                for p in predictions
            ]
            prompt = MARKET_ANALYSIS_PROMPT.format(
                crop=crop,
                current_price=current_price,
                price_data=pd_data,
                location=mandi or "Punjab",
            )
            analysis_json = await llm_client.generate_json(
                SYSTEM_PROMPT, prompt, tier=ModelTier.PRIMARY
            )
            ai_text = analysis_json.get(
                "analysis",
                analysis_json.get("answer", ""),
            )
            llm_best_sell = analysis_json.get("best_sell_window")
            if llm_best_sell:
                best_sell = llm_best_sell

            # If LLM returned empty text, use fallback
            if not ai_text or len(ai_text.strip()) < 10:
                raise ValueError("LLM returned empty analysis")

        except Exception as e:
            logger.warning(f"Market AI failed, using fallback: {e}")
            ai_text = self._generate_fallback_analysis(
                crop, trend, current_price, predictions, crop_info
            )

        return PricePredictionResponse(
            crop=crop,
            current_price_pkr=current_price,
            currency="PKR",
            unit="per 40 kg (1 maund)",
            support_price_pkr=crop_info.get("support_price"),
            mandi=mandi or "Average (All Pakistan)",
            season=crop_info["season"],
            predictions=predictions,
            trend=trend,
            ai_analysis=ai_text,
            best_sell_window=best_sell,
            forecast_days=days_ahead,
            generated_at=datetime.now().isoformat(),
            disclaimer=(
                "Predictions are AI-generated estimates. Actual prices may vary. "
                "Consult local mandi rates before selling."
            ),
        )

    # ═══════════════════════════════════════════════════════════
    #  get_current_price
    # ═══════════════════════════════════════════════════════════
    async def get_current_price(self, crop: str) -> Dict:
        """Get current market price for a crop"""
        crop = crop.lower().strip()
        if crop not in self.BASE_PRICES:
            raise ValueError(f"Crop '{crop}' not supported.")

        crop_info = self.BASE_PRICES[crop]
        base = crop_info["price_pkr"]
        current_month = datetime.now().month
        seasonal = self._get_seasonal_factor(crop_info, current_month)
        price = round(base * seasonal)

        return {
            "crop": crop,
            "price_pkr_per_40kg": price,
            "current_price_pkr": price,
            "currency": "PKR",
            "unit": "per 40 kg (1 maund)",
            "support_price_pkr": crop_info.get("support_price"),
            "season": crop_info["season"],
            "last_updated": datetime.now().isoformat(),
        }

    # ═══════════════════════════════════════════════════════════
    #  get_trends
    # ═══════════════════════════════════════════════════════════
    async def get_trends(
        self, crop: str, period: str = "30d"
    ) -> MarketTrendResponse:
        """Get historical price trends"""
        crop = crop.lower().strip()
        if crop not in self.BASE_PRICES:
            raise ValueError(f"Crop '{crop}' not supported.")

        crop_info = self.BASE_PRICES[crop]
        base = crop_info["price_pkr"]
        volatility = crop_info["volatility"]

        days_map = {"7d": 7, "14d": 14, "30d": 30, "90d": 90}
        num_days = days_map.get(period, int(period.replace("d", "")))

        history: List[Dict] = []
        price = base * 0.9
        today = datetime.now()

        for i in range(num_days):
            dt = today - timedelta(days=num_days - i)
            month = dt.month
            seasonal = self._get_seasonal_factor(crop_info, month)
            change = random.gauss(base * 0.003, base * volatility * 0.3)
            price += change
            price = max(price, base * 0.5)
            price = min(price, base * 1.8)

            history.append({
                "date": dt.strftime("%Y-%m-%d"),
                "price_pkr": round(price),
                "volume_estimate": round(random.uniform(500, 2000)),
            })

        prices_list = [h["price_pkr"] for h in history]

        return MarketTrendResponse(
            crop=crop,
            period=period,
            currency="PKR",
            unit="per 40 kg",
            historical_prices=history,
            avg_price_pkr=round(sum(prices_list) / len(prices_list)),
            min_price_pkr=min(prices_list),
            max_price_pkr=max(prices_list),
            trend_analysis=(
                f"{crop.capitalize()} fluctuated between PKR {min(prices_list):,} "
                f"and PKR {max(prices_list):,} over {period}."
            ),
            seasonal_patterns=(
                f"Peak months: {crop_info.get('peak_months', [])}, "
                f"Low months: {crop_info.get('low_months', [])}"
            ),
        )

    # ═══════════════════════════════════════════════════════════
    #  get_sell_advice
    # ═══════════════════════════════════════════════════════════
    async def get_sell_advice(
        self, crop: str, quantity_kg: float = 1000
    ) -> Dict:
        """Get smart selling advice"""
        crop = crop.lower().strip()
        if crop not in self.BASE_PRICES:
            raise ValueError(f"Crop '{crop}' not supported.")

        # Get 14-day prediction for sell window analysis
        pred = await self.predict_price(crop, 14)

        crop_info = self.BASE_PRICES[crop]
        current_month = datetime.now().month
        is_peak = current_month in crop_info.get("peak_months", [])
        is_low = current_month in crop_info.get("low_months", [])

        maunds = quantity_kg / 40
        current_price = pred.current_price_pkr
        total_value_now = round(current_price * maunds)

        best_pred = max(
            pred.predictions, key=lambda p: p.predicted_price_pkr
        )
        total_value_wait = round(best_pred.predicted_price_pkr * maunds)

        # Determine urgency and advice
        if is_peak:
            advice = (
                f"**Good time to sell!** {crop.capitalize()} prices are in peak season. "
                f"Current rate PKR {current_price:,}/40kg. "
                f"Your {quantity_kg}kg ({maunds:.1f} maunds) is worth approximately "
                f"**PKR {total_value_now:,}**."
            )
            urgency = "high"
        elif is_low:
            advice = (
                f"**Consider holding** if you have storage. "
                f"{crop.capitalize()} prices are in low season at PKR {current_price:,}/40kg. "
                f"Prices typically improve in coming months."
            )
            urgency = "low"
        else:
            advice = (
                f"**Normal market conditions.** {crop.capitalize()} at PKR {current_price:,}/40kg. "
                f"Your {quantity_kg}kg is worth approximately **PKR {total_value_now:,}**. "
                f"Watch market for better opportunities."
            )
            urgency = "medium"

        return {
            "crop": crop,
            "quantity_kg": quantity_kg,
            "quantity_maund": round(maunds, 1),
            "current_price_per_40kg": current_price,
            "current_price_pkr": current_price,
            "currency": "PKR",
            "unit": "per 40 kg (1 maund)",
            "best_predicted_price": best_pred.predicted_price_pkr,
            "best_sell_date": best_pred.date,
            "potential_revenue_now": total_value_now,
            "potential_revenue_wait": total_value_wait,
            "total_value_pkr": total_value_now,
            "advice": advice,
            "recommendation": pred.ai_analysis,
            "sell_urgency": urgency,
            "is_peak_season": is_peak,
            "trend": pred.trend,
        }


# ── Singleton ──────────────────────────────────────────────
market_service = MarketPredictionService()