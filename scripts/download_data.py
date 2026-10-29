"""Pobieranie zbioru CIC-IDS2017 (MachineLearningCSV) do data/01_raw/.

Uzycie:
    python scripts/download_data.py                 # pobierz + rozpakuj
    python scripts/download_data.py --url <URL>     # wlasny mirror archiwum zip
    python scripts/download_data.py --zip plik.zip  # rozpakuj recznie pobrane archiwum
    python scripts/download_data.py --check         # sprawdz kompletnosc plikow
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "01_raw"

# Oficjalna strona: https://www.unb.ca/cic/datasets/ids-2017.html
# (link do archiwum moze sie zmieniac - wtedy uzyj --url albo --zip)
DEFAULT_URL = (
    "http://cicresearch.ca/CICDataset/CIC-IDS-2017/Dataset/CIC-IDS-2017/CSVs/"
    "MachineLearningCSV.zip"
)

EXPECTED_FILES = [
    "Monday-WorkingHours.pcap_ISCX.csv",
    "Tuesday-WorkingHours.pcap_ISCX.csv",
    "Wednesday-workingHours.pcap_ISCX.csv",
    "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv",
    "Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv",
    "Friday-WorkingHours-Morning.pcap_ISCX.csv",
    "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv",
    "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
]


def download(url: str, target: Path) -> Path:
    import requests

    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"Pobieranie {url} -> {target}")
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with open(target, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                done += len(chunk)
                if total:
                    print(f"\r  {done / total:6.1%}", end="")
    print()
    return target


def extract(zip_path: Path, out_dir: Path) -> None:
    """Rozpakowuje tylko pliki CSV, ignorujac strukture katalogow w archiwum."""
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            name = Path(member.filename).name
            if not name.endswith(".csv"):
                continue
            print(f"  rozpakowuje {name}")
            with zf.open(member) as src, open(out_dir / name, "wb") as dst:
                dst.write(src.read())


def check(out_dir: Path) -> bool:
    missing = [f for f in EXPECTED_FILES if not (out_dir / f).exists()]
    for f in EXPECTED_FILES:
        status = "BRAK" if f in missing else "OK  "
        print(f"[{status}] {f}")
    return not missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--zip", type=Path, help="lokalne archiwum MachineLearningCSV.zip")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        return 0 if check(RAW_DIR) else 1

    zip_path = args.zip or download(args.url, RAW_DIR / "MachineLearningCSV.zip")
    extract(zip_path, RAW_DIR)
    return 0 if check(RAW_DIR) else 1


if __name__ == "__main__":
    sys.exit(main())
