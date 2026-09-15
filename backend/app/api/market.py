from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional
from backend.app.database.neo4j_service import Neo4jService
from backend.app.market.market_data_service import MarketDataService
from backend.app.api.deps import get_current_user_id

router = APIRouter(prefix="/api/market", tags=["Market Intelligence"])
db = Neo4jService()
market_service = MarketDataService()

class WatchlistAddSchema(BaseModel):
    symbol: str = Field(..., description="Asset ticker symbol, e.g. TCS, AAPL")
    name: Optional[str] = Field(None, description="Asset or company name")
    asset_type: Optional[str] = Field("STOCK", description="STOCK, ETF, CRYPTO, COMMODITY")

@router.get("/quote/{symbol}")
def get_asset_quote(symbol: str):
    """
    Returns asset market quote with price, daily change, currency, and provenance tags (LIVE, DELAYED, STALE, UNAVAILABLE).
    """
    try:
        quote = market_service.get_quote(symbol)
        return {
            "status": "SUCCESS",
            "quote": quote.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/watchlist")
def get_watchlist(user_id: str = Depends(get_current_user_id)):
    """
    Returns the user's watchlist enriched with latest quotes and change percentages.
    """
    try:
        watchlist_items = db.get_watchlist(user_id)
        symbols = [item["symbol"] for item in watchlist_items if item.get("symbol")]
        quotes = market_service.get_batch_quotes(symbols) if symbols else {}

        enriched = []
        for item in watchlist_items:
            sym = item["symbol"]
            q = quotes.get(sym)
            enriched.append({
                "symbol": sym,
                "name": item.get("name") or sym,
                "asset_type": item.get("asset_type") or "STOCK",
                "price": q.price if q else 0.0,
                "change_percent": q.change_percent if q else 0.0,
                "currency": q.currency if q else "INR",
                "status": q.status if q else "UNAVAILABLE",
                "source": q.source if q else "None",
                "timestamp": q.timestamp if q else None
            })

        return {
            "status": "SUCCESS",
            "watchlist": enriched
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/watchlist")
def add_to_watchlist(payload: WatchlistAddSchema, user_id: str = Depends(get_current_user_id)):
    """
    Adds an asset to the user's watchlist.
    """
    try:
        quote = market_service.get_quote(payload.symbol)
        resolved_name = payload.name or (quote.symbol if quote.status != "UNAVAILABLE" else payload.symbol)
        
        result = db.add_to_watchlist(
            user_id=user_id,
            symbol=payload.symbol,
            name=resolved_name,
            asset_type=payload.asset_type
        )
        return {
            "status": "SUCCESS",
            "item": result,
            "quote": quote.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/watchlist/{symbol}")
def remove_from_watchlist(symbol: str, user_id: str = Depends(get_current_user_id)):
    """
    Removes an asset from the user's watchlist.
    """
    try:
        res = db.remove_from_watchlist(user_id, symbol)
        return {
            "status": "SUCCESS",
            "removed": res.get("removed", False),
            "symbol": symbol
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
def search_assets(query: str = Query(..., min_length=1, description="Asset symbol or keyword")):
    """
    Searches available assets across NSE, BSE, US markets, and ETFs.
    """
    try:
        results = market_service.search_assets(query)
        return {
            "status": "SUCCESS",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
