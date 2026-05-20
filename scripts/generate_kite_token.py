#!/usr/bin/env python3
"""Generate Kite access token and update .env.

Add this redirect URL in https://developers.kite.trade/ for your app:
  http://127.0.0.1:8765/

Usage:
  python scripts/generate_kite_token.py
"""

from __future__ import annotations

import re
import socket
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
REDIRECT_PORT = 8765
REDIRECT_URL = f"http://127.0.0.1:{REDIRECT_PORT}/"


class ReuseHTTPServer(HTTPServer):
    allow_reuse_address = True


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", port))
            return False
        except OSError:
            return True


def load_env() -> dict[str, str]:
    values: dict[str, str] = {}
    if not ENV_PATH.exists():
        return values
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def update_env(access_token: str) -> None:
    text = ENV_PATH.read_text() if ENV_PATH.exists() else ""
    if re.search(r"^KITE_ACCESS_TOKEN=", text, re.MULTILINE):
        text = re.sub(r"^KITE_ACCESS_TOKEN=.*$", f"KITE_ACCESS_TOKEN={access_token}", text, flags=re.MULTILINE)
    else:
        text += f"\nKITE_ACCESS_TOKEN={access_token}\n"
    if re.search(r"^USE_TICK_SIMULATOR=", text, re.MULTILINE):
        text = re.sub(r"^USE_TICK_SIMULATOR=.*$", "USE_TICK_SIMULATOR=false", text, flags=re.MULTILINE)
    else:
        text += "USE_TICK_SIMULATOR=false\n"
    ENV_PATH.write_text(text)
    print(f"Updated {ENV_PATH} (KITE_ACCESS_TOKEN, USE_TICK_SIMULATOR=false)")


def exchange_token(api_key: str, api_secret: str, request_token: str) -> int:
    from kiteconnect import KiteConnect

    kite = KiteConnect(api_key=api_key)
    data = kite.generate_session(request_token, api_secret=api_secret)
    update_env(data["access_token"])
    kite.set_access_token(data["access_token"])
    profile = kite.profile()
    print(f"\nSuccess! Logged in as: {profile.get('user_name')} ({profile.get('broker')})")
    print("\nRestart Docker workers:")
    print("  docker compose up -d --force-recreate worker-market backend")
    return 0


def main() -> int:
    import sys

    env = load_env()
    api_key = env.get("KITE_API_KEY") or input("KITE_API_KEY: ").strip()
    api_secret = env.get("KITE_API_SECRET") or input("KITE_API_SECRET: ").strip()
    if not api_key or not api_secret:
        print("Error: KITE_API_KEY and KITE_API_SECRET required in .env")
        return 1

    try:
        from kiteconnect import KiteConnect
    except ImportError:
        print("Install: pip install kiteconnect")
        return 1

    # Manual: paste request_token from redirect URL immediately after login
    if len(sys.argv) > 1:
        token = sys.argv[1].strip()
        if "request_token=" in token:
            from urllib.parse import parse_qs, urlparse

            token = parse_qs(urlparse(token).query).get("request_token", [token])[0]
        try:
            return exchange_token(api_key, api_secret, token)
        except Exception as e:
            print(f"Failed: {e}")
            print("Request tokens expire in ~2 minutes. Log in again and run immediately:")
            print("  python3 scripts/generate_kite_token.py '<paste full redirect URL>'")
            return 1

    kite = KiteConnect(api_key=api_key)
    login_url = kite.login_url()

    result: dict[str, str] = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):  # noqa: A003
            return

        def do_GET(self):
            qs = parse_qs(urlparse(self.path).query)
            token = qs.get("request_token", [None])[0]
            status = qs.get("status", ["unknown"])[0]
            if token and status == "success":
                result["request_token"] = token
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<h2>Login successful.</h2><p>You can close this tab and return to the terminal.</p>"
                )
            else:
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h2>Login failed or missing request_token.</h2>")

    if port_in_use(REDIRECT_PORT):
        print(f"Error: port {REDIRECT_PORT} is already in use.")
        print("A previous token script may still be running. Free the port, then retry:")
        print(f"  lsof -ti :{REDIRECT_PORT} | xargs kill")
        print("\nOr paste the redirect URL manually (request_token expires in ~2 min):")
        print("  python3 scripts/generate_kite_token.py '<paste full redirect URL after login>'")
        return 1

    server = ReuseHTTPServer(("127.0.0.1", REDIRECT_PORT), CallbackHandler)
    print(f"\nRedirect URL (must be registered in Kite Connect app): {REDIRECT_URL}")
    print("\nOpening Kite login in your browser...")
    print("If it does not open, visit:\n")
    print(login_url)
    print()
    webbrowser.open(login_url)

    print(f"Waiting for login callback on {REDIRECT_URL} ...")
    while "request_token" not in result:
        server.handle_request()

    return exchange_token(api_key, api_secret, result["request_token"])


if __name__ == "__main__":
    sys.exit(main())
