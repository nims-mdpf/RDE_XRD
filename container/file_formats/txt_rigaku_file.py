from __future__ import annotations

import datetime
import re
from collections import defaultdict
from collections.abc import Generator
from pathlib import Path

import pandas as pd
from rdetoolkit.exceptions import StructuredError
from rdetoolkit.models.rde2types import MetaType, RepeatedMetaType
from rdetoolkit.rde2util import CharDecEncoding
from rdetoolkit.rdelogger import get_logger

from file_formats.file import BaseFileReader, BaseMetaParser
from file_formats.rasx_rigaku_schema import ExtendMetaType


class FileReader(BaseFileReader):
    """Reads and processes structured ras files into data and metadata blocks.

    This class is responsible for reading structured files which have specific patterns for data and metadata.
    It then separates the contents into data blocks and metadata blocks.

    Attributes:
        data (dict[str, pd.DataFrame]): Dictionary to store separated data blocks.
        meta (dict[str, list[str]]): Dictionary to store separated metadata blocks.

    """

    __mode__ = "txt"

    def __init__(self, config: dict):
        super().__init__(config)
        self.meta: dict[str, ExtendMetaType] = {}

    def read(self, srcpath: Path) -> Generator[tuple[pd.DataFrame, ExtendMetaType]]:
        """Read the structured file and returns separated data and metadata.

        Args:
            srcpath (Path): The path of the structured file to read.

        Returns:
            tuple[tuple[pd.DataFrame, ExtendMetaType], ...]: A tuple containing two dictionaries -
            the first one for data blocks and the second one for metadata blocks.

        Raises:
            StructuredError: If the file is formatted incorrectly.

        """
        enc = CharDecEncoding.detect_text_file_encoding(srcpath)  # MEMO: It may not be judged correctly.
        if enc in ["macroman", "mac_roman", ""]:
            # False character code detection
            enc = "cp932"
        with open(srcpath, encoding=enc) as f:
            self.data, self.meta = self.split_data_meta(f.read().splitlines())
        if not self.data or not self.meta:
            err_msg = f"Cannot read the file because it is formatted incorrectly: {srcpath}"
            raise StructuredError(err_msg)

        self.region_num = len(self.data.keys())
        for data_key, meta_key in zip(self.data, self.meta, strict=False):
            yield self.convert_dtype(self.data[data_key]), self.meta[meta_key]

    def convert_dtype(self, dataframe: pd.DataFrame, *, totype: str = "float") -> pd.DataFrame:
        """Convert data type.

        Args:
            dataframe (pd.DataFrame): Data frame before conversion.
            totype (str): Converted data type.

        Returns:
            pd.DataFrame: Data frame after conversion.

        """
        return dataframe.map(self.__helper_convert_string_numeric, dtype=totype)

    def get_region_number(self, *, input_path: Path | None = None) -> int:
        """Get the number of regions.

        Args:
            input_path (Path | None): Measurement file path.

        Returns:
            int: Number of regions.

        """
        if input_path is None:
            return self.region_num
        data_meta_mappings = [df_data for df_data, _ in self.read(input_path)]
        self.region_num = len(data_meta_mappings)
        return self.region_num

    def split_data_meta(self, contents: list) -> tuple[dict[str, pd.DataFrame], dict[str, ExtendMetaType]]:
        """Private method to split the contents into data and metadata blocks.

        Args:
            contents: The contents of the structured file as a string.

        Returns:
            tuple[dict[str, pd.DataFrame], dict[str, ExtendMetaType]]: A tuple containing two dictionaries -
            the first one for data blocks and the second one for metadata blocks.

        """
        meta_lines: dict = {}
        data_lines = []
        meta_blocks: dict[str, ExtendMetaType] = {}
        data_blocks: dict[str, pd.DataFrame] = {}

        for line_org in contents:
            line = line_org.strip()
            tokens = [s.strip() for s in line.split(self.config['xrd']['delimiter_type'])]
            if len(line) == 0:
                continue
            if line[0].isalpha():
                if len(tokens) <= 1:
                    continue
                if any(s in tokens[0] for s in ["StartTime", "StopTime"]) and \
                        not self._is_valid_datetime(tokens):
                    continue
                # header section
                meta_lines[tokens[0]] = " ".join(tokens[1:])
            else:
                # data section
                data_lines.append(tokens)

        if meta_lines:
            meta_blocks["series_meta1"] = meta_lines
        if data_lines and meta_lines:
            column = self._make_header(meta_lines)
            data_blocks["series_value1"] = pd.DataFrame(data_lines, columns=column)

        return data_blocks, meta_blocks

    def _make_header(self, meta_lines: dict) -> list[str]:
        """Make a header using provided header information.

        Args:
            meta_lines (dict): The header information dictionary.

        Returns:
            list[str]: The constructed header string.

        """
        if 'ScanningMode' not in meta_lines:
            meta_lines['ScanningMode'] = self.config['xrd']['scanning_mode_if_not_exist']
        x_label = self.config['xrd']['meas_scan_axis_x'] \
            if self.config['xrd']['meas_scan_axis_x']  else meta_lines['ScanningMode']
        x_unit = "(" + self.config['xrd']['meas_scan_unit_x'] + ")" \
            if self.config['xrd']['meas_scan_unit_x'] else ""
        y_label = self.config['xrd']['meas_scan_axis_y'] \
            if self.config['xrd']['meas_scan_axis_y'] else "Intensity"
        y_unit = "(" + self.config['xrd']['meas_scan_unit_y'] + ")" \
            if self.config['xrd']['meas_scan_unit_y'] else ""

        return [f"{x_label} {x_unit}", f"{y_label} {y_unit}"]

    def __helper_convert_string_numeric(self, x: str, dtype: str) -> float | int:
        """Convert string numeric.

        Args:
            x (str): Before conversion.
            dtype (str): Converted data type.

        Returns:
            pd.DataFrame: After conversion.

        """
        if dtype not in ["float", "int"]:
            err_msg = f"UnSupported dtype: {dtype}"
            raise StructuredError(err_msg)
        try:
            if dtype == "float":
                return float(x)
            return int(x)
        except ValueError:
            err_msg = f"Failed to convert {x} to {dtype}"
            raise StructuredError(err_msg) from None

    def _is_valid_datetime(self, tokens: list) -> bool:
        """Date validity check."""
        try:
            datetime.datetime.strptime(" ".join(tokens[1:]), "%Y/%m/%d %H:%M:%S").astimezone(datetime.UTC)
            return True
        except ValueError:
            logger = get_logger(__name__, file_path="data/logs/invalid_datetime.log")
            logger.error(f"Invalid datetime. {tokens[0]}: {tokens[1:]}")
            return False

class MetaParser(BaseMetaParser):
    """Parses metadata and saves it to a specified path.

    This class is designed to parse metadata from a dictionary and save it to a specified path using
    a provided Meta object. It can handle both constant and repeated metadata.

    """

    __mode__ = "txt"

    def __init__(self, *, metadata_def_json_path: Path | None = None, config: dict[str, str | None]):
        super().__init__(metadata_def_json_path=metadata_def_json_path, config=config)
        self.repeated_meta_info: RepeatedMetaType = defaultdict(list)

    def parse(self, data: ExtendMetaType) -> tuple[MetaType, RepeatedMetaType]:
        """Parse and extract constant and repeated metadata from the provided data.

        Args:
            data: The data containing metadata.

        Returns:
            tuple[MetaType, RepeatedMetaType]: A tuple containing two dictionaries - the first one for constant metadata
            and the second one for repeated metadata.

        """
        if not isinstance(data, dict):
            return self.const_meta_info, self.repeated_meta_info

        for k, v in data.items():
            if not isinstance(v, str):
                continue
            if k == "X-Ray":
                x_ray_value = v
                voltage, current = re.split(r'[/\s]+', x_ray_value, maxsplit=1)
                self.repeated_meta_info["txt.x-ray_tube_voltage"].append(voltage)
                self.repeated_meta_info["txt.x-ray_tube_current"].append(current)
            elif k == "入射スリット" and '/' in v:
                # MEMO: A desperate measure to prevent type:number in metadata-def.json
                #       from handling fractions (e.g. 1/3).
                incident_slit_value = v
                numerator, denominator = incident_slit_value.rstrip('deg').split("/")
                self.repeated_meta_info[k].append(int(numerator) / int(denominator))
            else:
                self.repeated_meta_info[k].append(v)

        return self.const_meta_info, self.repeated_meta_info
