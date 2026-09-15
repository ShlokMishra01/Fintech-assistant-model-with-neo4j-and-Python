from backend.app.database.neo4j_service import Neo4jService
from backend.app.nlu.question_parser import parse_question
from backend.app.engine.financial_engine import (
    check_purchase_safety,
    calculate_savings_rate,
    calculate_emergency_fund,
    calculate_emergency_runway,
    calculate_category_expenses,
    calculate_debt_burden,
    calculate_comprehensive_health,
    generate_financial_summary,
    calculate_portfolio_metrics,
    calculate_net_worth
)
from backend.app.market.market_data_service import MarketDataService
from backend.app.services.response_generator import generate_explanation

class GraphRAG:

    def __init__(self, db=None, market_service=None):
        self.db = db or Neo4jService()
        self.market_service = market_service or MarketDataService()

    def retrieve_subgraph(self, user_id, intent, entities=None):
        """
        Targeted retrieval of the exact subgraphs needed for a given intent.
        Avoids dumping the entire database.
        """
        entities = entities or {}

        if intent == "PURCHASE_SAFETY":
            return self.db.get_purchase_context(user_id)

        elif intent == "SAVINGS_ANALYSIS":
            return self.db.get_savings_context(user_id)

        elif intent in ["EMERGENCY_FUND_ANALYSIS", "EMERGENCY_RUNWAY_ANALYSIS"]:
            return self.db.get_emergency_fund_context(user_id)

        elif intent in ["EXPENSE_BREAKDOWN", "CATEGORY_EXPENSE"]:
            return self.db.get_financial_context(user_id)

        elif intent == "DEBT_ANALYSIS":
            return self.db.get_purchase_context(user_id)

        elif intent in ["FINANCIAL_HEALTH", "FINANCIAL_SUMMARY"]:
            return self.db.get_summary_context(user_id)

        elif intent == "PORTFOLIO_ANALYSIS":
            portfolio = self.db.get_user_portfolio(user_id)
            holdings = portfolio.get("holdings", [])
            symbols = [h["symbol"] for h in holdings if h.get("symbol")]
            quotes = self.market_service.get_batch_quotes(symbols) if symbols else {}
            return {
                "portfolio": portfolio,
                "quotes": quotes,
                "symbol": entities.get("symbol")
            }

        elif intent == "NET_WORTH":
            ctx = self.db.get_summary_context(user_id)
            portfolio = self.db.get_user_portfolio(user_id)
            holdings = portfolio.get("holdings", [])
            symbols = [h["symbol"] for h in holdings if h.get("symbol")]
            quotes = self.market_service.get_batch_quotes(symbols) if symbols else {}
            ctx["portfolio"] = portfolio
            ctx["quotes"] = quotes
            return ctx

        elif intent == "MARKET_QUERY":
            sym = entities.get("symbol") or "TCS"
            quote = self.market_service.get_quote(sym)
            return {
                "symbol": sym,
                "quote": quote.to_dict() if hasattr(quote, "to_dict") else quote
            }

        else:
            return self.db.get_financial_context(user_id)

    def execute_reasoning(self, intent, context, entities=None):
        """
        Executes deterministic mathematical reasoning over the retrieved subgraph.
        """
        entities = entities or {}

        if intent == "PURCHASE_SAFETY":
            amount = entities.get("amount") or 0.0
            return check_purchase_safety(context, amount)

        elif intent == "SAVINGS_ANALYSIS":
            return calculate_savings_rate(context)

        elif intent == "EMERGENCY_FUND_ANALYSIS":
            return calculate_emergency_fund(context)

        elif intent == "EMERGENCY_RUNWAY_ANALYSIS":
            return calculate_emergency_runway(context)

        elif intent == "EXPENSE_BREAKDOWN":
            return calculate_category_expenses(context)

        elif intent == "CATEGORY_EXPENSE":
            target_cat = entities.get("category", "General")
            all_cat_stats = calculate_category_expenses(context)
            matching_cat = next((c for c in all_cat_stats["categories"] if c["category"].lower() == target_cat.lower()), None)
            return {
                "requested_category": target_cat,
                "category_spent": matching_cat["amount"] if matching_cat else 0.0,
                "percentage_of_total": matching_cat["percentage"] if matching_cat else 0.0,
                "total_expenses": all_cat_stats["total_expenses"],
                "all_categories": all_cat_stats["categories"]
            }

        elif intent == "DEBT_ANALYSIS":
            return calculate_debt_burden(context)

        elif intent == "FINANCIAL_HEALTH":
            return calculate_comprehensive_health(context)

        elif intent == "FINANCIAL_SUMMARY":
            return generate_financial_summary(context)

        elif intent == "PORTFOLIO_ANALYSIS":
            portfolio = context.get("portfolio", {})
            quotes = context.get("quotes", {})
            metrics = calculate_portfolio_metrics(portfolio, quotes)
            target_symbol = entities.get("symbol") if entities else None
            if target_symbol:
                clean_sym = target_symbol.upper().replace(".NS", "").replace(".BO", "")
                holding = next((h for h in metrics.get("holdings", []) if h["symbol"].upper().startswith(clean_sym)), None)
                if holding:
                    return {
                        "intent": "PORTFOLIO_ANALYSIS",
                        "target_symbol": target_symbol,
                        "holding": holding,
                        "total_invested": holding["invested_value"],
                        "total_current_value": holding["current_value"],
                        "profit_loss": holding["profit_loss"],
                        "return_pct": holding["return_pct"],
                        "portfolio_summary": metrics
                    }
            metrics["intent"] = "PORTFOLIO_ANALYSIS"
            return metrics

        elif intent == "NET_WORTH":
            portfolio = context.get("portfolio", {})
            quotes = context.get("quotes", {})
            portfolio_metrics = calculate_portfolio_metrics(portfolio, quotes) if portfolio else None
            nw = calculate_net_worth(context, portfolio_metrics)
            nw["intent"] = "NET_WORTH"
            return nw

        elif intent == "MARKET_QUERY":
            quote = context.get("quote", {})
            if hasattr(quote, "to_dict"):
                quote = quote.to_dict()
            quote["intent"] = "MARKET_QUERY"
            return quote

        else:
            return generate_financial_summary(context)

    def construct_evidence_payload(self, intent, reasoning_result, context):
        """
        Builds a verifiable evidence structure linking facts, calculations, and recommendations.
        """
        sym = "₹"
        evidence_items = []

        if intent == "PURCHASE_SAFETY":
            ev = reasoning_result.get("evidence", {})
            evidence_items = [
                {"label": "Current Account Balance", "value": f"{sym}{ev.get('current_balance', 0):,}", "source": "Account.balance"},
                {"label": "Pending EMI Obligations", "value": f"{sym}{ev.get('pending_emi', 0):,}", "source": "EMI.amount"},
                {"label": "Purchase Cost", "value": f"{sym}{ev.get('purchase_amount', 0):,}", "source": "User Query"},
                {"label": "Post-Purchase Remaining Balance", "value": f"{sym}{ev.get('balance_after_purchase', 0):,}", "source": "Deterministic Math"},
                {"label": "Recommended 3-Month Emergency Buffer", "value": f"{sym}{ev.get('emergency_requirement', 0):,}", "source": "Emergency Fund Formula"}
            ]

        elif intent == "SAVINGS_ANALYSIS":
            evidence_items = [
                {"label": "Total Monthly Income", "value": f"{sym}{reasoning_result.get('total_income', 0):,}", "source": "Income.amount"},
                {"label": "Total Monthly Expenses", "value": f"{sym}{reasoning_result.get('total_expenses', 0):,}", "source": "Transaction.amount"},
                {"label": "Net Monthly Savings", "value": f"{sym}{reasoning_result.get('savings', 0):,}", "source": "Deterministic Math"},
                {"label": "Savings Rate", "value": f"{reasoning_result.get('savings_rate', 0)}%", "source": "Savings Formula"}
            ]

        elif intent == "EMERGENCY_RUNWAY_ANALYSIS":
            evidence_items = [
                {"label": "Current Liquid Balance", "value": f"{sym}{reasoning_result.get('current_balance', 0):,}", "source": "Account.balance"},
                {"label": "Monthly Expenses", "value": f"{sym}{reasoning_result.get('monthly_expenses', 0):,}", "source": "Transaction.amount"},
                {"label": "Months of Runway", "value": f"{reasoning_result.get('runway_months', 0)} months", "source": "Runway Formula"},
                {"label": "Buffer Health Status", "value": reasoning_result.get("status", "INSUFFICIENT"), "source": "Health Classifier"}
            ]

        elif intent == "EXPENSE_BREAKDOWN":
            evidence_items = [
                {"label": "Total Monthly Expenses", "value": f"{sym}{reasoning_result.get('total_expenses', 0):,}", "source": "Ledger Sum"},
                {"label": "Highest Spending Category", "value": f"{reasoning_result.get('top_category', 'None')} ({sym}{reasoning_result.get('top_amount', 0):,})", "source": "Category Analytics"}
            ]

        elif intent == "DEBT_ANALYSIS":
            evidence_items = [
                {"label": "Total Outstanding Loan Principal", "value": f"{sym}{reasoning_result.get('total_outstanding_debt', 0):,}", "source": "Loan.outstanding"},
                {"label": "Pending Monthly EMI", "value": f"{sym}{reasoning_result.get('monthly_emi', 0):,}", "source": "EMI.amount"},
                {"label": "Debt-to-Income (DTI) Ratio", "value": f"{reasoning_result.get('dti_ratio', 0)}%", "source": "DTI Formula"},
                {"label": "Debt Risk Assessment", "value": reasoning_result.get("assessment", "Healthy"), "source": "Risk Classifier"}
            ]

        elif intent == "FINANCIAL_HEALTH":
            evidence_items = [
                {"label": "Overall Financial Health Score", "value": f"{reasoning_result.get('health_score', 0)} / 100", "source": "Composite Scoring Model"},
                {"label": "Financial Grade", "value": f"Grade {reasoning_result.get('grade', 'B')}", "source": "Grading Engine"},
                {"label": "Savings Rate", "value": f"{reasoning_result.get('savings_rate', 0)}%", "source": "Savings Model"},
                {"label": "Emergency Runway", "value": f"{reasoning_result.get('runway_months', 0)} months", "source": "Runway Model"},
                {"label": "DTI Ratio", "value": f"{reasoning_result.get('dti_ratio', 0)}%", "source": "Debt Model"}
            ]

        elif intent == "PORTFOLIO_ANALYSIS":
            if reasoning_result.get("target_symbol") and reasoning_result.get("holding"):
                h = reasoning_result["holding"]
                evidence_items = [
                    {"label": "Holding Ticker", "value": h.get("symbol", ""), "source": "Holding.symbol"},
                    {"label": "Units & Avg Buy Price", "value": f"{h.get('quantity', 0)} shares @ {sym}{h.get('buy_price', 0):,}", "source": "Holding Ledger"},
                    {"label": "Invested Capital", "value": f"{sym}{h.get('invested_value', 0):,}", "source": "Deterministic Math"},
                    {"label": "Current Market Price", "value": f"{sym}{h.get('current_price', 0):,} ({h.get('status', 'LIVE')})", "source": f"{h.get('source', 'OpenBB')}"},
                    {"label": "Current Valuation", "value": f"{sym}{h.get('current_value', 0):,}", "source": "Deterministic Math"},
                    {"label": "Unrealized Profit/Loss", "value": f"{'+' if h.get('profit_loss', 0) >= 0 else ''}{sym}{h.get('profit_loss', 0):,} ({h.get('return_pct', 0)}%)", "source": "Deterministic Math"}
                ]
            else:
                inv = reasoning_result.get("total_invested", 0)
                val = reasoning_result.get("total_current_value", 0)
                pnl = reasoning_result.get("profit_loss", 0)
                ret = reasoning_result.get("return_pct", 0)
                count = reasoning_result.get("holdings_count", 0)
                evidence_items = [
                    {"label": "Total Invested Capital", "value": f"{sym}{inv:,}", "source": "Holding Ledger"},
                    {"label": "Current Portfolio Valuation", "value": f"{sym}{val:,}", "source": "OpenBB Live Quotes / Cache"},
                    {"label": "Total Unrealized Profit/Loss", "value": f"{'+' if pnl >= 0 else ''}{sym}{pnl:,}", "source": "Deterministic Math"},
                    {"label": "Total Portfolio Return", "value": f"{'+' if ret >= 0 else ''}{ret}%", "source": "Deterministic Math"},
                    {"label": "Total Holdings Count", "value": f"{count} assets", "source": "Portfolio Node"}
                ]

        elif intent == "NET_WORTH":
            evidence_items = [
                {"label": "Liquid Cash Balance", "value": f"{sym}{reasoning_result.get('liquid_cash', 0):,}", "source": "Account.balance"},
                {"label": "Investment Portfolio Valuation", "value": f"{sym}{reasoning_result.get('portfolio_value', 0):,}", "source": "Portfolio Valuation"},
                {"label": "Total Consolidated Assets", "value": f"{sym}{reasoning_result.get('total_assets', 0):,}", "source": "Deterministic Math"},
                {"label": "Total Liabilities (Debt Outstanding)", "value": f"{sym}{reasoning_result.get('total_liabilities', 0):,}", "source": "Loan.outstanding"},
                {"label": "Total Net Worth", "value": f"{sym}{reasoning_result.get('total_net_worth', 0):,}", "source": "Deterministic Math"},
                {"label": "Liquid Net Worth (Cash - Pending EMIs)", "value": f"{sym}{reasoning_result.get('liquid_net_worth', 0):,}", "source": "Deterministic Math"}
            ]

        elif intent == "MARKET_QUERY":
            curr = reasoning_result.get("currency", "INR")
            curr_sym = "₹" if curr == "INR" else ("$" if curr == "USD" else curr)
            evidence_items = [
                {"label": "Security Ticker", "value": reasoning_result.get("symbol", ""), "source": "Market Data Provider"},
                {"label": "Current Market Price", "value": f"{curr_sym}{reasoning_result.get('price', 0):,.2f}", "source": f"{reasoning_result.get('source', 'OpenBB')}"},
                {"label": "24h Price Change", "value": f"{'+' if reasoning_result.get('change_percent', 0) >= 0 else ''}{reasoning_result.get('change_percent', 0):.2f}%", "source": f"{reasoning_result.get('source', 'OpenBB')}"},
                {"label": "Data Freshness Status", "value": reasoning_result.get("status", "LIVE"), "source": "Resilient Fallback Policy"}
            ]

        return {
            "intent": intent,
            "facts": evidence_items,
            "raw_result": reasoning_result
        }

    def process_query(self, question, user_id="U001"):
        """
        Complete GraphRAG pipeline:
        NLU -> Targeted Subgraph Retrieval -> Deterministic Math -> Grounded Evidence -> LLM Explanation.
        """
        parsed = parse_question(question)
        intent = parsed["intent"]

        if intent == "UNKNOWN":
            return {
                "query": question,
                "intent": "UNKNOWN",
                "decision": None,
                "math_result": None,
                "evidence": [],
                "explanation": "I'm sorry, I couldn't understand that financial question. You can ask about purchase affordability (e.g. 'Can I spend ₹15000 on a phone?'), savings rate, emergency runway, expenses breakdown, portfolio performance, net worth, or live market quotes."
            }

        context = self.retrieve_subgraph(user_id, intent, entities=parsed)
        math_result = self.execute_reasoning(intent, context, entities=parsed)
        evidence_payload = self.construct_evidence_payload(intent, math_result, context)
        explanation = generate_explanation(math_result, question=question)

        return {
            "query": question,
            "intent": intent,
            "entities": parsed,
            "math_result": math_result,
            "evidence": evidence_payload["facts"],
            "explanation": explanation
        }
