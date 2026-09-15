import time
from datetime import datetime
from typing import Optional, Dict, List
from backend.app.market.models import MarketQuote, MarketStatus, WatchlistItem

# In-memory TTL cache: { symbol: (MarketQuote, timestamp) }
_QUOTE_CACHE: Dict[str, tuple[MarketQuote, float]] = {}
CACHE_TTL_SECONDS = 60.0

SYMBOL_ALIASES = {
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "RELIANCE": "RELIANCE.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "TATAMOTORS": "TATAMOTORS.NS",
    "SBIN": "SBIN.NS",
    "WIPRO": "WIPRO.NS",
    "ITC": "ITC.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
    "NIFTY": "^NSEI",
    "NIFTY50": "^NSEI",
    "NIFTYBEES": "NIFTYBEES.NS",
    "GOLDBEES": "GOLDBEES.NS",
    "GOLD": "GOLDBEES.NS",
}

COMMON_CATALOG = [
    {"symbol": "TCS.NS", "display_symbol": "TCS", "name": "Tata Consultancy Services", "asset_type": "STOCK", "currency": "INR"},
    {"symbol": "INFY.NS", "display_symbol": "INFY", "name": "Infosys Limited", "asset_type": "STOCK", "currency": "INR"},
    {"symbol": "RELIANCE.NS", "display_symbol": "RELIANCE", "name": "Reliance Industries", "asset_type": "STOCK", "currency": "INR"},
    {"symbol": "HDFCBANK.NS", "display_symbol": "HDFCBANK", "name": "HDFC Bank Limited", "asset_type": "STOCK", "currency": "INR"},
    {"symbol": "ICICIBANK.NS", "display_symbol": "ICICIBANK", "name": "ICICI Bank Limited", "asset_type": "STOCK", "currency": "INR"},
    {"symbol": "TATAMOTORS.NS", "display_symbol": "TATAMOTORS", "name": "Tata Motors Limited", "asset_type": "STOCK", "currency": "INR"},
    {"symbol": "NIFTYBEES.NS", "display_symbol": "NIFTYBEES", "name": "Nippon India ETF Nifty 50 BeES", "asset_type": "INDEX_FUND", "currency": "INR"},
    {"symbol": "GOLDBEES.NS", "display_symbol": "GOLDBEES", "name": "Nippon India ETF Gold BeES", "asset_type": "GOLD", "currency": "INR"},
    {"symbol": "AAPL", "display_symbol": "AAPL", "name": "Apple Inc.", "asset_type": "STOCK", "currency": "USD"},
    {"symbol": "MSFT", "display_symbol": "MSFT", "name": "Microsoft Corporation", "asset_type": "STOCK", "currency": "USD"},
    {"symbol": "GOOGL", "display_symbol": "GOOGL", "name": "Alphabet Inc.", "asset_type": "STOCK", "currency": "USD"},
]

class MarketDataService:
    """
    Market Data Service wrapping OpenBB with resilient fallbacks and explicit data statuses.
    Ensures normalized, validated market intelligence without propagating provider specifics.
    """

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        clean = (symbol or "").strip().upper()
        if clean in SYMBOL_ALIASES:
            return SYMBOL_ALIASES[clean]
        # If bare ticker with 3-10 alphabets and no dot, check if likely Indian stock
        if clean.isalpha() and 2 <= len(clean) <= 12 and not clean.endswith(".NS") and not clean.endswith(".BO"):
            # Check catalog first
            for item in COMMON_CATALOG:
                if item["display_symbol"] == clean:
                    return item["symbol"]
        return clean

    @classmethod
    def get_quote(cls, symbol: str, fallback_price: Optional[float] = None) -> MarketQuote:
        norm_sym = cls.normalize_symbol(symbol)
        now = time.time()

        # 1. Check TTL cache
        if norm_sym in _QUOTE_CACHE:
            cached_quote, timestamp = _QUOTE_CACHE[norm_sym]
            if (now - timestamp) < CACHE_TTL_SECONDS:
                return cached_quote

        # 2. Try OpenBB primary provider
        quote = cls._fetch_via_openbb(norm_sym)
        
        # 3. Try yfinance fallback provider if OpenBB unavailable
        if quote is None:
            quote = cls._fetch_via_yfinance(norm_sym)

        # 4. If external providers unavailable but user supplied fallback/seed price
        if quote is None and fallback_price is not None and fallback_price > 0:
            quote = MarketQuote(
                symbol=norm_sym,
                name=symbol,
                current_price=round(fallback_price, 2),
                previous_close=round(fallback_price, 2),
                change=0.0,
                change_percent=0.0,
                market_timestamp=datetime.now().isoformat(),
                source="USER_ENTERED / SEED",
                status=MarketStatus.USER_ENTERED
            )

        # 5. Last resort: UNAVAILABLE status (Never invent a fake price)
        if quote is None:
            quote = MarketQuote(
                symbol=norm_sym,
                name=symbol,
                current_price=None,
                previous_close=None,
                change=None,
                change_percent=None,
                market_timestamp=datetime.now().isoformat(),
                source="UNAVAILABLE",
                status=MarketStatus.UNAVAILABLE
            )

        # Cache result
        _QUOTE_CACHE[norm_sym] = (quote, now)
        return quote

    @classmethod
    def _fetch_via_openbb(cls, symbol: str) -> Optional[MarketQuote]:
        try:
            from openbb import obb
            res = obb.equity.price.quote(symbol=symbol, provider="yfinance")
            records = res.to_df().to_dict(orient="records")
            if not records:
                return None
            row = records[0]
            price = row.get("last_price")
            if price is None or price <= 0:
                return None

            prev_close = row.get("prev_close") or price
            change = round(price - prev_close, 2)
            change_pct = round((change / prev_close * 100), 2) if prev_close > 0 else 0.0
            currency = row.get("currency") or ("INR" if symbol.endswith(".NS") else "USD")

            return MarketQuote(
                symbol=symbol,
                name=row.get("name") or symbol,
                asset_type="STOCK",
                currency=currency,
                current_price=round(float(price), 2),
                previous_close=round(float(prev_close), 2),
                change=change,
                change_percent=change_pct,
                market_timestamp=datetime.now().isoformat(),
                source="OpenBB (yfinance provider)",
                status=MarketStatus.LIVE
            )
        except Exception:
            return None

    @classmethod
    def _fetch_via_yfinance(cls, symbol: str) -> Optional[MarketQuote]:
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            price = info.last_price
            if price is None or price <= 0:
                return None

            prev_close = info.previous_close or price
            change = round(price - prev_close, 2)
            change_pct = round((change / prev_close * 100), 2) if prev_close > 0 else 0.0
            currency = info.currency or ("INR" if symbol.endswith(".NS") else "USD")

            return MarketQuote(
                symbol=symbol,
                name=symbol,
                asset_type="STOCK",
                currency=currency,
                current_price=round(float(price), 2),
                previous_close=round(float(prev_close), 2),
                change=change,
                change_percent=change_pct,
                market_timestamp=datetime.now().isoformat(),
                source="yfinance (Direct Fallback)",
                status=MarketStatus.LIVE
            )
        except Exception:
            return None

    @classmethod
    def get_quotes(cls, symbols: List[str]) -> Dict[str, MarketQuote]:
        return {s: cls.get_quote(s) for s in symbols}

    @classmethod
    def get_batch_quotes(cls, symbols: List[str]) -> Dict[str, MarketQuote]:
        return cls.get_quotes(symbols)

    @classmethod
    def search_symbols(cls, query: str) -> List[dict]:
        q = (query or "").strip().lower()
        if not q:
            return COMMON_CATALOG[:8]
        results = []
        for item in COMMON_CATALOG:
            if q in item["symbol"].lower() or q in item["display_symbol"].lower() or q in item["name"].lower():
                results.append(item)
        return results

    @classmethod
    def search_assets(cls, query: str) -> List[dict]:
        return cls.search_symbols(query)
