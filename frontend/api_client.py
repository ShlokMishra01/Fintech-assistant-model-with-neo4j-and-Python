import requests
import streamlit as st
from typing import Optional, Dict, Any

API_BASE_URL = "http://127.0.0.1:8001"

class FinanceAPIClient:
    """
    Centralized HTTP client for communicating with the FastAPI backend.
    Automatically attaches session credentials and handles timeouts and connection errors.
    """

    @staticmethod
    def _headers() -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json"
        }
        token = st.session_state.get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
            headers["X-Session-Token"] = token
        return headers

    @classmethod
    def _get(cls, path: str, params: Optional[dict] = None) -> Dict[str, Any]:
        url = f"{API_BASE_URL}{path}"
        try:
            resp = requests.get(url, headers=cls._headers(), params=params, timeout=12)
            if resp.status_code == 401:
                st.session_state["token"] = None
                st.session_state["user"] = None
                st.error("Session expired. Please log in again.")
                return {}
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Cannot connect to backend server at localhost:8000. Please ensure the FastAPI server is running.")
            return {}
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    def _post(cls, path: str, json_data: Optional[dict] = None) -> Dict[str, Any]:
        url = f"{API_BASE_URL}{path}"
        try:
            resp = requests.post(url, headers=cls._headers(), json=json_data, timeout=20)
            if resp.status_code == 401:
                st.session_state["token"] = None
                st.session_state["user"] = None
                st.error("Session expired. Please log in again.")
                return {}
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError:
            try:
                err_detail = resp.json().get("detail", resp.text)
            except Exception:
                err_detail = resp.text
            return {"error": err_detail, "status_code": resp.status_code}
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Cannot connect to backend server at localhost:8000.")
            return {"error": "Connection error"}
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    def _delete(cls, path: str) -> Dict[str, Any]:
        url = f"{API_BASE_URL}{path}"
        try:
            resp = requests.delete(url, headers=cls._headers(), timeout=12)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    # Auth
    @classmethod
    def login(cls, username: str, password: str) -> Dict[str, Any]:
        url = f"{API_BASE_URL}/api/auth/login"
        try:
            resp = requests.post(url, json={"username": username, "password": password}, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                st.session_state["token"] = data.get("token")
                st.session_state["user"] = data.get("user") or {"username": username, "name": username}
                return {"success": True, "data": data}
            else:
                return {"success": False, "error": resp.json().get("detail", "Invalid username or password")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def signup(cls, username: str, password: str, name: str, initial_balance: float = 25000.0) -> Dict[str, Any]:
        url = f"{API_BASE_URL}/api/auth/signup"
        try:
            resp = requests.post(url, json={
                "username": username,
                "password": password,
                "name": name,
                "initial_balance": initial_balance
            }, timeout=8)
            if resp.status_code in [200, 201]:
                data = resp.json()
                st.session_state["token"] = data.get("token")
                st.session_state["user"] = data
                return {"success": True, "data": data}
            else:
                return {"success": False, "error": resp.json().get("detail", "Sign-up failed")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Finance Overview & Analytics
    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        return cls._get("/api/finance/summary")

    @classmethod
    def get_expenses(cls) -> Dict[str, Any]:
        return cls._get("/api/finance/expenses")

    @classmethod
    def get_savings(cls) -> Dict[str, Any]:
        return cls._get("/api/finance/savings")

    @classmethod
    def get_emergency_fund(cls) -> Dict[str, Any]:
        return cls._get("/api/finance/emergency-fund")

    @classmethod
    def get_debt(cls) -> Dict[str, Any]:
        return cls._get("/api/finance/debt")

    @classmethod
    def get_health(cls) -> Dict[str, Any]:
        return cls._get("/api/finance/health")

    # Transactions
    @classmethod
    def get_transactions(cls, limit: int = 100) -> Dict[str, Any]:
        return cls._get("/api/transactions", params={"limit": limit})

    @classmethod
    def create_transaction(cls, payload: dict) -> Dict[str, Any]:
        return cls._post("/api/transactions", json_data=payload)

    @classmethod
    def delete_transaction(cls, tx_id: str) -> Dict[str, Any]:
        return cls._delete(f"/api/transactions/{tx_id}")

    # Goals
    @classmethod
    def get_goals(cls) -> Dict[str, Any]:
        return cls._get("/api/goals")

    @classmethod
    def create_goal(cls, name: str, target_amount: float, current_amount: float, target_date: str) -> Dict[str, Any]:
        return cls._post("/api/goals", json_data={
            "name": name,
            "target_amount": target_amount,
            "current_amount": current_amount,
            "target_date": target_date
        })

    # Portfolio
    @classmethod
    def get_portfolio(cls) -> Dict[str, Any]:
        return cls._get("/api/portfolio")

    @classmethod
    def add_investment_transaction(cls, payload: dict) -> Dict[str, Any]:
        return cls._post("/api/portfolio/transactions", json_data=payload)

    @classmethod
    def parse_investment(cls, text: str) -> Dict[str, Any]:
        return cls._post("/api/portfolio/parse", json_data={"text": text})

    @classmethod
    def delete_holding(cls, holding_id: str) -> Dict[str, Any]:
        return cls._delete(f"/api/portfolio/holdings/{holding_id}")

    @classmethod
    def get_net_worth(cls) -> Dict[str, Any]:
        return cls._get("/api/portfolio/net-worth")

    # Market Intelligence & Watchlist
    @classmethod
    def get_quote(cls, symbol: str) -> Dict[str, Any]:
        return cls._get(f"/api/market/quote/{symbol}")

    @classmethod
    def get_watchlist(cls) -> Dict[str, Any]:
        return cls._get("/api/market/watchlist")

    @classmethod
    def add_to_watchlist(cls, symbol: str, name: Optional[str] = None, asset_type: str = "STOCK") -> Dict[str, Any]:
        return cls._post("/api/market/watchlist", json_data={
            "symbol": symbol,
            "name": name,
            "asset_type": asset_type
        })

    @classmethod
    def remove_from_watchlist(cls, symbol: str) -> Dict[str, Any]:
        return cls._delete(f"/api/market/watchlist/{symbol}")

    @classmethod
    def search_assets(cls, query: str) -> Dict[str, Any]:
        return cls._get("/api/market/search", params={"query": query})

    # AI Assistant
    @classmethod
    def ask_assistant(cls, question: str) -> Dict[str, Any]:
        return cls._post("/api/assistant/query", json_data={"question": question})
