import json
from pathlib import Path

import httpx

RAW = Path("data/raw")
URL = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{celex}"

DOCS = {
    "32011R1227": "Regulation (EU) No 1227/2011 on wholesale energy market integrity and transparency (REMIT)",
    "32019R0943": "Regulation (EU) 2019/943 on the internal market for electricity",
}


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = {}
    with httpx.Client(follow_redirects=True, timeout=60,
                      headers={"User-Agent": "GridMind learning project"}) as client:
        for celex, title in DOCS.items():
            url = URL.format(celex=celex)
            manifest[celex] = {"title": title, "source_url": url}
            path = RAW / f"{celex}.html"
            if path.exists():
                print(f"skip {celex} (already downloaded)")
                continue
            resp = client.get(url)
            if resp.status_code != 200 or "<html" not in resp.text[:2000].lower() or len(resp.text) < 20_000:
                print(f"FAILED {celex}: status {resp.status_code}. Save {url} manually as {path}")
                continue
            path.write_text(resp.text, encoding="utf-8")
            print(f"saved {celex} ({len(resp.text):,} chars)")
    (RAW / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()