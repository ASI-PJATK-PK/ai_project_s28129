# Raport EDA: IDS na danych OT (HAI 21.03)

Pełna analiza: [`notebooks/EDA_s28129.ipynb`](../notebooks/EDA_s28129.ipynb). Wykresy i tabele tworzy `kedro run --pipeline=eda`.

## 1. Opis danych

[HAI 21.03](https://github.com/icsdataset/hai) (licencja CC BY-SA 4.0) to pomiary ze stanowiska hardware-in-the-loop z prawdziwymi sterownikami PLC: kocioł (P1), turbina (P2), uzdatnianie wody (P3) i symulacja zapotrzebowania na moc (P4). Każdy wiersz to stan instalacji w jednej sekundzie.

| Plik | Wiersze | Okres (2020) | Ataki | Udział rekordów ataku | Rola |
|---|---|---|---|---|---|
| `train1` | 216 001 | 11.07 00:00 – 13.07 12:00 | 0 | 0% | trening |
| `test1` | 43 201 | 7.07 15:00 – 8.07 03:00 | 5 | 1,5% | walidacja |
| `test2` | 118 801 | 9.07 15:00 – 11.07 00:00 | 20 | 2,9% | test |

Każdy plik ma 84 kolumny: `time`, 79 punktów pomiarowych i 4 etykiety.

## 2. Główne obserwacje

- **Jakość:** nie ma braków ani duplikatów, a pomiary są co sekundę bez przerw. 19 kolumn jest stałych we wszystkich plikach, a 3 tylko w `train1`.
- **Szereg czasowy:** autokorelacja po 1 sekundzie to 0,999, a plik treningowy jest późniejszy niż testowe.
- **Rozkłady:** są wielomodalne, bo instalacja pracuje w kilku stanach ustalonych. Skala jest bardzo różna: odchylenie od 0,0016 do 6823.
- **Ataki:** to 2,5% rekordów testowych, trwają od 17 do 422 sekund i dotyczą głównie procesu P1. 154 rekordy ataku nie mają etykiety procesu.
- **Korelacje:** 13 par ma |r| > 0,99, ale w parach polecenie/położenie zaworu zależność rozjeżdża się podczas ataku.
- **Etykiety:** skutek ataku trwa dłużej niż etykieta. Przez pierwszą minutę po ataku rekordy są wyraźnie dalej od normy.

![Histogramy](figures/histograms.png)

![Boxploty](figures/boxplots.png)

![Zmienne kategoryczne](figures/counts.png)

![Korelacje](figures/correlation.png)

![Pairplot](figures/pairplot.png)

![Przykład ataku](figures/attack_example.png)

## 3. Decyzje o danych

Po decyzjach zostaje 56 cech: 79 − 19 stałych − 3 stałe w train − `P4_ST_PS`.

| # | Decyzja | Dlaczego | Przykład z danych |
|---|---|---|---|
| D1 | HAI 21.03 zamiast CIC-IDS2017 | projekt dotyczy OT, a CIC-IDS2017 to ruch biurowy; HAI ma realne PLC i publiczny dostęp | pliki train mają 0 rekordów ataku |
| D2 | tylko `train1`, `test1`, `test2` | tyle wystarczy do projektu, a różnice train/test są fizycznie małe | `P1_B2004`: 17% poza zakresem, ale o 0,02 odchylenia |
| D3 | podział po plikach, nie losowy | sąsiednie sekundy są prawie identyczne, więc losowy podział zawyżyłby wynik | autokorelacja 0,999 po 1 s |
| D4 | usunięcie 1. wiersza `train1` | ten sam pomiar jest w train i test | 11.07 00:00:00, 79 z 79 wartości zgodnych |
| D5 | usunięcie 19 kolumn stałych | jedna wartość nie niesie informacji | `P1_PP02D` zawsze równe 1 |
| D6 | 3 kolumny stałe w train poza modelem | model nie nauczy się kolumny o jednej wartości | `P1_PCV02D` ≠ 12: 185 rekordów, wszystkie atak |
| D7 | tylko etykieta `attack` | `attack_P*` są niepełne i byłyby przeciekiem | 154 rekordy ataku bez procesu |
| D8 | bez accuracy | ataki to 2,5% rekordów | brak alarmów daje 97,5% accuracy |
| D9 | `time` nie jest cechą | model nauczyłby się harmonogramu testów | w 8 godzinach doby nie ma żadnego ataku |
| D10 | zostawiamy wartości odstające | w train to prawdziwe stany instalacji | `P4_HT_FD`: 0,8% rekordów powyżej 5 odchyleń |
| D11 | usuwamy `P4_ST_PS` | dokładna kopia `P4_HT_PS`, także podczas ataków | 0→0, 10→50 w każdym rekordzie |
| D12 | nie usuwamy kolumn skorelowanych | rozjazd polecenia i położenia zaworu to objaw ataku | `FCV03`: 0,01% rekordów normalnych, 4,8% ataku |
| D13 | pairplot: 5 zmiennych, po 1500 rekordów na klasę | 56 zmiennych to 1540 wykresów, a ataki by zniknęły | wybór według statystyki KS |
| D14 | etykiety bez zmian | ręczna poprawa byłaby dopasowywaniem pod wynik | `P2_Emerg`: 47 s, z tego 35 s z etykietą |

## 4. Dalsze kroki (etap 3)

1. **Czyszczenie:** usunąć kolumny i wiersz według D4, D5, D6 i D11.
2. **Podział:** `train1` do treningu, `test1` do walidacji, `test2` do testu.
3. **Standaryzacja:** dopasować tylko na `train1`.
4. **Feature engineering (opcjonalnie):** różnice polecenie − położenie zaworu, jeśli model będzie za słaby.
