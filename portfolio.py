from dash import Dash, html, dcc, Input, Output, State, dash_table
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from auth.schwab_auth import get_client

app = Dash(__name__)

def fetch_portfolio_data(holdings):
    rows=[]
    for h in holdings:
        ticker = h["ticker"]
        shares = h["shares"]
        avg_cost = h["avg_cost"]

        try:
            current_price = yf.Ticker(ticker).fast_info["last_price"]
        except:
            current_price = 0

        market_value = round(current_price * shares, 2)
        cost_basis = round(avg_cost * shares, 2)
        pnl = round(market_value - cost_basis, 2)
        pnl_pct = round((pnl / cost_basis) * 100, 2) if cost_basis else 0

        rows.append({
            "Ticker": ticker,
            "Shares": shares,
            "Avg Cost": avg_cost,
            "Current Price": round(current_price,2),
            "Market Value": market_value,
            "P&L ($)": pnl,
            "P&L (%)": pnl_pct
        })
    return pd.DataFrame(rows)

def fetch_performance(holdings):
    combined = None
    for h in holdings:
        hist = yf.download(h["ticker"], period="6mo", interval="1d", auto_adjust=True)
        hist.columns = hist.columns.get_level_values(0)
        hist["value"] = hist["Close"] * h["shares"]
        combined = hist[["value"]] if combined is None else combined + hist[["value"]]
    return combined

app.layout = html.Div(
    style={
        "fontFamily": "'Segoe UI', sans-serif",
        "backgroundColor": "#0f1117",
        "color": "#e0e0e0",
        "minHeight": "100vh",
        "padding": "32px"
    },
    children=[
        html.H1("Portfolio Dashboard", style={"color":"#00d4aa", "marginBottom":"24px"}),

        dcc.Store(id="portfolio-store",data=[]),

        html.Div(
            style={"display": "flex", "gap": "12px", "marginBottom": "24px", "alignItems": "center"},
            children=[
                dcc.Input(id="input-ticker", placeholder="Ticker (e.g. AAPL)", type="text",
                          style={"padding": "8px", "backgroundColor": "#1e2130", "color": "#e0e0e0","border": "1px solid #333", "borderRadius": "4px"}),
                dcc.Input(id="input-shares", placeholder="Shares", type="number",
                          style={"padding": "8px", "backgroundColor": "#1e2130", "color": "#e0e0e0", "border": "1px solid #333", "borderRadius": "4px"}),
                dcc.Input(id="input-cost", placeholder="Avg Cost ($)", type="number",
                          style={"padding": "8px", "backgroundColor": "#1e2130", "color": "#e0e0e0", "border": "1px solid #333", "borderRadius": "4px"}),
                html.Button("Add Position", id="add-button", n_clicks=0,
                            style={"padding": "8px 16px", "backgroundColor": "#00d4aa", "color": "#0f1117",
                                   "border": "none", "borderRadius": "4px", "cursor": "pointer", "fontWeight": "bold"}),
                html.Button("Clear All", id="clear-button", n_clicks=0,
                            style={"padding": "8px 16px", "backgroundColor": "#ff4444", "color": "white",
                                   "border": "none", "borderRadius": "4px", "cursor": "pointer"})
            ]
        ),

        html.H3("Positions", style={"color": "#00d4aa"}),
        dash_table.DataTable(
            id="positions-table",
            style_table={"overflowX": "auto"},
            style_cell={"backgroundColor": "#1e2130", "color": "#e0e0e0", "border": "1px solid #333", "padding": "8px"},
            style_data_conditional=[
                {"if": {"filter_query": "{P&L ($) < 0", "column_id": "P&L ($)"}, "color": "#ff444"},
                {"if": {"filter_query": "{P&L ($) < 0", "column_id": "P&L ($)"}, "color": "#00d4aa"},
                {"if": {"filter_query": "{P&L (%) < 0", "column_id": "P&L (%)"}, "color": "#ff444"},
                {"if": {"filter_query": "{P&L (%) < 0", "column_id": "P&L (%)"}, "color": "#00d4aa"}
            ]
        ),
        html.Div(
            style={"display": "flex", "gap": "24px", "marginTop": "32px"},
            children=[
                dcc.Graph(id="allocation-chart", style={"flex": "1"}),
                dcc.Graph(id="performance-chart", style={"flex": "2"})
            ]
        )
    ]
)

from dash import ctx

@app.callback(
    Output("portfolio-store", "data"),
    Input("add-button", "n_clicks"),
    Input("clear-button", "n_clicks"),
    State("input-ticker", "value"),
    State("input-shares", "value"),
    State("input-cost", "value"),
    State("portfolio-store", "data")
)

def update_portfolio(add_clicks, clear_clicks, ticker, shares, cost, portfolio):
    triggered = ctx.triggered_id
    if triggered == "clear-button":
        return[]

    if triggered == "add-button":
        if ticker and shares and cost:
            portfolio.append({
                "ticker": ticker.upper().strip(),
                "shares": float(shares),
                "avg_cost": float(cost)
            })
    return portfolio

@app.callback(
    Output("positions-table", "data"),
    Output("positions-table", "columns"),
    Output("allocation-chart", "figure"),
    Output("performance-chart", "figure"),
    Input("portfolio-store", "data")
)

def update_visuals(portfolio):
    empty_fig = go.Figure().update_layout(
        paper_bgcolor="#0f1117", plot_bgcolor="#0f1117", font=dict(color="#e0e0e0")
    )

    if not portfolio:
        return [], [], empty_fig, empty_fig

    df = fetch_portfolio_data(portfolio)

    columns = [{"name": c, "id": c} for c in df.columns]
    table_data = df.to_dict("records")

    pie = px.pie(
        df, values="Market Value", names="Ticker",
        title="Portfolio Allocation",
        color_discrete_sequence=px.colors.sequential.Teal
    )
    pie.update_layout(paper_bgcolor="#0f1117", font=dict(color="#e0e0e0"))

    perf = fetch_performance(portfolio)
    perf_fig = go.Figure()
    if perf is not None:
        perf_fig.add_trace(go.Scatter(
            x=perf.index, y=perf["value"],
            fill="tozeroy", line=dict(color="#00d4aa"),
            name="Portfolio Value"
        ))
    perf_fig.update_layout(
        title="Portfolio Value - Last 6 Months",
        paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
        font=dict(color="#e0e0e0")
    )

    return table_data, columns, pie, perf_fig

if __name__ == "__main__":
    app.run(debug=True)