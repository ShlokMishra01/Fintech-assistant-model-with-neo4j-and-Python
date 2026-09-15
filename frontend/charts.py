import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any

DARK_PALETTE = [
    "#06b6d4", # cyan
    "#8b5cf6", # purple
    "#10b981", # emerald
    "#f59e0b", # amber
    "#ec4899", # pink
    "#3b82f6", # blue
    "#14b8a6", # teal
    "#f97316"  # orange
]

def apply_dark_layout(fig, title: str = "", height: int = 340):
    """
    Applies consistent premium dark theme styling to Plotly figures.
    """
    fig.update_layout(
        title={
            "text": f"<b>{title}</b>" if title else "",
            "font": {"size": 15, "color": "#f1f5f9"},
            "x": 0.02,
            "y": 0.95
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94a3b8", "family": "Outfit, sans-serif"},
        margin=dict(l=20, r=20, t=45 if title else 20, b=20),
        height=height,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color="#cbd5e1")
        )
    )
    return fig

def render_allocation_donut(allocations: List[Dict[str, Any]], title: str = "Asset Allocation", is_asset_type: bool = True):
    """
    Renders an elegant donut chart for asset or holding allocation.
    """
    if not allocations:
        fig = go.Figure()
        fig.add_annotation(text="No active holdings to display", showarrow=False, font=dict(size=14, color="#64748b"))
        return apply_dark_layout(fig, title=title, height=300)

    labels = [item.get("asset_type" if is_asset_type else "symbol", "Other") for item in allocations]
    values = [item.get("value", 0.0) for item in allocations]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.62,
        textinfo="label+percent",
        textposition="outside",
        marker=dict(colors=DARK_PALETTE, line=dict(color="#0f172a", width=2)),
        hovertemplate="<b>%{label}</b><br>Value: ₹%{value:,.2f}<br>Share: %{percent}<extra></extra>"
    )])

    return apply_dark_layout(fig, title=title, height=340)

def render_net_worth_breakdown(net_worth_data: Dict[str, Any]):
    """
    Visualizes Consolidated Assets vs Liabilities and Net Worth.
    """
    if not net_worth_data:
        return go.Figure()

    categories = ["Liquid Cash", "Portfolio Value", "Total Debt", "Net Worth"]
    values = [
        net_worth_data.get("liquid_cash", 0),
        net_worth_data.get("portfolio_value", 0),
        -net_worth_data.get("total_liabilities", 0),
        net_worth_data.get("total_net_worth", 0)
    ]
    colors = ["#06b6d4", "#8b5cf6", "#f43f5e", "#10b981"]

    fig = go.Figure(go.Bar(
        x=categories,
        y=values,
        marker_color=colors,
        text=[f"₹{abs(v):,.0f}" for v in values],
        textposition="auto",
        hovertemplate="<b>%{x}</b><br>Amount: ₹%{y:,.2f}<extra></extra>"
    ))

    fig.update_yaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.06)", zerolinecolor="rgba(255, 255, 255, 0.2)")
    fig.update_xaxes(showgrid=False)
    return apply_dark_layout(fig, title="Asset & Liability Breakdown", height=320)

def render_expense_categories_bar(categories: List[Dict[str, Any]]):
    """
    Renders horizontal bar chart of spending per category.
    """
    if not categories:
        fig = go.Figure()
        fig.add_annotation(text="No expense transactions recorded", showarrow=False, font=dict(size=14, color="#64748b"))
        return apply_dark_layout(fig, title="Monthly Category Expenses", height=280)

    cats = [c["category"] for c in categories]
    amts = [c["amount"] for c in categories]

    fig = go.Figure(go.Bar(
        x=amts,
        y=cats,
        orientation="h",
        marker=dict(
            color=amts,
            colorscale=[[0, "#38bdf8"], [1, "#0284c7"]],
            line=dict(color="#0f172a", width=1)
        ),
        text=[f"₹{a:,.0f}" for a in amts],
        textposition="outside",
        hovertemplate="<b>%{y}</b>: ₹%{x:,.2f}<extra></extra>"
    ))

    fig.update_xaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.06)")
    fig.update_yaxes(showgrid=False, autorange="reversed")
    return apply_dark_layout(fig, title="Monthly Category Expenses", height=300)

def render_savings_gauge(savings_rate: float):
    """
    Renders a semi-circular radial gauge indicating savings rate vs healthy benchmarks.
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=savings_rate,
        number={"suffix": "%", "font": {"size": 32, "color": "#f8fafc"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#475569"},
            "bar": {"color": "#06b6d4"},
            "bgcolor": "#1e293b",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 20], "color": "rgba(239, 68, 68, 0.25)"},
                {"range": [20, 40], "color": "rgba(245, 158, 11, 0.25)"},
                {"range": [40, 100], "color": "rgba(16, 185, 129, 0.25)"}
            ],
            "threshold": {
                "line": {"color": "#34d399", "width": 3},
                "thickness": 0.8,
                "value": 20
            }
        }
    ))

    return apply_dark_layout(fig, title="Monthly Savings Rate", height=240)
