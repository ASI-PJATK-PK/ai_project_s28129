"""Generuje docs/architecture_diagram.png (matplotlib, bez zaleznosci od graphviz)."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parents[1] / "docs" / "architecture_diagram.png"

COLORS = {
    "data": "#dbeafe",
    "etl": "#dcfce7",
    "ml": "#fef3c7",
    "serve": "#fce7f3",
    "ops": "#ede9fe",
}

fig, ax = plt.subplots(figsize=(16, 9))
ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.axis("off")


def box(x, y, w, h, title, body, color):
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.15",
            fc=color, ec="#334155", lw=1.4,
        )
    )
    ax.text(x + w / 2, y + h - 0.28, title, ha="center", va="top", fontsize=11, weight="bold")
    ax.text(x + w / 2, y + h - 0.7, body, ha="center", va="top", fontsize=8.5, linespacing=1.4)
    return (x, y, w, h)


def arrow(a, b, label="", side="h"):
    ax_, ay, aw, ah = a
    bx, by, bw, bh = b
    if side == "h":
        start, end = (ax_ + aw, ay + ah / 2), (bx, by + bh / 2)
    elif side == "down":
        start, end = (ax_ + aw / 2, ay), (bx + bw / 2, by + bh)
    else:  # up
        start, end = (ax_ + aw / 2, ay + ah), (bx + bw / 2, by)
    ax.add_patch(
        FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=16, lw=1.4, color="#334155")
    )
    if label:
        ax.text((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.12, label,
                ha="center", fontsize=8, style="italic", color="#475569")


ax.text(8, 8.75, "IDS oparty na detekcji anomalii – architektura systemu",
        ha="center", fontsize=15, weight="bold")

# --- warstwa danych / ETL / ML (gora) ---
src = box(0.3, 5.2, 2.6, 2.6, "Źródła danych",
          "CIC-IDS2017\n(CSV, 2 dni)\n\npon.: ruch normalny\npt.: Botnet, PortScan,\nDDoS\n\ndata/01_raw", COLORS["data"])
etl = box(3.5, 5.2, 3.4, 2.6, "ETL – Kedro",
          "DataCatalog\n\neda  →  preprocessing\n(czyszczenie, skalowanie,\npodział train/val/test)", COLORS["etl"])
ml = box(7.5, 5.2, 3.6, 2.6, "ML – Kedro",
         "training:\nbaseline, Isolation Forest\nAutoML: PyCaret\n\nevaluation:\nROC-AUC, F1, FPR", COLORS["ml"])
reg = box(11.7, 5.2, 4.0, 2.6, "Zapisany model",
          "data/06_models\nmodel.pkl, scaler.pkl\n\nmetryki →\ndata/08_reporting", COLORS["ml"])

arrow(src, etl, "CSV")
arrow(etl, ml, "train/val/test")
arrow(ml, reg, "artefakty")

# --- serving (dol) ---
ui = box(0.3, 1.0, 3.6, 2.6, "UI – Streamlit",
         "upload pliku CSV\ntabela alertów\nhistogram anomaly_score", COLORS["serve"])
api = box(4.7, 1.0, 4.2, 2.6, "API – FastAPI",
          "POST /predict\n→ anomaly_score, is_attack\n\nGET /health", COLORS["serve"])
arrow(ui, api, "HTTP / JSON")
ax.add_patch(FancyArrowPatch((12.6, 5.2), (8.2, 3.6), arrowstyle="-|>", mutation_scale=16,
                             lw=1.4, color="#334155"))
ax.text(11.2, 4.85, "ładowanie modelu", fontsize=8, style="italic", color="#475569")

# --- orkiestracja i wdrozenie ---
af = box(9.7, 0.4, 2.9, 2.2, "Apache Airflow",
         "DAG:\npreprocessing\n→ training\n→ evaluation", COLORS["ops"])
ax.add_patch(FancyArrowPatch((11.15, 2.6), (7.0, 5.2), arrowstyle="-|>", mutation_scale=14,
                             lw=1.2, ls="--", color="#6d28d9"))
ax.text(11.15, 2.75, "kedro run --pipeline=…", ha="center", fontsize=8, color="#6d28d9",
        style="italic")

ax.add_patch(FancyBboxPatch((0.1, 0.15), 12.7, 3.75, boxstyle="round,pad=0.05",
                            fc="none", ec="#0ea5e9", lw=1.6, ls="--"))
ax.text(0.3, 3.7, "Docker / docker-compose:  api · ui · airflow", fontsize=9, color="#0369a1",
        weight="bold")

box(13.2, 0.4, 2.5, 2.2, "Wdrożenie",
    "obrazy Docker\n→ DockerHub", COLORS["ops"])

OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=150, bbox_inches="tight", facecolor="white")
print(f"Zapisano {OUT}")
