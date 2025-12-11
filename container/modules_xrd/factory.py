from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from rdetoolkit.exceptions import StructuredError
from rdetoolkit.models.rde2types import RdeOutputResourcePath
from rdetoolkit.rde2util import read_from_json_file

from modules_xrd.bruker.uxd.inputfile_handler import FileReader as UxdFileReader
from modules_xrd.bruker.uxd.meta_handler import MetaParser as UxdMetaParser
from modules_xrd.graph_handler import GraphPlotter
from modules_xrd.inputfile_handler import FileReader as XrdFileReader
from modules_xrd.invoice_handler import InvoiceWriter
from modules_xrd.meta_handler import MetaParser as XrdMetaParser
from modules_xrd.models import ScaleType
from modules_xrd.rigaku.ras.inputfile_handler import FileReader as RasFileReader
from modules_xrd.rigaku.ras.meta_handler import MetaParser as RasMetaParser
from modules_xrd.rigaku.rasx.inputfile_handler import FileReader as RasxFileReader
from modules_xrd.rigaku.rasx.meta_handler import MetaParser as RasxMetaParser
from modules_xrd.rigaku.txt.inputfile_handler import FileReader as TxtFileReader
from modules_xrd.rigaku.txt.meta_handler import MetaParser as TxtMetaParser
from modules_xrd.structured_handler import StructuredDataProcessor

RIGAKU_SUFFIX_CLASS_MAPPING = {
    "rigaku": {
        ".ras": (RasFileReader, RasMetaParser),
        ".rasx": (RasxFileReader, RasxMetaParser),
        ".txt": (TxtFileReader, TxtMetaParser),
    },
}

BRUKER_SUFFIX_CLASS_MAPPING = {
    "bruker": {
        ".uxd": (UxdFileReader, UxdMetaParser),
    },
}


class XrdFactory:
    """Obtain a variety of data for use in the XRD's Structured processing."""

    def __init__(
        self,
        invoice_writer: InvoiceWriter,
        file_reader: XrdFileReader,
        meta_parser: XrdMetaParser,
        graph_plotter: GraphPlotter,
        structured_processor: StructuredDataProcessor,
    ):
        self.invoice_writer = invoice_writer
        self.file_reader = file_reader
        self.meta_parser = meta_parser
        self.graph_plotter = graph_plotter
        self.structured_processor = structured_processor

    @staticmethod
    def get_config(resource_paths: RdeOutputResourcePath, path_tasksupport: Path) -> tuple[Any, Path]:
        """Obtain a variety of data.

        Obtain configuration data.

        Args:
            resource_paths (RdeOutputResourcePath): output file.
            path_tasksupport (Path): tasksupport path.

        Returns:
            config (Any): config data.
            processing_file (Path): processing file.

        """
        if not len(resource_paths.rawfiles):
            err_msg = "No measurement file found."
            raise StructuredError(err_msg)

        # Get priorities
        ext_priority = {
            ".rasx": 1,
            ".ras": 2,
            ".txt": 3,
        }
        sorted_files: list[Path] = sorted(
            resource_paths.rawfiles,
            key=lambda f: ext_priority.get(os.path.splitext(f)[1].lower(), float('inf')),
        )
        processing_file = sorted_files[0]

        suffix = processing_file.suffix.lower()
        rdeconfig_file = path_tasksupport.joinpath("rdeconfig.yaml")

        # Get the graph scale of the representative image from rdeconfig.yaml.
        # TODO: Processes that should be moved to rdetoolkit in the future.
        if not rdeconfig_file.exists():
            err_msg = f"File not found: {rdeconfig_file}"
            raise StructuredError(err_msg)
        try:
            with open(rdeconfig_file) as file:
                config = yaml.safe_load(file)
        except Exception:
            err_msg = f"Invalid configuration file: {rdeconfig_file}"
            raise StructuredError(err_msg) from None

        if suffix == ".txt":
            # Determine the file delimiter.
            config['xrd']['delimiter_type'] = XrdFileReader.determine_delimiter(processing_file)

            # Get bounds for differential_evolution.
            invoice_obj = read_from_json_file(resource_paths.invoice_org)
            invoice_scanning_mode = invoice_obj.get("custom", "").get("scanning_mode_if_not_exist")
            config["xrd"]["scanning_mode_if_not_exist"] = \
                invoice_scanning_mode if invoice_scanning_mode is not None else "2Theta-Theta"

        return config, processing_file

    @staticmethod
    def get_objects(rawfile: Path, path_tasksupport: Path, config: dict) -> tuple[Path, XrdFactory]:
        """Obtain a variety of data.

        Retrieve the class to be executed.
        Obtain the metadata definition file to be used.

        Args:
            rawfile (Path): measurement file.
            path_tasksupport (Path): tasksupport path.
            config (dict): config data.

        Returns:
            metadata_def (Path): Metadata file path.
            module (Any): classes
                InvoiceWriter (class): Overwrite invoice file.
                FilaReader (class): Reads and processes structured files into data and metadata blocks.
                MetaParser (class): Parses metadata and saves it to a specified path.
                GraphPlotter (class): Utility for plotting data using various types of plots.
                StructuredDataProcessor (class): Template class for parsing structured data.

        """
        suffix = rawfile.suffix.lower()

        # (Only on manufacturer: rigaku, bruker) Input file extension check
        valid_extensions = {
            "rigaku": {".ras", ".rasx", ".txt"},
            "bruker": {".uxd"},
        }
        manufacturer = config['xrd']['manufacturer']
        if suffix not in valid_extensions.get(manufacturer, set()):
            err_msg = f"Format Error: Input data extension is incorrect: {suffix}"
            raise StructuredError(err_msg)

        # Obtain classes according to manufacturer and file extension.
        class_filereader, class_metaparser = get_classes(manufacturer, suffix)

        # Gets the scale type of the graph.
        main_image_scaletype, other_image_scaletype = get_scale_types(config['xrd']['main_image_setting'])

        # Determine the file delimiter.
        delimiter_type: str = ""
        if suffix == ".txt":
            delimiter_type = "_tab" if config['xrd']['delimiter_type'] == "\t" else "_space"

        # Change the metadata definition file according to the file format.
        metadata_def = path_tasksupport.joinpath(f'metadata-def_{manufacturer}_{suffix[1:]}{delimiter_type}.json')

        module = XrdFactory(
            InvoiceWriter(config),
            class_filereader(config),
            class_metaparser(metadata_def_json_path=metadata_def, config=config),
            GraphPlotter(main_image_scaletype, other_image_scaletype),
            StructuredDataProcessor(),
        )

        return metadata_def, module


def get_classes(manufacturer: str, suffix: str) -> tuple[type[XrdFileReader], type[XrdMetaParser]]:
    """Get the appropriate FileReader and MetaParser classes based on the manufacturer and file suffix."""
    try:
        match manufacturer:
            case "rigaku":
                return RIGAKU_SUFFIX_CLASS_MAPPING[manufacturer][suffix]
            case "bruker":
                return BRUKER_SUFFIX_CLASS_MAPPING[manufacturer][suffix]
            case _:
                raise KeyError
    except KeyError:
        err_msg = f"Unsupported combination of manufacturer '{manufacturer}' and file extension '{suffix}'"
        raise StructuredError(err_msg) from None


def get_scale_types(main_image_setting: str) -> tuple[ScaleType, ScaleType]:
    """Get the scale types for the main and other images based on the configuration.

    Args:
        main_image_setting (str): The setting for the main image scale type.

    Returns:
        Tuple[ScaleType, ScaleType]: The scale types for the main and other images.

    """
    if main_image_setting == "log":
        return ScaleType.log, ScaleType.linear
    return ScaleType.linear, ScaleType.log
