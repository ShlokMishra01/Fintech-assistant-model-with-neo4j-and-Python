import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from fastapi.testclient import TestClient
from backend.main import app
from backend.scripts.seed_db import seed_database
from backend.config import APP_PASSWORD, APP_USERNAME

client = TestClient(app)

def test_portfolio_and_market_endpoints():
    print("==================================================")
    print(" RUNNING PORTFOLIO & MARKET INTELLIGENCE TESTS")
    print("==================================================")

    # 1. Re-seed database with clean demo data
    seed_database()

    # 2. Authenticate
    login = client.post("/api/auth/login", json={"username": APP_USERNAME, "password": APP_PASSWORD})
    assert login.status_code == 200, "Login failed"
    token = login.json().get("token")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # 3. Test Portfolio Retrieval
    print("\n[1] Testing GET /api/portfolio:")
    res = client.get("/api/portfolio", headers=headers)
    assert res.status_code == 200, f"Failed GET /api/portfolio: {res.text}"
    p_data = res.json()["portfolio"]
    assert "total_invested" in p_data
    assert "total_current_value" in p_data
    assert "profit_loss" in p_data
    assert "return_pct" in p_data
    assert len(p_data["holdings"]) >= 3
    print(f"  - Portfolio Holdings Count: {len(p_data['holdings'])}")
    print(f"  - Total Invested: ₹{p_data['total_invested']:,} | Current: ₹{p_data['total_current_value']:,} | P/L: ₹{p_data['profit_loss']:,} ({p_data['return_pct']}%)")
    print("  -> GET /api/portfolio [PASS]")

    # 4. Test Net Worth Calculation
    print("\n[2] Testing GET /api/portfolio/net-worth:")
    nw_res = client.get("/api/portfolio/net-worth", headers=headers)
    assert nw_res.status_code == 200
    nw = nw_res.json()["net_worth"]
    assert "liquid_cash" in nw
    assert "portfolio_value" in nw
    assert "total_assets" in nw
    assert "total_liabilities" in nw
    assert "total_net_worth" in nw
    assert "liquid_net_worth" in nw
    print(f"  - Liquid Cash: ₹{nw['liquid_cash']:,} | Portfolio: ₹{nw['portfolio_value']:,}")
    print(f"  - Total Net Worth: ₹{nw['total_net_worth']:,} | Liquid Net Worth: ₹{nw['liquid_net_worth']:,}")
    print("  -> GET /api/portfolio/net-worth [PASS]")

    # 5. Test Natural Language Investment Parse Preview
    print("\n[3] Testing POST /api/portfolio/parse:")
    parse_res = client.post("/api/portfolio/parse", json={"text": "Bought 10 TCS shares at 3200"}, headers=headers)
    assert parse_res.status_code == 200
    parsed = parse_res.json()
    assert parsed["status"] == "PARSED"
    assert parsed["candidate"]["quantity"] == 10.0
    assert parsed["candidate"]["price"] == 3200.0
    assert parsed["candidate"]["total_amount"] == 32000.0
    print(f"  - NL Parse Candidate: {parsed['candidate']['quantity']}x {parsed['candidate']['symbol']} @ ₹{parsed['candidate']['price']}")
    print("  -> POST /api/portfolio/parse [PASS]")

    # 6. Test Investment Transaction Execution (Atomic cash balance update)
    print("\n[4] Testing POST /api/portfolio/transactions:")
    tx_payload = {
        "symbol": "INFY",
        "name": "Infosys Limited",
        "asset_type": "STOCK",
        "transaction_type": "BUY",
        "quantity": 5.0,
        "price": 1800.0,
        "date_str": "2026-09-13"
    }
    tx_res = client.post("/api/portfolio/transactions", json=tx_payload, headers=headers)
    assert tx_res.status_code == 200, f"Failed investment tx: {tx_res.text}"
    tx_data = tx_res.json()["result"]
    assert tx_data["symbol"] == "INFY"
    assert tx_data["new_quantity"] == 5.0
    print(f"  - Executed BUY 5x INFY: Account New Balance = ₹{tx_data.get('new_account_balance', 'N/A')}")
    print("  -> POST /api/portfolio/transactions [PASS]")

    # 7. Test Market Intelligence Quote
    print("\n[5] Testing GET /api/market/quote/TCS:")
    m_res = client.get("/api/market/quote/TCS")
    assert m_res.status_code == 200
    q = m_res.json()["quote"]
    assert "price" in q
    assert "status" in q
    assert q["status"] in ["LIVE", "DELAYED", "STALE", "USER_ENTERED"]
    print(f"  - Quote TCS: ₹{q['price']} ({q['status']} via {q['source']})")
    print("  -> GET /api/market/quote [PASS]")

    # 8. Test Watchlist CRUD
    print("\n[6] Testing Watchlist Endpoints:")
    wl_res = client.get("/api/market/watchlist", headers=headers)
    assert wl_res.status_code == 200, f"Failed GET /api/market/watchlist: {wl_res.text}"
    wl = wl_res.json()["watchlist"]
    print(f"  - Watchlist count: {len(wl)}")

    add_wl = client.post("/api/market/watchlist", json={"symbol": "TATAMOTORS", "name": "Tata Motors"}, headers=headers)
    assert add_wl.status_code == 200
    print("  - Added TATAMOTORS to watchlist [OK]")

    del_wl = client.delete("/api/market/watchlist/TATAMOTORS", headers=headers)
    assert del_wl.status_code == 200
    print("  - Removed TATAMOTORS from watchlist [OK]")
    print("  -> Watchlist CRUD [PASS]")

    # 9. Test Assistant GraphRAG for Portfolio Query
    print("\n[7] Testing POST /api/assistant/query (Portfolio & Net Worth Intents):")
    ai_p = client.post("/api/assistant/query", json={"question": "How is my portfolio performing?"}, headers=headers)
    assert ai_p.status_code == 200
    ai_p_data = ai_p.json()
    assert ai_p_data["intent"] == "PORTFOLIO_ANALYSIS"
    assert len(ai_p_data["evidence"]) >= 3
    print(f"  - Portfolio Query Intent: {ai_p_data['intent']} (Evidence items: {len(ai_p_data['evidence'])})")

    ai_nw = client.post("/api/assistant/query", json={"question": "What is my total net worth?"}, headers=headers)
    assert ai_nw.status_code == 200
    ai_nw_data = ai_nw.json()
    assert ai_nw_data["intent"] == "NET_WORTH"
    print(f"  - Net Worth Query Intent: {ai_nw_data['intent']} (Evidence items: {len(ai_nw_data['evidence'])})")
    print("  -> Assistant Portfolio & Net Worth GraphRAG [PASS]")

    print("\n==================================================")
    print(" ALL PORTFOLIO & MARKET TESTS PASSED (100%)!")
    print("==================================================")

if __name__ == "__main__":
    test_portfolio_and_market_endpoints()
