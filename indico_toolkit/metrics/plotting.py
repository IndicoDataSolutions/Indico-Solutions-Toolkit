import plotly as py
import plotly.graph_objects as go
from typing import Iterable, Union


class Plotting:
    def __init__(self):
        self._plot_data = []
        self.layout = go.Layout()

    def add_barplot_data(
        self,
        x_data: Iterable[str],
        y_data: Iterable[Union[int, float]],
        name: str = "",
        color: str = "blue",
    ):
        """
        Add a bar plot object to your data.
        Args:
            x_data (Iterable[str]): Values/Groups that will go on X axis
            y_data (Iterable[Union[int, float]]): Values that will be plotted on y axis
            name (str, optional): If you have multiple bar plot groups, the distinct name for this group,
                                  e.g. "Model ID: 121". Defaults to "".
            color (str, optional): Choose a color, can be css name or rgb like 'rgb(31, 119, 180)'. Defaults to "blue".
        """
        self._plot_data.append(
            go.Bar(x=x_data, y=y_data, name=name, marker=dict(color=color))
        )

    def add_line_data(
        self,
        x_data: Iterable[str],
        y_data: Iterable[Union[int, float]],
        name: str = "",
        color: str = "blue",
    ):
        """
        Add a bar plot object to your data.
        Args:
            x_data (Iterable[str]): Values/Groups that will go on X axis
            y_data (Iterable[Union[int, float]]): Values that will be plotted on y axis
            name (str, optional): If you have multiple line plot groups, the distinct name for this group,
                                  e.g. "Model ID: 121". Defaults to "".
            color (str, optional): Choose a color, can be css name or rgb like 'rgb(31, 119, 180)'. Defaults to "blue".
        """
        self._plot_data.append(
            go.Scatter(x=x_data, y=y_data, name=name, marker=dict(color=color))
        )

    def define_layout(
        self,
        yaxis_title: str = "",
        legend_title: str = "",
        plot_title: str = "",
        xaxis_title: str = "",
    ):
        """
        Add labels to your visualization
        Args:
            yaxis_title (str, optional): Title for the y axis, e.g. "F1 Score". Defaults to "".
            xaxis_title (str, optional): Title for the x axis. Defaults to "".
            legend_title (str, optional): A title for the plot's legend e.g. "Model IDs". Defaults to "".
            plot_title (str, optional): A title above the plot. Defaults to "".
        """
        self.layout = go.Layout(
            title=plot_title,
            yaxis=dict(title=yaxis_title),
            xaxis=dict(title=xaxis_title),
            legend=dict(title=legend_title),
        )

    def plot(self, path_to_write_plot: str):
        """
        Write an html plot to disc. Will also open the plot automatically in your browser, where
        you will interactive functionality and the ability to download a copy as a PNG as well.
        Args:
            path_to_write_plot (str): where you want to write plot, e.g. "./myplot.html"
        """
        py.offline.plot(
            {"data": self._plot_data, "layout": self.layout},
            filename=path_to_write_plot,
        )
