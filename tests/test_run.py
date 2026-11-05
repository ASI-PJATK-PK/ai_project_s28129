"""Test rejestracji pipeline'ow projektu."""

from ai_project_s28129.pipeline_registry import register_pipelines


def test_eda_pipeline_is_registered():
    pipelines = register_pipelines()
    assert "eda" in pipelines
    assert len(pipelines["eda"].nodes) > 0
