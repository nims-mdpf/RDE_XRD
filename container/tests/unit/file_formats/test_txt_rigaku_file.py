import json
import os
import os
from pathlib import Path
import pandas as pd
import pytest
from typing import Final

from rdetoolkit.exceptions import StructuredError
from rdetoolkit.rde2util import Meta
from file_formats.txt_rigaku_file import FileReader, MetaParser


INPUT_FILE = Path('tests/inputdata/test.TXT')
SINGLE_REGION_NUM: Final[int] = 1
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
        "2Theta/Theta ": [10.0, 10.01, 10.02, 10.03, 10.04],
        "Intensity ": [2740.0, 2700.0, 2740.0, 2705.0, 2645.0]
    })


@pytest.fixture
def read_data_0():
    return pd.DataFrame({
        "2Theta/Theta ": ['10', '10.01', '10.02', '10.03', '10.04'],
        "Intensity ": ['2740', '2700', '2740', '2705', '2645']
    })


@pytest.fixture
def read_meta():
    return {
        'Sample': '202401_MS99',
        'Filename': 'C:\\Data\\Xrd\\2020\\202401\\202401_MS99_2θ_θ.raw',
        'Goniometer': 'MiniFlex 300/600 +',
        'Attachment': '標準試料台',
        'Monochromater': 'None',
        'X': '0',
        'Y': '0',
        'Z': '0',
        'ScanningMode': '2Theta/Theta',
        'ScanningType': 'Continuos Scanning',
        'X-Ray': '30kV/10mA',
        'IHS': '10.0mm',
        'DS': '0.625deg',
        'SS': '8.0mm',
        'RS': '13.0mm(Open)',
        'Start': '10',
        'Stop': '60',
        'Step': '0.01',
        'Speed': '3',
        'Offset': '0',
        'TempUnit': 'Celsius',
        'StartTime': '2024/01/31 14:38:41',
        'StartTemp': '0',
        'StopTime': '2024/01/31 14:57:15',
        'StopTemp': '0'
    }


@pytest.fixture
def tab_metadata_def(tmp_path):
    """サンプルのmetadata-def.json"""
    tab_metadata_def = {
        "txt.comment": {
            "name": {
                "ja": "コメント",
                "en": "Comment"
            },
            "schema": {
                "type": "string"
            },
            "mode": "txt形式",
            "originalName": "Comments",
            "variable": 1
        },
        "txt.specimen": {
            "name": {
                "ja": "試料",
                "en": "Specimen"
            },
            "schema": {
                "type": "string"
            },
            "mode": "txt形式",
            "originalName": "Sample",
            "variable": 1
        },
        "txt.selected_detector_name": {
            "name": {
                "ja": "使用検出器名称",
                "en": "Selected Detector Name"
            },
            "schema": {
                "type": "string"
            },
            "mode": "txt形式",
            "originalName": "Goniometer",
            "variable": 1
        },
        "txt.x-ray_tube_current": {
            "name": {
                "ja": "X線管電流",
                "en": "X-ray Tube Current"
            },
            "schema": {
                "type": "number"
            },
            "mode": "txt形式",
            "unit": "mA",
            "originalName": "X-Ray",
            "variable": 1
        },
        "txt.x-ray_tube_voltage": {
            "name": {
                "ja": "X線管電圧",
                "en": "X-ray Tube Voltage"
            },
            "schema": {
                "type": "number"
            },
            "mode": "txt形式",
            "unit": "kV",
            "originalName": "X-Ray",
            "variable": 1
        },
        "txt.scan_axis": {
            "name": {
                "ja": "スキャン軸",
                "en": "Scan Axis"
            },
            "schema": {
                "type": "string"
            },
            "mode": "txt形式",
            "originalName": "ScanningMode",
            "variable": 1
        },
        "txt.scan_starting_date_time": {
            "name": {
                "ja": "スキャン開始時刻",
                "en": "Scan Starting Date Time"
            },
            "schema": {
                "type": "string",
                "format": "date-time"
            },
            "mode": "txt形式",
            "originalName": "StartTime",
            "variable": 1
        },
        "txt.scan_ending_date_time": {
            "name": {
                "ja": "スキャン終了時刻",
                "en": "Scan Ending Date Time"
            },
            "schema": {
                "type": "string",
                "format": "date-time"
            },
            "mode": "txt形式",
            "originalName": "StopTime",
            "variable": 1
        },
        "txt.scan_mode": {
            "name": {
                "ja": "スキャンモード",
                "en": "Scan Mode"
            },
            "schema": {
                "type": "string"
            },
            "mode": "txt形式",
            "originalName": "ScanningType",
            "variable": 1
        },
        "txt.scan_speed": {
            "name": {
                "ja": "スキャンスピード",
                "en": "Scan Speed"
            },
            "schema": {
                "type": "number"
            },
            "mode": "txt形式",
            "unit": "deg/min",
            "originalName": "Speed",
            "variable": 1
        },
        "txt.scan_step_size": {
            "name": {
                "ja": "スキャンステップサイズ",
                "en": "Scan Step Size"
            },
            "schema": {
                "type": "number"
            },
            "mode": "txt形式",
            "unit": "deg",
            "originalName": "Step",
            "variable": 1
        },
        "txt.scan_starting_position": {
            "name": {
                "ja": "スキャン開始位置",
                "en": "Scan Starting Position"
            },
            "schema": {
                "type": "number"
            },
            "mode": "txt形式",
            "unit": "deg",
            "originalName": "Start",
            "variable": 1
        },
        "txt.scan_ending_position": {
            "name": {
                "ja": "スキャン終了位置",
                "en": "Scan Ending Position"
            },
            "schema": {
                "type": "number"
            },
            "mode": "txt形式",
            "unit": "deg",
            "originalName": "Stop",
            "variable": 1
        },
        "txt.attachment": {
            "name": {
                "ja": "付属試料台",
                "en": "Attachment"
            },
            "schema": {
                "type": "string"
            },
            "mode": "txt形式",
            "originalName": "Attachment",
            "variable": 1
        },
        "txt.monochromator": {
            "name": {
                "ja": "分光器",
                "en": "Monochromator"
            },
            "schema": {
                "type": "string"
            },
            "mode": "txt形式",
            "originalName": "Monochromater",
            "variable": 1
        },
        "txt.incidentbeampath_divergence_slit_width（angle)": {
            "name": {
                "ja": "入射光_発散スリット幅（角度）",
                "en": "incidentBeamPath_divergence slit width（angle)"
            },
            "schema": {
                "type": "number"
            },
            "mode": "txt形式",
            "unit": "deg",
            "originalName": "DS",
            "variable": 1
        },
        "txt.diffractedbeampath_anti-scatter_slit_width": {
            "name": {
                "ja": "出射光_散乱スリット幅",
                "en": "diffractedBeamPath_anti-scatter slit width"
            },
            "schema": {
                "type": "number"
            },
            "mode": "txt形式",
            "unit": "mm",
            "originalName": "SS",
            "variable": 1
        },
        "txt.diffractedbeampath_receiving_slit_width": {
            "name": {
                "ja": "出射光_受光スリット幅",
                "en": "diffractedBeamPath_receiving slit width"
            },
            "schema": {
                "type": "number"
            },
            "mode": "txt形式",
            "unit": "mm",
            "originalName": "RS",
            "variable": 1
        }
    }
    tab_metadata_def_path = tmp_path / "metadata-def.json"
    with open(tab_metadata_def_path, mode="w", encoding="utf-8") as f:
        json.dump(tab_metadata_def, f)
    return tab_metadata_def_path


@pytest.fixture
def tab_class_meta(tab_metadata_def):
    return Meta(tab_metadata_def)


@pytest.fixture
def space_metadata_def(tmp_path):
    """サンプルのmetadata-def.json"""
    space_metadata_def = {
        "txt.comment": {
            "name": {
                "ja": "コメント",
                "en": "Comment"
            },
            "schema": {
                "type": "string"
            },
            "mode": "txt形式",
            "originalName": "Comments",
            "variable": 1
        },
        "txt.specimen": {
            "name": {
                "ja": "試料",
                "en": "Specimen"
            },
            "schema": {
                "type": "string"
            },
            "mode": "txt形式",
            "originalName": "Sample",
            "variable": 1
        },
        "txt.selected_detector_name": {
            "name": {
                "ja": "使用検出器名称",
                "en": "Selected Detector Name"
            },
            "schema": {
                "type": "string"
            },
            "mode": "txt形式",
            "originalName": "Goniometer",
            "variable": 1
        },
        "txt.x-ray_tube_current": {
            "name": {
                "ja": "X線管電流",
                "en": "X-ray Tube Current"
            },
            "schema": {
                "type": "number"
            },
            "mode": "txt形式",
            "unit": "mA",
            "originalName": "X-Ray",
            "variable": 1
        },
        "txt.x-ray_tube_voltage": {
            "name": {
                "ja": "X線管電圧",
                "en": "X-ray Tube Voltage"
            },
            "schema": {
                "type": "number"
            },
            "mode": "txt形式",
            "unit": "kV",
            "variable": 1
        },
        "txt.scan_axis": {
            "name": {
                "ja": "スキャン軸",
                "en": "Scan Axis"
            },
            "schema": {
                "type": "string"
            },
            "mode": "txt形式",
            "originalName": "ScanningMode",
            "variable": 1
        },
        "txt.scan_starting_date_time": {
            "name": {
                "ja": "スキャン開始時刻",
                "en": "Scan Starting Date Time"
            },
            "schema": {
                "type": "string",
                "format": "date-time"
            },
            "mode": "txt形式",
            "variable": 1
        },
        "txt.scan_ending_date_time": {
            "name": {
                "ja": "スキャン終了時刻",
                "en": "Scan Ending Date Time"
            },
            "schema": {
                "type": "string",
                "format": "date-time"
            },
            "mode": "txt形式",
            "variable": 1
        },
        "txt.scan_mode": {
            "name": {
                "ja": "スキャンモード",
                "en": "Scan Mode"
            },
            "schema": {
                "type": "string"
            },
            "mode": "txt形式",
            "originalName": "ScanningType",
            "variable": 1
        },
        "txt.scan_speed": {
            "name": {
                "ja": "スキャンスピード",
                "en": "Scan Speed"
            },
            "schema": {
                "type": "number"
            },
            "mode": "txt形式",
            "unit": "deg/min",
            "variable": 1
        },
        "txt.scan_step_size": {
            "name": {
                "ja": "スキャンステップサイズ",
                "en": "Scan Step Size"
            },
            "schema": {
                "type": "number"
            },
            "mode": "txt形式",
            "unit": "deg",
            "originalName": "Step",
            "variable": 1
        },
        "txt.scan_starting_position": {
            "name": {
                "ja": "スキャン開始位置",
                "en": "Scan Starting Position"
            },
            "schema": {
                "type": "number"
            },
            "mode": "txt形式",
            "unit": "deg",
            "originalName": "Start",
            "variable": 1
        },
        "txt.scan_ending_position": {
            "name": {
                "ja": "スキャン終了位置",
                "en": "Scan Ending Position"
            },
            "schema": {
                "type": "number"
            },
            "mode": "txt形式",
            "unit": "deg",
            "originalName": "Stop",
            "variable": 1
        },
        "txt.attachment": {
            "name": {
                "ja": "付属試料台",
                "en": "Attachment"
            },
            "schema": {
                "type": "string"
            },
            "mode": "txt形式",
            "originalName": "Attachment",
            "variable": 1
        },
        "txt.monochromator": {
            "name": {
                "ja": "分光器",
                "en": "Monochromator"
            },
            "schema": {
                "type": "string"
            },
            "mode": "txt形式",
            "originalName": "Monochromater",
            "variable": 1
        },
        "txt.incidenting_slit": {
            "name": {
                "ja": "入射スリット",
                "en": "incidenting slit"
            },
            "schema": {
                "type": "number"
            },
            "mode": "txt形式",
            "unit": "deg",
            "originalName": "入射スリット",
            "variable": 1
        },
        "txt.receiving_slit_1": {
            "name": {
                "ja": "受光スリット1",
                "en": "receiving slit 1"
            },
            "schema": {
                "type": "number"
            },
            "mode": "txt形式",
            "unit": "mm",
            "originalName": "受光スリット1",
            "variable": 1
        },
        "txt.receiving_slit_2": {
            "name": {
                "ja": "受光スリット2",
                "en": "receiving slit 2"
            },
            "schema": {
                "type": "number"
            },
            "mode": "txt形式",
            "unit": "mm",
            "originalName": "受光スリット2",
            "variable": 1
        }
    }
    space_metadata_def_path = tmp_path / "metadata-def.json"
    with open(space_metadata_def_path, mode="w", encoding="utf-8") as f:
        json.dump(space_metadata_def, f)
    return space_metadata_def_path


@pytest.fixture
def space_class_meta(space_metadata_def):
    return Meta(space_metadata_def)


@pytest.fixture
def tab_input_meta():
    """サンプルの入力メタデータ"""
    return {
        'Sample': '202401_MS99',
        'Filename': 'C:\\Data\\Xrd\\2020\\202401\\202401_MS99_2θ_θ.raw',
        'Goniometer': 'MiniFlex 300/600 +',
        'Attachment': '標準試料台',
        'Monochromater': 'None',
        'X': '0',
        'Y': '0',
        'Z': '0',
        'ScanningMode': '2Theta/Theta',
        'ScanningType': 'Continuos Scanning',
        'X-Ray': '30kV/10mA',
        'IHS': '10.0mm',
        'DS': '0.625deg',
        'SS': '8.0mm',
        'RS': '13.0mm(Open)',
        'Start': '10',
        'Stop': '60',
        'Step': '0.01',
        'Speed': '3',
        'Offset': '0',
        'TempUnit': 'Celsius',
        'StartTime': '2024/01/31 14:38:41',
        'StartTemp': '0',
        'StopTime': '2024/01/31 14:57:15',
        'StopTemp': '0'
    }


@pytest.fixture
def space_input_meta():
    """サンプルの入力メタデータ"""
    return {
        'ScanningMode': '2Theta/Theta',
        'ScanningType': 'Continuos Scanning',
        'X-Ray': '45kV/200mA',  # if k == "X-Ray"
        '入射スリット': '1/3deg',  # elif k == "入射スリット" and '/' in v
        '受光スリット1': '8.000mm',
        '受光スリット2': '13.000mm',
        'Start': '10',
        'Stop': '70',
        'Step': '0.01'
    }


@pytest.fixture
def tab_parse_meta():
    """サンプルの出力メタデータ"""
    return {
        'Sample': ['202401_MS99'],
        'Filename': ['C:\\Data\\Xrd\\2020\\202401\\202401_MS99_2θ_θ.raw'],
        'Goniometer': ['MiniFlex 300/600 +'],
        'Attachment': ['標準試料台'],
        'Monochromater': ['None'],
        'X': ['0'],
        'Y': ['0'],
        'Z': ['0'],
        'ScanningMode': ['2Theta/Theta'],
        'ScanningType': ['Continuos Scanning'],
        'txt.x-ray_tube_voltage': ['30kV'],
        'txt.x-ray_tube_current': ['10mA'],
        'IHS': ['10.0mm'],
        'DS': ['0.625deg'],
        'SS': ['8.0mm'],
        'RS': ['13.0mm(Open)'],
        'Start': ['10'],
        'Stop': ['60'],
        'Step': ['0.01'],
        'Speed': ['3'],
        'Offset': ['0'],
        'TempUnit': ['Celsius'],
        'StartTime': ['2024/01/31 14:38:41'],
        'StartTemp': ['0'],
        'StopTime': ['2024/01/31 14:57:15'],
        'StopTemp': ['0']
    }


@pytest.fixture
def space_parse_meta():
    """サンプルの出力メタデータ"""
    return {
        'ScanningMode': ['2Theta/Theta'],
        'ScanningType': ['Continuos Scanning'],
        'txt.x-ray_tube_voltage': ['45kV'],
        'txt.x-ray_tube_current': ['200mA'],
        '入射スリット': [0.3333333333333333],  # MEMO: input -> 1/3deg
        '受光スリット1': ['8.000mm'],
        '受光スリット2': ['13.000mm'],
        'Start': ['10'],
        'Stop': ['70'],
        'Step': ['0.01']
    }


@pytest.fixture
def tab_output_meta():
    """ファイル出力後メタデータ"""
    return {
        "constant": {},
        "variable": [{
            'txt.specimen': {'value': '202401_MS99'},
            'txt.selected_detector_name': {'value': 'MiniFlex 300/600 +'},
            'txt.x-ray_tube_current': {'value': 10, 'unit': 'mA'},
            'txt.x-ray_tube_voltage': {'value': 30, 'unit': 'kV'},
            'txt.scan_axis': {'value': '2Theta/Theta'},
            'txt.scan_starting_date_time': {'value': '2024-01-31T14:38:41'},
            'txt.scan_ending_date_time': {'value': '2024-01-31T14:57:15'},
            'txt.scan_mode': {'value': 'Continuos Scanning'},
            'txt.scan_speed': {'value': 3, 'unit': 'deg/min'},
            'txt.scan_step_size': {'value': 0.01, 'unit': 'deg'},
            'txt.scan_starting_position': {'value': 10, 'unit': 'deg'},
            'txt.scan_ending_position': {'value': 60, 'unit': 'deg'},
            'txt.attachment': {'value': '標準試料台'},
            'txt.monochromator': {'value': 'None'},
            'txt.incidentbeampath_divergence_slit_width（angle)': {'value': 0.625, 'unit': 'deg'},
            'txt.diffractedbeampath_anti-scatter_slit_width': {'value': 8.0, 'unit': 'mm'},
            'txt.diffractedbeampath_receiving_slit_width': {'value': 13.0, 'unit': 'mm'}
        }]
    }


@pytest.fixture
def space_output_meta():
    """ファイル出力後メタデータ"""
    return {
        "constant": {},
        "variable": [{
            'txt.x-ray_tube_current': {'value': 200, 'unit': 'mA'},
            'txt.x-ray_tube_voltage': {'value': 45, 'unit': 'kV'},
            'txt.scan_axis': {'value': '2Theta/Theta'},
            'txt.scan_mode': {'value': 'Continuos Scanning'},
            'txt.scan_step_size': {'value': 0.01, 'unit': 'deg'},
            'txt.scan_starting_position': {'value': 10, 'unit': 'deg'},
            'txt.scan_ending_position': {'value': 70, 'unit': 'deg'},
            'txt.incidenting_slit': {'value': 0.3333333333333333, 'unit': 'deg'},
            'txt.receiving_slit_1': {'value': 8.0, 'unit': 'mm'},
            'txt.receiving_slit_2': {'value': 13.0, 'unit': 'mm'}
        }]
    }


# inputfile_handler


def test_read(read_data, read_meta, temp_dir):
    """ファイル読み込み"""

    # 正常(標準)
    reader = FileReader(RDE_CONFIG_YAML)
    reader.config['xrd']['delimiter_type'] = "\t"
    for data, meta in reader.read(INPUT_FILE):  # MEMO: read内でGeneratorが使われている
        pd.testing.assert_frame_equal(data, read_data, check_dtype=False)
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


def test_convert_dtype(read_data):
    """データ型変換"""
    reader = FileReader(RDE_CONFIG_YAML)

    data = reader.convert_dtype(read_data)
    assert data['2Theta/Theta '].dtypes == 'float64'
    assert data['Intensity '].dtypes == 'float64'


def test_get_region_number():
    """リージョン番号取得"""

    # 引数(標準)
    reader = FileReader(RDE_CONFIG_YAML)
    reader.config['xrd']['delimiter_type'] = "\t"
    for _, _ in reader.read(INPUT_FILE):
        region_num = reader.get_region_number()
    assert region_num == SINGLE_REGION_NUM

    # インスタンス変数
    reader_instance = FileReader(RDE_CONFIG_YAML)
    reader_instance.config['xrd']['delimiter_type'] = "\t"
    reader_instance.region_num = SINGLE_REGION_NUM
    region_num_instance = reader_instance.get_region_number()
    assert region_num_instance == reader.region_num


def test_split_data_meta(read_data_0, read_meta):
    """データとメタの分離"""
    reader = FileReader(RDE_CONFIG_YAML)
    reader.config['xrd']['delimiter_type'] = "\t"

    with open(INPUT_FILE, encoding='cp932') as f:
        reader.data, reader.meta = reader.split_data_meta(f.read().splitlines())
    pd.testing.assert_frame_equal(reader.data['series_value1'], read_data_0, check_dtype=False)
    assert reader.meta['series_meta1'] == read_meta


# meta_handler


def test_parse(tab_input_meta, tab_metadata_def, tab_parse_meta, space_input_meta, space_metadata_def, space_parse_meta):
    """構文解析"""

    # tab区切り
    handler_tab = MetaParser(metadata_def_json_path=tab_metadata_def, config=RDE_CONFIG_YAML)
    _, repeated_meta_info_tab = handler_tab.parse(tab_input_meta)
    assert repeated_meta_info_tab == tab_parse_meta

    # スペース区切り
    handler_space = MetaParser(metadata_def_json_path=space_metadata_def, config=RDE_CONFIG_YAML)
    _, repeated_meta_info_space = handler_space.parse(space_input_meta)
    assert repeated_meta_info_space == space_parse_meta


def test_save_meta(temp_dir, tab_class_meta, tab_parse_meta, tab_output_meta, space_class_meta, space_parse_meta, space_output_meta):
    """csvファイル出力"""
    metadata_def = temp_dir / "metadata-def.json"
    save_path = temp_dir / "metadata.json"

    # tab区切り
    repeated_meta_info_tab = tab_parse_meta
    handler_tab = MetaParser(metadata_def_json_path=metadata_def, config=RDE_CONFIG_YAML)
    _ = handler_tab.save_meta(save_path, tab_class_meta, repeated_meta_info=repeated_meta_info_tab)
    assert os.path.exists(save_path)
    with open(save_path, "r", encoding="utf-8") as f:
        contents_tab = json.load(f)
    assert contents_tab == tab_output_meta
    if os.path.exists(save_path):
        os.remove(save_path)

    # スペース区切り
    repeated_meta_info_space = space_parse_meta
    handler_space = MetaParser(metadata_def_json_path=metadata_def, config=RDE_CONFIG_YAML)
    _ = handler_space.save_meta(save_path, space_class_meta, repeated_meta_info=repeated_meta_info_space)
    assert os.path.exists(save_path)
    with open(save_path, "r", encoding="utf-8") as f:
        contents_space = json.load(f)
    assert contents_space == space_output_meta
    if os.path.exists(save_path):
        os.remove(save_path)
