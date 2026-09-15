import streamlit as st
import pandas as pd
from datetime import date
from frontend.styles import apply_custom_styles
from frontend.api_client import FinanceAPIClient
from frontend.charts import (
    render_allocation_donut,
    render_net_worth_breakdown,
    render_expense_categories_bar,
    render_savings_gauge
)

# ---------------------------------------------------------
# Application Configuration & State
# ---------------------------------------------------------
st.set_page_config(
    page_title="Personal Finance AI | Portfolio Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_styles()

if "token" not in st.session_state:
    st.session_state["token"] = None
if "user" not in st.session_state:
    st.session_state["user"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "nl_tx_candidate" not in st.session_state:
    st.session_state["nl_tx_candidate"] = None
if "nl_inv_candidate" not in st.session_state:
    st.session_state["nl_inv_candidate"] = None

# ---------------------------------------------------------
# Authentication Screen
# ---------------------------------------------------------
def render_auth_screen():
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-top: 40px; margin-bottom: 24px;">
            <div style="font-size: 40px; margin-bottom: 8px;">⚡</div>
            <h1 style="font-size: 32px; font-weight: 700; margin-bottom: 4px; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                Personal Finance AI
            </h1>
            <p style="color: #94a3b8; font-size: 15px;">Deterministic Portfolio Intelligence & GraphRAG Wealth Platform</p>
        </div>
        """, unsafe_allow_html=True)

        auth_tab1, auth_tab2 = st.tabs(["🔐 Sign In", "✨ Create Account"])

        with auth_tab1:
            st.markdown("### Access Terminal")
            username = st.text_input("Username", key="login_username", value="Rahul")
            password = st.text_input("Password", type="password", key="login_password", value="password123")

            c_sub1, c_sub2 = st.columns([1, 1])
            with c_sub1:
                if st.button("Sign In →", use_container_width=True, type="primary"):
                    if not username or not password:
                        st.warning("Please enter your username and password.")
                    else:
                        with st.spinner("Authenticating with Neo4j Knowledge Graph..."):
                            res = FinanceAPIClient.login(username, password)
                            if res.get("success"):
                                st.rerun()
                            else:
                                st.error(res.get("error", "Invalid credentials"))

            with c_sub2:
                if st.button("⚡ 1-Click Demo Login (Rahul)", use_container_width=True):
                    with st.spinner("Connecting demo account..."):
                        res = FinanceAPIClient.login("Rahul", "password123")
                        if res.get("success"):
                            st.rerun()
                        else:
                            st.error(res.get("error", "Failed to login as demo user"))

        with auth_tab2:
            st.markdown("### Register New Portfolio")
            new_user = st.text_input("Choose Username", key="reg_user")
            new_name = st.text_input("Full Name", key="reg_name")
            new_pass = st.text_input("Password", type="password", key="reg_pass")
            new_bal = st.number_input("Initial Liquid Balance (₹)", min_value=1000.0, value=35000.0, step=5000.0)

            if st.button("Complete Sign Up →", use_container_width=True, type="primary"):
                if not new_user or not new_pass or not new_name:
                    st.warning("Please fill in all registration fields.")
                else:
                    with st.spinner("Initializing Neo4j Graph and User Portfolio..."):
                        res = FinanceAPIClient.signup(new_user, new_pass, new_name, new_bal)
                        if res.get("success"):
                            st.success("Account created! Logging in...")
                            FinanceAPIClient.login(new_user, new_pass)
                            st.rerun()
                        else:
                            st.error(res.get("error", "Sign up failed"))

# ---------------------------------------------------------
# Sidebar Navigation & User Context
# ---------------------------------------------------------
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; padding: 10px 0 18px 0;">
            <span style="font-size: 26px;">⚡</span>
            <div>
                <div style="font-weight: 700; font-size: 17px; color: #f1f5f9; letter-spacing: -0.3px;">FINANCE AI</div>
                <div style="font-size: 11px; color: #38bdf8; font-weight: 500;">PORTFOLIO INTELLIGENCE</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        user = st.session_state.get("user") or {}
        user_name = user.get("name") or user.get("username") or "Investor"

        st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 10px; padding: 10px 14px; margin-bottom: 20px;">
            <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase;">Active Session</div>
            <div style="font-weight: 600; font-size: 14px; color: #e2e8f0;">{user_name}</div>
            <div style="display: flex; align-items: center; gap: 6px; font-size: 11px; color: #34d399; margin-top: 3px;">
                <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #34d399;"></span>
                Neo4j Graph & OpenBB Online
            </div>
        </div>
        """, unsafe_allow_html=True)

        nav_options = [
            "📊 Executive Overview",
            "💳 Transactions & Cashflow",
            "📈 Portfolio Intelligence",
            "📉 Analytics & Health",
            "🎯 Goals & Milestones",
            "🤖 AI Assistant (GraphRAG)",
            "🌐 Market Intelligence"
        ]

        active_nav = st.radio("Navigation", nav_options, label_visibility="collapsed")

        st.markdown("---")
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state["token"] = None
            st.session_state["user"] = None
            st.rerun()

        return active_nav

# ---------------------------------------------------------
# Page 1: Executive Overview
# ---------------------------------------------------------
def render_overview():
    st.markdown("""
    <div class="hero-banner">
        <h2 class="hero-title">Executive Wealth Overview</h2>
        <p class="hero-subtitle">Consolidated view of liquid reserves, live portfolio valuation, and debt commitments.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Fetching verified graph metrics..."):
        summary = FinanceAPIClient.get_summary()
        portfolio_res = FinanceAPIClient.get_portfolio()
        net_worth_res = FinanceAPIClient.get_net_worth()

    nw = net_worth_res.get("net_worth", {})
    port = portfolio_res.get("portfolio", {})

    # Top KPI Row
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        tot_nw = nw.get("total_net_worth", 0.0)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Net Worth</div>
            <div class="kpi-value">₹{tot_nw:,.2f}</div>
            <div class="kpi-sub trend-up">Liquid: ₹{nw.get('liquid_net_worth', 0):,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        curr_port = port.get("total_current_value", 0.0)
        pnl = port.get("profit_loss", 0.0)
        pnl_sign = "+" if pnl >= 0 else ""
        trend_class = "trend-up" if pnl >= 0 else "trend-down"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Portfolio Valuation</div>
            <div class="kpi-value">₹{curr_port:,.2f}</div>
            <div class="kpi-sub {trend_class}">{pnl_sign}₹{pnl:,.2f} ({port.get('return_pct', 0)}%)</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        savings_rate = summary.get("savings_rate", 0.0)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Monthly Savings Rate</div>
            <div class="kpi-value">{savings_rate:.1f}%</div>
            <div class="kpi-sub trend-up">Saved ₹{summary.get('savings', 0):,.0f} this month</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        score = summary.get("financial_health_score", 0.0)
        grade = summary.get("financial_health_grade", "B")
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Financial Health</div>
            <div class="kpi-value">{score:.0f} / 100</div>
            <div class="kpi-sub trend-neutral">Rating: Grade {grade}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Charts Row
    ch1, ch2 = st.columns([1.2, 1])

    with ch1:
        st.markdown("#### Consolidated Balance Sheet")
        fig_nw = render_net_worth_breakdown(nw)
        st.plotly_chart(fig_nw, use_container_width=True)

    with ch2:
        st.markdown("#### Asset Allocation")
        allocations = port.get("asset_allocation", [])
        fig_alloc = render_allocation_donut(allocations, title="Distribution by Asset Class")
        st.plotly_chart(fig_alloc, use_container_width=True)

# ---------------------------------------------------------
# Page 2: Transactions & Cashflow
# ---------------------------------------------------------
def render_transactions():
    st.markdown("""
    <div class="hero-banner">
        <h2 class="hero-title">Transactions & Cashflow</h2>
        <p class="hero-subtitle">Log expenses or income using natural language or structured entries with real-time graph reconciliation.</p>
    </div>
    """, unsafe_allow_html=True)

    t_tab1, t_tab2 = st.tabs(["💬 Natural Language Entry", "📝 Manual Entry Form"])

    with t_tab1:
        st.markdown("##### Log with Natural Language")
        st.markdown("<p style='color: #94a3b8; font-size: 13px;'>Type plain English e.g., <i>'Spent ₹1500 on groceries yesterday'</i> or <i>'Received ₹45000 salary'</i></p>", unsafe_allow_html=True)
        nl_input = st.text_input("Enter transaction phrase", placeholder="e.g. Spent ₹2,500 on dinner with friends", key="nl_tx_input")

        if st.button("Parse & Ingest Transaction", type="primary"):
            if nl_input.strip():
                with st.spinner("Processing natural language through NLU and Graph engine..."):
                    res = FinanceAPIClient.create_transaction({"natural_language_input": nl_input})
                    if res.get("status") == "SUCCESS":
                        st.success(f"✅ {res.get('impact_summary')}")
                        st.rerun()
                    else:
                        st.error(res.get("error", "Failed to ingest transaction"))

    with t_tab2:
        st.markdown("##### Structured Transaction")
        with st.form("manual_tx_form"):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                tx_type = st.selectbox("Type", ["EXPENSE", "INCOME"])
                amount = st.number_input("Amount (₹)", min_value=1.0, value=1000.0, step=100.0)
            with col_b:
                category = st.text_input("Category", value="Food" if tx_type == "EXPENSE" else "Salary")
                tx_date = st.date_input("Date", value=date.today())
            with col_c:
                description = st.text_input("Description", value="Daily expense")
                submitted = st.form_submit_button("Record Transaction", type="primary", use_container_width=True)

            if submitted:
                with st.spinner("Persisting transaction into Neo4j..."):
                    payload = {
                        "amount": amount,
                        "category_name": category,
                        "transaction_type": tx_type,
                        "description": description,
                        "date_str": tx_date.isoformat()
                    }
                    res = FinanceAPIClient.create_transaction(payload)
                    if res.get("status") == "SUCCESS":
                        st.success("Transaction recorded successfully!")
                        st.rerun()
                    else:
                        st.error(res.get("error", "Error creating transaction"))

    st.markdown("---")
    st.markdown("#### Transaction Ledger")

    tx_data = FinanceAPIClient.get_transactions(limit=100)
    tx_list = tx_data.get("transactions", [])

    if tx_list:
        df_rows = []
        for t in tx_list:
            df_rows.append({
                "ID": t.get("id"),
                "Date": t.get("date"),
                "Description": t.get("description"),
                "Category": t.get("category"),
                "Type": t.get("type"),
                "Amount (₹)": f"₹{t.get('amount', 0):,.2f}"
            })
        df = pd.DataFrame(df_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        col_del1, col_del2 = st.columns([3, 1])
        with col_del2:
            tx_to_del = st.selectbox("Select ID to delete", [t["id"] for t in tx_list], key="tx_del_select")
            if st.button("Delete Transaction", type="secondary", use_container_width=True):
                with st.spinner("Removing transaction and reconciling bank balance..."):
                    del_res = FinanceAPIClient.delete_transaction(tx_to_del)
                    if del_res.get("status") == "SUCCESS":
                        st.success(f"Deleted {tx_to_del}! Restored balance: ₹{del_res.get('restored_balance', 0):,.2f}")
                        st.rerun()
                    else:
                        st.error("Failed to delete transaction")
    else:
        st.info("No transactions recorded yet. Add your first transaction above!")

# ---------------------------------------------------------
# Page 3: Portfolio Intelligence
# ---------------------------------------------------------
def render_portfolio():
    st.markdown("""
    <div class="hero-banner">
        <h2 class="hero-title">Portfolio Intelligence & Asset Management</h2>
        <p class="hero-subtitle">Real-time valuation backed by OpenBB market feeds, deterministic P/L, and natural language trade execution.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Fetching live market prices for portfolio holdings..."):
        port_res = FinanceAPIClient.get_portfolio()
        portfolio = port_res.get("portfolio", {})
        holdings = portfolio.get("holdings", [])
        accounts = port_res.get("accounts", [])

    # Portfolio KPIs
    c1, c2, c3, c4 = st.columns(4)
    tot_inv = portfolio.get("total_invested", 0.0)
    tot_val = portfolio.get("total_current_value", 0.0)
    pnl = portfolio.get("profit_loss", 0.0)
    ret_pct = portfolio.get("return_pct", 0.0)

    pnl_sign = "+" if pnl >= 0 else ""
    pnl_class = "trend-up" if pnl >= 0 else "trend-down"

    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Invested Capital</div>
            <div class="kpi-value">₹{tot_inv:,.2f}</div>
            <div class="kpi-sub trend-neutral">{len(holdings)} active holdings</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Current Valuation</div>
            <div class="kpi-value">₹{tot_val:,.2f}</div>
            <div class="kpi-sub {pnl_class}">Live / Cached Feeds</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Unrealized Profit/Loss</div>
            <div class="kpi-value {pnl_class}">{pnl_sign}₹{pnl:,.2f}</div>
            <div class="kpi-sub {pnl_class}">{pnl_sign}{ret_pct:.2f}% Total Return</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        first_acc = accounts[0] if accounts else {}
        cash_bal = first_acc.get("balance", 0.0)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Available Liquid Cash</div>
            <div class="kpi-value">₹{cash_bal:,.2f}</div>
            <div class="kpi-sub trend-neutral">{first_acc.get('bank', 'Cash Account')}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Trade Entry Section (Natural Language Confirmation Preview + Structured Form)
    st.markdown("### Execute Investment Trade")
    st.markdown("<p style='color: #94a3b8; font-size: 13px;'>Investments atomically debit/credit your liquid cash balance without polluting lifestyle expenses.</p>", unsafe_allow_html=True)

    inv_tab1, inv_tab2 = st.tabs(["💬 Natural Language Trade (with Preview)", "📝 Structured Order Form"])

    with inv_tab1:
        st.markdown("##### Natural Language Investment Preview")
        nl_trade_input = st.text_input(
            "Enter trade instruction",
            placeholder="e.g. Bought 10 TCS shares at 3200",
            key="nl_trade_text"
        )

        col_p1, col_p2 = st.columns([1, 3])
        with col_p1:
            if st.button("Parse Trade Preview →", type="primary", use_container_width=True):
                if nl_trade_input.strip():
                    with st.spinner("Extracting trade details and checking live quote..."):
                        preview_res = FinanceAPIClient.parse_investment(nl_trade_input)
                        if preview_res.get("status") == "PARSED":
                            st.session_state["nl_inv_candidate"] = preview_res.get("candidate")
                        else:
                            st.error(preview_res.get("message", "Unable to parse investment action"))

        candidate = st.session_state.get("nl_inv_candidate")
        if candidate:
            st.markdown("""
            <div style="background: rgba(6, 182, 212, 0.08); border: 1px solid rgba(6, 182, 212, 0.3); border-radius: 12px; padding: 18px 22px; margin: 16px 0;">
                <div style="color: #38bdf8; font-weight: 700; font-size: 15px; margin-bottom: 8px;">📋 TRADE CONFIRMATION PREVIEW</div>
                <div style="font-size: 13px; color: #cbd5e1; line-height: 1.6;">
                    Please confirm the parsed parameters before executing. Cash account will be atomically adjusted.
                </div>
            </div>
            """, unsafe_allow_html=True)

            c_cand1, c_cand2, c_cand3, c_cand4 = st.columns(4)
            with c_cand1:
                conf_sym = st.text_input("Symbol", value=candidate.get("symbol", "TCS"), key="conf_sym")
            with c_cand2:
                conf_type = st.selectbox("Action", ["BUY", "SELL"], index=0 if candidate.get("transaction_type") == "BUY" else 1, key="conf_type")
            with c_cand3:
                conf_qty = st.number_input("Quantity", value=float(candidate.get("quantity", 1)), min_value=0.01, step=1.0, key="conf_qty")
            with c_cand4:
                conf_price = st.number_input("Price per Unit (₹)", value=float(candidate.get("price", 100)), min_value=0.01, step=10.0, key="conf_price")

            total_calc = round(conf_qty * conf_price, 2)
            st.markdown(f"**Total Capital Impact:** `₹{total_calc:,.2f}` ({'Debit from cash' if conf_type == 'BUY' else 'Credit to cash'})")

            b_col1, b_col2 = st.columns([1, 1])
            with b_col1:
                if st.button("✅ Confirm & Execute Trade", type="primary", use_container_width=True):
                    with st.spinner("Executing atomic investment transaction in Neo4j..."):
                        trade_payload = {
                            "symbol": conf_sym,
                            "name": candidate.get("detected_asset", conf_sym),
                            "asset_type": candidate.get("asset_type", "STOCK"),
                            "transaction_type": conf_type,
                            "quantity": conf_qty,
                            "price": conf_price,
                            "date_str": date.today().isoformat()
                        }
                        res = FinanceAPIClient.add_investment_transaction(trade_payload)
                        if res.get("status") == "SUCCESS":
                            st.success(f"🎉 Successfully executed {conf_type} of {conf_qty}x {conf_sym}!")
                            st.session_state["nl_inv_candidate"] = None
                            st.rerun()
                        else:
                            st.error(res.get("error", "Transaction execution failed"))
            with b_col2:
                if st.button("❌ Cancel / Discard", use_container_width=True):
                    st.session_state["nl_inv_candidate"] = None
                    st.rerun()

    with inv_tab2:
        with st.form("manual_trade_form"):
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1:
                t_sym = st.text_input("Asset Symbol", value="TCS", placeholder="e.g. TCS, AAPL, NIFTYBEES")
                t_action = st.selectbox("Action", ["BUY", "SELL"])
            with c_f2:
                t_type = st.selectbox("Asset Class", ["STOCK", "INDEX_FUND", "GOLD", "MUTUAL_FUND", "CRYPTO"])
                t_name = st.text_input("Asset Name", value="Tata Consultancy Services")
            with c_f3:
                t_qty = st.number_input("Shares / Units", min_value=0.01, value=5.0, step=1.0)
                t_price = st.number_input("Execution Price (₹)", min_value=0.01, value=3200.0, step=50.0)

            t_submit = st.form_submit_button("Submit Trade Order", type="primary", use_container_width=True)
            if t_submit:
                with st.spinner("Recording trade order..."):
                    payload = {
                        "symbol": t_sym,
                        "name": t_name,
                        "asset_type": t_type,
                        "transaction_type": t_action,
                        "quantity": t_qty,
                        "price": t_price,
                        "date_str": date.today().isoformat()
                    }
                    res = FinanceAPIClient.add_investment_transaction(payload)
                    if res.get("status") == "SUCCESS":
                        st.success("Trade executed successfully!")
                        st.rerun()
                    else:
                        st.error(res.get("error", "Trade execution failed"))

    st.markdown("---")
    st.markdown("#### Current Holdings Table")

    if holdings:
        h_rows = []
        for h in holdings:
            st_val = h.get("status", "LIVE")
            badge = f"🟢 {st_val}" if st_val == "LIVE" else (f"🟡 {st_val}" if st_val in ["DELAYED", "USER_ENTERED"] else f"🔴 {st_val}")
            h_pnl = h.get("profit_loss", 0.0)
            pnl_str = f"{'+' if h_pnl >= 0 else ''}₹{h_pnl:,.2f} ({h.get('return_pct', 0)}%)"

            h_rows.append({
                "Holding ID": h.get("holding_id"),
                "Symbol": h.get("symbol"),
                "Asset Name": h.get("name"),
                "Type": h.get("asset_type"),
                "Units": f"{h.get('quantity', 0):,}",
                "Avg Buy (₹)": f"₹{h.get('average_cost', 0):,.2f}",
                "Market Price (₹)": f"₹{h.get('current_price', 0):,.2f}",
                "Current Valuation (₹)": f"₹{h.get('current_value', 0):,.2f}",
                "Profit / Loss": pnl_str,
                "Status": badge,
                "Source": h.get("source", "OpenBB")
            })

        df_holdings = pd.DataFrame(h_rows)
        st.dataframe(df_holdings, use_container_width=True, hide_index=True)

        col_hdel1, col_hdel2 = st.columns([3, 1])
        with col_hdel2:
            h_to_del = st.selectbox("Delete Holding", [h["holding_id"] for h in holdings], key="h_del_sel")
            if st.button("Delete Holding Position", type="secondary", use_container_width=True):
                with st.spinner("Removing holding node..."):
                    res = FinanceAPIClient.delete_holding(h_to_del)
                    if res.get("status") == "SUCCESS":
                        st.success("Holding deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete holding")
    else:
        st.info("No holdings found in portfolio. Use the trade execution panel above to add positions.")

# ---------------------------------------------------------
# Page 4: Analytics & Health
# ---------------------------------------------------------
def render_analytics():
    st.markdown("""
    <div class="hero-banner">
        <h2 class="hero-title">Financial Health & Analytics</h2>
        <p class="hero-subtitle">Algorithmic risk evaluation, Debt-to-Income (DTI), category breakdowns, and emergency buffer runway.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Computing analytics across graph nodes..."):
        health = FinanceAPIClient.get_health()
        expenses = FinanceAPIClient.get_expenses()
        emergency = FinanceAPIClient.get_emergency_fund()
        debt = FinanceAPIClient.get_debt()

    # Health Score Hero
    c_h1, c_h2, c_h3 = st.columns([1, 1, 1.2])

    with c_h1:
        st.markdown("#### Health Rating")
        score = health.get("health_score", 0.0)
        grade = health.get("grade", "B")
        st.markdown(f"""
        <div class="kpi-card" style="text-align: center; padding: 26px;">
            <div class="kpi-label">Composite Health Score</div>
            <div style="font-size: 48px; font-weight: 800; color: #38bdf8;">{score:.0f}</div>
            <div style="font-size: 16px; font-weight: 600; color: #34d399; margin-top: 4px;">Grade {grade}</div>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 8px;">{health.get('summary', '')}</div>
        </div>
        """, unsafe_allow_html=True)

    with c_h2:
        st.markdown("#### Savings Gauge")
        fig_gauge = render_savings_gauge(health.get("savings_rate", 0.0))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with c_h3:
        st.markdown("#### Debt & Emergency Reserves")
        runway = health.get("runway_months", 0.0)
        dti = health.get("dti_ratio", 0.0)
        shortfall = health.get("emergency_shortfall", 0.0)

        st.markdown(f"""
        <div class="kpi-card">
            <div class="fact-row">
                <span class="fact-label">Emergency Buffer Runway:</span>
                <span class="fact-val">{runway:.1f} months</span>
            </div>
            <div class="fact-row">
                <span class="fact-label">Reserve Shortfall:</span>
                <span class="fact-val" style="color: {'#f87171' if shortfall > 0 else '#34d399'}">₹{shortfall:,.2f}</span>
            </div>
            <div class="fact-row">
                <span class="fact-label">Debt-to-Income (DTI):</span>
                <span class="fact-val">{dti:.1f}% ({'Healthy' if dti <= 20 else 'Elevated'})</span>
            </div>
            <div class="fact-row">
                <span class="fact-label">Total Outstanding Debt:</span>
                <span class="fact-val">₹{debt.get('total_outstanding_debt', 0):,.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Spending Distribution by Category")
    cat_list = expenses.get("categories", [])
    fig_exp = render_expense_categories_bar(cat_list)
    st.plotly_chart(fig_exp, use_container_width=True)

# ---------------------------------------------------------
# Page 5: Goals & Milestones
# ---------------------------------------------------------
def render_goals():
    st.markdown("""
    <div class="hero-banner">
        <h2 class="hero-title">Financial Goals & Milestones</h2>
        <p class="hero-subtitle">Track targeted capital accumulation, savings milestones, and target achievement dates.</p>
    </div>
    """, unsafe_allow_html=True)

    goals_data = FinanceAPIClient.get_goals()
    goal_list = goals_data.get("goals", []) if isinstance(goals_data, dict) else []

    col_g1, col_g2 = st.columns([2, 1])

    with col_g1:
        st.markdown("#### Active Milestones")
        if goal_list:
            for g in goal_list:
                target = float(g.get("target_amount", g.get("target", 100000)))
                current = float(g.get("current_amount", g.get("current", 0)))
                progress = min(1.0, current / target) if target > 0 else 0.0

                st.markdown(f"""
                <div class="kpi-card" style="margin-bottom: 14px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-weight: 700; font-size: 16px; color: #f8fafc;">{g.get('name', 'Goal')}</div>
                        <div style="font-size: 12px; color: #38bdf8; font-weight: 600;">Target: {g.get('target_date', 'N/A')}</div>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 14px;">
                        <span style="color: #94a3b8;">Accumulated: <b>₹{current:,.2f}</b></span>
                        <span style="color: #cbd5e1;">Target: <b>₹{target:,.2f}</b> ({progress*100:.1f}%)</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(progress)
        else:
            st.info("No goals tracked yet. Define a target milestone on the right.")

    with col_g2:
        st.markdown("#### Add New Goal")
        with st.form("new_goal_form"):
            g_name = st.text_input("Goal Name", placeholder="e.g. Down Payment for Home")
            g_target = st.number_input("Target Amount (₹)", min_value=1000.0, value=200000.0, step=10000.0)
            g_curr = st.number_input("Current Seed Amount (₹)", min_value=0.0, value=25000.0, step=5000.0)
            g_date = st.date_input("Target Date", value=date.today())
            g_submit = st.form_submit_button("Create Goal", type="primary", use_container_width=True)

            if g_submit:
                with st.spinner("Linking goal to user in Knowledge Graph..."):
                    res = FinanceAPIClient.create_goal(g_name, g_target, g_curr, g_date.isoformat())
                    if res.get("status") == "SUCCESS":
                        st.success("Goal established successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to establish goal")

# ---------------------------------------------------------
# Page 6: AI Assistant (GraphRAG with Evidence Cards)
# ---------------------------------------------------------
def render_assistant():
    st.markdown("""
    <div class="hero-banner">
        <h2 class="hero-title">GraphRAG Financial AI Assistant</h2>
        <p class="hero-subtitle">Deterministic math over the Neo4j Knowledge Graph, validated against LLM hallucination and numerical drift.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("##### Suggested Inquiries")
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)

    preset_query = None
    with col_q1:
        if st.button("📱 Can I buy a phone for ₹15,000?", use_container_width=True):
            preset_query = "Can I spend ₹15,000 on a phone?"
    with col_q2:
        if st.button("📈 How is my portfolio performing?", use_container_width=True):
            preset_query = "How is my portfolio performing?"
    with col_q3:
        if st.button("🏛️ What is my total net worth?", use_container_width=True):
            preset_query = "What is my total net worth?"
    with col_q4:
        if st.button("🛡️ How much emergency fund do I need?", use_container_width=True):
            preset_query = "How much emergency fund do I need?"

    # Chat history display
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("evidence"):
                with st.expander("🔍 Verified Evidence Card & Calculation Sources", expanded=False):
                    st.markdown("""
                    <div class="evidence-box">
                        <div class="evidence-header">
                            <span>🛡️ Zero-Hallucination Audit Trail (Neo4j Graph)</span>
                        </div>
                    """, unsafe_allow_html=True)
                    for item in msg["evidence"]:
                        st.markdown(f"""
                        <div class="fact-row">
                            <span class="fact-label">{item.get('label')}:</span>
                            <span class="fact-val">{item.get('value')} <span class="fact-src">[{item.get('source')}]</span></span>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

    # Chat input
    user_query = st.chat_input("Ask any question regarding affordability, portfolio, savings, or market quotes...")
    query_to_run = preset_query or user_query

    if query_to_run:
        st.session_state["chat_history"].append({"role": "user", "content": query_to_run})
        with st.chat_message("user"):
            st.markdown(query_to_run)

        with st.chat_message("assistant"):
            with st.spinner("Executing GraphRAG pipeline: Intent -> Subgraph -> Math -> Validator -> LLM..."):
                resp = FinanceAPIClient.ask_assistant(query_to_run)
                explanation = resp.get("explanation", "I encountered an error analyzing your request.")
                evidence = resp.get("evidence", [])

                st.markdown(explanation)
                if evidence:
                    with st.expander("🔍 Verified Evidence Card & Calculation Sources", expanded=True):
                        st.markdown("""
                        <div class="evidence-box">
                            <div class="evidence-header">
                                <span>🛡️ Zero-Hallucination Audit Trail (Neo4j Graph)</span>
                            </div>
                        """, unsafe_allow_html=True)
                        for item in evidence:
                            st.markdown(f"""
                            <div class="fact-row">
                                <span class="fact-label">{item.get('label')}:</span>
                                <span class="fact-val">{item.get('value')} <span class="fact-src">[{item.get('source')}]</span></span>
                            </div>
                            """, unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                st.session_state["chat_history"].append({
                    "role": "assistant",
                    "content": explanation,
                    "evidence": evidence
                })

# ---------------------------------------------------------
# Page 7: Market Intelligence & Watchlist
# ---------------------------------------------------------
def render_market():
    st.markdown("""
    <div class="hero-banner">
        <h2 class="hero-title">Market Intelligence & Watchlist</h2>
        <p class="hero-subtitle">Real-time asset quotes, resilient OpenBB/yfinance fallbacks, and personal watchlist tracker.</p>
    </div>
    """, unsafe_allow_html=True)

    m_col1, m_col2 = st.columns([1.8, 1.2])

    with m_col1:
        st.markdown("#### Live Asset Ticker Lookup")
        q_search = st.text_input("Enter Ticker Symbol (e.g. TCS, INFY, AAPL, NIFTYBEES)", value="TCS", key="market_search_input")

        if st.button("Fetch Live Quote 🔍", type="primary"):
            if q_search.strip():
                with st.spinner(f"Querying OpenBB provider for {q_search.upper()}..."):
                    quote_res = FinanceAPIClient.get_quote(q_search.strip())
                    quote = quote_res.get("quote", {})
                    if quote:
                        st.session_state["active_quote"] = quote
                    else:
                        st.error("Quote not found")

        active_q = st.session_state.get("active_quote")
        if active_q:
            price = active_q.get("current_price", active_q.get("price", 0.0))
            chg = active_q.get("change_percent", 0.0)
            status = active_q.get("status", "LIVE")
            curr = active_q.get("currency", "INR")
            sym_char = "₹" if curr == "INR" else ("$" if curr == "USD" else curr)

            status_badge_class = "status-live" if status == "LIVE" else ("status-delayed" if status == "DELAYED" else "status-stale")
            chg_class = "trend-up" if chg >= 0 else "trend-down"

            st.markdown(f"""
            <div class="kpi-card" style="margin-top: 14px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 22px; font-weight: 700; color: #f8fafc;">{active_q.get('symbol')}</div>
                        <div style="font-size: 13px; color: #94a3b8;">{active_q.get('name')}</div>
                    </div>
                    <span class="status-badge {status_badge_class}">{status}</span>
                </div>
                <div style="margin-top: 16px; display: flex; align-items: baseline; gap: 14px;">
                    <div style="font-size: 32px; font-weight: 800; color: #f1f5f9;">{sym_char}{price:,.2f}</div>
                    <div class="{chg_class}" style="font-size: 16px; font-weight: 600;">{'+' if chg >= 0 else ''}{chg:.2f}%</div>
                </div>
                <div style="margin-top: 12px; font-size: 12px; color: #64748b;">
                    Provider Source: <b>{active_q.get('source')}</b> | Timestamp: {active_q.get('timestamp') or active_q.get('market_timestamp', 'Just now')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("➕ Add to My Watchlist", use_container_width=True):
                with st.spinner("Updating watchlist in Neo4j..."):
                    res = FinanceAPIClient.add_to_watchlist(active_q.get("symbol"), active_q.get("name"), active_q.get("asset_type", "STOCK"))
                    if res.get("status") == "SUCCESS":
                        st.success(f"Added {active_q.get('symbol')} to your watchlist!")
                        st.rerun()

    with m_col2:
        st.markdown("#### Personal Watchlist")
        with st.spinner("Fetching watchlist quotes..."):
            wl_res = FinanceAPIClient.get_watchlist()
            wl_items = wl_res.get("watchlist", [])

        if wl_items:
            for item in wl_items:
                sym = item.get("symbol")
                w_price = item.get("price", 0.0)
                w_chg = item.get("change_percent", 0.0)
                w_curr = item.get("currency", "INR")
                sym_c = "₹" if w_curr == "INR" else "$"
                chg_c = "trend-up" if w_chg >= 0 else "trend-down"

                st.markdown(f"""
                <div class="kpi-card" style="margin-bottom: 10px; padding: 12px 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-weight: 700; color: #f1f5f9;">{sym}</span>
                            <span style="font-size: 11px; color: #64748b; margin-left: 6px;">{item.get('asset_type')}</span>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-weight: 600; color: #f1f5f9;">{sym_c}{w_price:,.2f}</div>
                            <div class="{chg_c}" style="font-size: 11px; font-weight: 600;">{'+' if w_chg >= 0 else ''}{w_chg:.2f}%</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            syms_to_rem = [it["symbol"] for it in wl_items]
            rem_sym = st.selectbox("Remove from Watchlist", syms_to_rem, key="rem_wl_select")
            if st.button("Remove Symbol", type="secondary", use_container_width=True):
                with st.spinner("Removing from watchlist..."):
                    FinanceAPIClient.remove_from_watchlist(rem_sym)
                    st.success(f"Removed {rem_sym}")
                    st.rerun()
        else:
            st.info("Your watchlist is currently empty. Look up a ticker on the left to track it.")

# ---------------------------------------------------------
# Main App Router
# ---------------------------------------------------------
def main():
    if not st.session_state.get("token"):
        render_auth_screen()
        return

    active_page = render_sidebar()

    if "Executive Overview" in active_page:
        render_overview()
    elif "Transactions" in active_page:
        render_transactions()
    elif "Portfolio" in active_page:
        render_portfolio()
    elif "Analytics" in active_page:
        render_analytics()
    elif "Goals" in active_page:
        render_goals()
    elif "Assistant" in active_page:
        render_assistant()
    elif "Market" in active_page:
        render_market()

if __name__ == "__main__":
    main()
