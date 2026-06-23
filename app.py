from dash import Dash, html, dcc, Input, Output, State
import yfinance as yf
import plotly.graph_objects as go
from layout import layout
import pandas as pd
import json

from plotly import plot

app = Dash(__name__)

app.layout = html.Div(
    style={
        "fontFamily": "'Segoe UI', sans-serif",
           "backgroundColor": "#0f1117",
           "color": "#e0e0e0",
           "minHeight": "100vh",
           "padding": "32px"
},
    children = [
    html.H1("Trading Dashboard", style={"color": "#00d4aa","marginBottom": "8px"}),

    dcc.Store(id="strategy-state", data={"running": False}),

    dcc.Dropdown(
        id="ticker-dropdown",
        options=[
            {"label": "Apple", "value": "AAPL"},
            {"label": "Amazon", "value": "AMZN"},
            {"label": "Google", "value": "GOOG"}
        ],
        value="AAPL",
        style={"width": "300px"}
    ),

    html.Button(
        id="strategy-button",
        children = "Run",
        n_clicks=0
    ),
    html.Div(id="strategy-status", children="Strategy: Off"),
    dcc.Graph(id="price-chart")
])

@app.callback(
    Output("price-chart", "figure"),
    Input("ticker-dropdown", "value"),
    Input("strategy-state","data")
)

def update_chart(ticker,state):
    df = yf.download(ticker, period="6mo", interval="1d",auto_adjust=True)
    df.columns = df.columns.get_level_values(0)

    fig = go.Figure()

app = Dash(__name__)

app.layout = html.Div(
    style={
        "fontFamily": "'Segoe UI', sans-serif",
           "backgroundColor": "#0f1117",
           "color": "#e0e0e0",
           "minHeight": "100vh",
           "padding": "32px"
},
    children = [
    html.H1("Trading Dashboard", style={"color": "#00d4aa","marginBottom": "8px"}),

    dcc.Store(id="strategy-state", data={"running": False}),

    dcc.Dropdown(
        id="ticker-dropdown",
        options=[
            {"label": "Apple", "value": "AAPL"},
            {"label": "Amazon", "value": "AMZN"},
            {"label": "Google", "value": "GOOG"}
        ],
        value="AAPL",
        style={"width": "300px"}
    ),

    html.Button(
        id="strategy-button",
        children = "Run",
        n_clicks=0
    ),
    html.Div(id="strategy-status", children="Strategy: Off"),
    dcc.Graph(id="price-chart")
])

@app.callback(
    Output("price-chart", "figure"),
    Input("ticker-dropdown", "value"),
    Input("strategy-state","data")
)

def update_chart(ticker,state):
    df = yf.download(ticker, period="6mo", interval="1d",auto_adjust=True)
    df.columns = df.columns.get_level_values(0)

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"]
    ))
    if state and state["running"]:
        df["SMA20"] = df["Close"].rolling(20).mean()
        df["SMA50"] = df["Close"].rolling(50).mean()

        fig.add_trace(go.Scatter(x=df.index, y=df["SMA20"], name="SMA20", line=dict(color="cyan", width=1.5)))
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"], name="SMA50", line=dict(color="orange", width=1.5)))

    fig.update_layout(
        title=f"{ticker} - Last 6 months",
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        font=dict(color="#e0e0e0"),
        xaxis_rangeslider_visible=False,
    )
    return fig

#@app.callback(
 #   Output("strategy-state", "data"),
  #  Output("strategy-button", "children"),
   # Output("strategy-status", "children"),
    #Input("strategy-button", "n_clicks"),
    S#tate("strategy-state", "data")
#)
#def toggle_strategy(n_clicks, state):
    #if not n_clicks:
      #  return state, "Run Strategy", "Strategy: Off"

   # if state["running"]:
        #new_state = {"running": False}
        #return new_state, "Run Strategy", "Strategy: Off"
  #  else:
       # new_state = {"running": True}
       # return new_state, "Stop Strategy", "Strategy: On"

#if __name__ == '__main__':
   # app.run(debug=True, port = 8051)
   # fig.add_trace(go.Candlestick(
   #     x=df.index,
   #     open=df["Open"],
    #    high=df["High"],
     #   low=df["Low"],
      #  close=df["Close"]
   # ))
  #  if state and state["running"]:
       # df["SMA20"] = df["Close"].rolling(20).mean()
        #df["SMA50"] = df["Close"].rolling(50).mean()

        #fig.add_trace(go.Scatter(x=df.index, y=df["SMA20"], name="SMA20", line=dict(color="cyan", width=1.5)))
        #fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"], name="SMA50", line=dict(color="orange", width=1.5)))

    #fig.update_layout(
     #   title=f"{ticker} - Last 6 months",
      #  paper_bgcolor="#0f1117",
       # plot_bgcolor="#0f1117",
        #font=dict(color="#e0e0e0"),
        #xaxis_rangeslider_visible=False,
    #)
    #return fig

#@app.callback(
#    Output("strategy-state", "data"),
 #   Output("strategy-button", "children"),
  #  Output("strategy-status", "children"),
   # Input("strategy-button", "n_clicks"),
    #State("strategy-state", "data")
#)
#def toggle_strategy(n_clicks, state):
 #   if not n_clicks:
  #      return state, "Run Strategy", "Strategy: Off"

   # if state["running"]:
    #    new_state = {"running": False}
     #   return new_state, "Run Strategy", "Strategy: Off"
    #else:
     #   new_state = {"running": True}
      #  return new_state, "Stop Strategy", "Strategy: On"

if __name__ == '__main__':
    app.run(debug=True, port = 8051)