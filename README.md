# ai_project_s28129 – IDS: wykrywanie ataków sieciowych jako anomalii

Projekt z przedmiotu **ASI**, PJATK. Zespół jednoosobowy: **s28129**.

## 1. Opis projektu

Projekt to prosty **IDS** (*Intrusion Detection System*), czyli system wykrywania włamań w ruchu sieciowym.
Model uczy się, jak wygląda **normalny ruch** w sieci, i oznacza jako podejrzane przepływy, które od niego odbiegają (**detekcja anomalii**).

| | |
|---|---|
| **Typ problemu** | detekcja anomalii, oceniana jak klasyfikacja binarna `BENIGN` / `ATTACK` |
| **Wejście** | przepływ sieciowy (*flow*) opisany 78 cechami: czas trwania, liczba i rozmiar pakietów, odstępy czasowe, flagi TCP, … |
| **Wyjście** | `anomaly_score` (im wyższy, tym bardziej podejrzany) i decyzja `is_attack` |
| **Użytkownik** | administrator sieci, który wrzuca plik CSV z przepływami i dostaje listę podejrzanych połączeń |

**Wartość praktyczna:** mała firma bez działu bezpieczeństwa dostaje prosty detektor, który nie potrzebuje bazy sygnatur ataków. Wystarczy mu wiedza o tym, jak wygląda normalny ruch, więc może zauważyć także ataki, których wcześniej nie widział.

## 2. Dane: CIC-IDS2017 (zakres: 2 dni)

Źródło: Canadian Institute for Cybersecurity (UNB), <https://www.unb.ca/cic/datasets/ids-2017.html>.
Zbiór zawiera ruch z realistycznej sieci firmowej. Cechy przepływów wyliczono narzędziem CICFlowMeter.

Używamy **dwóch dni** z ośmiu plików CSV:

| Plik | Zawartość | Rola |
|---|---|---|
| `Monday-WorkingHours.pcap_ISCX.csv` | ok. 530 tys. przepływów, **tylko ruch normalny** | trening |
| `Friday-WorkingHours-Morning.pcap_ISCX.csv` | ruch normalny + Botnet (Ares) | walidacja / test |
| `Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv` | ruch normalny + skanowanie portów | walidacja / test |
| `Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv` | ruch normalny + DDoS (LOIC) | walidacja / test |

**Podział:**
- **train**: poniedziałek (model widzi wyłącznie ruch normalny)
- **validation / test**: piątek podzielony losowo 50/50 ze stratyfikacją po etykiecie
- wszystkie typy ataków traktujemy jako jedną klasę `ATTACK`

**Znane problemy danych** (do obsłużenia w preprocessingu): wartości `Infinity`/`NaN` w `Flow Bytes/s` i `Flow Packets/s`, duplikaty, kolumny stałe, spacje w nazwach kolumn, zduplikowana kolumna `Fwd Header Length`.

### Pobranie danych
Dane nie są w repozytorium (`.gitignore`).

```bash
python scripts/download_data.py                  # pobiera archiwum i rozpakowuje 4 potrzebne pliki do data/01_raw/
python scripts/download_data.py --zip <plik.zip>  # jeśli archiwum pobrano ręcznie ze strony UNB
python scripts/download_data.py --check          # sprawdza, czy pliki są na miejscu
```

## 3. Model i metryki

| Rola | Model |
|---|---|
| Baseline | próg na odległości od średniej (z-score) |
| **Model główny** | **Isolation Forest** (scikit-learn) |
| AutoML | PyCaret `pycaret.anomaly` (wymaganie etapu 4) |

- **Próg alarmu** dobierany na walidacji tak, aby odsetek fałszywych alarmów (FPR) nie przekraczał **1%**
- **Metryki:** ROC-AUC, precision, recall, F1, FPR, a w raporcie dodatkowo recall osobno dla Botnet / PortScan / DDoS

## 4. Architektura

Diagram: [`docs/architecture_diagram.png`](docs/architecture_diagram.png), opis: [`docs/architecture.md`](docs/architecture.md).

| Moduł | Technologia | Zadanie |
|---|---|---|
| ETL | Kedro | wczytanie CSV, EDA, czyszczenie, skalowanie, podział danych |
| ML | Kedro + scikit-learn / PyCaret | trening, dobór progu, ewaluacja, zapis modelu |
| API | FastAPI | `POST /predict`, `GET /health` |
| UI | Streamlit | upload CSV, tabela podejrzanych przepływów, histogram wyników |
| Automatyzacja | Airflow | DAG: preprocessing → training → evaluation |
| Wdrożenie | Docker Compose | kontenery `api` + `ui` |

## 5. Plan implementacji

| Etap | Co powstanie | Pliki | Kryterium „zrobione” |
|---|---|---|---|
| **1. Planowanie** ✅ | temat, dane, architektura, szkielet Kedro, backlog | `README.md`, `docs/`, `conf/base/catalog.yml` | repo + diagram + GitHub Project |
| **2. EDA** | rozkłady cech, braki i `inf`, duplikaty, rozkład etykiet, korelacje, boxploty | `notebooks/EDA_s28129.ipynb`, `pipelines/eda/`, `docs/eda_report.md` | `kedro run --pipeline=eda` zapisuje wykresy do `data/08_reporting` |
| **3. Preprocessing** | czyszczenie (`inf`→NaN→usunięcie, duplikaty, kolumny stałe), etykieta binarna, `StandardScaler` dopasowany tylko na train, podział val/test | `pipelines/preprocessing/`, `tests/test_preprocessing.py` | pliki train/val/test w `data/05_model_input`, testy `pytest` przechodzą |
| **4. Model + AutoML** | baseline z-score, Isolation Forest, PyCaret anomaly; dobór progu na walidacji (FPR ≤ 1%) | `pipelines/training/`, `pipelines/evaluation/` | `model.pkl` + `metrics.json`, tabela porównania 3 modeli |
| **5. Ocena i wersjonowanie** | walidacja krzyżowa, macierz pomyłek, recall per typ ataku, wersjonowane modele | `conf/base/catalog.yml` (`versioned: true`) | raport w `docs/` |
| **6. Airflow** | DAG uruchamiający `kedro run` dla kolejnych pipeline'ów | `airflow/dags/ids_pipeline.py` | DAG przechodzi w Airflow UI |
| **7. API + UI** | FastAPI ładuje model i scaler; Streamlit wysyła CSV do API i pokazuje wyniki | `app/api/main.py`, `app/ui/app.py` | `/docs` (Swagger) działa, UI pokazuje alerty |
| **8. Docker** | obrazy `api` i `ui`, `docker-compose.yml` | `Dockerfile`, `docker-compose.yml` | `docker compose up` uruchamia całość |

Szczegółowa lista zadań: GitHub Projects oraz [`docs/backlog.md`](docs/backlog.md).

**Poza zakresem:** analiza ruchu na żywo, surowe pliki PCAP, rozpoznawanie konkretnego typu ataku, deep learning.

## 6. Struktura repozytorium

```
ai_project_s28129/
├── conf/base/             # catalog.yml, parameters.yml
├── data/                  # 01_raw … 08_reporting (poza gitem)
├── docs/                  # diagram, architektura, backlog
├── notebooks/             # notebooki Jupyter (EDA, eksperymenty)
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
kedro run                          # pipeline'y dochodzą w kolejnych etapach
pytest
```
