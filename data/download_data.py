"""Download the raw dataset into data/raw/ (run from the repo root: python data/download_data.py)."""
from pathlib import Path
from urllib.request import urlretrieve

FILES = {
    # Tableau "Superstore Sales" sample (Canada, 2009-2012), mirrored by Curran Kelleher
    "superstore.csv": "https://raw.githubusercontent.com/curran/data/gh-pages/superstoreSales/superstoreSales.csv",
}

raw = Path(__file__).parent / "raw"
raw.mkdir(exist_ok=True)
for name, url in FILES.items():
    print(f"Downloading {name} ...")
    urlretrieve(url, raw / name)
print("Done.")
