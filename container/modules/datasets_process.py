from __future__ import annotations

from typing import Final

from rdetoolkit.errors import catch_exception_with_message
from rdetoolkit.models.rde2types import RdeInputDirPaths, RdeOutputResourcePath
from rdetoolkit.rde2util import Meta

from modules_xrd.factory import XrdFactory


@catch_exception_with_message()
def dataset(srcpaths: RdeInputDirPaths, resource_paths: RdeOutputResourcePath) -> None:
    """Execute structured processing in XRD.

    Execute structured text processing, metadata extraction, and visualization.
    It handles structured text processing, metadata extraction, and graphing.
    Other processing required for structuring may be implemented as needed.

    Args:
        srcpaths (RdeInputDirPaths): Paths to input resources for processing.
        resource_paths (RdeOutputResourcePath): Paths to output resources for saving results.

    Returns:
        None

    Note:
        The actual function names and processing details may vary depending on the project.

    """
    region_num: int = 1
    # Get config
    config, processing_file = XrdFactory.get_config(resource_paths, srcpaths.tasksupport)
    # Get the class to use
    metadata_def, module = XrdFactory.get_objects(processing_file, srcpaths.tasksupport, config)

    compressd_files: list[str] = []
    # Read Input File -> Save Meta -> Struct
    for data, meta in module.file_reader.read(processing_file):
        region_num = module.file_reader.get_region_number()

        # Get meta
        const_meta, repeat_meta = module.meta_parser.parse(meta)

        # Save csv
        module.structured_processor.save_csv(resource_paths, processing_file, data, region_num=region_num)
        # Execute save process for structured files, only when a .rasx file is input,
        # as there are other files(xml, txt) compressed.
        if processing_file.suffix == ".rasx":
            compressd_files = module.file_reader.get_files_from_rasx(processing_file)
            module.structured_processor.save_structured_contents(resource_paths, processing_file, compressd_files)

        # Plot
        module.graph_plotter.plot_main(data, resource_paths, processing_file, region_num)

        # Overwrite invoice
        # (custom/measurement_measured_date)
        module.invoice_writer.overwrite_invoice_measured_date(resource_paths, processing_file.suffix, const_meta, repeat_meta)

    # Save Meta
    # Add the graph scale meta
    # Read metadata about graph scale from rdeconfig.yaml and add it to the repeating metadata list.
    if config.get("main_image_setting"):
        config['main_image_setting'] = [config['main_image_setting'] for _ in range(region_num)]
        module.meta_parser.repeated_meta_info.update(config)
    module.meta_parser.save_meta(resource_paths.meta.joinpath("metadata.json"), Meta(metadata_def))

    # Plot
    # Integrated graph image if needed
    multi_resion_num: Final[int] = 2
    if region_num == multi_resion_num:
        module.graph_plotter.multiplot_main(resource_paths, processing_file)
