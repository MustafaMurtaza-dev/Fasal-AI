from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from loguru import logger
from app.services.market_prediction_service import market_service

router = APIRouter()

@router.get("/market/predict/{crop}")
async def predict(crop: str, days: int = Query(7, ge=1, le=30), mandi: Optional[str] = None):
    try: return await market_service.predict_price(crop, days, mandi)
    except ValueError as e: raise HTTPException(400, str(e))
    except Exception as e: raise HTTPException(500, str(e))

@router.get("/market/current/{crop}")
async def current(crop: str):
    try: return await market_service.get_current_price(crop)
    except Exception as e: raise HTTPException(500, str(e))

@router.get("/market/trends/{crop}")
async def trends(crop: str, period: str = Query("30d")):
    try: return await market_service.get_trends(crop, period)
    except Exception as e: raise HTTPException(500, str(e))

@router.get("/market/sell-advice/{crop}")
async def sell(crop: str, quantity_kg: float = Query(1000, ge=1)):
    try: return await market_service.get_sell_advice(crop, quantity_kg)
    except Exception as e: raise HTTPException(500, str(e))

@router.get("/market/supported-crops")
async def supported():
    return {"crops": list(market_service.BASE_PRICES.keys()), "prices": market_service.BASE_PRICES}