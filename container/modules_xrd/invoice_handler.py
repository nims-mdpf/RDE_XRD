from __future__ import annotations

import re
import zoneinfo
from datetime import datetime
from typing import Any

from rdetoolkit.exceptions import StructuredError
from rdetoolkit.invoicefile import InvoiceFile, overwrite_invoicefile_for_dpfterm
from rdetoolkit.models.rde2types import MetaType, RdeOutputResourcePath, RepeatedMetaType
from rdetoolkit.rde2util import CharDecEncoding, read_from_json_file, write_to_json_file


class InvoiceWriter:
    """Invoice overwriter.

    Overwrite invoice.json files depending on conditions.

    """

    END_OF_21_CENTURY = 2100
    END_OF_YEAR = 12
    END_OF_MONTH = 31

    def __init__(self, config: dict):
        self.config: dict = config

    def overwrite_invoice_measured_date(
        self,
        resource_paths: RdeOutputResourcePath,
        suffix: str,
        const_meta: MetaType,
        repeat_meta: RepeatedMetaType,
    ) -> None:
        """Overwrite invoice if needed.

        The date is to be obtained from the output device and output to invoice.
        The measurement date and time are written automatically to the invoice.json file
        # based on the file meta data output from the device, so I added a process to write it to invoice.json.

        Args:
            resource_paths (RdeOutputResourcePath): Paths to output resources for saving results.
            suffix (str): Input file extension.
            const_meta (MetaType): Metadata defined as constant.
            repeat_meta (RepeatedMetaType): Metadata defined as variable.

        """
        invoice_obj = read_from_json_file(resource_paths.invoice_org)
        update_invoice_term_info = self._get_update_mesurement_date_dpf_metadata(
            suffix,
            invoice_obj,
            const_meta,
            repeat_meta,
        )
        if update_invoice_term_info:
            overwrite_invoicefile_for_dpfterm(
                invoice_obj,
                resource_paths.invoice_org,
                resource_paths.invoice_schema_json,
                update_invoice_term_info,
            )
            invoice_org_obj = InvoiceFile(resource_paths.invoice_org)
            invoice_org_obj.overwrite(resource_paths.invoice.joinpath("invoice.json"))

    def overwrite_invoice_sample_name(
        self,
        resource_paths: RdeOutputResourcePath,
    ) -> None:
        """Overwrite sample name if needed.

        About filename-mapping-rule
        If the item filename_mapping_rule in the rdeconfig.yaml file is true,
        change the dataset name and sample information based on the file name.

        Args:
            resource_paths (RdeOutputResourcePath): Paths to output resources for saving results.

        """
        if not self.config['xrd']['filename_mapping_rule']:
            return

        suffix = resource_paths.rawfiles[0].suffix
        if not (self.config['xrd']['manufacturer'] == "rigaku" and suffix in {".ras", ".rasx"}):
            return

        invoice_org_obj = InvoiceFile(resource_paths.invoice_org)
        invoice_org_obj.invoice_obj = read_from_json_file(resource_paths.invoice_org)

        file_name_sections = resource_paths.rawfiles[0].stem.split("_")
        if len(file_name_sections) > 1:
            invoice_org_obj.invoice_obj["sample"]["sampleId"] = None
            invoice_org_obj.invoice_obj["sample"]["names"][0] = file_name_sections[1]
        else:
            err_msg = "Invalid Filename Error: A file without delimiters has been inputted."
            raise StructuredError(err_msg)

        enc = CharDecEncoding.detect_text_file_encoding(resource_paths.invoice_org)
        write_to_json_file(resource_paths.invoice_org, invoice_org_obj.invoice_obj, enc=enc)
        invoice_org_obj.overwrite(resource_paths.invoice.joinpath("invoice.json"))

    def _get_update_mesurement_date_dpf_metadata(
        self,
        suffix: str,
        invoice_obj: dict[str, Any],
        const_meta: MetaType,
        repeat_meta: RepeatedMetaType,
    ) -> dict[str, str]:
        """Update metadata information about the measurement date and time.

        This function works exclusively with rigaku.
        Due to the different vocabulary used in rigaku to indicate the measurement date and time,
        the process is specifically defined for these formats.

        Args:
            suffix (str): file extension
            invoice_obj (dict[str, Any]): Object of ivnoice.json or invoice_org.json
            const_meta (dict[str, str]): Metadata defined as constant
            repeat_meta (dict[str, list[str]]): Metadata defined as variable

        Returns:
            dict[str, str]: Metadata information updated with the measurement date and time

        """
        update_invoice_term_info: dict[str, str] = {}
        if "measurement_measured_date" not in invoice_obj["custom"]:
            return update_invoice_term_info

        keywd: str = ""
        date_expressions: datetime | None = None
        match suffix.lower():
            case ".ras":
                keywd = "MEAS_SCAN_START_TIME"
            case ".rasx":
                keywd = "rasx.scan_starting_date_time"
            case ".txt":
                keywd = "StartTime"
            case ".uxd":
                keywd = ";contentof"
                date_expressions = self._extract_date(repeat_meta, keywd)

        mesurement_date_value = invoice_obj["custom"].get("measurement_measured_date")
        if const_meta.get(keywd) and not mesurement_date_value:
            update_invoice_term_info["measurement_measured_date"] = str(const_meta[keywd])
        elif repeat_meta.get(keywd) and not mesurement_date_value:
            if date_expressions is None:
                update_invoice_term_info["measurement_measured_date"] = str(repeat_meta[keywd][0])
            else:
                update_invoice_term_info["measurement_measured_date"] = str(date_expressions)
        return update_invoice_term_info

    def _extract_date(self, repeat_meta: RepeatedMetaType, keywd: str) -> datetime | None:
        """Find out if the date can be extracted.

        Args:
            repeat_meta (RepeatedMetaType): Repeated meta.
            keywd (str): item of measurement date and time.

        Returns:
            datetime | None: Extracted string. (Return 'None' if not possible.)

        """
        # date :sample of Regular expression operations
        date_type = re.compile(r"""(
            (^\d{4})        # First 4 digits number
            (\D)            # Something other than numbers
            (\d{1,2})       # 1 or 2 digits number
            (\D)            # Something other than numbers
            (\d{1,2})       # 1 or 2 digits number
            )""", re.VERBOSE)

        sentence = repeat_meta[keywd][0]
        if isinstance(sentence, str):
            hit_date = date_type.search(sentence)
            if hit_date:
                split = hit_date.groups()
                year, month, day = int(split[1]), int(split[3]), int(split[5])
                if year <= self.END_OF_21_CENTURY and \
                        month <= self.END_OF_YEAR and \
                        day <= self.END_OF_MONTH:
                    return datetime.strptime(
                        str(year) + '-' + str(month) + '-' + str(day),
                        '%Y-%m-%d',
                    ).astimezone(tz=zoneinfo.ZoneInfo(key='Asia/Tokyo'))

        return None
