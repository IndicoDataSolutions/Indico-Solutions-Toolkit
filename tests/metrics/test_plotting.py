import pytest
from plotly.graph_objects import Bar
from indico_toolkit.metrics import Plotting


def test_add_barplot_data():
    plotting = Plotting()
    plotting.add_barplot_data(["a", "b"], [1, 2])
    plotting.add_barplot_data(["a", "b"], [3, 4])
    assert len(plotting._plot_data) == 2
    assert isinstance(plotting._plot_data[0], Bar)


def test_add_barplot_exception():
    with pytest.raises(ValueError):
        plotting = Plotting()
        plotting.add_barplot_data("Whoops!", [1, 2])
