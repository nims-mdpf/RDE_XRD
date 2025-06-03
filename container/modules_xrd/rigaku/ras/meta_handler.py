from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from rdetoolkit.models.rde2types import MetaType, RepeatedMetaType

from modules_xrd.interfaces import ExtendMetaType
from modules_xrd.meta_handler import MetaParser as XrdMetaParser


class MetaParser(XrdMetaParser):
    """Parses metadata and saves it to a specified path.

    This class is designed to parse metadata from a dictionary and save it to a specified path using
    a provided Meta object. It can handle both constant and repeated metadata.

    Attributes:
        const_meta_info (MetaType | None): Dictionary to store constant metadata.
        repeated_meta_info (RepeatedMetaType | None): Dictionary to store repeated metadata.

    """

    __mode__ = "ras"

    def __init__(self, *, metadata_def_json_path: Path | None = None, config: dict[str, str | None]):
        super().__init__(metadata_def_json_path=metadata_def_json_path, config=config)
        self.repeated_meta_info: RepeatedMetaType = defaultdict(list)

    def parse(self, data: ExtendMetaType) -> tuple[MetaType, RepeatedMetaType]:
        """Parse and extract constant and repeated metadata from the provided data.

        Args:
            data (ExtendMetaType): The data containing metadata.

        Returns:
            tuple[MetaType, RepeatedMetaType]: A tuple containing two dictionaries - the first one for constant metadata
            and the second one for repeated metadata.

        """
        if isinstance(data, list):
            self.__convert_multi_region_headeritems(data)
        return self.const_meta_info, self.repeated_meta_info

    def __transform_meta(self, meta_string_line: str) -> tuple[str, str]:
        """Transform a meta string into a key-value pair.

        This function takes a meta string in the format '*<key> "<value>"',
        removes the '*', splits the string at ', ', and removes the double
        quotations from the value.

        Args:
            meta_string_line (str): A meta string in the format '*<key> "<value>"'.

        Returns:
            tuple: A tuple containing the key and value as separate strings.

        Examples:
            >>> transform_meta('*sample_meta "1000"')
            ('sample_meta', '1000')

        """
        del_prefix_string = meta_string_line.replace("*", "")
        match = re.match(r'(\S+)\s+"([^"]*)"', del_prefix_string)
        if match:
            key, value = list(match.groups())
            key, value = self.__validate_meta_items(key, value)
            return key, value
        return "", ""

    def __convert_multi_region_headeritems(self, headers: list[Any]) -> dict:
        """Process to merge multiple header information.

        If multiple regions exist and you want to output them as "variable" in metadata.json,
        because it is necessary to convert them to the format of dict[str, list[str]].

        Args:
            headers (list[Any]): list object with one or more header information

        Returns:
            dict: Merged Header Information

        Examples:
            d1 = {"*FILE_OPERATOR" : "administrator", "*FILE_SMAPLE" : "M001"}
            d2 = {"*FILE_OPERATOR" : "admin", "*FILE_SAMPLE" : "M002", "ID": "10"}
            headers = [d1, d2]
            rtn = __multi_region_header(dictHdrs)
            >>> {"*FILE_OPERATOR" : ["administrator", "admin"], "*FILE_SAMPLE" : ["M001", "M002"], "ID": ["10"]}

        """
        for header in headers:
            key, value = self.__transform_meta(header)
            if key:
                self.repeated_meta_info[key].append(value)
        return dict(self.repeated_meta_info)

    def __validate_meta_items(self, meta_key: str, meta_value: str) -> tuple[str, str]:
        """Validate meta items.

        Args:
            meta_key (str): Key.
            meta_value (str): Value.

        Returns:
            tuple: A tuple containing the key and value as separate strings.

        """
        variadation_target_meta_keys = ["MEAS_SCAN_AXIS_X", "MEAS_COND_XG_WAVE_TYPE"]
        if meta_key not in variadation_target_meta_keys:
            return meta_key, meta_value

        _local_meta_key = meta_key
        _local_meta_value = meta_value
        if _local_meta_key == "MEAS_COND_XG_WAVE_TYPE":
            if "a" in _local_meta_value:
                _local_meta_value = _local_meta_value.replace("a", "_alpha")
            if "b" in _local_meta_value:
                _local_meta_value = _local_meta_value.replace("b", "_beta")
        elif _local_meta_key == "MEAS_SCAN_AXIS_X":
            if _local_meta_value in ["TwoThetaTheta", "2θ/θ"]:
                _local_meta_value = "2Theta-Theta"
        return _local_meta_key, _local_meta_value
