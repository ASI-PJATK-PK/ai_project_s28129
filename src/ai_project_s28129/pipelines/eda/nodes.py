"""Node'y pipeline'u EDA: raporty jakosci danych i wykresy dla HAI 21.03."""

from __future__ import annotations

import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)

LABELS = ["attack", "attack_P1", "attack_P2", "attack_P3"]
NON_FEATURES = ["time", "source", *LABELS]


def _features(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in NON_FEATURES]


def _varying(df: pd.DataFrame) -> list[str]:
    """Kolumny zmienne w pliku treningowym (w stalych nie ma czego ogladac)."""
    train = df[df["source"] == "train1"]
    nunique = train[_features(df)].nunique()
    return list(nunique[nunique > 1].index)


def _continuous(df: pd.DataFrame) -> list[str]:
    train = df[df["source"] == "train1"]
    return [c for c in _varying(df) if train[c].nunique() > 10]


def _episode_bounds(attack: pd.Series) -> list[tuple[int, int]]:
    """Pozycje (start, koniec) ciaglych odcinkow z attack == 1."""
    a = attack.to_numpy().astype(int)
    starts = np.where((a == 1) & (np.r_[0, a[:-1]] == 0))[0]
    ends = np.where((a == 1) & (np.r_[a[1:], 0] == 0))[0]
    return list(zip(starts, ends))


def combine_files(train1: pd.DataFrame, test1: pd.DataFrame, test2: pd.DataFrame) -> pd.DataFrame:
    """Laczy pliki w jedna tabele z kolumna source."""
    parts = {"train1": train1, "test1": test1, "test2": test2}
    df = pd.concat([x.assign(source=name) for name, x in parts.items()], ignore_index=True)
    df["time"] = pd.to_datetime(df["time"])
    logger.info("Wczytano %d wierszy i %d cech", len(df), len(_features(df)))
    return df


def file_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Podsumowanie plikow: rozmiar, zakres czasu, ciaglosc, braki, duplikaty, ataki."""
    rows = []
    for source, x in df.groupby("source", sort=False):
        rows.append(
            {
                "file": source,
                "rows": len(x),
                "start": x["time"].min(),
                "end": x["time"].max(),
                "max_step_s": x["time"].diff().dt.total_seconds().max(),
                "missing_values": int(x[_features(df)].isna().sum().sum()),
                "duplicated_rows": int(x[_features(df)].duplicated().sum()),
                "attack_rows": int(x["attack"].sum()),
                "attack_share": round(x["attack"].mean(), 4),
                "attack_episodes": len(_episode_bounds(x["attack"])),
            }
        )
    result = pd.DataFrame(rows)
    logger.info("Podsumowanie plikow:\n%s", result.to_string(index=False))
    return result


def column_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Statystyki kolumn liczone na train1 oraz zachowanie kolumn stalych w testach."""
    train = df[df["source"] == "train1"]
    test = df[df["source"] != "train1"]
    features = _features(df)
    result = train[features].describe().T[["mean", "std", "min", "25%", "50%", "75%", "max"]]
    result.insert(0, "dtype", train[features].dtypes.astype(str))
    result.insert(1, "process", [c.split("_")[0] for c in features])
    result["unique_train"] = train[features].nunique()
    result["unique_test"] = test[features].nunique()
    result["missing"] = df[features].isna().sum()
    result["constant_in_train"] = result["unique_train"] == 1
    result["varies_only_in_test"] = result["constant_in_train"] & (result["unique_test"] > 1)
    logger.info(
        "Kolumny stale w train: %d, w tym zmienne w test: %d",
        result["constant_in_train"].sum(),
        result["varies_only_in_test"].sum(),
    )
    return result.round(4).rename_axis("column").reset_index()


def attack_episodes(df: pd.DataFrame) -> pd.DataFrame:
    """Lista atakow: plik, start, czas trwania i rekordy etykiet procesow."""
    rows = []
    for source, x in df[df["source"] != "train1"].groupby("source", sort=False):
        for start, end in _episode_bounds(x["attack"]):
            episode = x.iloc[start : end + 1]
            rows.append(
                {
                    "file": source,
                    "start": episode["time"].iloc[0],
                    "duration_s": len(episode),
                    "rows_P1": int(episode["attack_P1"].sum()),
                    "rows_P2": int(episode["attack_P2"].sum()),
                    "rows_P3": int(episode["attack_P3"].sum()),
                    "rows_without_process": int((episode[LABELS[1:]].sum(axis=1) == 0).sum()),
                }
            )
    result = pd.DataFrame(rows)
    logger.info("Atakow: %d", len(result))
    return result


def plot_histograms(df: pd.DataFrame) -> plt.Figure:
    """Histogramy zmiennych ciaglych: train1 kontra normalny ruch z testow."""
    columns = _continuous(df)
    train = df[df["source"] == "train1"]
    normal = df[(df["source"] != "train1") & (df["attack"] == 0)]
    n_cols = 7
    n_rows = int(np.ceil(len(columns) / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 2.6, n_rows * 1.9))
    for ax, column in zip(axes.flat, columns):
        bins = np.histogram_bin_edges(train[column], bins=40)
        ax.hist(train[column], bins=bins, density=True, alpha=0.6, label="train1")
        ax.hist(normal[column], bins=bins, density=True, alpha=0.6, label="test: normalne")
        ax.set_title(column, fontsize=8)
        ax.tick_params(labelsize=6)
        ax.set_yticks([])
    for ax in axes.flat[len(columns) :]:
        ax.axis("off")
    axes.flat[0].legend(fontsize=6)
    fig.tight_layout()
    logger.info("Histogramy: %d zmiennych", len(columns))
    return fig


def plot_boxplots(df: pd.DataFrame, sample: int, random_state: int) -> plt.Figure:
    """Boxploty na wartosciach standaryzowanych, zeby wszystkie zmienne miescily sie na jednej osi."""
    columns = _continuous(df)
    train = df[df["source"] == "train1"]
    scaled = (train[columns] - train[columns].mean()) / train[columns].std()
    scaled = scaled.sample(sample, random_state=random_state)
    fig, ax = plt.subplots(figsize=(15, 5))
    ax.boxplot(scaled.to_numpy(), tick_labels=columns, flierprops={"markersize": 1, "alpha": 0.3})
    ax.axhline(0, color="grey", lw=0.5)
    ax.set_ylabel("odchylenia standardowe od sredniej")
    ax.set_title("train1: rozklad zmiennych ciaglych po standaryzacji")
    ax.tick_params(axis="x", labelrotation=90, labelsize=7)
    fig.tight_layout()
    return fig


def plot_counts(df: pd.DataFrame) -> plt.Figure:
    """Countploty zmiennych kategorycznych: etykiety, proces celu i flagi stanu."""
    test = df[df["source"] != "train1"]
    attacks = test[test["attack"] == 1]
    process = attacks[LABELS[1:]].idxmax(axis=1).str.replace("attack_", "")
    process = process.where(attacks[LABELS[1:]].sum(axis=1) > 0, "brak etykiety")
    fig, axes = plt.subplots(1, 4, figsize=(15, 3.6))
    sns.countplot(data=test, x="source", hue="attack", ax=axes[0])
    axes[0].set_yscale("log")
    axes[0].set_title("Rekordy w testach (skala log)")
    sns.countplot(x=process, ax=axes[1], order=["P1", "P2", "P3", "brak etykiety"])
    axes[1].set_title("Rekordy ataku wg procesu")
    sns.countplot(data=df, x="P4_HT_PS", hue="source", ax=axes[2])
    axes[2].set_yscale("log")
    axes[2].set_title("P4_HT_PS (skala log)")
    flags = pd.DataFrame(
        {
            "P1_PCV02D != 12": test["P1_PCV02D"] != 12,
            "P2_Emerg = 1": test["P2_Emerg"] == 1,
            "P2_OnOff = 0": test["P2_OnOff"] == 0,
        }
    )
    counts = pd.DataFrame(
        {
            "attack = 1": flags[test["attack"] == 1].sum(),
            "attack = 0": flags[test["attack"] == 0].sum(),
        }
    )
    counts.plot.bar(ax=axes[3], rot=15)
    axes[3].set_title("Odchylenia kolumn stalych w train")
    fig.tight_layout()
    return fig


def plot_correlation(df: pd.DataFrame) -> plt.Figure:
    """Heatmapa korelacji zmiennych na ruchu normalnym."""
    train = df[df["source"] == "train1"]
    corr = train[_varying(df)].corr()
    fig, ax = plt.subplots(figsize=(13, 11))
    sns.heatmap(corr, cmap="coolwarm", center=0, vmin=-1, vmax=1, ax=ax, xticklabels=True, yticklabels=True)
    ax.tick_params(labelsize=6)
    ax.set_title("Korelacja Pearsona, train1")
    fig.tight_layout()
    return fig


def plot_pairplot(df: pd.DataFrame, columns: list[str], sample: int, random_state: int) -> plt.Figure:
    """Pairplot wybranych zmiennych; rowna liczba rekordow normalnych i atakow."""
    test = df[df["source"] != "train1"]
    parts = [
        test[test["attack"] == value].sample(sample, random_state=random_state) for value in (0, 1)
    ]
    grid = sns.pairplot(
        pd.concat(parts)[[*columns, "attack"]],
        hue="attack",
        corner=True,
        height=1.8,
        plot_kws={"s": 6, "alpha": 0.4},
    )
    return grid.figure


def plot_attack_example(df: pd.DataFrame, example: dict) -> plt.Figure:
    """Przebieg ataku: skutek fizyczny trwa dluzej niz etykieta attack."""
    window = df[(df["source"] == "test2") & df["time"].between(example["start"], example["end"])]
    fig, ax = plt.subplots(figsize=(11, 3.4))
    ax.plot(window["time"], window["P2_SIT01"], label="P2_SIT01 (obroty turbiny)")
    ax.plot(window["time"], window["P2_Emerg"] * window["P2_SIT01"].max(), label="P2_Emerg (skalowane)")
    ax.fill_between(
        window["time"],
        0,
        window["P2_SIT01"].max(),
        where=window["attack"] == 1,
        color="red",
        alpha=0.15,
        label="attack = 1",
    )
    ax.legend(fontsize=8, loc="lower left")
    ax.set_title("Atak z wylaczeniem awaryjnym turbiny, test2")
    fig.tight_layout()
    return fig
