# ai_project_s28129 – IDS dla środowisk OT oparty na detekcji anomalii

Projekt z przedmiotu **ASI**, PJATK. Zespół jednoosobowy: **s28129**.

## 1. Opis projektu

Projekt to prosty **IDS** (*Intrusion Detection System*) dla środowiska **OT**, czyli systemów sterujących procesem przemysłowym.
Model uczy się, jak wygląda **normalna praca instalacji**, i oznacza sekundy, w których pomiary od niej odbiegają (**detekcja anomalii**).

| | |
|---|---|
| **Typ problemu** | detekcja anomalii, oceniana jak klasyfikacja binarna `normalne` / `atak` |
| **Wejście** | stan instalacji w danej sekundzie: pomiary i polecenia ze sterowników PLC |
| **Wyjście** | `anomaly_score` (im wyższy, tym bardziej podejrzany) i decyzja `is_attack` |
| **Użytkownik** | operator lub inżynier automatyki, który wrzuca plik CSV i dostaje listę podejrzanych chwil |

**Wartość praktyczna:** ataki na automatykę przemysłową mogą uszkodzić instalację lub ją zatrzymać. Taki detektor nie potrzebuje bazy sygnatur, bo wystarczy mu wiedza o normalnej pracy, więc może zauważyć także ataki, których wcześniej nie widział.

## 2. Dane: HAI 21.03

Źródło: <https://github.com/icsdataset/hai> (licencja CC BY-SA 4.0). Pomiary pochodzą ze stanowiska hardware-in-the-loop z prawdziwymi sterownikami PLC: kocioł, turbina, uzdatnianie wody i symulacja zapotrzebowania na moc.

| Plik | Zawartość | Rola |
|---|---|---|
| `train1.csv.gz` | 216 001 sekund, sama normalna praca | trening |
| `test1.csv.gz` | 43 201 sekund, 5 ataków | walidacja |
| `test2.csv.gz` | 118 801 sekund, 20 ataków | test |

Każdy plik ma 84 kolumny: `time`, 79 punktów pomiarowych i 4 etykiety. Do modelu trafi 56 cech. Decyzje i ich uzasadnienia są w [`docs/eda_report.md`](docs/eda_report.md).

### Pobranie danych
Dane nie są w repozytorium (`.gitignore`).

```bash
python scripts/download_data.py          # pobiera 3 pliki do data/01_raw/ (około 53 MB)
python scripts/download_data.py --check  # sprawdza, czy pliki są na miejscu
```

## 3. Model i metryki

| Rola | Model |
|---|---|
| Baseline | próg na odległości od średniej (z-score) |
| **Model główny** | **Isolation Forest** (scikit-learn) |
| AutoML | PyCaret `pycaret.anomaly` (wymaganie etapu 4) |

- **Próg alarmu** dobierany na walidacji tak, aby odsetek fałszywych alarmów (FPR) nie przekraczał **1%**
- **Metryki:** ROC-AUC, precision, recall, F1, FPR

## 4. Architektura

Diagram: [`docs/architecture_diagram.png`](docs/architecture_diagram.png), opis: [`docs/architecture.md`](docs/architecture.md).

| Moduł | Technologia | Zadanie |
|---|---|---|
| ETL | Kedro | wczytanie CSV, EDA, czyszczenie, skalowanie, podział danych |
| ML | Kedro + scikit-learn / PyCaret | trening, dobór progu, ewaluacja, zapis modelu |
| API | FastAPI | `POST /predict`, `GET /health` |
| UI | Streamlit | upload CSV, tabela podejrzanych chwil, histogram wyników |
| Automatyzacja | Airflow | DAG: preprocessing → training → evaluation |
| Wdrożenie | Docker Compose | kontenery `api` + `ui` |

## 5. Plan implementacji

| Etap | Co powstanie | Pliki | Kryterium „zrobione” |
|---|---|---|---|
| **1. Planowanie** ✅ | temat, architektura, szkielet Kedro, backlog | `README.md`, `docs/`, `conf/base/catalog.yml` | repo + diagram + GitHub Project |
| **2. EDA** ✅ | analiza jakości danych, wykresy, decyzje o danych | `notebooks/EDA_s28129.ipynb`, `pipelines/eda/`, `docs/eda_report.md` | `kedro run --pipeline=eda` zapisuje tabele i wykresy |
| **3. Preprocessing** | usunięcie kolumn, podział po plikach, `StandardScaler` dopasowany tylko na train | `pipelines/preprocessing/`, `tests/test_preprocessing.py` | dane w `data/05_model_input`, testy `pytest` przechodzą |
| **4. Model + AutoML** | baseline z-score, Isolation Forest, PyCaret anomaly; dobór progu na walidacji (FPR ≤ 1%) | `pipelines/training/`, `pipelines/evaluation/` | `model.pkl` + `metrics.json`, tabela porównania 3 modeli |
| **5. Ocena i wersjonowanie** | walidacja krzyżowa, macierz pomyłek, wersjonowane modele | `conf/base/catalog.yml` (`versioned: true`) | raport w `docs/` |
| **6. Airflow** | DAG uruchamiający `kedro run` dla kolejnych pipeline'ów | `airflow/dags/ids_pipeline.py` | DAG przechodzi w Airflow UI |
| **7. API + UI** | FastAPI ładuje model i scaler; Streamlit wysyła CSV do API i pokazuje wyniki | `app/api/main.py`, `app/ui/app.py` | `/docs` (Swagger) działa, UI pokazuje alerty |
| **8. Docker** | obrazy `api` i `ui`, `docker-compose.yml` | `Dockerfile`, `docker-compose.yml` | `docker compose up` uruchamia całość |

Szczegółowa lista zadań: GitHub Projects oraz [`docs/backlog.md`](docs/backlog.md).

**Poza zakresem:** analiza na żywo, ruch sieciowy i pliki PCAP, rozpoznawanie konkretnego typu ataku, deep learning.

## 6. Struktura repozytorium

```
ai_project_s28129/
├── conf/base/             # catalog.yml, parameters.yml
├── data/                  # 01_raw … 08_reporting (poza gitem)
├── docs/                  # raport EDA, wykresy, architektura, backlog
├── notebooks/             # EDA_s28129.ipynb
├── scripts/               # pobieranie danych, generowanie diagramu
├── src/ai_project_s28129/ # kod Kedro (pipelines, nodes)
├── tests/
├── requirements.txt
├── LICENSE
└── README.md
```

## 7. Uruchomienie

```bash
python -m venv .venv
.venv\Scripts\activate             # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_data.py
kedro run --pipeline=eda
pytest
```

## 8. Źródła

- H.-K. Shin, W. Lee, J.-H. Yun, B.-G. Min, *Two ICS Security Datasets and Anomaly Detection Contest on the HIL-based Augmented ICS Testbed*, CSET 2021.
- Kedro: <https://docs.kedro.org>
