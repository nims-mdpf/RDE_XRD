from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from rdetoolkit.models.rde2types import MetaType, RepeatedMetaType
from rdetoolkit.rde2util import CharDecEncoding

from modules_xrd.interfaces import ExtendMetaType
from modules_xrd.meta_handler import MetaParser as XrdMetaParser
from modules_xrd.models import MeasurementConditions


class MetaParser(XrdMetaParser):
    """Template class for parsing and saving metadata.

    This class serves as a template for the development team to parse and save metadata. It implements
    the IMetaParser interface. Developers can use this template class as a foundation for adding
    specific parsing and saving logic for metadata based on the project's requirements.

    Args:
        data (MetaType): The metadata to be parsed and saved.

    Returns:
        tuple[MetaType, MetaType]: A tuple containing the parsed constant and repeated metadata.

    Example:
        meta_parser = MetaParser()
        parsed_const_meta, parsed_repeated_meta = meta_parser.parse(data)
        meta_obj = rde2util.Meta(metaDefFilePath='meta_definition.json')
        saved_info = meta_parser.save_meta('saved_meta.json', meta_obj,
                                        const_meta_info=parsed_const_meta,
                                        repeated_meta_info=parsed_repeated_meta)

    """

    __mode__ = "rasx"

    def __init__(self, *, metadata_def_json_path: Path | None = None, config: dict[str, str | None]):
        super().__init__(metadata_def_json_path=metadata_def_json_path, config=config)
        self.repeated_meta_info: RepeatedMetaType = defaultdict(list)
        self.meta_def_obj: dict[str, Any] = {}
        if self.metadata_def_json_path:
            self.load_invoice_file(self.metadata_def_json_path)

    def parse(self, data: ExtendMetaType) -> tuple[MetaType, RepeatedMetaType]:
        """Parse and extract constant and repeated metadata from the provided data.

        Args:
            data (ExtendMetaType): The data containing metadata.

        Returns:
            tuple[MetaType, RepeatedMetaType]: A tuple containing two dictionaries - the first one for constant metadata
            and the second one for repeated metadata.

        """
        if isinstance(data, MeasurementConditions):
            self.__recuresive_search_dict(data.model_dump())
        return self.const_meta_info, self.repeated_meta_info

    def load_invoice_file(self, invoice_def_json_path: Path) -> None:
        """Load invoice file.

        Args:
            invoice_def_json_path (Path): Invoice define json path.

        """
        enc = CharDecEncoding.detect_text_file_encoding(invoice_def_json_path)
        with open(invoice_def_json_path, encoding=enc) as f:
            self.meta_def_obj = json.load(f)

    def __recuresive_search_dict(self, nested_dict: dict) -> None:
        """Recuresive search dictionary.

        Args:
            nested_dict (dict): Dictionaries to search.

        """
        for k, v in nested_dict.items():
            if isinstance(v, dict):
                self.__recuresive_search_dict(v)
                continue

            _match_key, _match_variable = self.__search_metadef_item(k)
            if _match_key is None:
                continue

            if _match_variable is not None:
                self.repeated_meta_info[_match_key].append(v)
            else:
                self.const_meta_info[k] = v

    def __search_metadef_item(self, key: str) -> tuple[str | None, int | None]:
        """Search for item in metadata definitions.

        Args:
            key (str): Metadata key.

        Returns:
            tuple[str | None, int | None]: Metadata Key and Value.

        """
        match_key: str | None = None
        match_variable: int | None = None
        for k, v in self.meta_def_obj.items():
            if v.get("originalName") == key:
                match_key = k
            if v.get("unit") == "$" + key:
                # The reason for retrieving the unit using get is that in rde2util::Meta::writefile,
                # if there's a Key that starts with $, it's designed to dynamically rewrite the unit in metadata.json.
                # Therefore, '$'+key is stored as the key that was matched.
                match_key = key
            if match_key is not None and v.get("variable") == 1:
                match_variable = 1
                break
        return match_key, match_variable
