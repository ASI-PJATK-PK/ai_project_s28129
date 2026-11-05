"""Testy node'ow pipeline'u EDA."""

import pandas as pd

from ai_project_s28129.pipelines.eda import nodes


def _sample() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": pd.date_range("2020-07-07", periods=6, freq="s"),
            "source": ["train1", "train1", "test1", "test1", "test1", "test1"],
            "P1_A": [1, 1, 1, 2, 2, 1],
            "P1_B": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "attack": [0, 0, 0, 1, 1, 0],
            "attack_P1": [0, 0, 0, 1, 0, 0],
            "attack_P2": [0, 0, 0, 0, 0, 0],
            "attack_P3": [0, 0, 0, 0, 0, 0],
        }
    )


def test_attack_episodes_counts_rows_without_process_label():
    result = nodes.attack_episodes(_sample())
    assert len(result) == 1
    assert result.loc[0, "duration_s"] == 2
    assert result.loc[0, "rows_without_process"] == 1


def test_column_summary_marks_column_constant_only_in_train():
    result = nodes.column_summary(_sample()).set_index("column")
    assert result.loc["P1_A", "constant_in_train"]
    assert result.loc["P1_A", "varies_only_in_test"]
    assert not result.loc["P1_B", "constant_in_train"]
