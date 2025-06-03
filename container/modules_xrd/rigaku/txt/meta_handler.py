from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from rdetoolkit.models.rde2types import MetaType, RepeatedMetaType

from modules_xrd.interfaces import ExtendMetaType
from modules_xrd.meta_handler import MetaParser as XrdMetaParser


class MetaParser(XrdMetaParser):
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
                voltage, current = x_ray_value.split("/")
                self.repeated_meta_info["txt.x-ray_tube_voltage"].append(voltage)
                self.repeated_meta_info["txt.x-ray_tube_current"].append(current)
            elif k == "入射スリット" and '/' in v:
                # MEMO: A desperate measure to prevent type:number in metadata-def.json from handling fractions (e.g. 1/3).
                incident_slit_value = v
                numerator, denominator = incident_slit_value.rstrip('deg').split("/")
                self.repeated_meta_info[k].append(int(numerator) / int(denominator))
            else:
                self.repeated_meta_info[k].append(v)

        return self.const_meta_info, self.repeated_meta_info
