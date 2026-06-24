import time
import re
import requests
import config
from pip._internal.utils import subprocess

import commander
import pandas as pd
from dash import Input, Output, State, ctx, html, no_update
import dash_bootstrap_components as dbc
from app_instance import app
import sqlalchemy
from sqlalchemy import text, create_engine

api_session = requests.Session()
api_session.auth = (commander.USER, commander.PWD)
api_session.cert = (commander.cert_file, commander.key_file)
api_session.verify = False
commander.requests = api_session

db_engine = config.get_engine()
PYTHON_EXE = "/home/lisa/dev/strat_ui/.venv/bin/python"
COMMANDER_SCRIPT = "/home/lisa/dev/strat_ui/commander.py"

TEAL = "#00D4AA"
RED = "#F43F5E"
MUTED = "#94A3B8"
TEXT = "#F1F5F9"
BORDER = "#1E293B"
UI_FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
SANS = "'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'Helvetica Neue', Helvetica, Arial, sans-serif"

def run_commander_cli(command_text):
    import sys
    import importlib
    built_in_subprocess = importlib.import_module("subprocess")
    cmd = [PYTHON_EXE, COMMANDER_SCRIPT, "--aws"]
    process = None
    try:
        process = built_in_subprocess.Popen(
            cmd,
            stdin = built_in_subprocess.PIPE,
            stdout = built_in_subprocess.PIPE,
            stderr = built_in_subprocess.PIPE,
            text=True,
        )
        process.stdin.write(f"{command_text}\n")
        process.stdin.flush()
        time.sleep(0.15)
        #full_input_sequence = f"{command_text}\nexit\n"
        stdout, stderr = process.communicate(input=f"{command_text}\n", timeout=5)
        return stdout + "\n" + stderr
    except built_in_subprocess.TimeoutExpired:
        if process is not None:
            process.kill()
        return "ERROR: Interactive console channel timed out."
    except Exception as e:
        if process is not None:
            process.kill()
        return f"ERROR: Failed to write to terminal stream: {str(e)}"

def parse_terminal_string(raw_text):
    parsed_profiles = {}
    if not raw_text:
        return parsed_profiles

    normalized_text = str(raw_text).replace('\r', '\n')
    lines = normalized_text.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = re.search(r"(?:^|\s)\d+:\s*(?:^|\s|\d+:\s*)([A-Za-z0-9\-_\.]+)\s*:\s*(.*)$", line)
        if match:
            symbol_key = match.group(1).strip()
            property_block = match.group(2).strip()

            if "file " in symbol_key.lower() or "traceback" in symbol_key.lower():
                continue

            properties = {}
            pairs = re.findall(r"([a-z_0-9]+)=([^\s]+)", property_block)
            for k, v in pairs:
                try:
                    properties[k] = float(v) if "nan" not in v.lower() else 0.0
                except ValueError:
                    properties[k] = v
            if properties:
                parsed_profiles[symbol_key] = properties

    return parsed_profiles

def parse_open_orders(raw_text):
    parsed_orders = []
    if not raw_text or "id=" not in str(raw_text).lower():
        return parsed_orders

    normalized_text = str(raw_text).replace('\r', '\n')
    lines = normalized_text.split("\n")

    seen_ids = set()

    for line in lines:
        line = line.strip()
        if not line or "id=" not in line.lower():
            continue

        match = re.search(r"Id=(\d+):\s*\[(.*?)\]\s*(.*?)\s+IntId=.*?\s+(Buy|Sell)\s+([\d\.]+)\s*@\s*([\d\.]+)\s*\$val=([\d\.]+)", line, re.IGNORECASE)
        if match:
            order_id = match.group(1)
            if order_id in seen_ids:
                continue
            seen_ids.add(order_id)

            parsed_orders.append({
                "id": match.group(1),
                "engine_sym": match.group(2),
                "ticker": match.group(3),
                "side": match.group(4).upper(),
                "qty": float(match.group(5)),
                "price": float(match.group(6)),
                "value": float(match.group(7))
            })

    return parsed_orders

def fetch_historical_trades(engine, view_preset, symbol_search=None):
    query_base = """
        SELECT execution_time, symbol, side, quantity, price, total_usd_value, execution_source
        FROM {}
    """
    conditions = []
    params = {}
    if view_preset == "TODAY":
        conditions.append("execution_time >= CURRENT_DATE")

    if symbol_search:
        conditions.append("symbol ILIKE :symbol")
        params["symbol"] = f"%{symbol_search.strip()}%"

    if conditions:
        query_base += " WHERE " + " AND ".join(conditions)

    query_base += " ORDER BY execution_time DESC LIMIT 200;"

    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query_base), conn, params=params)
        return df
    except:
        print("DB ERROR: Failed to extract trade logs")
        return pd.DataFrame()


def clean_string(val):
    return str(val) if val is not None else ""

def fallback_msg(txt, style=None):
    final_style = style if style is not None else {"color": MUTED, "fontSize": "0.85rem"}
    return [html.Span(str(txt), style=final_style)]

def empty_chart():
    return {"data": [], "layout": {"paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)", "margin": {"l": 40, "r": 10, "b": 20, "t": 10}, "xaxis": {"color": MUTED}, "yaxis": {"color": MUTED, "showgrid": True, "gridcolor": BORDER}}}

@app.callback(
    #Output("global-feedback", "children"),
    Output("portfolio-status-indicator", "children"),
    Output("portfolio-status-indicator", "style"),
    Output("order-feedback-node", "children"),
    Output("live-bid-price", "children"),
    Output("live-ask-price", "children"),
    Output("symbol-dropdown", "options"),
    Output("symbol-dropdown", "value"),
    Output("long-dollars-node", "children"),
    Output("short-dollars-node", "children"),
    Output("total-pnl-node", "children"),
    Output("total-pnl-node", "style"),
    Output("daily-pnl-node", "children"),
    Output("ledger-table-container", "children"),
    Output("open-orders-table-container", "children"),
    Output("activity-feed-container", "children"),
   # Output("dollar-pnl-graph", "figure"),
    Output("percent-pnl-graph", "figure"),
    Output("cached-pnl-history", "data"),

    Input("all-on-btn", "n_clicks"),
    Input("all-off-btn", "n_clicks"),
    Input("manual-buy-btn", "n_clicks"),
    Input("manual-sell-btn", "n_clicks"),
    Input("heartbeat-interval", "n_intervals"),
    Input("exchange-quick-filter", "value"),

    State("order-sym", "value"),
    State("order-qty", "value"),
    State("order-px", "value"),
    State("ledger-filter-input", "value"),
    State("cached-pnl-history", "data"),
    prevent_initial_call=False
)

def process_trading_desk(all_on, all_off, buy, sell, heartbeat, quick_exchange, sym, qty, px, filter_text, chart_store):
    triggered = ctx.triggered_id
    console_output_str = ""
    portfolio_enabled = None

    total_long_exposure = 0.0
    total_short_exposure = 0.0
    aggregated_cumu_pnl = 0.0
    aggregated_daily_pnl = 0.0
    enabled_rows_count = 0
    dropdown_options = []
    table_rows = []

    if triggered == "all-on-btn":
        console_output_str = run_commander_cli("on")
        if "portfolio enabled" in console_output_str.lower():
            portfolio_enabled = True

    elif triggered == "all-off-btn":
        console_output_str = run_commander_cli("alloff")
        if "portfolio disabled" in console_output_str.lower():
            portfolio_enabled = False

    elif triggered =="manual-buy-btn" and sym and px:
        console_output_str = run_commander_cli(f"buy {str(sym).strip()} px={px} qty={qty or 0.15}")

    elif triggered == "manual-sell-btn" and sym and px:
        console_output_str = run_commander_cli(f"sell {str(sym).strip()} px={px} qty={qty or 0.15}")

    raw_pl_output = run_commander_cli("pl *")
    asset_data_map = parse_terminal_string(raw_pl_output)

    raw_orders_output = run_commander_cli("orders")
    open_orders_list = parse_open_orders(raw_orders_output)

    order_rows = []
    for o in open_orders_list:
        is_buy = o['side'] == 'BUY'
        engine_key = o['engine_sym']

        current_market_px = 0.0
        if asset_data_map and engine_key in asset_data_map:
            current_market_px = float(asset_data_map[engine_key].get("refpx", 0.0))

        if current_market_px > 0:
            px_distance = current_market_px - o['price']
            pct_distance = (px_distance / current_market_px) * 100
            distance_str = f"{pct_distance:.2f}%" if is_buy else f"{-pct_distance:+.2f}%"
            market_px_str = f"${current_market_px:,.4f}"
        else:
            distance_str = "N/A"
            market_px_str = "FETCHING..."

        order_rows.append(html.Tr([
            html.Td(f"#{o['id']}", style={"color": MUTED, "fontWeight": "600"}),
            html.Td(o['engine_sym'], style={"fontSize": "1rem"}),
            html.Td(o['side'], style={"color": TEAL if is_buy else RED, "fontWeight": "700"}),
            html.Td(f"{o['qty']:.4f}"),
            html.Td(f"${o['price']:,.4f}"),
            html.Td(market_px_str, style={"color": TEXT}),
            html.Td(distance_str, style={"color": MUTED, "fontFamily": MONO}),
            html.Td(f"${o['value']:,.2f}", style={"color": TEAL if is_buy else RED})
        ]))

    if order_rows:
        open_orders_layout = dbc.Table([
            html.Thead(html.Tr([
                html.Th("ID"), html.Th("Engine Identifier Path"), html.Th("Side"),
                html.Th("Quantity"), html.Th("Limit Price"), html.Th("Current Price"),
                html.Th("Dist. to Fill"), html.Th("Est. Value")
            ]), style={"color": MUTED, "fontSize": "1rem"}),
            html.Tbody(order_rows)
        ], bordered=True, hover=True, size="sm", responsive=True, style={"color": TEXT, "fontSize": "0.85rem", "marginTop": "0.5rem"})
    else:
        open_orders_layout = html.Div("No active working orders.", style={"color": MUTED, "fontSize": "0.8rem", "fontFamily": MONO, "padding": "0.5rem 0"})

    df_activity = fetch_historical_trades(db_engine, "TODAY", None)
    activity_items = []

    if not df_activity.empty:
        for _, r in df_activity.head(4).iterrows():
            is_buy = str(r['side']).upper() == 'BUY'
            actor = "You manually" if str(r['execution_source']).upper() == "MANUAL" else "The system automatically"
            verb = "bought" if is_buy else "sold"
            clean_ticker = str(r['symbol']).split('.')[-1].replace('-SWAP', '').replace('.S', '')
            timestamp = pd.to_datetime(r['execution_time']).strftime('%H:%M:%S')

            sentence = f"[{timestamp}] {actor} {verb} {r['quantity']:.2f} units of {clean_ticker} at ${r['price']:,.2f}."
            color_border = TEAL if is_buy else RED

            activity_items.append(html.Div(
                sentence,
                style={
                    "color": TEXT,
                    "borderLeft": f"3px solid {color_border}",
                    "paddingLeft": "8px",
                    "marginBottom": "0.5rem",
                    "lineHeight": "1.3"
                }
            ))

    if not activity_items:
        activity_items = html.Div("Live monitoring active. No trades executed today.", style={"color": MUTED, "fontStyle": "italic"})

    if not console_output_str:
        clean_display = str(raw_pl_output)

        if "Traceback" in clean_display:
            clean_display = clean_display.split("Traceback")[0]
        elif "EOFError" in clean_display:
            clean_display = clean_display.split("EOFError")[0]

        if "\n: 1: OKEX" in clean_display:
            clean_display = clean_display.split("\n2: ")[0]

        if clean_display.endswith("\n3:"):
            clean_display = clean_display.rsplit("\n3:", 1)[0]
        elif clean_display.endswith("\n2:"):
            clean_display = clean_display.rsplit("\n2:", 1)[0]

        console_output_str = clean_display.strip()
    if triggered in ["manual-buy-btn", "manual-sell-btn", "all-on-btn", "all-off-btn"]:
        if "error" in console_output_str.lower() or "fail" in console_output_str.lower():
            order_feedback = html.Span("EXECUTION FAILED", style = {"color": RED})
        else:
            order_feedback = html.Span("TRANSMITTED SUCCESSFULLY", style={"color": TEAL})
    else:
        order_feedback = ""

    asset_data_map = parse_terminal_string(raw_pl_output)

    dropdown_options = []
    table_rows = []
    total_long_exposure = 0.0
    total_short_exposure = 0.0
    aggregated_cumu_pnl = 0.0
    enabled_rows_count = 0

    if asset_data_map:
        dropdown_options = [{f"label": str(k), "value": str(k)} for k in sorted(asset_data_map.keys())]
        for asset_name, props in asset_data_map.items():
            enabled = int(props.get("enabled", 0))
            if enabled ==1:
                enabled_rows_count += 1

            ref_px = props.get("refpx", 0.0)
            cumu_pnl = props.get("cumu_net_pnl", 0.0)
            daily_pnl = props.get("daily_net_pnl", props.get("daily_pnl", 0.0))
            long_dlrs = props.get("long_dollars", 0.0)
            short_dlrs = props.get("short_dollars", 0.0)

            if quick_exchange and quick_exchange != "ALL":
                if quick_exchange.lower() not in asset_name.lower():
                    continue

            if filter_text:
                f_term = str(filter_text).upper().strip()
                if f_term not in asset_name.upper() and f_term not in ("ENABLED" if enabled else "DISABLED"):
                    continue

            total_long_exposure += long_dlrs
            total_short_exposure += short_dlrs
            aggregated_cumu_pnl += cumu_pnl
            aggregated_daily_pnl += daily_pnl

            table_rows.append(html.Tr([
                html.Td(asset_name, style={"fontWeight": "600", "fontSize": "1rem"}),
                html.Td("ENABLED" if enabled else "DISABLED", style={"color": TEAL if enabled else RED, "fontSize": "0.75rem"}),
                html.Td(f"${ref_px:,.4f}"),
                html.Td(f"${long_dlrs:,.2f}", style={"color": TEAL if long_dlrs > 0 else TEXT}),
                html.Td(f"${short_dlrs:,.2f}", style={"color": RED if short_dlrs > 0 else TEXT}),
                html.Td(f"${cumu_pnl:,.2f}", style={"color": TEAL if cumu_pnl >= 0 else RED})
            ]))

        if portfolio_enabled is None:
            portfolio_enabled = True if enabled_rows_count > 0 else False

    if portfolio_enabled is True:
        badge_text = "ENABLED"
        badge_style = {
            "display": "inline-block", "padding": "0.25rem 0.75rem", "borderRadius": "4px",
            "fontFamily": SANS, "fontSize": "0.9rem", "fontWeight": "700", "letterSpacing": "0.04em",
            "backgroundColor": "rgba(0, 212, 170, 0.15)", "color": TEAL, "border": f"1px solid {TEAL}"
        }
    else:
        badge_text = "DISABLED"
        badge_style = {
            "display": "inline-block", "padding": "0.25rem 0.75rem", "borderRadius": "4px",
            "fontFamily": SANS, "fontSize": "0.9rem", "fontWeight": "700", "letterSpacing": "0.04em",
            "backgroundColor": "rgba(244, 63, 94, 0.15)", "color": RED, "border": f"1px solid {RED}"
        }

    if not isinstance(chart_store, dict) or "times" not in chart_store:
        chart_store = {
            "times": [],
            "dollars": [],
            "long_track": [],
            "short_track": [],
            "net_track": [],
            "spread_track": []
        }

    required_keys = ["long_track", "short_track", "net_track", "spread_track"]
    for r_key in required_keys:
        if r_key not in chart_store:
            chart_store[r_key] = [0.0] * len(chart_store.get("times", [])
                                             )
    current_timestamp = time.strftime('%H:%M:%S')
    chart_store["times"].append(current_timestamp)
    chart_store["dollars"].append(aggregated_cumu_pnl)
    chart_store["long_track"].append(total_long_exposure)
    chart_store["short_track"].append(total_short_exposure)
    chart_store["net_track"].append(total_long_exposure + total_short_exposure)
    chart_store["spread_track"].append(total_long_exposure - total_short_exposure)

    for k in chart_store.keys():
        if k != "times":
            chart_store[k] = chart_store[k][-100:]
    chart_store["times"] = chart_store["times"][-100:]

    dollar_fig = {
        "data": [{"x": chart_store["times"], "y": chart_store["dollars"], "type": "scatter", "mode": "lines",
                  "line": {"color": TEAL, "width": 2}}],
        "layout": {"paper_bgcolor": "rgba(0,0,0,0)",
                   "plot_bgcolor": "rgba(0,0,0,0)",
                   "margin": {"l": 50, "r": 10, "b": 20, "t": 10},
                   "xaxis": {"color": MUTED,
                             "showgrid": True,
                             "gridcolor": MUTED,
                             "tickfont": {"size": 9}},
                   "yaxis": {
                       "color": MUTED,
                       "showgrid": True,
                       "gridcolor": "rgba(30, 41, 59, 0.4)",
                       "tickprefix": "$",
                       "tickfont": {"size": 9}}}
    }
    exposure_fig = {
        "data": [
            {
                "x": chart_store["times"],
                "y": chart_store["long_track"],
                "type": "scatter",
                "mode": "lines",
                "name": "Long",
                "line": {"color": TEAL, "width": 2},
                "yaxis": "y1"
            },
            {
                "x": chart_store["times"],
                "y": chart_store["short_track"],
                "type": "scatter",
                "mode": "lines",
                "name": "Short",
                "line": {"color": RED, "width": 2},
                "yaxis": "y1"
            },
            {
                "x": chart_store["times"],
                "y": chart_store["net_track"],
                "type": "scatter",
                "mode": "lines",
                "name": "Short + Long",
                "line": {"color": "#3B2F6", "width": 2},
                "yaxis": "y2"
            },
            {
                "x": chart_store["times"],
                "y": chart_store["spread_track"],
                "type": "scatter",
                "mode": "lines",
                "name": "Long - Short (Net Exposure)",
                "line": {"color": "#EAB308", "width": 2},
                "yaxis": "y2"
            }],
        "layout": {
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "margin": {"l": 50, "r": 10, "b": 20, "t": 10},
            "showLegend": True,
            "legend": {
                "font": {"color": "#FFFFFF", "size": 10, "weight": "600"},
                "orientation": "h",
                "y": -0.25
            },
            "xaxis": {
                "color": "F1F5F9",
                "showgrid": True,
                "gridcolor": MUTED,
                "tickfont": {"size": 9}},
            "yaxis": {
                "color": TEAL,
                "showgrid": True,
                "gridcolor": "rgba(30, 41, 59, 0.4)",
                "tickprefix": "$",
                "tickfont": {"size": 9},
                "autorange": True
            },
            "yaxis2": {
                "color": "#3B82F6",
                "anchor": "x",
                "overlaying": "y",
                "side": "right",
                "showgrid": False,
                "tickprefix": "$",
                "tickfont": {"size": 9},
                "autorange": True
            }
        }
    }

    if table_rows:
        table_rows.append(html.Tr([
            html.Td("TOTALS", style={"fontWeight": "800", "color": TEAL, "fontSize": "1rem", "letterSpacing": "0.05em"}),
            html.Td("", style={"borderTop": f"2px solid {BORDER}"}),
            html.Td("", style={"borderTop": f"2px solid {BORDER}"}),
            html.Td(f"${total_long_exposure:,.2f}", style={"fontWeight": "700", "color": TEAL, "borderTop": f"2px solid {BORDER}"}),
            html.Td(f"${total_short_exposure:,.2f}", style={"fontWeight": "700", "color": RED, "borderTop": f"2px solid {BORDER}"}),
            html.Td(f"${aggregated_cumu_pnl:,.2f}", style={"fontWeight": "700", "color": TEAL if aggregated_cumu_pnl >= 0 else RED, "borderTop": f"2px solid {BORDER}"}),
        ], style={"backgroundColor": "#0F172A", "borderTop": f"2px solid {BORDER}"}))

        table_layout = [
            dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Engine Profile ID"), html.Th("State"), html.Th("Reference Px"), html.Th("Long Capital"), html.Th("Short Capital"), html.Th("Cumulative Net P&L")
                ]), style={"color": MUTED, "fontSize": "1rem"}),
                html.Tbody(table_rows)
            ], bordered=True, hover=True, size="sm", responsive=True, style={"color": TEXT, "fontSize": "1rem"})
            ]
    else:
        table_layout = fallback_msg("No active system rows found.", style={"color": TEXT})
    if not dropdown_options:
        dropdown_options = [{"label": "BTC-USDT", "value": "BTC-USDT"}]
        dropdown_value_out = "BTC-USDT"
    elif triggered is None or triggered == "heartbeat-interval":
        from dash import no_update
        dropdown_value_out = no_update
    else:
        dropdown_value_out = dropdown_options[0]["value"]

    long_dollars_text = f"${total_long_exposure:,.2f}"
    short_dollars_text = f"${total_short_exposure:,.2f}"
    status_text = "SHELL SYNCHRONIZED"
    status_style = {"color": TEAL, "fontSize": "1.3rem", "fontWeight": "700"}

    if portfolio_enabled is True:
        status_text = "PORTFOLIO: ENABLED"
        status_style = {"color": TEAL, "fontSize": "1.3rem", "fontWeight": "700", "letterSpacing": "0.05em"}
    else:
        status_text = "PORTFOLIO: DISABLED"
        status_style = {"color": RED, "fontSize": "1.3rem", "fontWeight": "700", "letterSpacing": "0.05em"}

    bid_out = "$0.0000"
    ask_out = "$0.0000"
    active_sym_key = str(sym).strip() if sym else "BTC"

    matched_profile = None
    if asset_data_map:
        for k in asset_data_map.keys():
            if active_sym_key.upper() in k.upper():
                matched_profile = asset_data_map[k]
                break

            if matched_profile:
                ref_px = float(matched_profile.get("refpx", 0.0))
                if ref_px > 0:
                    bid_out = f"${(ref_px * 0.99995):,.4f}"
                    ask_out = f"${(ref_px * 1.00005):,.4f}"
                else:
                    bid_out = "FETCHING..."
                    ask_out = "FETCHING..."

    dynamic_base_value = total_long_exposure + total_short_exposure - aggregated_cumu_pnl
    if dynamic_base_value != 0:
        total_pnl_pct = (aggregated_cumu_pnl / abs(dynamic_base_value)) * 100.0
    else:
        total_pnl_pct = 0.0

    pnl_color = TEAL if aggregated_cumu_pnl >=0 else RED
    total_pnl_text = [
        html.Span(f"${aggregated_cumu_pnl:+,.2f}", style={"fontSize": "2rem", "fontWeight": "700"})
        #html.Span(f"({total_pnl_pct:+.2f}%)", style={"fontSize": "1.1rem", "fontWeight": "500", "marginLeft": "8px", "opacity": "0.85"})
        ]
    total_pnl_style= {"fontFamily": SANS, "color": pnl_color, "display": "flex", "alignItems": "baseline"}

    daily_pnl_color = TEAL if aggregated_daily_pnl >= 0 else RED
    daily_pnl_text = [
        html.Span(f"${aggregated_daily_pnl:+,.2f}", style={"fontSize": "2rem", "fontWeight": "700"})
    ]

    return (
        #str(console_output_str),
        str(status_text),
        status_style,
        order_feedback,
        bid_out,
        ask_out,
        dropdown_options,
        dropdown_value_out,
        str(long_dollars_text),
        str(short_dollars_text),
        total_pnl_text,
        total_pnl_style,
        daily_pnl_text,
        table_layout,
        open_orders_layout,
        activity_items,
        #dollar_fig,
        exposure_fig,
        chart_store,
    )

@app.callback(
    Output("server-clock", "children"),
    Input("clock-timer", "n_intervals")
)

def render_clock(n):
    return f"SYS TIME: {time.strftime('%H:%M:%S')}"

@app.callback(
    Output("order-sym", "value"),
    Input("symbol-dropdown", "value")
)
def sync_dropdown_to_manual_input(dropdown_val):
    if not dropdown_val:
        return ""
    return str(dropdown_val).strip()

@app.callback(
    Output("trade-log-table-container", "children"),
    Input("trade-log-filter-preset","value"),
    Input("trade-log-search", "value"),
    Input("heartbeat-interval", "n_intervals")
)

def render_trade_ledger(view_preset, search_val, n_intervals):
    df_trades = fetch_historical_trades(db_engine, view_preset, search_val)

    if df_trades.empty:
        return [html.Div("No transactions found for selected filter parameters", style={"color": MUTED, "fontSize": "0.8rem", "fontFamily": MONO})]

    table_rows = []
    for _, r in df_trades.iterrows():
        is_buy = str(r['side']).upper() == 'BUY'
        formatted_time = pd.to_datetime(r['execution_time']).strftime('%Y-%m-%d %H:%M:%S')

        table_rows.append(html.Tr([
            html.Td(formatted_time, style={"color": MUTED}),
            html.Td(str(r['symbol']).upper(), style={"fontWeight": "600"}),
            html.Td(str(r['side']).upper(), style={"color": TEAL if is_buy else RED, "fontWeight": "700"}),
            html.Td(f"{r['quantity']:.4f}"),
            html.Td(f"${r['price']:,.2f}"),
            html.Td(f"${r['total_usd_value']:,.2f}", style={"color": TEAL if is_buy else RED}),
            html.Td(str(r['execution_source']).upper(), style={"fontSize": "1rem", "color": MUTED})
        ]))

    return [
        dbc.Table([
            html.Thead(html.Tr([
                html.Th("Timestamp"), html.Th("Symbol"), html.Th("Side"), html.Th("Qty"), html.Th("Execution PX"), html.Th("Total Value"), html.Th("Source")
            ]), style={"color": MUTED, "fontSize": "1rem"}),
            html.Tbody(table_rows)
        ], bordered=True, hover=True, size="sm", responsive=True, style={"color": TEXT, "fontSize": "1rem", "fontFamily": MONO})
    ]