from __future__ import annotations

from pathlib import Path
from typing import Final, Literal

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.ticker import ScalarFormatter
from plotly import express as px
from rdetoolkit.errors import catch_exception_with_message
from rdetoolkit.exceptions import StructuredError
from rdetoolkit.models.rde2types import RdeOutputResourcePath

from modules_xrd.interfaces import IGraphPlotter
from modules_xrd.models import ScaleType


class GraphPlotter(IGraphPlotter[pd.DataFrame]):
    """Utility for plotting data using various types of plots.

    This class provides methods to generate and save different types of plots based on provided data.
    It supports line plots, log-scale plots, and multi-plots where multiple series are plotted on the same graph.

    """

    def __init__(
        self,
        main_image_scaletype: Literal[ScaleType.linear, ScaleType.log],
        other_image_scaletype: Literal[ScaleType.linear, ScaleType.log],
    ):
        """Init.

        Args:
            main_image_scaletype (ScaleType): main image scale type (Linear scale, Logarithmic scale).
            other_image_scaletype (ScaleType): other image scale type (Linear scale, Logarithmic scale).

        """
        self.title = ""
        self.multi_df: pd.DataFrame = []
        self.main_image_scaletype = main_image_scaletype
        self.other_image_scaletype = other_image_scaletype

    @catch_exception_with_message(error_message="Error: Could not draw graph")
    def plot_main(
        self,
        data: pd.DataFrame,
        resource_paths: RdeOutputResourcePath,
        processing_file: Path,
        region_num: int,
    ) -> None:
        """Plot main.

        Depending on the type of scale and the number of regions, the graph title, graph scale, and destination are processed.

        Args:
            data (pd.DataFrame): measurement data.
            resource_paths (RdeOutputResourcePath): Paths to output resources for saving results.
            processing_file (Path): processing file.
            region_num (int): Number of regions

        """
        single_region_num: Final[int] = 1
        multi_region_num: Final[int] = 2

        self._set_multi_dataset(data)
        image_basename = processing_file.stem
        if region_num == single_region_num:
            self._plot_single_region(data, resource_paths, image_basename)
        elif region_num == multi_region_num:
            self._plot_multiple_regions(data, resource_paths, image_basename)

    @catch_exception_with_message(error_message="Error: Could not draw graph")
    def multiplot_main(
        self,
        resource_paths: RdeOutputResourcePath,
        processing_file: Path,
    ) -> None:
        """Multiplot main.

        If there are two regions, the two graphs are displayed together.

        Args:
            resource_paths (RdeOutputResourcePath): Paths to output resources for saving results.
            processing_file (Path): processing file.

        """
        image_basename = processing_file.stem
        save_path = resource_paths.main_image.joinpath(f"{image_basename}_log.png") \
            if self.main_image_scaletype == ScaleType.log \
            else resource_paths.main_image.joinpath(f"{image_basename}.png")

        title = self.set_title_from_filename(save_path)
        self.multiplot(save_path, title=title, scale=self.main_image_scaletype)

    @catch_exception_with_message(error_message="Error: Could not draw graph")
    def plot(
        self,
        data: pd.DataFrame,
        htmlpath: Path,
        save_path: Path,
        *,
        title: str | None = None,
        xlabel: str | None = None,
        ylabel: str | None = None,
        scale: ScaleType = ScaleType.linear,
    ) -> None:
        """Plot and save a linear graph based on provided data.

        Args:
            data (pd.DataFrame): measurement data
            htmlpath (Path): Basename for the saved html image.
            save_path (Path): Basename for the saved image.
            title (str | None): Title for the graph. Defaults to None.
            xlabel (str | None): Title for the graph. Defaults to None.
            ylabel (str | None): Title for the graph. Defaults to None.
            scale (ScaleType): Information about the graph scale.

        """
        title = title or self.title or ""
        col = data.columns
        xlabel = xlabel or col[0]
        ylabel = ylabel or col[1]
        fig, ax = plt.subplots()

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if scale == ScaleType.linear:
            ax.set_title(title)
            ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
            data.plot(ax=ax, x=col[0], y=col[1], legend=False)
        else:
            ax.set_title(title)
            ax.set_yscale("log")
            data.plot(ax=ax, x=col[0], y=col[1], legend=False)

        fig.savefig(save_path)

        if scale == ScaleType.linear:
            self._to_html(data, col[0], col[1], htmlpath)

        plt.cla()
        plt.close()

    @catch_exception_with_message(error_message="Error: Could not draw graph")
    def multiplot(
        self,
        save_path: Path,
        *,
        data_series_1: pd.DataFrame | None = None,
        data_series_2: pd.DataFrame | None = None,
        title: str | None = None,
        xlabel: str | None = None,
        ylabel: str | None = None,
        scale: ScaleType = ScaleType.linear,
    ) -> None:
        """Plot two series of data on the same graph.

        Args:
            save_path (Path): Path where the plot will be saved.
            data_series_1 (pd.DataFrame): First set of data to be plotted.
            data_series_2 (pd.DataFrame): Second set of data to be plotted.
            title (str | None): Title of the graph. Defaults to an empty string.
            xlabel (str | None): Label for the x-axis. Defaults to an empty string.
            ylabel (str | None): Label for the y-axis. Defaults to the column name of the first data series.
            scale (ScaleType): Information about the graph scale.

        """
        title, data_series_1, data_series_2 = self._set_data_title(title, data_series_1, data_series_2)

        if data_series_1 is None or data_series_2 is None:
            err_msg = "Error: No input data to multi graphing."
            raise StructuredError(err_msg)

        col_series_1 = data_series_1.columns
        col_series_2 = data_series_2.columns
        xlabel = xlabel or col_series_1[0]
        ylabel = ylabel or col_series_1[1]

        fig, ax = plt.subplots()

        ax.set_ylabel(ylabel)
        if scale == ScaleType.linear:
            ax.set_title(title)
            ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
            data_series_1.plot(ax=ax, x=col_series_1[0], y=col_series_1[1], legend=False)
            data_series_2.plot(ax=ax, x=col_series_2[0], y=col_series_2[1], legend=False)
        else:
            ax.set_title(title + "(log)")
            ax.set_yscale("log")
            data_series_1.plot(ax=ax, x=col_series_1[0], y=col_series_1[1], legend=False)
            data_series_2.plot(ax=ax, x=col_series_2[0], y=col_series_2[1], legend=False)

        fig.savefig(save_path)

    @catch_exception_with_message(error_message="Type error: illegal type detected")
    def set_title_from_filename(self, filepath: str | Path) -> str:
        """Set the title name of the graph from the filename.

        Args:
            filepath (str | Path): Filename.

        Returns:
            str: Title name of the graph.

        """
        if isinstance(filepath, str):
            filepath = Path(filepath)
        return filepath.stem

    def _set_data_title(
        self,
        title: str | None = None,
        data_series_1: pd.DataFrame | None = None,
        data_series_2: pd.DataFrame | None = None,
    ) -> tuple[str, pd.DataFrame | None, pd.DataFrame | None]:
        """Set the title and multi region data.

        Args:
            title (str | None): Title of the graph. Defaults to an empty string.
            data_series_1 (pd.DataFrame): First set of data to be plotted.
            data_series_2 (pd.DataFrame): Second set of data to be plotted.

        Returns:
            title (str): Title of the graph. Defaults to an empty string.
            data_series_1 (pd.DataFrame): First set of data to be plotted.
            data_series_2 (pd.DataFrame): Second set of data to be plotted.

        """
        if title is None:
            title = self.title if self.title else ""

        if data_series_1 is None and len(self.multi_df) > 1:
            data_series_1 = self.multi_df[0]
        if data_series_2 is None and len(self.multi_df) > 1:
            data_series_2 = self.multi_df[1]

        return title, data_series_1, data_series_2

    def _set_multi_dataset(self, data: pd.DataFrame) -> None:
        """Methods to store datasets to be graphed into instance variables.

        Args:
            data (pd.DataFrame): data to be graphed

        """
        self.multi_df.append(data)

    def _plot_single_region(self, data: pd.DataFrame, resource_paths: RdeOutputResourcePath, image_basename: str) -> None:
        """Plot for a single region."""
        main_save_path, other_save_path = self._make_imagefilename(self.main_image_scaletype, resource_paths, image_basename)
        htmlpath = self._savefilename(resource_paths.struct.joinpath(f"{image_basename}.html"), region_num=1, scale=None)
        for save_path, scale in ((main_save_path, self.main_image_scaletype), (other_save_path, self.other_image_scaletype)):
            title = self.set_title_from_filename(save_path)
            self.plot(data, htmlpath, save_path, title=title, scale=scale)

    def _plot_multiple_regions(self, data: pd.DataFrame, resource_paths: RdeOutputResourcePath, image_basename: str) -> None:
        """Plot for multiple regions."""
        for scale in [self.other_image_scaletype, self.main_image_scaletype]:
            save_path = self._savefilename(resource_paths.other_image.joinpath(f"{image_basename}.png"), region_num=2, scale=scale)
            htmlpath = self._savefilename(resource_paths.struct.joinpath(f"{image_basename}.html"), region_num=2, scale=None)
            title = self.set_title_from_filename(save_path)
            self.plot(data, htmlpath, save_path, title=title, scale=scale)

    def _savefilename(self, filepath: str | Path, region_num: int, scale: ScaleType | None) -> Path:
        """Rename the destination file path.

        When supporting multiple regions, the file name of files with the same name
        is changed to a filename with an index appended at the end.
        If the scale of the graph is log, the filename is renamed to indicate this.

        Args:
            filepath (str | Path): The file path to be changed.
            region_num (int): Number of regions.
            scale (ScaleType): Information about the graph scale.

        Raises:
            StructuredError: An exception occurs if an invalid number of regions is passed.

        Returns:
            Path: save file name.

        """
        single_region_num: Final[int] = 1
        multi_region_num: Final[int] = 2

        if isinstance(filepath, str):
            filepath = Path(filepath)

        if region_num > multi_region_num or region_num < single_region_num:
            err_msg = f"illegal region number: {region_num}"
            raise StructuredError(err_msg)

        dirname = filepath.parent
        basename = filepath.stem
        suffix = filepath.suffix
        scale_suffix = "_log" if scale == ScaleType.log else ""

        if region_num == single_region_num:
            new_filename = f"{basename}{scale_suffix}{suffix}"
            return dirname / new_filename

        idx = 1
        while True:
            new_filename = f"{basename}_{idx}{scale_suffix}{suffix}"
            new_filepath = dirname / new_filename
            if not new_filepath.exists():
                break
            idx += 1

        return new_filepath

    def _make_imagefilename(
        self,
        main_image_scaletype: ScaleType,
        resource_paths: RdeOutputResourcePath,
        image_basename: str,
    ) -> tuple[Path, Path]:
        """Make the destination file path.

        Args:
            main_image_scaletype (ScaleType): main image scaletype.
            resource_paths (RdeOutputResourcePath): Paths to output resources for saving results.
            image_basename (str): image basename.

        Returns:
            tuple[Path, Path]: main image path, other image path.

        """
        if main_image_scaletype.value == "log":
            main_save_path = resource_paths.main_image.joinpath(f"{image_basename}_log.png")
            other_save_path = resource_paths.other_image.joinpath(f"{image_basename}.png")
        else:
            main_save_path = resource_paths.main_image.joinpath(f"{image_basename}.png")
            other_save_path = resource_paths.other_image.joinpath(f"{image_basename}_log.png")

        return main_save_path, other_save_path

    def _to_html(self, data: pd.DataFrame, col_x: str, col_y: str, htmlpath: Path) -> None:
        """Output graph images in html.

        Args:
            data (pd.DataFrame): Graph data to be output.
            col_x (str): label or position.
            col_y (str): label or position.
            htmlpath (Path): Output path of the html file.

        """
        fig = px.line(data, x=col_x, y=col_y)
        with open(htmlpath, "w") as f:
            f.write(fig.to_html(include_plotlyjs="cdn"))
