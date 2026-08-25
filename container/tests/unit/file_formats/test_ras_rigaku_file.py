import json
import os
from pathlib import Path
import pandas as pd
import pytest
from typing import Final

from rdetoolkit.exceptions import StructuredError
from rdetoolkit.rde2util import Meta

from file_formats.ras_rigaku_file import FileReader, MetaParser

INPUT_FILE = Path('tests/inputdata/test.ras')
SINGLE_REGION_NUM: Final[int] = 1
MULTI_REGION_NUM: Final[int] = 2
RDE_CONFIG_YAML: dict = {
    'system': {
        'magic_variable': True,
        'save_thumbnail_image': True,
    },
    'xrd': {
        'filename_mapping_rule': True,
        'manufacturer': 'rigaku',
        'main_image_setting': None,
        'meas_scan_axis_x': None,
        'meas_scan_unit_x': None,
        'meas_scan_axis_y': None,
        'meas_scan_unit_y': None
    }
}


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def read_data():
    return pd.DataFrame({
        "2Theta-Theta (deg)": [25.0000, 25.0100, 25.0200, 25.0300, 25.0400],
        "Intensity (counts)": [13.0000, 7.0000, 12.0000, 6.0000, 3.0000]
    })


@pytest.fixture
def sample_data_0():
    return pd.DataFrame({
        "2Theta-Theta (deg)": ['25.0000', '25.0100', '25.0200', '25.0300', '25.0400'],
        "Intensity (counts)": ['13.0000', '7.0000', '12.0000', '6.0000', '3.0000']
    })


@pytest.fixture
def read_meta():
    return [
        '*DISP_LINE_COLOR "4294901760"',
        '*FILE_COMMENT "XRD example"',
        '*FILE_MD5 ""',
        '*FILE_MEMO "Rigaku XRD memo"',
        '*FILE_OPERATOR "English"',
        '*FILE_PACKAGE_NAME ""',
        '*FILE_PART_ID "GeneralMeasurement(BB)"',
        '*FILE_SAMPLE "Test Sample"',
        '*FILE_TYPE "RAS_RAW"',
        '*FILE_USERGROUP "Academic"',
        '*FILE_VERSION "1"',
        '*HW_ATTACHMENT_ID "ATT0033"',
        '*HW_ATTACHMENT_NAME "ASC6_Reflection"',
        '*HW_COUNTER_ID-0 "CUT0041"',
        '*HW_COUNTER_ID-2 "CMC0020"',
        '*HW_COUNTER_NAME-0 "DteX250(H)"',
        '*HW_COUNTER_NAME-2 "None"',
        '*HW_COUNTER_PIXEL_SIZE "0.075"',
        '*HW_COUNTER_SELECT_NAME "DteX250(H)"',
        '*HW_GONIOMETER_ID "GON0021"',
        '*HW_GONIOMETER_NAME "Standard"',
        '*HW_GONIOMETER_RADIUS-0 "90.0"',
        '*HW_GONIOMETER_RADIUS-1 "114.0"',
        '*HW_GONIOMETER_RADIUS-2 "190.0"',
        '*HW_GONIOMETER_RADIUS-3 "300.0"',
        '*HW_GONIOMETER_RADIUS-4 "187.0"',
        '*HW_GONIOMETER_RADIUS-5 "300.0"',
        '*HW_GONIOMETER_RADIUS-6 "113.0"',
        '*HW_GONIOMETER_RADIUS-7 "331.0"',
        '*HW_I_OPT_ID-1 "CBO0029"',
        '*HW_I_OPT_ID-2 "ISL0021"',
        '*HW_R_ATTENUATER_AUTOMODE "0"',
        '*HW_R_OPT_ID-0 "RSS0022"',
        '*HW_R_OPT_ID-1 "RCR0023"',
        '*HW_R_OPT_ID-2 "RSO0021"',
        '*HW_R_OPT_ID-3 "RRS0022"',
        '*HW_R_OPT_ID-4 "ATN0021"',
        '*HW_SAMPLE_HOLDER_ID "SMP0023"',
        '*HW_SAMPLE_HOLDER_NAME "Z"',
        '*HW_XG_CURRENT_UNIT "mA"',
        '*HW_XG_FOCUS "0.4mm x 8mm"',
        '*HW_XG_FOCUS_TYPE "Fine"',
        '*HW_XG_TARGET_ATOMIC_NUMBER "29"',
        '*HW_XG_TARGET_NAME "Cu"',
        '*HW_XG_TYPE "Hermetic"',
        '*HW_XG_VOLTAGE_UNIT "kV"',
        '*HW_XG_WAVE_LENGTH_ALPHA1 "1.540593"',
        '*HW_XG_WAVE_LENGTH_ALPHA2 "1.544414"',
        '*HW_XG_WAVE_LENGTH_BETA "1.392246"',
        '*HW_XG_WAVE_LENGTH_UNIT "Angstrom"',
        '*MEAS_COND_AXIS_NAME_INTERNAL-0 "ThetaS"',
        '*MEAS_COND_AXIS_NAME_INTERNAL-1 "ThetaD"',
        '*MEAS_COND_AXIS_NAME-0 "ThetaS"',
        '*MEAS_COND_AXIS_NAME-1 "ThetaD"',
        '*MEAS_COND_AXIS_OFFSET-0 "0.8349"',
        '*MEAS_COND_AXIS_OFFSET-1 "0.2882"',
        '*MEAS_COND_AXIS_POSITION-0 "0.0000"',
        '*MEAS_COND_AXIS_POSITION-1 "0.0000"',
        '*MEAS_COND_AXIS_UNIT-0 "deg"',
        '*MEAS_COND_AXIS_UNIT-1 "deg"',
        '*MEAS_COND_OPT_ATTR "DB"',
        '*MEAS_COND_OPT_NAME ""',
        '*MEAS_COND_XG_CURRENT "30"',
        '*MEAS_COND_XG_VOLTAGE "40"',
        '*MEAS_COND_XG_WAVE_TYPE "Ka"',
        '*MEAS_DATA_COUNT "3501"',
        '*MEAS_SCAN_AXIS_X "TwoThetaTheta"',
        '*MEAS_SCAN_AXIS_X_INTERNAL "TwoThetaTheta"',
        '*MEAS_SCAN_END_TIME "11/21/2017 08:37:42"',
        '*MEAS_SCAN_MODE "CONTINUOUS"',
        '*MEAS_SCAN_RESOLUTION_X "0.0002"',
        '*MEAS_SCAN_SPEED "8.0000"',
        '*MEAS_SCAN_SPEED_UNIT "deg/min"',
        '*MEAS_SCAN_START "25.0000"',
        '*MEAS_SCAN_START_TIME "11/21/2017 08:32:31"',
        '*MEAS_SCAN_STEP "0.0100"',
        '*MEAS_SCAN_STOP "60.0000"',
        '*MEAS_SCAN_UNEQUALY_SPACED "False"',
        '*MEAS_SCAN_UNIT_X "deg"',
        '*MEAS_SCAN_UNIT_Y "counts"'
    ]


@pytest.fixture
def metadata_def(tmp_path):
    """metadata-def.json"""
    metadata_def = {
        "ras.specimen": {
            "name": {
                "ja": "試料",
                "en": "Specimen"
            },
            "schema": {
                "type": "string"
            },
            "order": 1,
            "mode": "ras形式",
            "originalName": "FILE_SAMPLE",
            "variable": 1
        },
        "ras.comment": {
            "name": {
                "ja": "コメント",
                "en": "Comment"
            },
            "schema": {
                "type": "string"
            },
            "order": 2,
            "mode": "ras形式",
            "originalName": "FILE_COMMENT",
            "variable": 1
        },
        "ras.selected_detector_name": {
            "name": {
                "ja": "使用検出器名称",
                "en": "Selected Detector Name"
            },
            "schema": {
                "type": "string"
            },
            "order": 3,
            "mode": "ras形式",
            "originalName": "HW_COUNTER_SELECT_NAME",
            "variable": 1
        },
        "ras.scan_axis": {
            "name": {
                "ja": "スキャン軸",
                "en": "Scan Axis"
            },
            "schema": {
                "type": "string"
            },
            "order": 4,
            "mode": "ras形式",
            "originalName": "MEAS_SCAN_AXIS_X",
            "variable": 1
        },
        "ras.scan_mode": {
            "name": {
                "ja": "スキャンモード",
                "en": "Scan Mode"
            },
            "schema": {
                "type": "string"
            },
            "order": 5,
            "mode": "ras形式",
            "originalName": "MEAS_SCAN_MODE",
            "variable": 1
        },
        "ras.x-ray_tube_current": {
            "name": {
                "ja": "X線管電流",
                "en": "X-ray Tube Current"
            },
            "schema": {
                "type": "number"
            },
            "order": 6,
            "unit": "$HW_XG_CURRENT_UNIT",
            "mode": "ras形式",
            "originalName": "MEAS_COND_XG_CURRENT",
            "variable": 1
        },
        "ras.x-ray_tube_voltage": {
            "name": {
                "ja": "X線管電圧",
                "en": "X-ray Tube Voltage"
            },
            "schema": {
                "type": "number"
            },
            "order": 7,
            "unit": "$HW_XG_VOLTAGE_UNIT",
            "mode": "ras形式",
            "originalName": "MEAS_COND_XG_VOLTAGE",
            "variable": 1
        },
        "ras.scan_starting_position": {
            "name": {
                "ja": "スキャン開始位置",
                "en": "Scan Starting Position"
            },
            "schema": {
                "type": "number"
            },
            "order": 8,
            "unit": "$MEAS_SCAN_UNIT_X",
            "mode": "ras形式",
            "originalName": "MEAS_SCAN_START",
            "variable": 1
        },
        "ras.scan_ending_position": {
            "name": {
                "ja": "スキャン終了位置",
                "en": "Scan Ending Position"
            },
            "schema": {
                "type": "number"
            },
            "order": 9,
            "unit": "$MEAS_SCAN_UNIT_X",
            "mode": "ras形式",
            "originalName": "MEAS_SCAN_STOP",
            "variable": 1
        },
        "ras.scan_step_size": {
            "name": {
                "ja": "スキャンステップサイズ",
                "en": "Scan Step Size"
            },
            "schema": {
                "type": "number"
            },
            "order": 10,
            "unit": "$MEAS_SCAN_UNIT_X",
            "mode": "ras形式",
            "originalName": "MEAS_SCAN_STEP",
            "variable": 1
        },
        "ras.scan_speed": {
            "name": {
                "ja": "スキャンスピード",
                "en": "Scan Speed"
            },
            "schema": {
                "type": "number"
            },
            "order": 11,
            "unit": "$MEAS_SCAN_SPEED_UNIT",
            "mode": "ras形式",
            "originalName": "MEAS_SCAN_SPEED",
            "variable": 1
        },
        "ras.scan_starting_date_time": {
            "name": {
                "ja": "スキャン開始時刻",
                "en": "Scan Starting Date Time"
            },
            "schema": {
                "type": "string"
            },
            "order": 12,
            "mode": "ras形式",
            "originalName": "MEAS_SCAN_START_TIME",
            "variable": 1
        },
        "ras.scan_ending_date_time": {
            "name": {
                "ja": "スキャン終了時刻",
                "en": "Scan Ending Date Time"
            },
            "schema": {
                "type": "string"
            },
            "order": 13,
            "mode": "ras形式",
            "originalName": "MEAS_SCAN_END_TIME",
            "variable": 1
        },
        "ras.memo": {
            "name": {
                "ja": "メモ",
                "en": "Memo"
            },
            "schema": {
                "type": "string"
            },
            "order": 14,
            "mode": "ras形式",
            "originalName": "FILE_MEMO",
            "variable": 1
        },
        "ras.measurement_operator": {
            "name": {
                "ja": "測定実施者",
                "en": "Measurement Operator"
            },
            "schema": {
                "type": "string"
            },
            "order": 15,
            "mode": "ras形式",
            "originalName": "FILE_OPERATOR",
            "variable": 1
        },
        "ras.detector_pixel_size": {
            "name": {
                "ja": "検出器ピクセルサイズ",
                "en": "Detector Pixel Size"
            },
            "schema": {
                "type": "number"
            },
            "order": 16,
            "unit": "mm",
            "mode": "ras形式",
            "originalName": "HW_COUNTER_PIXEL_SIZE",
            "variable": 1
        },
        "ras.x-ray_target_material": {
            "name": {
                "ja": "X線ターゲットの材質",
                "en": "X-ray Target Material"
            },
            "schema": {
                "type": "string"
            },
            "order": 17,
            "mode": "ras形式",
            "originalName": "HW_XG_TARGET_NAME",
            "variable": 1
        },
        "ras.k_alpha_1_wavelength": {
            "name": {
                "ja": "K_alpha1の波長",
                "en": "K_alpha_1 Wavelength"
            },
            "schema": {
                "type": "number"
            },
            "order": 18,
            "unit": "Angstrom",
            "mode": "ras形式",
            "originalName": "HW_XG_WAVE_LENGTH_ALPHA1",
            "variable": 1
        },
        "ras.k_alpha_2_wavelength": {
            "name": {
                "ja": "K_alpha2の波長",
                "en": "K_alpha_2 Wavelength"
            },
            "schema": {
                "type": "number"
            },
            "order": 19,
            "unit": "Angstrom",
            "mode": "ras形式",
            "originalName": "HW_XG_WAVE_LENGTH_ALPHA2",
            "variable": 1
        },
        "ras.k_beta_wavelength": {
            "name": {
                "ja": "K_betaの波長",
                "en": "K_beta Wavelength"
            },
            "schema": {
                "type": "number"
            },
            "order": 20,
            "unit": "Angstrom",
            "mode": "ras形式",
            "originalName": "HW_XG_WAVE_LENGTH_BETA",
            "variable": 1
        },
        "ras.optics_attribute": {
            "name": {
                "ja": "光学系属性",
                "en": "Optics Attribute"
            },
            "schema": {
                "type": "string"
            },
            "order": 21,
            "mode": "ras形式",
            "originalName": "MEAS_COND_OPT_ATTR",
            "variable": 1
        },
        "ras.wavelength_type": {
            "name": {
                "ja": "波長タイプ",
                "en": "Wavelength Type"
            },
            "schema": {
                "type": "string"
            },
            "order": 22,
            "mode": "ras形式",
            "originalName": "MEAS_COND_XG_WAVE_TYPE",
            "variable": 1
        },
        "ras.data_point_number": {
            "name": {
                "ja": "データ点数",
                "en": "Data Point Number"
            },
            "schema": {
                "type": "number"
            },
            "order": 23,
            "mode": "ras形式",
            "originalName": "MEAS_DATA_COUNT",
            "variable": 1
        },
        "ras.scan_axis_unit": {
            "name": {
                "ja": "スキャン軸の単位",
                "en": "Scan Axis Unit"
            },
            "schema": {
                "type": "string"
            },
            "order": 24,
            "mode": "ras形式",
            "originalName": "MEAS_SCAN_UNIT_X",
            "variable": 1
        },
        "ras.intensity_unit": {
            "name": {
                "ja": "強度の単位",
                "en": "Intensity Unit"
            },
            "schema": {
                "type": "string"
            },
            "order": 25,
            "mode": "ras形式",
            "originalName": "MEAS_SCAN_UNIT_Y",
            "variable": 1
        }
    }
    metadata_def_path = tmp_path / "metadata-def.json"
    with open(metadata_def_path, mode="w", encoding="utf-8") as f:
        json.dump(metadata_def, f)
    return metadata_def_path


@pytest.fixture
def class_meta(metadata_def):
    return Meta(metadata_def)


@pytest.fixture
def input_meta():
    """入力メタデータ"""
    return [
        '*DISP_LINE_COLOR "4294901760"',
        '*FILE_COMMENT "XRD example"',
        '*FILE_MD5 ""',
        '*FILE_MEMO "Rigaku XRD memo"',
        '*FILE_OPERATOR "English"',
        '*FILE_PACKAGE_NAME ""',
        '*FILE_PART_ID "GeneralMeasurement(BB)"',
        '*FILE_SAMPLE "Test Sample"',
        '*FILE_TYPE "RAS_RAW"',
        '*FILE_USERGROUP "Academic"',
        '*FILE_VERSION "1"',
        '*HW_ATTACHMENT_ID "ATT0033"',
        '*HW_ATTACHMENT_NAME "ASC6_Reflection"',
        '*HW_COUNTER_ID-0 "CUT0041"',
        '*HW_COUNTER_ID-2 "CMC0020"',
        '*HW_COUNTER_NAME-0 "DteX250(H)"',
        '*HW_COUNTER_NAME-2 "None"',
        '*HW_COUNTER_PIXEL_SIZE "0.075"',
        '*HW_COUNTER_SELECT_NAME "DteX250(H)"',
        '*HW_GONIOMETER_ID "GON0021"',
        '*HW_GONIOMETER_NAME "Standard"',
        '*HW_GONIOMETER_RADIUS-0 "90.0"',
        '*HW_GONIOMETER_RADIUS-1 "114.0"',
        '*HW_GONIOMETER_RADIUS-2 "190.0"',
        '*HW_GONIOMETER_RADIUS-3 "300.0"',
        '*HW_GONIOMETER_RADIUS-4 "187.0"',
        '*HW_GONIOMETER_RADIUS-5 "300.0"',
        '*HW_GONIOMETER_RADIUS-6 "113.0"',
        '*HW_GONIOMETER_RADIUS-7 "331.0"',
        '*HW_I_OPT_ID-1 "CBO0029"',
        '*HW_I_OPT_ID-2 "ISL0021"',
        '*HW_R_ATTENUATER_AUTOMODE "0"',
        '*HW_R_OPT_ID-0 "RSS0022"',
        '*HW_R_OPT_ID-1 "RCR0023"',
        '*HW_R_OPT_ID-2 "RSO0021"',
        '*HW_R_OPT_ID-3 "RRS0022"',
        '*HW_R_OPT_ID-4 "ATN0021"',
        '*HW_SAMPLE_HOLDER_ID "SMP0023"',
        '*HW_SAMPLE_HOLDER_NAME "Z"',
        '*HW_XG_CURRENT_UNIT "mA"',
        '*HW_XG_FOCUS "0.4mm x 8mm"',
        '*HW_XG_FOCUS_TYPE "Fine"',
        '*HW_XG_TARGET_ATOMIC_NUMBER "29"',
        '*HW_XG_TARGET_NAME "Cu"',
        '*HW_XG_TYPE "Hermetic"',
        '*HW_XG_VOLTAGE_UNIT "kV"',
        '*HW_XG_WAVE_LENGTH_ALPHA1 "1.540593"',
        '*HW_XG_WAVE_LENGTH_ALPHA2 "1.544414"',
        '*HW_XG_WAVE_LENGTH_BETA "1.392246"',
        '*HW_XG_WAVE_LENGTH_UNIT "Angstrom"',
        '*MEAS_COND_AXIS_NAME_INTERNAL-0 "ThetaS"',
        '*MEAS_COND_AXIS_NAME_INTERNAL-1 "ThetaD"',
        '*MEAS_COND_AXIS_NAME_INTERNAL-10 "CBO-M"',
        '*MEAS_COND_AXIS_NAME_INTERNAL-11 "CBO"',
        '*MEAS_COND_AXIS_NAME_INTERNAL-12 "IncidentSollerSlit"',
        '*MEAS_COND_AXIS_NAME_INTERNAL-13 "IncidentSlitBox"',
        '*MEAS_COND_AXIS_NAME_INTERNAL-14 "IncidentSlitBox"',
        '*MEAS_COND_AXIS_NAME_INTERNAL-15 "IncidentSlitBox"',
        '*MEAS_COND_AXIS_NAME_INTERNAL-16 "Zs"'
    ]


@pytest.fixture
def parse_meta():
    """構文解析後メタデータ"""
    return {
        'DISP_LINE_COLOR': ['4294901760'],
        'FILE_COMMENT': ['XRD example'],
        'FILE_MD5': [''],
        'FILE_MEMO': ['Rigaku XRD memo'],
        'FILE_OPERATOR': ['English'],
        'FILE_PACKAGE_NAME': [''],
        'FILE_PART_ID': ['GeneralMeasurement(BB)'],
        'FILE_SAMPLE': ['Test Sample'],
        'FILE_TYPE': ['RAS_RAW'],
        'FILE_USERGROUP': ['Academic'],
        'FILE_VERSION': ['1'],
        'HW_ATTACHMENT_ID': ['ATT0033'],
        'HW_ATTACHMENT_NAME': ['ASC6_Reflection'],
        'HW_COUNTER_ID-0': ['CUT0041'],
        'HW_COUNTER_ID-2': ['CMC0020'],
        'HW_COUNTER_NAME-0': ['DteX250(H)'],
        'HW_COUNTER_NAME-2': ['None'],
        'HW_COUNTER_PIXEL_SIZE': ['0.075'],
        'HW_COUNTER_SELECT_NAME': ['DteX250(H)'],
        'HW_GONIOMETER_ID': ['GON0021'],
        'HW_GONIOMETER_NAME': ['Standard'],
        'HW_GONIOMETER_RADIUS-0': ['90.0'],
        'HW_GONIOMETER_RADIUS-1': ['114.0'],
        'HW_GONIOMETER_RADIUS-2': ['190.0'],
        'HW_GONIOMETER_RADIUS-3': ['300.0'],
        'HW_GONIOMETER_RADIUS-4': ['187.0'],
        'HW_GONIOMETER_RADIUS-5': ['300.0'],
        'HW_GONIOMETER_RADIUS-6': ['113.0'],
        'HW_GONIOMETER_RADIUS-7': ['331.0'],
        'HW_I_OPT_ID-1': ['CBO0029'],
        'HW_I_OPT_ID-2': ['ISL0021'],
        'HW_R_ATTENUATER_AUTOMODE': ['0'],
        'HW_R_OPT_ID-0': ['RSS0022'],
        'HW_R_OPT_ID-1': ['RCR0023'],
        'HW_R_OPT_ID-2': ['RSO0021'],
        'HW_R_OPT_ID-3': ['RRS0022'],
        'HW_R_OPT_ID-4': ['ATN0021'],
        'HW_SAMPLE_HOLDER_ID': ['SMP0023'],
        'HW_SAMPLE_HOLDER_NAME': ['Z'],
        'HW_XG_CURRENT_UNIT': ['mA'],
        'HW_XG_FOCUS': ['0.4mm x 8mm'],
        'HW_XG_FOCUS_TYPE': ['Fine'],
        'HW_XG_TARGET_ATOMIC_NUMBER': ['29'],
        'HW_XG_TARGET_NAME': ['Cu'],
        'HW_XG_TYPE': ['Hermetic'],
        'HW_XG_VOLTAGE_UNIT': ['kV'],
        'HW_XG_WAVE_LENGTH_ALPHA1': ['1.540593'],
        'HW_XG_WAVE_LENGTH_ALPHA2': ['1.544414'],
        'HW_XG_WAVE_LENGTH_BETA': ['1.392246'],
        'HW_XG_WAVE_LENGTH_UNIT': ['Angstrom'],
        'MEAS_COND_AXIS_NAME_INTERNAL-0': ['ThetaS'],
        'MEAS_COND_AXIS_NAME_INTERNAL-1': ['ThetaD'],
        'MEAS_COND_AXIS_NAME_INTERNAL-10': ['CBO-M'],
        'MEAS_COND_AXIS_NAME_INTERNAL-11': ['CBO'],
        'MEAS_COND_AXIS_NAME_INTERNAL-12': ['IncidentSollerSlit'],
        'MEAS_COND_AXIS_NAME_INTERNAL-13': ['IncidentSlitBox'],
        'MEAS_COND_AXIS_NAME_INTERNAL-14': ['IncidentSlitBox'],
        'MEAS_COND_AXIS_NAME_INTERNAL-15': ['IncidentSlitBox'],
        'MEAS_COND_AXIS_NAME_INTERNAL-16': ['Zs']
    }


@pytest.fixture
def output_meta():
    """ファイル出力後メタデータ"""
    return {
        "constant": {},
        "variable": [{
            'ras.specimen': {'value': 'Test Sample'},
            'ras.comment': {'value': 'XRD example'},
            'ras.selected_detector_name': {'value': 'DteX250(H)'},
            'ras.memo': {'value': 'Rigaku XRD memo'},
            'ras.measurement_operator': {'value': 'English'},
            'ras.detector_pixel_size': {'value': 0.075, 'unit': 'mm'},
            'ras.x-ray_target_material': {'value': 'Cu'},
            'ras.k_alpha_1_wavelength': {'value': 1.540593, 'unit': 'Angstrom'},
            'ras.k_alpha_2_wavelength': {'value': 1.544414, 'unit': 'Angstrom'},
            'ras.k_beta_wavelength': {'value': 1.392246, 'unit': 'Angstrom'}
        }]
    }


## inputfile_handler


def test_read(read_data, read_meta, temp_dir):
    """ファイル読み込み"""

    # 正常(標準)
    reader = FileReader(RDE_CONFIG_YAML)
    for data, meta in reader.read(INPUT_FILE):  # MEMO: read内でGeneratorが使われている
        pd.testing.assert_frame_equal(data, read_data)
        assert meta == read_meta

    # データなし
    empty_file = temp_dir / "empty_file.txt"
    Path(empty_file).touch()
    reader_no_data = FileReader(RDE_CONFIG_YAML)
    with pytest.raises(StructuredError) as e:
        for _, _ in reader_no_data.read(empty_file):
            pass
    assert str(e.value).startswith("Cannot read the file because it is formatted incorrectly:")
    if os.path.exists(empty_file):
        os.remove(empty_file)


def test_get_region_number():
    """リージョン番号取得"""

    # 引数(標準)
    reader = FileReader(RDE_CONFIG_YAML)
    for _, _ in reader.read(INPUT_FILE):
        region_num = reader.get_region_number()
    assert region_num == SINGLE_REGION_NUM

    # インスタンス変数
    reader_instance = FileReader(RDE_CONFIG_YAML)
    reader_instance.region_num = SINGLE_REGION_NUM
    region_num_instance = reader_instance.get_region_number()
    assert region_num_instance == reader.region_num


def test_split_data_meta(sample_data_0, read_meta):
    """データとメタの分離"""
    reader = FileReader(RDE_CONFIG_YAML)

    with open(INPUT_FILE, encoding='ascii') as f:
        reader.data, reader.meta = reader.split_data_meta(f.read())
    pd.testing.assert_frame_equal(reader.data['series_value1'], sample_data_0)
    assert reader.meta['series_meta1'] == read_meta


def test_make_header(read_meta):
    """グラフのラベルを作成"""

    # ラベルをカスタムしない(標準)
    reader = FileReader(RDE_CONFIG_YAML)
    header = reader.make_header(read_meta)
    assert header == ['2Theta-Theta (deg)', 'Intensity (counts)']

    # ラベルをカスタムする
    config: dict = {
        'system': {
            'magic_variable': True,
            'save_thumbnail_image': True,
        },
        'xrd': {
            'filename_mapping_rule': True,
            'manufacturer': 'rigaku',
            'main_image_setting': None,
            'meas_scan_axis_x': "XXX",
            'meas_scan_unit_x': "width",
            'meas_scan_axis_y': "YYY",
            'meas_scan_unit_y': "height"
        }
    }
    reader_custom = FileReader(config)
    header_custom = reader_custom.make_header(read_meta)
    assert header_custom == ['XXX (width)', 'YYY (height)']


def test_search_element_with_substring(read_meta):
    """メタデータの項目に対する値を取得"""
    reader = FileReader(RDE_CONFIG_YAML)

    # データあり
    label = reader.search_element_with_substring(read_meta, "MEAS_SCAN_AXIS_X")
    assert label == 'TwoThetaTheta'

    # データなし
    label_no_data = reader.search_element_with_substring(read_meta, "NO_DATA")
    assert label_no_data == ''


def test_convert_dtype(read_data):
    """データ型変換"""
    reader = FileReader(RDE_CONFIG_YAML)

    data = reader.convert_dtype(read_data)
    assert data['2Theta-Theta (deg)'].dtypes == 'float64'
    assert data['Intensity (counts)'].dtypes == 'float64'


## meta_handler


def test_parse(input_meta, metadata_def, parse_meta):
    """構文解析"""

    # 引数(標準)
    handler = MetaParser(metadata_def_json_path=metadata_def, config=RDE_CONFIG_YAML)
    _, repeated_meta_info = handler.parse(input_meta)
    assert repeated_meta_info == parse_meta

    # インスタンス変数
    handler_instance = MetaParser(metadata_def_json_path=metadata_def, config=RDE_CONFIG_YAML)
    handler_instance.repeated_meta_info = input_meta
    _, repeated_meta_info_instance = handler_instance.parse(None)
    assert repeated_meta_info_instance == handler_instance.repeated_meta_info


def test_save_meta(temp_dir, class_meta, parse_meta, output_meta):
    """csvファイル出力(引数)"""
    metadata_def = temp_dir / "metadata-def.json"
    save_path = temp_dir / "metadata.json"

    # 引数(標準)
    repeated_meta_info = parse_meta
    handler = MetaParser(metadata_def_json_path=metadata_def, config=RDE_CONFIG_YAML)
    _ = handler.save_meta(save_path, class_meta, repeated_meta_info=repeated_meta_info)
    assert os.path.exists(save_path)
    with open(save_path, "r", encoding="utf-8") as f:
        contents = json.load(f)
    assert contents == output_meta
    if os.path.exists(save_path):
        os.remove(save_path)

    # インスタンス変数
    handler_instance = MetaParser(metadata_def_json_path=metadata_def, config=RDE_CONFIG_YAML)
    handler_instance.repeated_meta_info = parse_meta
    _ = handler_instance.save_meta(save_path, class_meta)
    assert os.path.exists(save_path)
    with open(save_path, "r", encoding="utf-8") as f:
        contents_instance = json.load(f)
    assert contents_instance == output_meta
    if os.path.exists(save_path):
        os.remove(save_path)
