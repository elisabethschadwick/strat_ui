from cProfile import label
from dash import html, dcc
import dash_bootstrap_components as dbc

TEAL = "#00D4AA"
RED = "#F43F5E"
MUTED = "#94A3B8"
TEXT = "#F1F5F9"
BG = "#0A0E1A"
CARD = "#111827"
BORDER = "#1E293B"
UI_FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
SANS = "'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'Helvetica Neue', Helvetica, Arial, sans-serif"

def card_wrapper(title, children_elements):
    return dbc.Card(
        dbc.CardBody([
            html.H5(title, style={"fontFamily": MONO, "color": TEAL, "fontSize": "1.5rem", "letterSpacing": "0.05em", "textTransform": "uppercase", "marginBottom": "1rem"}),
            html.Div(children_elements)
        ]),
        style={"backgroundColor": CARD, "border": f"1px solid {BORDER}", "borderRadius": "8px", "marginBottom": "1.5rem"}
    )

layout = html.Div(
    style={"backgroundColor": BG, "minHeight": "100vh", "padding": "2rem", "color": TEXT, "fontFamily": UI_FONT, "fontSize": "20px"},
    children=[
        html.Div([
            html.H3("MAIN STRATEGY DASHBOARD", style={"fontFamily": MONO, "fontWeight": "700", "color": TEXT, "letterSpacing": "0.15em", "margin": "0"}),
            html.Div(id="server-clock", style={"color": MUTED, "fontSize": "1rem"})
        ], style={"display": "flex", "justify-content": "space-between", "align-Items": "center", "paddingBottom": "1rem", "borderBottom": f"1px solid {BORDER}", "marginBottom": "2rem"}),
        card_wrapper("CURRENT STATUS & SYSTEM CONTROL", [
            dbc.Row([
                dbc.Col([
                    html.Div("Portfolio State:", style={
                        "fontSize": "1rem",
                        "color": MUTED,
                        "fontWeight": "700",
                        "letterSpacing": "0.06em",
                        "marginBottom": "0.5rem"}),
                    html.Div("SYNCHRONIZING", id="portfolio-status-indicator", style={"fontSize": "1.2rem", "fontWeight": "700", "color": MUTED})
                ], width=2),

                dbc.Col([
                        html.Div("Portfolio Actions:", style={
                        "fontSize": "1rem",
                        "color": MUTED,
                        "marginBottom": "0.55rem",
                        "fontWeight": "700",
                        "letterSpacing": "0.06em",
                        "textAlign": "center"
                    }),
                    html.Div([
                        dbc.Button("On",
                                   id="all-on-btn",
                                   color="success",
                                   style={
                                       "fontWeight": "700",
                                       "fontSize": "1.5rem",
                                       "borderRadius": "4px",
                                       "padding": "0.4rem 1.1rem"}),
                        dbc.Button("Off",
                                   id="all-off-btn",
                                   color="danger",
                                   className="ms-2",
                                   style={
                                       "fontWeight": "700",
                                       "fontSize": "1.5rem",
                                       "borderRadius": "4px",
                                       "padding": "0.4rem 1.1rem"}),
                    ], className="d-flex justify-content-center")
                ], width=2, style={
                    "borderRight": f"1px solid {BORDER}",
                    "paddingRight": "1.5rem",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "center",
                    "alignItems": "center"
                }),

                dbc.Col([
                    html.Div("Net P&L:", style={
                        "fontSize": "1rem",
                        "color": MUTED,
                        "fontWeight": "700",
                        "color": MUTED,
                        "marginBottom": "0.25rem"}),
                    html.Div("$0.00", id="total-pnl-node", style={
                        "fontSize": "2rem",
                        "fontWeight": "700",
                        "color": RED,
                        "fontFamily": SANS})
                ], width=2, className="ps-3"),

                dbc.Col([
                    html.Div("Daily P&L:", style={
                        "fontSize": "1rem",
                        "color": MUTED,
                        "fontWeight": "700",
                        "color": MUTED,
                        "marginBottom": "0.25rem"}),
                    html.Div("$0.00", id="daily-pnl-node", style={
                        "fontSize": "2rem",
                        "fontWeight": "700",
                        "color": RED,
                        "fontFamily": SANS})
                ], width=2),

                dbc.Col([
                    html.Div ("Current Long Capital:", style={
                        "fontSize": "1rem",
                        "color": MUTED,
                        "fontWeight": "700",
                        "marginBottom": "0.5rem",
                        "letterSpacing": "0.05em"}),
                    html.Div("$0.00", id="long-dollars-node", style={
                        "fontSize": "2rem",
                        "fontWeight": "600",
                        "color": TEAL,
                        "fontFamily": SANS})
                ], width=2),

                dbc.Col([
                    html.Div("Current Short Capital:", style={
                        "fontSize": "1rem",
                        "color": MUTED,
                        "fontWeight": "700",
                        "marginBottom": "0.25rem",
                        "letterSpacing": "0.05em"}),
                    html.Div("$0.00", id="short-dollars-node", style={
                        "fontSize": "2rem",
                        "fontWeight": "600",
                        "color": RED,
                        "fontFamily": SANS})
                ],width=2)
            ], align="center", className="g-2")
        ]),
        dbc.Row([
            dbc.Col([
                card_wrapper("WORKING ACTIVE LIMIT ORDERS", [
                    html.Div(id="open-orders-table-container")
                ]),
            ], lg=8, md=12),

            dbc.Col([
                card_wrapper("RECENT SYSTEM ACTIVITY", [
                    html.Div(
                        id="activity-feed-container",
                        style={
                            "maxHeight": "180px",
                            "overflowY": "auto",
                            "paddingRight": "5px",
                            "fontFamily": SANS,
                            "fontSize": "1rem"
                        }
                    )
                ]),
            ], lg=4, md=12)
        ], className="mb-3"),

        card_wrapper("AVAILABLE SYMBOLS", [
            html.Div("Select active symbol profile from 'pl *' registry map:", style={"fontSize": "1rem", "color": MUTED, "marginBottom": "0.5rem"}),
            dbc.Select(
                id="symbol-dropdown",
                options=[{"label": "BTC", "value": "BTC"}],
                value="BTC",
                style={
                    "backgroundColor": "#0D1526",
                    "color": "#F8FAFC",
                    "border": f"1px solid {BORDER}",
                    "fontFamily": SANS,
                    "fontSize": "1.1rem",
                    "paddingTop": "0.5rem",
                    "paddingBottom": "0.5rem",
                    "borderRadius": "4px",
                    "height": "auto"
                }
            )
        ]),

        card_wrapper("MANUAL ORDERS", [
            dbc.Row([
                dbc.Col([
                    html.Div("Order Target Symbol", style={"fontSize": "1rem", "color": MUTED, "marginBottom": "0.25rem"}),
                    dbc.Input(id="order-sym",
                              placeholder="BTC",
                              type="text",
                              style={
                                  "backgroundColor": "#0D1526",
                                  "color": TEXT,
                                  "border": f"1px solid {BORDER}"})
                ], md=3),
                dbc.Col([
                    html.Div("Execution Quantity Size", style={"fontSize": "1rem", "color": MUTED, "marginBottom": "0.25rem"}),
                    dbc.Input(id="order-qty", placeholder="0.15", type="number", style={"backgroundColor": "#0D1526", "color": TEXT, "border": f"1px solid {BORDER}"})
                ], md=3),
                dbc.Col([
                    html.Div("Limit Price Threshold", style={"fontSize": "1rem", "color": MUTED, "marginBottom": "0.25rem"}),
                    dbc.Input(id="order-px", placeholder="0.15", type="number", style={"backgroundColor": "#0D1526", "color": TEXT, "border": f"1px solid {BORDER}"})
                ], md=3),
                dbc.Col([
                    html.Div("\u00a0", style={"marginBottom": "0.25rem"}),
                    html.Div([
                        dbc.Button("BUY", id="manual-buy-btn", color="success", className="me-2", style={"width": "70px", "fontWeight": "700"}),
                        dbc.Button("SELL", id="manual-sell-btn", color="danger", style={"width": "70px", "fontWeight": "700"}),
                        html.Div(id="order-feedback-node", style={
                            "display": "inline-block",
                            "marginLeft": "15px",
                            "fontSize": "1rem",
                            "fontFamily": MONO,
                            "fontWeight": "600",
                            "verticalAlign": "middle"
                        })
                    ], style={"display": "flex", "alignItems": "center"})
                ], md=3)
            ], className="g-3"),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Span("CURRENT BID: ", style={"color": MUTED, "fontSize": "1rem"}),
                        html.Span("$0.0000", id="live-bid-price", style={"color": TEAL, "fontWeight": "700", "fontFamily": MONO, "fontSize": "0.9rem"})
                    ], style={"backgroundColor": "#0D1526", "padding": "0.5rem 1rem", "borderRadius": "4px", "border": f"1px solid {BORDER}"})
                ], md=6),
                dbc.Col([
                    html.Div([
                        html.Span("CURRENT ASK: ", style={"color": MUTED, "fontSize": "1rem"}),
                        html.Span("$0.0000", id="live-ask-price", style={"color": RED, "fontWeight": "700", "fontFamily": MONO, "fontSize": "0.9rem"})
                    ], style={"backgroundColor": "#0D1526", "padding": "0.5rem 1rem", "borderRadius": "4px", "border": f"1px solid {BORDER}"})
                ], md=6),
            ], className="g-3 mt-1"),
        ]),

        card_wrapper("CURRENT POSITIONS", [
            html.Div([
                dbc.RadioItems(
                    id="exchange-quick-filter",
                    className="btn-group d-flex w-100",
                    inputClassName="btn-check",
                    labelStyle={
                        "color": "#CBD5E1",
                        "borderColor": BORDER,
                        "fontWeight": "600",
                    },
                    labelClassName="btn btn-outline-primary py-2",
                    labelCheckedClassName="active",
                    options=[
                        {"label": "All", "value": "ALL"},
                        {"label": "Binance", "value": "BINANCE"},
                        {"label": "OKX", "value": "OKEX"},
                    ],
                    value="ALL",
                    style={"marginBottom": "1rem", "width": "100%"}
                ),
                dbc.Input(
                    id="ledger-filter-input",
                    placeholder="Filter by asset identifier or exchange origin...",
                    type="text",
                    style={
                        "backgroundColor": "#0D1526",
                        "color": TEXT,
                        "border": f"1px solid {BORDER}",
                        "width": "100%",
                        "padding": "0.6rem"
                    }
                )
            ], style={"display": "flex", "alignItems": "center", "flexWrap": "wrap"}),
            html.Div(id="ledger-table-container")
        ]),

        card_wrapper("HISTORICAL TRANSACTIONS", [
            dbc.Row([
                dbc.Col([
                    dbc.RadioItems(
                        id="trade-log-filter-preset",
                        options=[
                            {"label": "Today Only", "value": "TODAY"},
                            {"label": "All History", "value": "ALL"},
                        ],
                        value="TODAY",
                        inline=True,
                        style={"fontFamily": MONO, "fontSize": "1rem", "color": TEXT}
                    )
                ], md=4),
                dbc.Col([
                    dbc.Input(id="trade-log-search", placeholder="Filter trades", type="text", size="sm", style={"backgroundColor": "#0D1526", "color": TEXT, "border": f"1px solid {BORDER}", "maxWidth": "300px"})
                ], md=8, className="d-flex justify-content-md-end")
            ], style={"marginBottom": "1rem"}, className="align-items-center"),
            html.Div(id="trade-log-table-container")
        ]),

        card_wrapper("STRATEGY PERFORMANCE (P&L)", [
            dbc.Row([
                dbc.Col([
                    html.Div("STRATEGY RETURN ($)", style={"fontSize": "1rem", "color": MUTED, "marginBottom": "0.5rem"}),
                    dcc.Graph(id="dollar-pnl-graph", config={"displayModeBar": False})
                ], lg=6, md=12),
                dbc.Col([
                    html.Div("SHORT / LONG POSITIONS (%)", style={"fontSize": "1rem", "color": MUTED, "marginBottom": "0.5rem"}),
                    dcc.Graph(id="percent-pnl-graph", config={"displayModeBar": False})
                ], lg=6, md=12)
            ])
        ]),

        dcc.Store(id="cached-pnl-history", data={"times": [], "dollars": [], "percentages": []}),
        dcc.Interval(id="heartbeat-interval", interval=10000, disabled=False),
        dcc.Interval(id="clock-timer", interval=10000, disabled=False)
    ]
)