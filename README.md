# ai_project_s28129 – NetGuard: mini-IDS oparty na detekcji anomalii

Projekt z przedmiotu **ASI**, PJATK. Zespół jednoosobowy: **s28129**.

## 1. Temat

**NetGuard** to prosty system wykrywania włamań (IDS).
Model uczy się, jak wygląda **normalny ruch sieciowy**, i oznacza jako podejrzane przepływy, które od niego odbiegają (**detekcja anomalii**).

- **Typ problemu:** detekcja anomalii, oceniana jako klasyfikacja binarna `BENIGN` / `ATTACK`
- **Wejście:** przepływ sieciowy (flow) opisany cechami statystycznymi (czas trwania, liczba i rozmiar pakietów, flagi TCP, …)
- **Wyjście:** `anomaly_score` i decyzja `is_attack`

**Wartość praktyczna:** mała firma bez działu bezpieczeństwa może wrzucić eksport ruchu ze swojej sieci i dostać listę podejrzanych połączeń, posortowaną od najbardziej podejrzanych. Detekcja anomalii może też złapać ataki, których nie ma w bazie sygnatur.

## 2. Dane: CIC-IDS2017

Źródło: Canadian Institute for Cybersecurity (UNB), <https://www.unb.ca/cic/datasets/ids-2017.html>

- 8 plików CSV (`MachineLearningCSV.zip`), ok. 2,8 mln przepływów, 78 cech numerycznych + kolumna `Label`
- 5 dni ruchu w sieci firmowej. **Poniedziałek to tylko normalny ruch**, a w kolejnych dniach są ataki: DoS/DDoS, PortScan, brute force FTP/SSH, ataki webowe, botnet

**Plan podziału:**

| Zbiór | Dane |
|---|---|
| train | poniedziałek (tylko BENIGN) |
| validation | wtorek–środa (dobór progu) |
| test | czwartek–piątek |

Ze względu na rozmiar danych w razie potrzeby pracujemy na losowej próbce.
Znane problemy do obsłużenia w preprocessingu: wartości `Infinity`/`NaN`, duplikaty, kolumny stałe, spacje w nazwach kolumn.

**Pobranie danych** (dane nie są w repo):

```bash
python scripts/download_data.py          # pobiera i rozpakowuje CSV do data/01_raw/
python scripts/download_data.py --check  # sprawdza, czy pliki są na miejscu
```

Jeśli link nie działa, pobierz `MachineLearningCSV.zip` ręcznie ze strony UNB i uruchom `python scripts/download_data.py --zip <ścieżka>`.

## 3. Modele i metryki

- **Baseline:** prosty próg na odległości od średniej (z-score)
- **Model główny:** Isolation Forest (scikit-learn)
- **AutoML:** PyCaret `pycaret.anomaly`
- **Metryki:** ROC-AUC, precision, recall, F1, odsetek fałszywych alarmów (FPR)

## 4. Architektura

Diagram: [`docs/architecture_diagram.png`](docs/architecture_diagram.png), opis: [`docs/architecture.md`](docs/architecture.md).

| Moduł | Technologia |
|---|---|
| ETL | Kedro (pipeline'y `eda`, `preprocessing`) |
| Model | Kedro + scikit-learn / PyCaret |
| API | FastAPI (`/predict`, `/health`) |
| UI | Streamlit (upload CSV, lista alertów) |
| Automatyzacja | Airflow |
| Wdrożenie | Docker / docker-compose |

## 5. Struktura

```
ai_project_s28129/
├── conf/base/           # catalog.yml, parameters.yml
├── data/                # 01_raw … 08_reporting (poza gitem)
├── docs/                # diagram architektury, opis, backlog
├── notebooks/
├── scripts/             # pobieranie danych, generowanie diagramu
├── src/ai_project_s28129/
├── tests/
├── requirements.txt
├── LICENSE
└── README.md
```

## 6. Uruchomienie

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/download_data.py
kedro run
```

## 7. Backlog

GitHub Projects (link w oddaniu) oraz [`docs/backlog.md`](docs/backlog.md).
