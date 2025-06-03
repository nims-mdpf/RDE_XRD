from __future__ import annotations

from pathlib import Path

from rdetoolkit import rde2util
from rdetoolkit.models.rde2types import MetaType, RepeatedMetaType

from modules_xrd.interfaces import ExtendMetaType, IMetaParser


class MetaParser(IMetaParser[ExtendMetaType]):
    """Parses metadata and saves it to a specified path.

    This class is designed to parse metadata from a dictionary and save it to a specified path using
    a provided Meta object. It can handle both constant and repeated metadata.

    Attributes:
        const_meta_info (MetaType | None): Dictionary to store constant metadata.
        repeated_meta_info (RepeatedMetaType | None): Dictionary to store repeated metadata.

    """

    def __init__(self, *, metadata_def_json_path: Path | None = None, config: dict[str, str | None]):
        self.const_meta_info: MetaType = {}
        self.repeated_meta_info: RepeatedMetaType = {}
        self.metadata_def_json_path = metadata_def_json_path
        self.config: dict = config

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
