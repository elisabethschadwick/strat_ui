import requests
import json
from urllib.parse import quote
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_url = "https://18.162.125.60:7800/"
username = "admin"
password = "abc123"
cert_file = "/home/lisa/certs/server.pem"
key_file = "/home/lisa/certs/key.pem"

session = requests.Session()
session.auth = (username, password)
session.cert = (cert_file, key_file)
session.verify = False

def parse_string(response_data):
    if not response_data or not isinstance(response_data, list):
        return {}

    raw_string = response_data[0]
    parts = raw_string.split()
    if len(parts) < 3:
        return {"raw_data": raw_string}

    parsed_data = {
        "timestamp": f"{parts[0]} {parts[1]}",
        "type": parts[2]
    }

    for part in parts[3:]:
        if "=" in part:
            k, v = part.split("=", 1)
            try:
                if '.' in v or 'e' in v.lower():
                    parsed_data[k] = float(v)
                else:
                    parsed_data[k] = int(v)
            except ValueError:
                parsed_data[k] = v

    return parsed_data

def send_direct_post(action, symbol_id=None, params=None):
    url = f"{base_url}command/?action={quote(action.strip())}"
    if symbol_id:
        url += f"&id={quote(symbol_id.trip())}"

    payload_dict = params if params is not None else {}
    json_string_body = json.dumps(payload_dict)

    print(f"Sending direct post -> action: '{action}'")
    print(f"Target URL: {url}")
    print(f"Payload Body: {json_string_body}")

    try:
        response = requests.post(
            url,
            json=json_string_body,
            cert=(cert_file, key_file),
            verify=False,
            timeout=15,
            auth=session.auth,
        )
        print(f" Response code: {response.status_code}")
        print(f" Response headers: {dict(response.headers)}")

        if response.status_code == 200:
            print("Connected successfully.")
            raw_json = response.json()
            clean_dictionary = parse_string(raw_json)
            print("\nSuccessfully parsed data")
            print(json.dumps(clean_dictionary, indent=4))
            if "cumu_net_pnl" in clean_dictionary:
                print(f"\nVerifying: Live Net P&L: {clean_dictionary['cumu_net_pnl']}")
        else:
            print(f"Failed to connect: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")






if __name__ == "__main__":
    send_direct_post(action="pl")