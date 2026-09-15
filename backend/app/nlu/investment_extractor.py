import re
from datetime import date
from typing import Optional, Dict, Any

ASSET_TYPE_KEYWORDS = {
    "MUTUAL_FUND": ["mutual fund", "mf", "fund", "sip", "sbi mutual"],
    "INDEX_FUND": ["index fund", "nifty", "etf", "niftybees"],
    "GOLD": ["gold", "goldbees", "sovereign gold"],
    "BOND": ["bond", "g-sec", "debenture"],
    "CRYPTO": ["bitcoin", "btc", "eth", "crypto"],
    "STOCK": ["shares", "share", "stock", "equity"]
}

TICKER_MAP = {
    "TCS": ("TCS.NS", "Tata Consultancy Services", "STOCK"),
    "INFY": ("INFY.NS", "Infosys Limited", "STOCK"),
    "RELIANCE": ("RELIANCE.NS", "Reliance Industries", "STOCK"),
    "HDFCBANK": ("HDFCBANK.NS", "HDFC Bank Limited", "STOCK"),
    "ICICIBANK": ("ICICIBANK.NS", "ICICI Bank Limited", "STOCK"),
    "TATAMOTORS": ("TATAMOTORS.NS", "Tata Motors Limited", "STOCK"),
    "GOLD": ("GOLDBEES.NS", "Nippon India ETF Gold BeES", "GOLD"),
    "INDEX FUND": ("NIFTYBEES.NS", "Nippon India ETF Nifty 50 BeES", "INDEX_FUND"),
    "NIFTY": ("NIFTYBEES.NS", "Nippon India ETF Nifty 50 BeES", "INDEX_FUND"),
    "AAPL": ("AAPL", "Apple Inc.", "STOCK"),
    "MSFT": ("MSFT", "Microsoft Corporation", "STOCK")
}

def extract_investment(text: str) -> Optional[Dict[str, Any]]:
    """
    Parses natural language investment inputs into structured transaction candidates.
    Supports confirmation preview and edit before execution.
    """
    if not text or not text.strip():
        return None

    clean_text = text.strip()
    text_lower = clean_text.lower()

    # Determine BUY vs SELL
    tx_type = "BUY"
    if any(w in text_lower for w in ["sold", "sell", "redeemed", "exit"]):
        tx_type = "SELL"
    elif "sip" in text_lower and any(w in text_lower for w in ["start", "started", "invested"]):
        tx_type = "BUY"

    # Determine Asset Type
    asset_type = "STOCK"
    for at, keywords in ASSET_TYPE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            asset_type = at
            break

    # Extract Quantity and Price
    # Pattern 1: "bought 10 TCS shares at ₹3,200 each" or "sold 5 TCS shares at 3500"
    qty_price_match = re.search(
        r"(?:bought|buy|sold|sell|purchased|invested in)?\s*(\d+(?:\.\d+)?)\s*(?:shares?|units?|stocks?|g|gms?)?\s*(?:of\s+)?([A-Za-z0-9\s]+?)\s*(?:shares?|units?|stocks?)?\s*(?:at|@|for)?\s*(?:₹|rs\.?|inr)?\s*([0-9,]+(?:\.\d+)?)\s*(?:each|per\s+unit|per\s+share)?",
        clean_text,
        re.IGNORECASE
    )

    quantity = None
    price = None
    asset_name = None

    if qty_price_match:
        try:
            potential_qty = float(qty_price_match.group(1))
            potential_name = qty_price_match.group(2).strip()
            potential_price = float(qty_price_match.group(3).replace(",", ""))
            
            # Sanity check on asset name
            if potential_name and not potential_name.lower().startswith("each"):
                quantity = potential_qty
                asset_name = potential_name
                price = potential_price
        except (ValueError, IndexError):
            pass

    # Pattern 2: "invested ₹10,000 in an index fund" or "invested 50000 in gold"
    if not quantity or not price:
        total_match = re.search(
            r"(?:invested|put|contributed|sip of|started a)\s*(?:₹|rs\.?|inr)?\s*([0-9,]+(?:\.\d+)?)\s*(?:in|into)?\s*([A-Za-z0-9\s]+)",
            clean_text,
            re.IGNORECASE
        )
        if total_match:
            try:
                tot_amount = float(total_match.group(1).replace(",", ""))
                cand_name = total_match.group(2).strip()
                # strip filler words
                cand_name = re.sub(r"\b(an|a|the|monthly|regular)\b", "", cand_name, flags=re.IGNORECASE).strip()
                if cand_name:
                    asset_name = cand_name
                    quantity = 1.0
                    price = tot_amount
            except (ValueError, IndexError):
                pass

    if not asset_name:
        # Fallback: check if known tickers are mentioned
        for ticker, info in TICKER_MAP.items():
            if re.search(r"\b" + re.escape(ticker) + r"\b", clean_text, re.IGNORECASE):
                asset_name = info[1]
                break

    if not asset_name:
        return None

    # Clean asset name
    asset_name = re.sub(r"\s*(shares?|units?|stocks?|each)\s*", "", asset_name, flags=re.IGNORECASE).strip()
    asset_name = asset_name.title() if len(asset_name) > 4 else asset_name.upper()

    # Map Symbol
    symbol = asset_name.upper()
    display_name = asset_name
    for key, info in TICKER_MAP.items():
        if key.lower() in asset_name.lower() or asset_name.upper() == key:
            symbol = info[0]
            display_name = info[1]
            asset_type = info[2]
            break

    if not symbol.endswith(".NS") and not symbol.endswith(".BO") and len(symbol) <= 6 and symbol.isalpha():
        # Default Indian equity symbol
        if asset_type == "STOCK":
            symbol = f"{symbol}.NS"

    qty = quantity if quantity is not None else 1.0
    pr = price if price is not None else 0.0
    total = round(qty * pr, 2)

    return {
        "detected_asset": display_name,
        "symbol": symbol,
        "asset_type": asset_type,
        "quantity": qty,
        "price": pr,
        "total_amount": total,
        "transaction_type": tx_type,
        "date": date.today().isoformat(),
        "is_confirmed": False
    }

extract_investment_transaction = extract_investment

