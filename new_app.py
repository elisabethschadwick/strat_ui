import dash
import dash_bootstrap_components as dbc
from app_instance import app
from layout import layout
app.config.suppress_callback_exceptions = True
app.layout = layout

import callbacks
import app_instance

if __name__ == '__main__':
    import commander

    app.run(
        #host="127.0.0.1",
        host="192.168.0.246",
        port=8050,
        debug=True,
        ssl_context=(commander.cert_file, commander.key_file)
    )