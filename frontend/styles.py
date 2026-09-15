import streamlit as st

def apply_custom_styles():
    """
    Injects custom CSS tokens and classes for a dense, high-contrast, modern dark financial terminal.
    """
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #f3f4f6;
        }

        code, pre, .mono {
            font-family: 'JetBrains Mono', monospace !important;
        }

        /* Top header padding reduction */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 3rem !important;
            max-width: 1400px;
        }

        /* Hero Banner */
        .hero-banner {
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.12) 0%, rgba(139, 92, 246, 0.12) 50%, rgba(16, 185, 129, 0.08) 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 24px 30px;
            margin-bottom: 24px;
            backdrop-filter: blur(12px);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }

        .hero-title {
            font-size: 26px;
            font-weight: 700;
            letter-spacing: -0.5px;
            margin-bottom: 6px;
            background: linear-gradient(90deg, #38bdf8, #818cf8, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero-subtitle {
            font-size: 14px;
            color: #9ca3af;
            margin-bottom: 0;
        }

        /* KPI Card Container */
        .kpi-card {
            background: #111827;
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 14px;
            padding: 18px 20px;
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
            position: relative;
            overflow: hidden;
        }

        .kpi-card:hover {
            transform: translateY(-2px);
            border-color: rgba(6, 182, 212, 0.4);
            box-shadow: 0 10px 25px -5px rgba(6, 182, 212, 0.1);
        }

        .kpi-label {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            font-weight: 600;
            color: #94a3b8;
            margin-bottom: 6px;
        }

        .kpi-value {
            font-size: 24px;
            font-weight: 700;
            color: #f8fafc;
            letter-spacing: -0.5px;
            margin-bottom: 4px;
        }

        .kpi-sub {
            font-size: 12px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .trend-up {
            color: #34d399;
        }

        .trend-down {
            color: #f87171;
        }

        .trend-neutral {
            color: #94a3b8;
        }

        /* Status Badges */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 3px 9px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .status-live {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .status-delayed {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        .status-stale {
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }

        .status-user {
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.3);
        }

        /* Evidence Card */
        .evidence-box {
            background: #0d1322;
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 12px;
            padding: 16px 20px;
            margin: 14px 0;
        }

        .evidence-header {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            font-weight: 600;
            color: #38bdf8;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 12px;
        }

        .fact-row {
            display: flex;
            justify-content: space-between;
            padding: 7px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 13px;
        }

        .fact-row:last-child {
            border-bottom: none;
        }

        .fact-label {
            color: #94a3b8;
        }

        .fact-val {
            font-weight: 600;
            color: #f1f5f9;
        }

        .fact-src {
            font-size: 11px;
            color: #64748b;
            font-style: italic;
            margin-left: 6px;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #0b0f19;
            border-right: 1px solid rgba(255, 255, 255, 0.06);
        }

        /* Interactive buttons */
        div.stButton > button {
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.2s ease;
        }

        div.stButton > button:hover {
            border-color: #06b6d4;
            box-shadow: 0 4px 15px -3px rgba(6, 182, 212, 0.25);
        }
    </style>
    """, unsafe_allow_html=True)
