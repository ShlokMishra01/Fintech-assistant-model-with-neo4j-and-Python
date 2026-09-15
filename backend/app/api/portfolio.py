from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from backend.app.database.neo4j_service import Neo4jService
from backend.app.market.market_data_service import MarketDataService
from backend.app.engine.financial_engine import (
    calculate_portfolio_metrics,
    calculate_net_worth
)
from backend.app.nlu.investment_extractor import extract_investment_transaction
from backend.app.api.deps import get_current_user_id

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])
db = Neo4jService()
market_service = MarketDataService()

class InvestmentTransactionSchema(BaseModel):
    symbol: str = Field(..., description="Asset ticker symbol, e.g. TCS, AAPL, NIFTYBEES")
    name: Optional[str] = Field(None, description="Company or fund name")
    asset_type: Optional[str] = Field("STOCK", description="STOCK, ETF, MUTUAL_FUND, CRYPTO, GOLD")
    transaction_type: str = Field("BUY", description="BUY or SELL")
    quantity: float = Field(..., gt=0, description="Quantity of units/shares")
    price: float = Field(..., gt=0, description="Price per unit/share")
    date_str: Optional[str] = Field(None, description="Transaction date in YYYY-MM-DD")
    account_id: Optional[str] = Field(None, description="Account ID for cash debit/credit")
    notes: Optional[str] = Field(None, description="Optional investment notes")

class ParseInvestmentSchema(BaseModel):
    text: str = Field(..., description="Natural language input, e.g. 'Bought 10 TCS shares at 3200'")

@router.get("")
def get_portfolio(user_id: str = Depends(get_current_user_id)):
    """
    Returns user portfolio with real-time market prices, allocations, and P/L metrics.
    """
    try:
        portfolio_raw = db.get_user_portfolio(user_id)
        holdings = portfolio_raw.get("holdings", [])
        
        symbols = [h["symbol"] for h in holdings if h.get("symbol")]
        quotes = market_service.get_batch_quotes(symbols) if symbols else {}
        
        metrics = calculate_portfolio_metrics(portfolio_raw, quotes)
        accounts = db.get_user_accounts(user_id)
        
        return {
            "status": "SUCCESS",
            "portfolio": metrics,
            "accounts": accounts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transactions")
def add_investment_transaction(
    payload: InvestmentTransactionSchema,
    user_id: str = Depends(get_current_user_id)
):
    """
    Executes an investment transaction:
    - Atomically debits or credits liquid cash in the designated account.
    - Updates holding units and weighted average cost.
    - Logs an InvestmentTransaction node in Neo4j.
    """
    try:
        # If account_id not provided, pick first available account
        account_id = payload.account_id
        if not account_id:
            accounts = db.get_user_accounts(user_id)
            if accounts:
                account_id = accounts[0].get("id")

        result = db.add_investment_transaction(
            user_id=user_id,
            symbol=payload.symbol,
            name=payload.name,
            asset_type=payload.asset_type,
            transaction_type=payload.transaction_type,
            quantity=payload.quantity,
            price=payload.price,
            date_str=payload.date_str,
            account_id=account_id,
            notes=payload.notes
        )
        return {
            "status": "SUCCESS",
            "result": result
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parse")
def parse_investment_prompt(payload: ParseInvestmentSchema):
    """
    Extracts structured investment details from natural language and enriches with live quote preview.
    Returns preview data for the user to confirm or edit before persisting.
    """
    try:
        extracted = extract_investment_transaction(payload.text)
        if not extracted:
            return {
                "status": "UNRECOGNIZED",
                "message": "Could not identify an investment action in the provided text.",
                "candidate": None
            }
        
        symbol = extracted.get("symbol")
        quote_info = None
        if symbol:
            try:
                q = market_service.get_quote(symbol)
                quote_info = {
                    "current_price": q.price,
                    "change_percent": q.change_percent,
                    "status": q.status,
                    "source": q.source
                }
            except Exception:
                pass

        return {
            "status": "PARSED",
            "candidate": {
                **extracted,
                "quote_preview": quote_info
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/holdings/{holding_id}")
def delete_holding(holding_id: str, user_id: str = Depends(get_current_user_id)):
    """
    Deletes a holding and its associated investment transactions.
    """
    try:
        res = db.delete_holding(user_id, holding_id)
        if not res.get("deleted"):
            raise HTTPException(status_code=404, detail="Holding not found or already deleted")
        return {
            "status": "SUCCESS",
            "message": f"Holding '{holding_id}' removed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/net-worth")
def get_net_worth(user_id: str = Depends(get_current_user_id)):
    """
    Calculates consolidated Total Net Worth and Liquid Net Worth deterministically.
    """
    try:
        summary_ctx = db.get_summary_context(user_id)
        portfolio_raw = db.get_user_portfolio(user_id)
        
        holdings = portfolio_raw.get("holdings", [])
        symbols = [h["symbol"] for h in holdings if h.get("symbol")]
        quotes = market_service.get_batch_quotes(symbols) if symbols else {}
        
        portfolio_metrics = calculate_portfolio_metrics(portfolio_raw, quotes) if portfolio_raw else None
        nw_metrics = calculate_net_worth(summary_ctx, portfolio_metrics)
        
        return {
            "status": "SUCCESS",
            "net_worth": nw_metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
