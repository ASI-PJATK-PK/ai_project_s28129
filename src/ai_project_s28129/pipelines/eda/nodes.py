"""Node'y pipeline'u EDA dla zbioru HAI 21.03."""

import logging

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)

LABELS = ["attack", "attack_P1", "attack_P2", "attack_P3"]


def _features(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in ["time", "source", *LABELS]]


def _train(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["source"] == "train1"]


def load_data(train1: pd.DataFrame, test1: pd.DataFrame, test2: pd.DataFrame) -> pd.DataFrame:
    parts = {"train1": train1, "test1": test1, "test2": test2}
    df = pd.concat([x.assign(source=name) for name, x in parts.items()], ignore_index=True)
    logger.info("Wczytano %d wierszy i %d cech", len(df), len(_features(df)))
    return df


def data_quality(df: pd.DataFrame) -> pd.DataFrame:
    """Dla kazdego pliku: wiersze, braki, duplikaty i rekordy ataku."""
    result = pd.DataFrame(
        {
            name: {
                "rows": len(x),
                "missing": x[_features(df)].isna().sum().sum(),
                "duplicates": x[_features(df)].duplicated().sum(),
                "attack_rows": x["attack"].sum(),
                "attacks": (x["attack"].diff() == 1).sum(),
            }
            for name, x in df.groupby("source", sort=False)
        }
    ).T
    logger.info("Jakosc danych:\n%s", result)
    return result.rename_axis("file").reset_index()


def column_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Statystyki kolumn na normalnej pracy (train1)."""
    stats = _train(df)[_features(df)].describe().T
    stats["unique"] = _train(df)[_features(df)].nunique()
    logger.info("Kolumny stale w train1: %d", (stats["unique"] == 1).sum())
    return stats


def plot_distributions(df: pd.DataFrame, columns: list[str]) -> plt.Figure:
    """Histogramy i boxploty wybranych zmiennych."""
    fig, axes = plt.subplots(2, len(columns), figsize=(2.2 * len(columns), 5))
    for i, column in enumerate(columns):
        axes[0, i].hist(_train(df)[column], bins=40)
        axes[0, i].set_title(column, fontsize=8)
        axes[1, i].boxplot(_train(df)[column], flierprops={"markersize": 1})
    fig.tight_layout()
    return fig


def plot_counts(df: pd.DataFrame) -> plt.Figure:
    """Countploty: ataki w plikach testowych i zmienna kategoryczna P4_HT_PS."""
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.2))
    sns.countplot(data=df[df["source"] != "train1"], x="source", hue="attack", ax=axes[0])
    sns.countplot(data=df, x="P4_HT_PS", ax=axes[1])
    for ax in axes:
        ax.set_yscale("log")
    fig.tight_layout()
    return fig


def plot_correlation(df: pd.DataFrame) -> plt.Figure:
    """Heatmapa korelacji zmiennych niestalych w train1."""
    train = _train(df)[_features(df)]
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(train.loc[:, train.nunique() > 1].corr(), cmap="coolwarm", center=0, ax=ax)
    ax.tick_params(labelsize=6)
    fig.tight_layout()
    return fig


def plot_pairplot(df: pd.DataFrame, columns: list[str], sample: int, random_state: int) -> plt.Figure:
    """Pairplot z rowna liczba rekordow normalnych i atakow."""
    test = df[df["source"] != "train1"]
    parts = [test[test["attack"] == v].sample(sample, random_state=random_state) for v in (0, 1)]
    return sns.pairplot(pd.concat(parts)[[*columns, "attack"]], hue="attack", corner=True, height=1.8).figure
