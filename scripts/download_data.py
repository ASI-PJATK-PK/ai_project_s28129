"""Pobieranie zbioru HAI 21.03 do data/01_raw/.

Uzycie:
    python scripts/download_data.py          # pobierz brakujace pliki
    python scripts/download_data.py --check  # sprawdz kompletnosc plikow
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "01_raw"

# Repozytorium zbioru: https://github.com/icsdataset/hai (licencja CC BY-SA 4.0)
BASE_URL = "https://raw.githubusercontent.com/icsdataset/hai/master/hai-21.03"
FILES = ["train1.csv.gz", "test1.csv.gz", "test2.csv.gz"]


def download(name: str) -> None:
    import requests

    print(f"Pobieranie {name}")
    with requests.get(f"{BASE_URL}/{name}", stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(RAW_DIR / name, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)


def check() -> bool:
    missing = [f for f in FILES if not (RAW_DIR / f).exists()]
    for f in FILES:
        print(f"[{'BRAK' if f in missing else 'OK  '}] {f}")
    return not missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if not args.check:
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        for name in FILES:
            if not (RAW_DIR / name).exists():
                download(name)
    return 0 if check() else 1


if __name__ == "__main__":
    sys.exit(main())
