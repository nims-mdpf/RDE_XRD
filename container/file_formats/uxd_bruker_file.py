from __future__ import annotations

from collections import defaultdict
from collections.abc import Generator
from enum import Enum
from pathlib import Path

import pandas as pd
from rdetoolkit.exceptions import StructuredError
from rdetoolkit.models.rde2types import MetaType, RepeatedMetaType
from rdetoolkit.rde2util import CharDecEncoding, Meta

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

    __mode__ = "uxd"

    TWO_TOKENS = 2

    class ToDataTypes(Enum):
        """Data types that allow only float and int."""

        FLOAT = "float"
        INT = "int"

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
        enc = CharDecEncoding.detect_text_file_encoding(srcpath)
        if enc in ["macroman", "mac_roman"]:
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

    def convert_dtype(self, dataframe: pd.DataFrame, *, totype: ToDataTypes = ToDataTypes.FLOAT) -> pd.DataFrame:
        """Convert data type.

        Args:
            dataframe (pd.DataFrame): Data frame before conversion.
            totype (ToDataTypes): Converted data type (float or int).

        Returns:
            pd.DataFrame: Data frame after conversion.

        """
        return dataframe.map(
            lambda x: self.__helper_convert_string_numeric(x, totype.value),
        )

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

    def split_data_meta(self, contents: list[str]) -> tuple[dict[str, pd.DataFrame], dict[str, ExtendMetaType]]:
        """Private method to split the contents into data and metadata blocks.

        Args:
            contents: The contents of the structured file as a string.

        Returns:
            tuple[dict[str, pd.DataFrame], dict[str, ExtendMetaType]]: A tuple containing two dictionaries -
            the first one for data blocks and the second one for metadata blocks.

        """
        meta_lines: dict = {}
        data_lines: list = []
        meta_blocks: dict[str, ExtendMetaType] = {}
        data_blocks: dict[str, pd.DataFrame] = {}
        is_header = True
        data_lines_label: list = []

        for line_org in contents:
            line = line_org.strip()
            if line.startswith(";"):
                meta_lines, data_lines_label = self._split_line_with_semicolon(
                    is_header, line, meta_lines, data_lines_label,
                )
            else:
                is_header, meta_lines, data_lines = self._split_line_normal(is_header, line, meta_lines, data_lines)

        if meta_lines:
            meta_blocks["series_meta1"] = meta_lines
        if data_lines and meta_lines:
            column = self._make_header(data_lines_label)
            data_blocks["series_value1"] = pd.DataFrame(data_lines, columns=column)

        return data_blocks, meta_blocks

    def _split_line_with_semicolon(
        self,
        is_header: bool,
        line: str,
        meta_lines: dict,
        data_lines_label: list,
    ) -> tuple[dict, list]:
        """Separate lines beginning with a semicolon into meta and label.

        Args:
            is_header (bool): Header or not (true(header)/false(data)).
            line (str): Contents.
            meta_lines (dict): Metadata.
            data_lines_label (list): Data label.

        Returns:
            dict: Metadata (after addition).
            list: Label (after addition).

        """
        if is_header:
            # candidate metadata
            # MEMO: Key-value separation will be done in meta_handler.py.
            meta_lines[line] = ""
        else:
            # candidate data label
            data_lines_label.append(line)

        return meta_lines, data_lines_label

    def _split_line_normal(
        self,
        is_header: bool,
        line: str,
        meta_lines: dict,
        data_lines: list,
    ) -> tuple[bool, dict, list]:
        """Separate rows into meta and data.

        Args:
            is_header (bool): Header or not (true(header)/false(data)).
            line (str): Contents.
            meta_lines (dict): Metadata.
            data_lines (list): Data.

        Returns:
            bool: Header or not (true(header)/false(data)).
            dict: Metadata (after addition).
            list: Data (after addition).

        """
        if is_header:
            tokens = [s.strip() for s in line.split("=", maxsplit=1)]
            if len(tokens) != self.TWO_TOKENS:
                return is_header, meta_lines, data_lines
            # header section
            meta_lines[tokens[0]] = tokens[1]
            if tokens[0] == "_2THETACOUNTS":
                is_header = False
        else:
            tokens = [s.strip() for s in line.split("\t")]
            # data section
            data_lines.append(tokens)

        return is_header, meta_lines, data_lines

    def _make_header(self, data_lines_label: list) -> list[str]:
        """Make a header using provided header information.

        Args:
            data_lines_label (list): The header information dictionary.

        Returns:
            list[str]: The constructed header string.

        """
        tokens = data_lines_label[0][1:].strip().split("\t") if len(data_lines_label) == 1 else ["Angle"]

        x_label = self.config['xrd']['meas_scan_axis_x'] if self.config['xrd']['meas_scan_axis_x'] else tokens[0]
        x_unit = "(" + self.config['xrd']['meas_scan_unit_x'] + ")" if self.config['xrd']['meas_scan_unit_x'] else ""
        y_label = self.config['xrd']['meas_scan_axis_y'] if self.config['xrd']['meas_scan_axis_y'] else "Intensity"
        y_unit = "(" + self.config['xrd']['meas_scan_unit_y'] + ")" if self.config['xrd']['meas_scan_unit_y'] else ""

        return [f"{x_label} {x_unit}", f"{y_label} {y_unit}"]

    def __helper_convert_string_numeric(self, x: str, dtype: str) -> float | int:
        """Convert string numeric.

        Args:
            x (str): Data before conversion.
            dtype (str): Converted data type.

        Returns:
            float | int: Converted data.

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


class MetaParser(BaseMetaParser):
    """Parses metadata and saves it to a specified path.

    This class is designed to parse metadata from a dictionary and save it to a specified path using
    a provided Meta object. It can handle both constant and repeated metadata.

    """

    __mode__ = "uxd"

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
            error_msg = "No data available."
            raise ValueError(error_msg)
        if not self.metadata_def_json_path:
            error_msg = "Metadata definition file is missing."
            raise ValueError(error_msg)

        meta_key_from_comment = self._get_meta_key_of_comments(self.metadata_def_json_path)

        for k, v in data.items():
            if not isinstance(v, str):
                continue
            # Getting Meta from Comment Lines
            if not k.startswith(";"):
                key, value = k, v
            else:
                key, value = self._separate_key_value_from_comment(k, meta_key_from_comment)
            self.repeated_meta_info[key].append(value)

        return self.const_meta_info, self.repeated_meta_info

    def _get_meta_key_of_comments(self, metadata_def_json_path: Path) -> dict:
        """Collect the prefix words of comment sentences that should be registered as meta.

        Since it seems that stolen words can be written with or without spaces and with or without case blurring,
        the dictionary should be keyed with no blurring.

        Args:
            metadata_def_json_path (Path): Metadata define file path.

        Returns:
            dict: Metadata define Object.

        """
        metadata_def_obj = Meta(metadef_filepath=metadata_def_json_path)

        meta_key_from_comment = {}
        for item in metadata_def_obj.metaDef.values():
            key_org = item.get("originalName")
            if not key_org:
                continue
            if not key_org.startswith(";"):
                continue
            key_prefix = key_org.replace(" ", "").lower()
            meta_key_from_comment[key_prefix] = key_org

        return meta_key_from_comment

    def _separate_key_value_from_comment(self, line: str, meta_key_from_comment: dict) -> tuple[str, str]:
        """Separate comment statements into meta's key and value.

        Args:
            line (str): Comment statements.
            meta_key_from_comment (dict): Metadata define Object.

        Returns:
            tuple[str, str]: Meta's key and value.

        """
        key: str = ""
        value: str = ""
        line_normalization = line.replace(" ", "").lower()
        for key_prefix, key_org in meta_key_from_comment.items():
            if not line_normalization.startswith(key_prefix):
                continue
            meta_value = line.strip()
            for _ in range(len(key_prefix)):
                meta_value = meta_value[1:].strip()
            key = key_org
            value = meta_value
            break

        return key, value

