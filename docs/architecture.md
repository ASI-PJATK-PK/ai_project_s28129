# Architektura – IDS dla OT (detekcja anomalii)

![Diagram architektury](architecture_diagram.png)

Diagram generuje `python scripts/draw_architecture.py`.

```mermaid
flowchart LR
    A[HAI 21.03 CSV<br/>train1, test1, test2] --> B[Kedro: eda]
    A --> C[Kedro: preprocessing]
    C --> D[Kedro: training<br/>baseline / Isolation Forest / PyCaret]
    D --> E[Kedro: evaluation]
    D --> F[(model.pkl + scaler.pkl)]
    F --> G[FastAPI /predict]
    G <--> H[Streamlit UI]
    I[Airflow DAG] -.->|kedro run| C & D & E
```

| Moduł | Opis |
|---|---|
| **ETL (Kedro)** | wczytanie 3 plików CSV z `data/01_raw`, EDA, usunięcie kolumn stałych, cechy czasowe, skalowanie; train = `train1`, walidacja = `test1`, test = `test2` |
| **ML** | trening detektora na normalnej pracy, dobór progu (FPR ≤ 1%), metryki, zapis modelu do `data/06_models` |
| **API (FastAPI)** | `POST /predict` przyjmuje pomiary i zwraca `anomaly_score` oraz `is_attack`; `GET /health` |
| **UI (Streamlit)** | upload pliku CSV, tabela podejrzanych chwil, histogram wyników |
| **Airflow** | DAG: preprocessing → training → evaluation |
| **Docker** | docker-compose z serwisami `api` i `ui` |
