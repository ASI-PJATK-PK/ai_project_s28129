"""Definicja pipeline'u EDA."""

from kedro.pipeline import Pipeline, node, pipeline

from . import nodes


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                nodes.combine_files,
                ["raw_train1", "raw_test1", "raw_test2"],
                "hai_flat",
                name="combine_files",
            ),
            node(nodes.file_summary, "hai_flat", "eda_file_summary", name="file_summary"),
            node(nodes.column_summary, "hai_flat", "eda_column_summary", name="column_summary"),
            node(nodes.attack_episodes, "hai_flat", "eda_attack_episodes", name="attack_episodes"),
            node(nodes.plot_histograms, "hai_flat", "eda_fig_histograms", name="plot_histograms"),
            node(
                nodes.plot_boxplots,
                ["hai_flat", "params:eda.boxplot_sample", "params:random_state"],
                "eda_fig_boxplots",
                name="plot_boxplots",
            ),
            node(nodes.plot_counts, "hai_flat", "eda_fig_counts", name="plot_counts"),
            node(nodes.plot_correlation, "hai_flat", "eda_fig_correlation", name="plot_correlation"),
            node(
                nodes.plot_pairplot,
                [
                    "hai_flat",
                    "params:eda.pairplot_columns",
                    "params:eda.pairplot_sample",
                    "params:random_state",
                ],
                "eda_fig_pairplot",
                name="plot_pairplot",
            ),
            node(
                nodes.plot_attack_example,
                ["hai_flat", "params:eda.example_attack"],
                "eda_fig_attack_example",
                name="plot_attack_example",
            ),
        ]
    )
