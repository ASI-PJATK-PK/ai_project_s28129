"""Definicja pipeline'u EDA."""

from kedro.pipeline import Pipeline, node, pipeline

from . import nodes


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(nodes.load_data, ["raw_train1", "raw_test1", "raw_test2"], "hai", name="load_data"),
            node(nodes.data_quality, "hai", "eda_quality", name="data_quality"),
            node(nodes.column_stats, "hai", "eda_stats", name="column_stats"),
            node(
                nodes.plot_distributions,
                ["hai", "params:eda.columns"],
                "eda_fig_distributions",
                name="plot_distributions",
            ),
            node(nodes.plot_counts, "hai", "eda_fig_counts", name="plot_counts"),
            node(nodes.plot_correlation, "hai", "eda_fig_correlation", name="plot_correlation"),
            node(
                nodes.plot_pairplot,
                ["hai", "params:eda.pairplot_columns", "params:eda.pairplot_sample", "params:random_state"],
                "eda_fig_pairplot",
                name="plot_pairplot",
            ),
        ]
    )
