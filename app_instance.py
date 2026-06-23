import dash
import dash_auth
import dash_bootstrap_components as dbc

VALID_USERNAME_PASSWORD_PAIRS = {
    'lisa': 'lisa2626'
}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])


auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)

app.server.secret_key = "replace_this_with_any_random_secure_string"

app.title = "Strategy Desk"

app.config.external_stylesheets = [
    dbc.themes.DARKLY,
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap"
]