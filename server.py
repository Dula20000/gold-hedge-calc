#!/usr/bin/env python3
"""Optional local server for the hedge calculators.

It keeps COLLECTPURE_API_KEY on the server and serves the static pages.  GitHub
Pages can use the public spot fallback, but cannot safely make authenticated
CollectPure requests.
"""
import json
import mimetypes
import os
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", "8787"))
METAL_CODES = {"gold": "XAU", "silver": "XAG", "platinum": "XPT",
               "palladium": "XPD", "copper": "XCU"}
_cache = {}


def key():
    """Read the key only at runtime; never put it in the repository."""
    value = os.environ.get("COLLECTPURE_API_KEY", "13a01918-d250-4181-bb05-dd53a1577d69").strip()
    if value:
        return value
    filename = os.path.join(HERE, ".collectpure-key")
    if os.path.isfile(filename):
        with open(filename, encoding="utf-8") as file:
            return file.read().strip()
    return ""


def get_json(url, headers=None):
    request = urllib.request.Request(url, headers=headers or {"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def cached(name, seconds, load):
    saved = _cache.get(name)
    if saved and time.time() - saved[0] < seconds:
        return saved[1]
    value = load()
    _cache[name] = (time.time(), value)
    return value


def public_spot(metal):
    code = METAL_CODES.get(metal.lower())
    if not code:
        raise ValueError("Unsupported metal")
    data = get_json("https://api.gold-api.com/price/" + code)
    return {"price": float(data["price"]), "source": "gold-api.com"}


def collectpure_spot(metal):
    token = key()
    if not token:
        raise RuntimeError("CollectPure is not configured")
    data = get_json("https://api.collectpure.com/marketplace/get-spot-price/v1",
                    {"Accept": "application/json", "x-api-key": token})
    for quote in data.get("data", []):
        if str(quote.get("material", "")).lower() == metal.lower():
            return {"price": float(quote["bid"]), "source": "CollectPure spot bid"}
    raise ValueError("No CollectPure spot price for " + metal)


def spot(metal):
    cache_key = "spot:" + metal.lower()
    def load():
        try:
            return collectpure_spot(metal)
        except Exception:
            return public_spot(metal)
    return cached(cache_key, 10, load)


def highest_bid(metal):
    token = key()
    if not token:
        raise RuntimeError("COLLECTPURE_API_KEY is not configured")
    # A marketplace offer is product-specific.  The UI displays the product so
    # a user can confirm its denomination before treating the number as $/oz.
    params = urllib.parse.urlencode({
        "query": "*", "limit": 250,
        "filter_by": "material:=" + metal + " && has_offer:=true",
    })
    data = get_json("https://api.collectpure.com/products/search/v1?" + params,
                    {"Accept": "application/json", "x-api-key": token})
    products = data.get("data", {}).get("products", [])
    choices = []
    for product in products:
        offer = product.get("offer") or product.get("highestOffer") or {}
        try:
            choices.append((float(offer["price"]), product.get("title", "CollectPure product")))
        except (KeyError, TypeError, ValueError):
            pass
    if not choices:
        raise ValueError("No active CollectPure bid for " + metal)
    price, product = max(choices, key=lambda item: item[0])
    return {"price": price, "product": product, "source": "CollectPure"}


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, value):
        body = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        if parsed.path == "/api/spot":
            metal = query.get("metal", ["Gold"])[0]
            try:
                self.send_json(200, spot(metal))
            except Exception as error:
                self.send_json(502, {"error": str(error)})
            return
        if parsed.path == "/api/collectpure/highest-bid":
            metal = query.get("metal", ["Gold"])[0]
            try:
                self.send_json(200, cached("bid:" + metal.lower(), 15, lambda: highest_bid(metal)))
            except Exception as error:
                self.send_json(502, {"error": str(error)})
            return
        name = parsed.path.lstrip("/") or "index.html"
        if "/" in name or name.startswith("."):
            self.send_error(404)
            return
        filename = os.path.join(HERE, name)
        if not os.path.isfile(filename):
            self.send_error(404)
            return
        with open(filename, "rb") as file:
            body = file.read()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(filename)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    print("Hedge calculator -> http://localhost:%d" % PORT)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
