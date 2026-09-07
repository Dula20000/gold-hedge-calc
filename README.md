# Metal Hedge Calculator

Open `index.html` to choose Gold, Silver, Platinum, Palladium, or Copper. Each
metal has its own URL (`gold.html`, `silver.html`, and so on) and the same hedge
calculator: live spot, one-tap spot / −1% / −2% / −3% / −4% bids, manual
position inputs, and a CollectPure highest-bid button.

## Run locally

The site works as static HTML, using the public spot-price fallback. To enable
the authenticated CollectPure bid button, run the included local server:

```bash
export COLLECTPURE_API_KEY='your-key'
python3 server.py
```

Then open `http://localhost:8787`. Alternatively place the key in an untracked
file named `.collectpure-key` beside `server.py`.

The API key must never be added to browser JavaScript, HTML, GitHub Pages, or a
commit. The server sends it only as the `x-api-key` header to CollectPure.

## Important bid note

CollectPure offers belong to particular products and denominations. The button
shows the matched product name; verify its unit and premium before treating the
number as a per-troy-ounce dealer bid. The calculator is indicative only and
does not place trades.
