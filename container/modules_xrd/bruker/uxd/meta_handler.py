from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from rdetoolkit.models.rde2types import MetaType, RepeatedMetaType
from rdetoolkit.rde2util import Meta

from modules_xrd.interfaces import ExtendMetaType
from modules_xrd.meta_handler import MetaParser as XrdMetaParser


class MetaParser(XrdMetaParser):
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
