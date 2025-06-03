from __future__ import annotations

import os
import zipfile
from collections.abc import Generator
from pathlib import Path
from typing import cast

import pandas as pd
from rdetoolkit.exceptions import StructuredError

from modules_xrd.inputfile_handler import FileReader as XrdFileReader
from modules_xrd.interfaces import ExtendMetaType
from modules_xrd.models import Data0, Data1, MeasurementConditions, Root


class FileReader(XrdFileReader):
    """A class to read rasx files and return a list of measurement data and settings.

    This class reads the information stored in rasx files (information described in Root.xml),
    retrieving both the measurement data and the configured settings file used during the measurement.

    Args:
        Attributes:
        data (dict[str, pd.DataFrame]): Stores the measurement data contained in Profile*.xml files,
                                        converted into pandas.DataFrame format.
        meta (dict[str, list[str]]): Stores the settings file used during measurement,
                                     contained in MeasurementConditions*.xml files, as an ExtendMetaType.

    """

    __mode__ = "rasx"

    def __init__(self, config: dict):
        super().__init__(config)
        self.meta: dict[str, MeasurementConditions] = {}

    def read(self, srcpath: Path) -> Generator[tuple[pd.DataFrame, ExtendMetaType], None, None]:
        """Read the structured file and returns separated data and metadata.

        Args:
            srcpath (Path): The path of the structured file to read.

        Returns:
            tuple[tuple[pd.DataFrame, ExtendMetaType], ...]: A tuple containing two dictionaries -
            the first one for data blocks and the second one for metadata blocks.

        Raises:
            StructuredError: If the file is formatted incorrectly.

        """
        self.meta = self.get_metadata(srcpath)
        self.data = self.get_data(srcpath)
        if not self.data or not self.meta:
            err_msg = f"Cannot read the file because it is formatted incorrectly: {srcpath}"
            raise StructuredError(err_msg)

        self.region_num = len(self.data.keys())
        for data_key, meta_key in zip(self.data, self.meta):
            header = self.make_header(self.meta[meta_key])
            data = self.reformat_dataframe(self.data[data_key], header=header)
            yield data, self.meta[meta_key]

    def get_region_number(self, *, input_path: Path | None = None) -> int:
        """Get the number of regions.

        Args:
            input_path (Path | None): Measurement file path.

        Returns:
            int: Number of regions.

        """
        if input_path is None:
            return self.region_num
        self.region_num = len([f for f in self.get_files_from_rasx(input_path) if "Profile" in f])
        return self.region_num

    def get_metadata(self, rasx_path: Path) -> dict[str, MeasurementConditions]:
        """Get metadata from compressed files.

        Args:
            rasx_path (Path): rasx raw file

        Yields:
            Tuple[str, MeasurementConditions]: the target file name and metadata within the compressed file

        Note:
            If you change the data class MeasurementConditions to a dictionary type:
            >>> rasx = SimpleRasxHangler('test.rasx')
            >>> for filename, meta in rasx.get_metadata():
            >>>     # convert dataclass to dict
            >>>     print(meta.dict())

        """
        metadata_files = [f for f in self.get_files_from_rasx(rasx_path) if "MesurementConditions" in f]
        self.metadata_map: dict[str, MeasurementConditions] = {}
        for filename in metadata_files:
            xml_data = self.open_file(filename, rasx_path)
            convert_xml_to_meta = self.__extract_metadata_from_xml(xml_data)
            convert_xml_to_meta = cast(MeasurementConditions, convert_xml_to_meta)
            if convert_xml_to_meta is not None:
                self.metadata_map[filename] = convert_xml_to_meta
            else:
                err_msg = "Could not read metadata [xml]"
                raise StructuredError(err_msg)
        return self.metadata_map

    def get_data(self, rasx_path: Path) -> dict[str, pd.DataFrame]:
        """Get mesurementdata from compressed files.

        Args:
            rasx_path (Path): rasx raw file

        Return:
            Tuple[str, pd.DataFrame]: the target file name and mesurementdata within the compressed file

        """
        files = [f for f in self.get_files_from_rasx(rasx_path) if "Profile" in f]
        self.data_maps: dict[str, pd.DataFrame] = {}
        for file in files:
            data = self.open_compressedfile_dataframe(file, rasx_path)
            self.data_maps[file] = data
        return self.data_maps

    def make_header(self, header_info: MeasurementConditions) -> list[str]:
        """Make a header using provided header information.

        Args:
            header_info (MeasurementConditions): The header information dictionary.

        Returns:
            list[str]: The constructed header string.

        """
        x_label = self.config['xrd']['meas_scan_axis_x']
        if not x_label:
            x_label = header_info.scaninformation.AxisName
        x_unit = self.config['xrd']['meas_scan_unit_x']
        if not x_unit:
            x_unit = header_info.scaninformation.PositionUnit
        y_label = self.config['xrd']['meas_scan_axis_y']
        if not y_label:
            y_label = "Intensity"
        y_unit = self.config['xrd']['meas_scan_unit_y']
        if not y_unit:
            y_unit = header_info.scaninformation.IntensityUnit
        return [f"{x_label} ({x_unit})", f"{y_label} ({y_unit})"]

    def reformat_dataframe(
        self,
        data: pd.DataFrame,
        *,
        header: list[str] | None = None,
    ) -> pd.DataFrame:
        """Reformat data frames. Multiply the second and third columns of measured data and add a header.

        Args:
            data (pd.DataFrame): Data frame to be reformatted.
            header (list[str] | None): header of the CSV file.

        Returns:
            pd.DataFrame: Reformatted data frame.

        """
        data[3] = data.iloc[:, 1] * data.iloc[:, 2]
        reformat_dataframe = pd.concat([data.iloc[:, 0].round(4), data.iloc[:, 3]], axis=1)
        if header:
            reformat_dataframe.columns = header
        else:
            _meta = list(self.metadata_map.values())[0]
            header = [
                _meta.scaninformation.AxisName,
                f"Intensity[{_meta.scaninformation.IntensityUnit}]",
            ]
            reformat_dataframe.columns = header
        return reformat_dataframe

    def get_files_from_rasx(self, rasx_path: Path) -> list[str]:
        """Get all file names in a .rasx file.

        Args:
            rasx_path (Path): rasx raw file

        Returns:
            list[str]: list of file names contained in rasx

        Raise:
            MyError: If an input rasx has an invalid configuration
            (such as not containing the correct file), an exception will be raised.

        Note:
            The files contained in the rasx are those stored in the ContentHashList of root.xml.
            Since rasx only contains two elements, it filters by data0 and data1.

        """
        with zipfile.ZipFile(str(rasx_path), "r") as rasx:
            root_xml_files = [name for name in rasx.namelist() if name.startswith("root.")]
            contents = self.open_file(root_xml_files[0], rasx_path)
        instance = Root.from_xml(contents)
        return self.__filter_list_from_rootxml_content(instance)

    def open_file(self, file_name: str, rasx_path: Path) -> bytes | str:
        """Open a specific file stored in a .rasx file.

        Args:
            file_name (str): name of the target file
            rasx_path (Path): rasx raw file

        Returns:
            str | bytes : contents of the file specified by the argument

        """
        _, ext = os.path.splitext(file_name)
        with zipfile.ZipFile(str(rasx_path), "r") as rasx, rasx.open(file_name) as frasx:
            contents = frasx.read()

        if ext in [".rasx", ".zip"]:
            return contents
        return contents.decode("utf-8")

    def open_compressedfile_dataframe(self, file_name: str, rasx_path: Path) -> pd.DataFrame:
        """Get a text file from a compressed file (rasx) and create a data frame.

        Args:
            file_name (str): text file to be converted into a data frame
            rasx_path (Path): rasx raw file

        Returns:
            pd.DataFrame: data frame read from file

        """
        with zipfile.ZipFile(str(rasx_path), "r") as cmpf, cmpf.open(file_name) as f:
            return pd.read_csv(f, sep="\t", header=None)

    def __filter_list_from_rootxml_content(self, root_xml_obj: Root | None) -> list[str]:
        """Filter list from rootxml content.

        Args:
            root_xml_obj (Root | None): Root xml object.

        Returns:
            list[str]: Filtered list.

        Raises:
            StructuredError: If the file is formatted incorrectly.

        """
        if root_xml_obj is None or (root_xml_obj.data0 is None and root_xml_obj.data1 is None):
            err_msg = "A file with an invalid configuration has been inputted."
            raise StructuredError(err_msg)

        filtered_list = []
        filtered_list.extend(self._extract_paths_from_data(root_xml_obj.data0, "Data0"))
        filtered_list.extend(self._extract_paths_from_data(root_xml_obj.data1, "Data1"))

        if not filtered_list:
            err_msg = "A file with an invalid configuration has been inputted."
            raise StructuredError(err_msg)

        return filtered_list

    def _extract_paths_from_data(self, data_obj: Data0 | Data1 | None, data_prefix: str) -> list[str]:
        """Extract paths from a data object.

        Args:
            data_obj: The data object containing contenthashlist.
            data_prefix (str): The prefix to be added to the data paths.

        Returns:
            list[str]: A list of data paths.

        """
        if data_obj is None:
            return []

        paths = []
        for contentslist in data_obj.contenthashlist:
            dataname = contentslist.get("Name")
            if dataname:
                datapath = os.path.join(data_prefix, dataname)
                paths.append(datapath)

        return paths

    def __extract_metadata_from_xml(self, xml_data: bytes | str) -> MeasurementConditions | None:
        """Extract metadata from XML data stored in compressed files (.rasx).

        Args:
            xml_data (bytes | str): textualized XML data

        Returns:
            MeasurementConditions: stores and returns metadata from XML into the data class MeasurementConditions.

        """
        return MeasurementConditions.from_xml(xml_data)
