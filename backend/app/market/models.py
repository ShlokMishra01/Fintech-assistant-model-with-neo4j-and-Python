from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class MarketStatus(str, Enum):
    LIVE = "LIVE"
    DELAYED = "DELAYED"
    STALE = "STALE"
    USER_ENTERED = "USER_ENTERED"
    UNAVAILABLE = "UNAVAILABLE"

class MarketQuote(BaseModel):
    symbol: str
    name: str = "Unknown Asset"
    asset_type: str = "STOCK"
    currency: str = "INR"
    current_price: Optional[float] = None
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    market_timestamp: Optional[str] = None
    source: str = "OpenBB"
    status: MarketStatus = MarketStatus.LIVE

    @property
    def price(self) -> Optional[float]:
        return self.current_price

    @property
    def timestamp(self) -> Optional[str]:
        return self.market_timestamp

    def to_dict(self) -> dict:
        d = self.model_dump()
        d["price"] = self.current_price
        d["timestamp"] = self.market_timestamp
        return d

class WatchlistItem(BaseModel):
    symbol: str
    name: Optional[str] = None
    asset_type: str = "STOCK"
    added_at: Optional[str] = None
