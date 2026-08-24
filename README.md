# Gold Hedge — Exit Calculator

Type the dealer's buy price, see instantly whether unwinding the whole position
(sell the coin + buy back the short future) nets a profit. Green glow = take it.

### Entering a price

The field takes a literal number (`4525.50`, `$4,525.50`) **or** shorthand that
resolves against live spot:

| Type | Means |
|---|---|
| `spot` | current spot (partial `s` / `sp` works while typing) |
| `-3%` or `-3` | spot minus 3% |
| `+1.5%` | spot plus 1.5% |
| `spot-2.5%` | same, spelled out |

The **Spot / −1% / −2% / −3% / −4%** buttons do the same thing in one tap, and
show the dollar figure they'll enter.

**Anything entered as a percentage stays pinned to spot** — the badge above the
field reads "pinned to spot −3% · follows the feed", and the price re-computes
itself on every 30s refresh, so the verdict can flip green→red on its own while
you're standing at the counter. Typing a literal number unpins it. Esc clears.
Text that isn't a valid price turns red rather than being coerced into a number.

## Run

`index.html` is self-contained and fetches its own prices, so any static host
works — GitHub Pages, or just a local file server:

```bash
python3 -m http.server 8899 --directory gold-hedge-calc
```

`server.py` is optional. Run it instead if TradingView ever starts refusing
browser requests; the page falls back to its `/api/quotes` proxy automatically,
and only that path can reach Yahoo (which sends no CORS headers at all).

## Hosting on GitHub Pages

Push the folder and enable Pages (Settings -> Pages -> Branch: `main`, `/root`).
Nothing else is needed — no build, no Actions, no secrets. Prices work because
both feeds allow cross-origin browser requests:

| Feed | CORS header |
|---|---|
| `api.gold-api.com` | `Access-Control-Allow-Origin: *` |
| `scanner.tradingview.com` | reflects the origin; **GET only**, and no custom request headers (so the page uses `/symbol?...`, not the JSON `POST /futures/scan`) |
| `query1.finance.yahoo.com` | none — server-side only, hence `server.py` |

**Note:** the defaults baked into `index.html` are a real position — cost basis,
futures entry, size. A public repo publishes them. Use a private repo (Pages on
private repos needs GitHub Pro) or run it locally if that matters.

## Live data

| Feed | Source | Notes |
|---|---|---|
| Spot XAU/USD | api.gold-api.com | real time, free, no key |
| /1OZV26 (Oct 2026 1-oz gold) | TradingView `COMEX:1OZV2026` | **10-minute delayed** |
| GCV26 cross-check | TradingView `COMEX:GCV2026` | sanity check on the thin 1OZ contract |
| fallback | Yahoo `1OZV26.CMX` | `server.py` only; rate-limits (429) under heavy polling |

A failed refresh serves the last good price flagged `stale` instead of blanking
the number. The **Futures price now (override)** field wins over the live feed —
use it to paste the real-time bid/ask off your broker before pulling the trigger.

## The math

```
net = (dealerBid − 4549.99)          physical leg
    + (4532.25 − futuresNow) × 1oz   short futures leg (1OZ contract = 1 oz = $1/point)
    − 1.00                           commissions (0.50/side × 2 sides)
    + 91.00                          2x miles on $4,549.99 @ 1.0 cpp
    + 91.00                          2% Costco cashback on $4,549.99

break-even dealer bid = 4549.99 − (everything except the physical leg)
```

Rewards are counted as profit by default; untick "Count miles + cashback as
profit" to see the hard-cash-only number. All inputs persist in localStorage.
