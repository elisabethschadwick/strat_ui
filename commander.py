#!/usr/bin/python3

import json
import requests
import os
from urllib.parse import quote
import urllib3
import argparse

urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)   # Turn off certificate verification warning

PROD = False

parser = argparse.ArgumentParser(description="Command strat1")
parser.add_argument('-p', '--prod', action='store_true', required=False, default=False, help='Connect to prod instance')
parser.add_argument('-a', '--aws', action='store_true', required=False, default=False, help='Use AWS URL (otherwise localhost)')

args = parser.parse_args()

if args.prod:
    PROD = True

if args.aws:
    #BASE_URL = "https://ec2-18-167-103-49.ap-east-1.compute.amazonaws.com:7800/"
    BASE_URL = "https://18.162.125.60:7800/"
else:
    BASE_URL = "https://192.168.0.6:7800/"
print("Base URL: ", BASE_URL)

if PROD:
    print("PRODUCTION MODE!")
    cert_file = "/home/ubuntu/config/certs/server.pem"  # For use locally on AWS machine
    key_file = "/home/ubuntu/config/certs/key.pem"
else:
    print("LOCAL MODE!")
    cert_file = "/home/lisa/certs/server.pem"
    key_file = "/home/lisa/certs/key.pem"

USER = "admin"
PWD = "abc123"

def send_tls_authenticated_get(sub_url):
    full_url = f"{BASE_URL}{sub_url}"
    verify = False

    try:
        response = requests.get(
            full_url,
            verify=verify,
            timeout=15,
            headers={"Content-Type": "application/json"},
            cert=(cert_file, key_file),
            auth=(USER, PWD)
        )

        print(f"--- Server Reply ---")
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(response.text)

    except requests.exceptions.SSLError as e:
        print(f"\nTLS/SSL Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"\nConnection Error: {e}")


def set_payload(params):
    payload = {}
    if params is not None:
        for (key, value) in params.items():
            payload[key] = value
    return payload

def add_detail(field, value):
    if value is not None and value != "":
        return f"&{field}={quote(value.strip())}"
    else:
        return ""


def send_tls_authenticated_post(sub_url, action, cacs_id = None, params = None):

    full_url = f"{BASE_URL}{sub_url}?action={quote(action.strip())}"
    full_url += add_detail("id", cacs_id)

    verify = False
    payload = set_payload(params)

    try:
        # print("\nEstablishing secure TLS connection...")
        response = requests.post(
            full_url,
            json=json.dumps(payload),
            cert=(cert_file, key_file),
            verify=verify,
            timeout=15,
            auth=(USER, PWD)
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"ERROR: Status Code: {response.status_code}")
            print("Response Body:", response.text)

    except requests.exceptions.SSLError as e:
        print(f"\nTLS/SSL Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"\nConnection Error: {e}")

    return None


def process_entry(entry):
    if type(entry) == str:
        print(entry.strip("'"))
    elif type(entry) == dict:
        for key in entry.keys():
            if key == "msg":
                process_entry(entry["msg"])
            elif key == "orders":
                orders = entry["orders"]
                if orders is None:
                    print("No orders live")
                else:
                    if type(orders) == list:
                        for i, order in enumerate(orders):
                            print(f"{i} : {order}")
                    elif type(orders) == dict:
                        ids = orders.keys()
                        for count, id in enumerate(sorted(ids)):
                            print(f"{count + 1} : Id={id}: {orders[id]}")
            elif key in [ "pl", "px", "book" ]:
                vals = entry[key]
                if vals is None:
                    print("No P&L returned")
                else:
                    for count, k2 in enumerate(sorted(vals.keys())):
                        print(f"{count + 1}: {k2} : {vals[k2]}")
            else:
                try:
                    key1 = key.strip("'")
                    val1 = entry[key].strip("'")
                    print(f"{key1}: {val1}")
                except:
                    print(f"{key}: {entry[key]}")
    elif type(entry) == list:
        for l2 in entry:
            process_entry(l2)


def process_response(response):
    if response is None:
        print("Response is None")
        return None
    process_entry(response)


def parse_order(parts):
    symbol = None
    qty = None
    px = None

    print(parts)
    for part in parts:
        if part == "":
            continue
        if "@" in part:
            subparts = part.split("@")
            if len(subparts) == 2:
                qty = subparts[0].strip().upper()
                px = subparts[1].strip().upper()
            else:
                print("Error: to use @ notation, must have qty@px notation")
                break
        elif "=" in part:
            subparts = part.split("=")
            if len(subparts) == 2:
                field = subparts[0].strip().upper()
                value = subparts[1].strip().upper()
                print(f"{field}: {value}")
                if field == "SYMBOL" or field == "SYM":
                    symbol = value
                elif field == "QTY" or field == "QTY":
                    qty = value
                elif field == "PX" or field == "PX":
                    px = value
            else:
                print("Error: need field=value notation")
                break
        else:
            print("Error: need field=value notation")
            break

    return symbol, qty, px


if __name__ == "__main__":
    # Ensure files exist to avoid immediate crashes
    if not (os.path.exists(cert_file) and os.path.exists(key_file)):
        print("Error: Certificate or Key file not found")
        exit(1)

    last_symbol = None

    SYMBOL_COMMANDS = [ "off", "on", "pl" ]

    line = 0
    while True:
        print("")
        line += 1
        if last_symbol is None:
            inp = input(f"{line}: ").strip()
        else:
            inp = input(f"{line} ({last_symbol}): ").strip()
        parts = inp.split(" ")

        command = parts[0].strip().lower()

        # Local command to set default symbol for convenience
        if command == "symbol" or command == "sym":
            if len(parts) == 2:
                old_symbol = last_symbol
                last_symbol = parts[1].strip().upper()
                if old_symbol is None:
                    print(f"Setting default symbol to: {last_symbol}")
                else:
                    print(f"Setting default symbol to: {last_symbol}  (previous symbol: {old_symbol})")
            else:
                old_symbol = last_symbol
                last_symbol = None
                if old_symbol is None:
                    print("Default symbol remains set to None")
                else:
                    print(f"Default symbol set to {last_symbol}  (previous symbol: {old_symbol})")
            continue

        if command in SYMBOL_COMMANDS:    # 1 or 2-entry commands that (optionally) take symbol as 2nd parameter
            cacs_id = None  # Default to getting whole portfolio ('ppl' command)
            if len(parts) == 2:
                cacs_id = parts[1].strip().upper()
                if cacs_id != "*":   # * is used to specify commands that operate on whole portfolio, but individually by asset. It can't be the default symbol
                    if cacs_id != last_symbol:
                        if last_symbol is None:
                            print(f"Setting default symbol to: {cacs_id}")
                        else:
                            print(f"Setting default symbol to: {cacs_id}  (previous symbol: {last_symbol})")
                    last_symbol = cacs_id
            else:
                cacs_id = last_symbol

            response = send_tls_authenticated_post("command/", command, cacs_id=cacs_id)
            process_response(response)
            continue

        if command == "ppl":
            response = send_tls_authenticated_post("command/", "pl")
            process_response(response)
            continue

        if command == "reloadparams":
            response = send_tls_authenticated_post("command/", "reloadparams")
            process_response(response)
            continue

        if command == "allon":
            response = send_tls_authenticated_post("command/", "on")
            process_response(response)
            continue

        if command == "alloff":
            response = send_tls_authenticated_post("command/", "off")
            process_response(response)
            continue

        if command == "maxorders":
            if len(parts) == 2:
                maxorders = parts[1].strip()
                try:
                    max_orders = int(maxorders)
                except ValueError:
                    print("Can't parse new max orders: ", maxorders)
                    continue
            else:
                print("Syntax: maxorders [qty]")
                continue
            response = send_tls_authenticated_post("command/", "maxorders", params={ "qty" : str(max_orders) })
            process_response(response)
            continue

        if command == "orders":
            response = send_tls_authenticated_post("command/", "orders", cacs_id=None)
            process_response(response)
            continue

        if command == "buy" or command == "b":
            side= "BUY"
            if len(parts) < 2:
                print("Syntax: b/buy [sym=symbol] [qty=qty] [px=px]")
            else:
                id, qty, px = parse_order(parts[1:])
                if id is None:
                    if last_symbol is None:
                        print("Error: symbol is required if no default symbol is set")
                        continue
                    else:
                        print(f"Using default symbol: {last_symbol}")
                        id = last_symbol

                if id is None:
                    print("Error: symbol is required")
                    continue
                if qty is None:
                    print("Error: qty is required")
                    continue
                if px is None:
                    print("Error: px is required")
                    continue

                print(f"Sending order: {side} {id} {qty} @ {px}")
                params = { "px" : px, "qty" : qty }
                response = send_tls_authenticated_post("command/", "buy", cacs_id=id, params=params)
                process_response(response)
            continue

        if command == "sell" or command == "s":
            side = "SELL"
            if len(parts) < 2:
                print("Syntax: s/sell [sym=symbol] [qty=qty] [px=px]")
            else:
                id, qty, px = parse_order(parts[1:])
                if id is None:
                    if last_symbol is None:
                        print("Error: symbol is required if no default symbol is set")
                        continue
                    else:
                        print(f"Using default symbol: {last_symbol}")
                        id = last_symbol

                if id is None:
                    print("Error: symbol is required")
                    continue
                if qty is None:
                    print("Error: qty is required")
                    continue
                if px is None:
                    print("Error: px is required")
                    continue

                print(f"Sending order: {side} {id} {qty} @ {px}")
                params = { "px" : px, "qty" : qty }
                response = send_tls_authenticated_post("command/", "sell", cacs_id=id, params=params)
                process_response(response)
            continue

        if command == "cancel":
            if len(parts) < 2:  # Cancel all
                response = send_tls_authenticated_post("command/", "cancel", cacs_id=None)
                process_response(response)
            else:
                if parts[1].strip().upper() == "EXCHID":
                    if len(parts) != 3:
                        print("syntax: cancel exchid <exchange_client_id>")
                    else:
                        params = { "exchid" : parts[2] }
                        response = send_tls_authenticated_post("command/", "cancel", cacs_id=None, params=params)
                        process_response(response)
                else:  # Cancel local order by local_ord_id
                    try:
                        ord_id = int(parts[1])
                    except ValueError:
                        print("Local orderID must be an integer")
                        continue
                    params = {"localid" : ord_id }
                    response = send_tls_authenticated_post("command/", "cancel", cacs_id=None, params=params)
                    process_response(response)
            continue

        if command == "reconnect":
            if len(parts) != 2:
                print("Syntax: reconnect <exchange_name>")
            else:
                exch_name = parts[1].upper()
                response = send_tls_authenticated_post("command/", "reconnect", params={ "exchange" : exch_name })
                process_response(response)
            continue

        if command == "reconnectfeed":
            if len(parts) != 2:
                print("Syntax: reconnectfeed <feed_name>")
            else:
                exch_name = parts[1].upper()
                response = send_tls_authenticated_post("command/", "reconnect", params={ "exchange" : exch_name })
                process_response(response)
            continue

        if command == "quit" or command == "exit":
            exit(0)
        elif command != "":   # Default command: send symbol and allow command out however it was provided
            response = send_tls_authenticated_post("command/", command, cacs_id=last_symbol)
            process_response(response)
        else:   # Print help on blank entry
            print("Commands: off, on, pl, orders, buy, sell, cancel, quit/exit")

