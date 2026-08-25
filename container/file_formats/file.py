import json
import os
import re
import zipfile
import zoneinfo
from abc import abstractmethod
from collections.abc import Generator
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Final, Literal

import chardet
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.ticker import ScalarFormatter
from plotly import express as px
from rdetoolkit import rde2util
from rdetoolkit.errors import catch_exception_with_message
from rdetoolkit.exceptions import StructuredError
from rdetoolkit.fileops import readf_json, writef_json
from rdetoolkit.invoicefile import InvoiceFile, overwrite_invoicefile_for_dpfterm
from rdetoolkit.models.rde2types import MetaType, RdeOutputResourcePath, RepeatedMetaType
from rdetoolkit.rde2util import CharDecEncoding
from sample_api_client import (
    entry_sample,
    find_sample,
    find_sample_detail,
    get_groupid,
    get_token,
    read_payload_file,
)

from file_formats.rasx_rigaku_schema import ExtendMetaType


class ScaleType(Enum):
    log = "log"
    linear = "linear"


class BaseFileReader:
    """Reads and processes structured files into data and metadata blocks.

    This class is responsible for reading structured files which have specific patterns for data and metadata.
    It then separates the contents into data blocks and metadata blocks.

    Attributes:
        data (dict[str, pd.DataFrame]): Dictionary to store separated data blocks.
        meta (dict[str, list[str]]): Dictionary to store separated metadata blocks.

    """

    def __init__(self, config: dict):
        self.data: dict[str, pd.DataFrame] = {}
        self.region_num = 0
        self.config = config

    @abstractmethod
    def read(self, srcpath: Path) -> Generator[tuple[pd.DataFrame, ExtendMetaType]]:
        """Input File Reading (implementation is in the subclass)."""
        raise NotImplementedError

    @abstractmethod
    def get_region_number(self, *, input_path: Path | None = None) -> int:
        """Get region number (implementation is in the subclass)."""
        raise NotImplementedError

    @staticmethod
    def determine_delimiter(file_path: Path) -> Literal["\t", " "]:
        r"""Determine delimiter.

        MEMO: If there are the same number of tabs and spaces,
            they should be tab-separated. (That's absurd.)
        MEMO: Redundant writing.

        Args:
            file_path (Path): measurement file.

        Returns:
            tuple[str, str]: [(r'\t' or ' '), ('_tab' or '_space')]

        """
        tab_count = 0
        space_count = 0

        enc = CharDecEncoding.detect_text_file_encoding(file_path)  # MEMO: It may not be judged correctly.
        if enc in ["macroman", "mac_roman", ""]:
            # False character code detection
            enc = "cp932"

        with open(file_path, encoding=enc) as file:
            for line in file:
                tab_count += line.count('\t')
                space_count += line.count(' ')

        if space_count > tab_count:
            return " "
        return "\t"

    def get_files_from_rasx(self, rasx_path: Path) -> list[str]:
        """Substance is in rigaku/rasx/inputfile_handler.py (only .rasx)."""
        return []


class BaseMetaParser:
    """Parses metadata and saves it to a specified path.

    This class is designed to parse metadata from a dictionary and save it to a specified path using
    a provided Meta object. It can handle both constant and repeated(variable) metadata.

    Attributes:
        const_meta_info (MetaType | None): Dictionary to store constant metadata.
        repeated_meta_info (RepeatedMetaType | None): Dictionary to store repeated metadata.

    """

    def __init__(self, *, metadata_def_json_path: Path | None = None, config: dict[str, str | None]):
        self.const_meta_info: MetaType = {}
        self.repeated_meta_info: RepeatedMetaType = {}
        self.metadata_def_json_path = metadata_def_json_path
        self.config: dict = config

    @abstractmethod
    def parse(self, data: ExtendMetaType) -> tuple[MetaType, RepeatedMetaType]:
        """Perform metadata parsing (implementation is in the subclass)."""
        raise NotImplementedError

    def save_meta(
        self,
        save_path: Path,
        metaobj: rde2util.Meta,
        *,
        const_meta_info: MetaType | None = None,
        repeated_meta_info: RepeatedMetaType | None = None,
    ) -> None:
        """Save parsed metadata to a file using the provided Meta object.

        Args:
            save_path (Path): The path where the metadata will be saved.
            metaobj (rde2util.Meta): The Meta object that handles operate of metadata.
            const_meta_info (MetaType | None): The constant metadata to save. Defaults to the
            internal const_meta_info if not provided.
            repeated_meta_info (RepeatedMetaType | None): The repeated metadata to save. Defaults
            to the internal repeated_meta_info if not provided.

        Returns:
            str: The result of the meta assignment operation.

        """
        if const_meta_info is None:
            const_meta_info = self.const_meta_info
        if repeated_meta_info is None:
            repeated_meta_info = self.repeated_meta_info
        metaobj.assign_vals(const_meta_info)
        metaobj.assign_vals(repeated_meta_info)

        metaobj.writefile(str(save_path))


class BaseStructuredDataProcessor:
    """Template class for parsing structured data.

    This class serves as a template for the development team to read and parse structured data.
    Developers can use this template class as a foundation for adding specific file reading
    and parsing logic based on the project's requirements.

    Attributes:
        df_series_1 (pd.DataFrame): The first series of data.
        df_series_2 (pd.DataFrame): The second series of data.

    Example:
        csv_handler = StructuredDataProcessor()
        df = pd.DataFrame([[1,2,3],[4,5,6]])
        loaded_data = csv_handler.to_csv(df, 'file2.txt')

    """

    def __init__(self) -> None:
        self.df_series_1 = pd.DataFrame()
        self.df_series_2 = pd.DataFrame()

    def save_csv(
            self,
            resource_paths: RdeOutputResourcePath,
            processing_file: Path,
            dataframe: pd.DataFrame,
            region_num: int,
    ) -> None:
        """Save structured data to a csv file.

        Args:
            resource_paths (RdeOutputResourcePath): Paths to output resources for saving results.
            processing_file (Path): processing file.
            dataframe (pd.DataFrame): The data to save.
            region_num (int): Region numbers.

        """
        rename_save_path = self.reindex_savefilename(
            resource_paths.struct.joinpath(f"{processing_file.stem}.csv"),
            region_num=region_num,
        )
        dataframe.to_csv(rename_save_path, index=False)

    def save_structured_contents(
        self,
        resource_paths: RdeOutputResourcePath,
        processing_file: Path,
        compressed_files: list[str],
    ) -> None:
        """Save a file with human-readable metadata to the specified folder.

        Args:
            resource_paths (RdeOutputResourcePath): Paths to output resources for saving results.
            processing_file (Path): processing file.
            compressed_files (list[str]): compressed files. (not use)

        Note:
            In RDE, the structured folder includes all files that are not included in
            main_image or other_image and should be outputted.

        """
        for cmpfile in compressed_files:
            basename = self._get_basename(cmpfile)
            contents = self._read_compressed_contents(str(cmpfile), str(processing_file)) \
                if processing_file is not None \
                else self._read_text_contents(cmpfile)
            self._write_contents(resource_paths.struct.joinpath(basename), contents)

    def reindex_savefilename(self, filepath: str | Path, region_num: int) -> Path:
        """Indexing file names.

        Args:
            filepath (str | Path): File name before renaming.
            region_num (int): Region numbers.

        Returns:
            Path: Renamed file name.

        """
        single_region_num: Final[int] = 1
        multi_region_num: Final[int] = 2

        if isinstance(filepath, str):
            filepath = Path(filepath)

        if region_num > multi_region_num or region_num < single_region_num:
            err_msg = f"illegal region number: {region_num}"
            raise StructuredError(err_msg)
        if region_num == single_region_num:
            return filepath

        dirname = filepath.parent
        basename = filepath.stem
        suffix = filepath.suffix

        idx = 1
        while True:
            new_filename = f"{basename}_{idx}{suffix}"
            new_filepath = dirname / new_filename
            if not new_filepath.exists():
                break
            idx += 1

        return new_filepath

    def _get_basename(self, src_path: str | Path) -> str:
        """Get the basename of the source path."""
        if isinstance(src_path, Path):
            return src_path.name
        return os.path.basename(src_path)

    def _read_compressed_contents(self, src_path: str, compressed_filepath: str) -> str:
        """Read the contents of a compressed file."""
        with zipfile.ZipFile(compressed_filepath, "r") as rasx, rasx.open(src_path) as frasx:
            contents_bytes = frasx.read()
        _, ext = os.path.splitext(src_path)
        contents = contents_bytes.decode("utf-8") if ext not in [".rasx", ".zip"] else ""
        if not contents and isinstance(contents_bytes, bytes):
            contents = str(contents_bytes)
        return contents

    def _read_text_contents(self, src_path: str | Path) -> str:
        """Read the contents of a text file."""
        enc = CharDecEncoding.detect_text_file_encoding(src_path)
        with open(src_path, encoding=enc) as f:
            return f.read()

    def _write_contents(self, save_path: Path, contents: str) -> None:
        """Write the contents to the save path."""
        with open(save_path, mode="w", encoding="utf-8") as f:
            f.write(contents)


class BaseGraphPlotter:
    """Utility for plotting data using various types of plots.

    This class provides methods to generate and save different types of plots based on provided data.
    The implementations are expected to be capable of plotting a simple graph using a given pandas DataFrame.
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
        self.multi_df: list = []
        self.main_image_scaletype = main_image_scaletype
        self.other_image_scaletype = other_image_scaletype
        plt.rcParams["font.family"] = "Noto Sans CJK JP"

    @catch_exception_with_message(error_message="Error: Could not draw graph")
    def plot_main(
        self,
        data: pd.DataFrame,
        resource_paths: RdeOutputResourcePath,
        processing_file: Path,
        region_num: int,
    ) -> None:
        """Plot main.

        Depending on the type of scale and the number of regions, the graph title, graph scale,
        and destination are processed.

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

    def _plot_single_region(
        self,
        data: pd.DataFrame,
        resource_paths: RdeOutputResourcePath,
        image_basename: str,
    ) -> None:
        """Plot for a single region."""
        main_save_path, other_save_path = self._make_imagefilename(
            self.main_image_scaletype, resource_paths, image_basename,
        )
        htmlpath = self._savefilename(
            resource_paths.struct.joinpath(f"{image_basename}.html"), region_num=1, scale=None,
        )
        for save_path, scale in \
                ((main_save_path, self.main_image_scaletype), (other_save_path, self.other_image_scaletype)):
            title = self.set_title_from_filename(save_path)
            self.plot(data, htmlpath, save_path, title=title, scale=scale)

    def _plot_multiple_regions(
        self,
        data: pd.DataFrame,
        resource_paths: RdeOutputResourcePath,
        image_basename: str,
    ) -> None:
        """Plot for multiple regions."""
        for scale in [self.other_image_scaletype, self.main_image_scaletype]:
            save_path = self._savefilename(
                resource_paths.other_image.joinpath(f"{image_basename}.png"), region_num=2, scale=scale,
            )
            htmlpath = self._savefilename(
                resource_paths.struct.joinpath(f"{image_basename}.html"), region_num=2, scale=None,
            )
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


class BaseInvoiceWriter:
    """Invoice writer.

    Overwrite invoice.json files depending on conditions.

    """

    def __init__(self, config: dict):
        self.config: dict = config

    def overwrite_invoice_if_needed(
        self,
        invoice_path: Path,
        resources: RdeOutputResourcePath,
    ) -> None:
        """Update an invoice JSON file using data from a CSV and API lookups.

        Args:
            invoice_path: Path to the JSON file that will be overwritten if changes occur.
            resources: Provides access to raw file paths, including the CSV source.

        The function reads the first matching ``fsmarttable*.csv`` file, extracts the
        ``sample/names`` column, and resolves the sample information via API calls.
        Depending on the lookup results, it updates ``invoice["sample"]`` with either
        a new sample entry or the existing sample ID and names. The updated invoice
        is then written back to ``dst_json``.

        """
        if not resources.smarttable_rawfile or \
                not resources.smarttable_rawfile.match("fsmarttable*csv"):
            return  # Not smarttable.

        with open(str(invoice_path), "rb") as f:
            raw_data = f.read()
            enc = chardet.detect(raw_data)["encoding"]
            if enc is not None:
                invoice_obj = json.loads(raw_data.decode(enc))
            else:
                return  # Could not load the character encoding.

        token = get_token()
        if not token:
            # df = pd.read_csv(resources.smarttable_rawfile, keep_default_na=False)  # Blank cells are None, not NaN.
            # payload_obj = read_payload_file()
            # payload_obj = self._set_sample_details(token, invoice_obj, payload_obj, df)
            return  # For local test

        df = pd.read_csv(resources.smarttable_rawfile, keep_default_na=False)  # Blank cells are None, not NaN.
        col_name = "sample/names"
        name = df.at[0, col_name] if col_name in df.columns else None
        if not name:
            return  # Sample name not set.

        dataset_id = invoice_obj["datasetId"]
        # Search by dataset ID and sample name (and group ID)
        samples = json.loads(find_sample(token, dataset_id, name)).get("data", [])

        # Narrow down candidate samples by name.
        # If there is no name match, proceed to new registration (determined during subsequent processing).
        name_matches = [s for s in samples if s["attributes"]["names"][0] == name]
        # If there are multiple samples with the same name, the first match is referenced.
        target_sample = name_matches[0] if name_matches else None

        # If `target sample` is `None`, register a new entry; if a value is present, select that sample.
        if target_sample is None:
            # Register as new if there are no sample names.
            payload_obj = read_payload_file()
            payload_obj["data"]["attributes"]["names"].append(name)
            payload_obj["data"]["relationships"]["owningGroup"]["data"]["id"] = get_groupid(token, dataset_id)
            payload_obj["data"]["relationships"]["owner"]["data"]["id"] = invoice_obj["sample"]["ownerId"]

            payload_obj = self._set_sample_details(token, invoice_obj, payload_obj, df)

            # New Sample Registration.
            sample_json = json.loads(entry_sample(token, payload_obj))
            invoice_obj["sample"]["names"] = [name]
        else:
            # Set registered samples.
            sample_json = json.loads(find_sample_detail(token, target_sample["id"]))
            invoice_obj["sample"]["names"] = sample_json["data"]["attributes"]["names"]

        invoice_obj["sample"]["sampleId"] = sample_json["data"]["id"]
        invoice_obj["sample"]["ownerId"] = sample_json["data"]["relationships"]["owner"]["data"]["id"]

        with invoice_path.open("w", encoding=enc) as f:
                    json.dump(invoice_obj, f, indent=4, ensure_ascii=False)

    def overwrite_invoice_measured_date(
        self,
        resource_paths: RdeOutputResourcePath,
        suffix: str,
        const_meta: MetaType,
        repeat_meta: RepeatedMetaType,
    ) -> None:
        """Overwrite invoice if needed.

        The date is to be obtained from the output device and output to invoice.
        The measurement date and time are written automatically to the invoice.json file
        # based on the file meta data output from the device, so I added a process to write it to invoice.json.

        Args:
            resource_paths (RdeOutputResourcePath): Paths to output resources for saving results.
            suffix (str): Input file extension.
            const_meta (MetaType): Metadata defined as constant.
            repeat_meta (RepeatedMetaType): Metadata defined as variable.

        """
        invoice_obj = readf_json(resource_paths.invoice_org)
        update_invoice_term_info = self._get_update_mesurement_date_dpf_metadata(
            suffix,
            invoice_obj,
            const_meta,
            repeat_meta,
        )
        if update_invoice_term_info:
            overwrite_invoicefile_for_dpfterm(
                invoice_obj,
                resource_paths.invoice_org,
                resource_paths.invoice_schema_json,
                update_invoice_term_info,
            )
            invoice_org_obj = InvoiceFile(resource_paths.invoice_org)
            invoice_org_obj.overwrite(resource_paths.invoice.joinpath("invoice.json"))

    def overwrite_invoice_sample_name(
        self,
        resource_paths: RdeOutputResourcePath,
    ) -> None:
        """Overwrite sample name if needed.

        About filename-mapping-rule
        If the item filename_mapping_rule in the rdeconfig.yaml file is true,
        change the dataset name and sample information based on the file name.

        Args:
            resource_paths (RdeOutputResourcePath): Paths to output resources for saving results.

        """
        if not self.config['xrd']['filename_mapping_rule']:
            return

        suffix = resource_paths.rawfiles[0].suffix
        if not (self.config['xrd']['manufacturer'] == "rigaku" and suffix in {".ras", ".rasx"}):
            return

        invoice_org_obj = InvoiceFile(resource_paths.invoice_org)
        invoice_org_obj.invoice_obj = readf_json(resource_paths.invoice_org)

        file_name_sections = resource_paths.rawfiles[0].stem.split("_")
        if len(file_name_sections) > 1:
            invoice_org_obj.invoice_obj["sample"]["sampleId"] = None
            invoice_org_obj.invoice_obj["sample"]["names"][0] = file_name_sections[1]
        else:
            err_msg = "Invalid Filename Error: A file without delimiters has been inputted."
            raise StructuredError(err_msg)

        enc = CharDecEncoding.detect_text_file_encoding(resource_paths.invoice_org)
        writef_json(resource_paths.invoice_org, invoice_org_obj.invoice_obj, enc=enc)
        invoice_org_obj.overwrite(resource_paths.invoice.joinpath("invoice.json"))

    def _get_update_mesurement_date_dpf_metadata(
        self,
        suffix: str,
        invoice_obj: dict[str, Any],
        const_meta: MetaType,
        repeat_meta: RepeatedMetaType,
    ) -> dict[str, str]:
        """Update metadata information about the measurement date and time.

        This function works exclusively with rigaku.
        Due to the different vocabulary used in rigaku to indicate the measurement date and time,
        the process is specifically defined for these formats.

        Args:
            suffix (str): file extension
            invoice_obj (dict[str, Any]): Object of ivnoice.json or invoice_org.json
            const_meta (dict[str, str]): Metadata defined as constant
            repeat_meta (dict[str, list[str]]): Metadata defined as variable

        Returns:
            dict[str, str]: Metadata information updated with the measurement date and time

        """
        update_invoice_term_info: dict[str, str] = {}
        if "measurement_measured_date" not in invoice_obj["custom"]:
            return update_invoice_term_info

        keywd: str = ""
        date_expressions: datetime | None = None
        match suffix.lower():
            case ".ras":
                keywd = "MEAS_SCAN_START_TIME"
            case ".rasx":
                keywd = "rasx.scan_starting_date_time"
            case ".txt":
                keywd = "StartTime"
            case ".uxd":
                keywd = "_DATEMEASURED"
                date_expressions = self._extract_date(repeat_meta, keywd)

        mesurement_date_value = invoice_obj["custom"].get("measurement_measured_date")
        if const_meta.get(keywd) and not mesurement_date_value:
            update_invoice_term_info["measurement_measured_date"] = str(const_meta[keywd])
        elif repeat_meta.get(keywd) and not mesurement_date_value and date_expressions:
            update_invoice_term_info["measurement_measured_date"] = str(date_expressions)
        elif repeat_meta.get(keywd) and not mesurement_date_value and repeat_meta[keywd][0]:
            update_invoice_term_info["measurement_measured_date"] = str(repeat_meta[keywd][0])

        return update_invoice_term_info

    def _extract_date(self, repeat_meta: RepeatedMetaType, keywd: str) -> datetime | None:
        """Find out if the date can be extracted.

        Args:
            repeat_meta (RepeatedMetaType): Repeated meta.
            keywd (str): item of measurement date and time.

        Returns:
            datetime | None: Extracted string. (Return 'None' if not possible.)

        """
        formats = [
            "%d-%b-%Y %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ]

        if keywd not in repeat_meta:
            return None

        sentence = repeat_meta[keywd][0]
        if not isinstance(sentence, str):
            return None

        for fmt in formats:
            try:
                return datetime.strptime(sentence, fmt).astimezone(tz=zoneinfo.ZoneInfo(key='UTC'))
            except ValueError:
                continue

        return None

    def _set_sample_details(self, token: str, invoice_obj: dict, payload_obj: dict, df: Any) -> dict:
        """Set sample details for sample api.

        Args:
            token: Api token.
            invoice_obj: Invoice object.
            payload_obj: payload object prior to update.
            df: Sample data.

        Returns:
            dict: Updated payload object.

        """
        col_keys = [
            "sample/names",           # 試料名(ローカルID)
            "sample/composition",     # 化学式・組成式・分子式など
          # "sample/hideOwner",       # 所有者秘匿
            "sample/referenceUrl",    # 参考URL
            "sample/relatedSamples",  # 関連試料
            "sample/tags",            # タグ
            "sample/description",     # 試料の説明
            "sample/generalAttributes.3adf9874-7bcb-e5f8-99cb-3d6fd9d7b55e",  # 一般名称
            "sample/generalAttributes.e2d20d02-2e38-2cd3-b1b3-66fdb8a11057",  # CAS番号
            "sample/generalAttributes.efcf34e7-4308-c195-6691-6f4d28ffc9bb",  # 結晶構造
            "sample/generalAttributes.7cc57dfb-8b70-4b3a-5315-fbce4cbf73d0",  # 試料形状
            "sample/generalAttributes.1e70d11d-cbdd-bfd1-9301-9612c29b4060",  # 試料購入日
            "sample/generalAttributes.5e166ac4-bfcd-457a-84bc-8626abe9188f",  # 購入元
            "sample/generalAttributes.0d0417a3-3c3b-496a-b0fb-5a26f8a74166",  # ロット番号、製造番号など
        ]

        for col_key in col_keys:
            col_value = df.at[0, col_key] if col_key in df.columns else None

            if col_value:
                second_key = re.split(r"[/.]", col_key)[1]
                leaf_key = re.split(r"[/.]", col_key)[-1]

                if second_key == "generalAttributes":
                    payload_obj["data"]["attributes"]["generalAttributes"].append({
                        "termId": leaf_key,
                        "value": col_value,
                    })
                elif second_key == "relatedSamples":
                    dataset_id = invoice_obj["datasetId"]
                    samples = json.loads(find_sample(token, dataset_id, col_value)).get("data", [])
                    name_matches = [s for s in samples if s["attributes"]["names"][0] == col_value]
                    related_sample = name_matches[0] if name_matches else None
                    if related_sample is None:
                        err_msg = f"The sample does not exist. {col_value}"
                        raise StructuredError(err_msg)

                    sample_json = json.loads(find_sample_detail(token, related_sample["id"]))
                    if sample_json["data"]["relationships"]["owner"]["data"]["id"] != invoice_obj["sample"]["ownerId"]:
                        err_msg = f"The sample does not exist. {col_value}"
                        raise StructuredError(err_msg)

                    payload_obj["data"]["attributes"]["relatedSamples"].append({
                        "relatedSampleId": related_sample["id"],
                        "description": "",  # Compromise
                    })
                else:
                    try:
                        payload_obj["data"]["attributes"][leaf_key] = json.loads(col_value)
                    except json.JSONDecodeError:
                        payload_obj["data"]["attributes"][leaf_key] = \
                            [col_value] if second_key in {"names", "tags"} \
                            else col_value

        return payload_obj
