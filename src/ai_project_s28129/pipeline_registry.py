"""Project pipelines."""
from __future__ import annotations

from kedro.pipeline import Pipeline

from ai_project_s28129.pipelines import eda as eda_pipeline


def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """
    eda = eda_pipeline.create_pipeline()
    return {"eda": eda, "__default__": eda}
