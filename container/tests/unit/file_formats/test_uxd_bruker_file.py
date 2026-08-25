import json
import os
from pathlib import Path
import pandas as pd
import pytest
from typing import Final

from rdetoolkit.exceptions import StructuredError
from rdetoolkit.rde2util import Meta

from file_formats.uxd_bruker_file import FileReader, MetaParser


INPUT_FILE = Path('tests/inputdata/test.uxd')
SINGLE_REGION_NUM: Final[int] = 1
RDE_CONFIG_YAML: dict = {
    "system": {
        'magic_variable': True,
        'save_thumbnail_image': True,
    },
    "xrd": {
        'filename_mapping_rule': True,
        'manufacturer': 'bruker',
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
        "2THETA ": [12.0, 12.020367, 12.040734, 12.061102, 12.081469],
        "Intensity ": [305.0, 343.0, 339.0, 365.0, 390.0]
    })


@pytest.fixture
def read_data_0():
    return pd.DataFrame({
        "2THETA ": ['12.000000', '12.020367', '12.040734', '12.061102', '12.081469'],
        "Intensity ": ['305.000000', '343.000000', '339.000000', '365.000000', '390.000000']
    })


@pytest.fixture
def read_meta():
    return {
        ';content of 2018 08 25 Hoge 150 12h.raw - (Diff Plus V4 file)': '',
        '_FILEVERSION': '3',
        '_SAMPLE': 'Commander Sample ID',
        '_USER': 'Lab Manager',
        '_GONIOMETER_CODE': '14',
        '_STAGE_CODE': '7',
        '; Goniometer : D8 theta/theta, stage : Chi drive': '',
        '_SAMPLE_CHANGER_CODE': '0',
        '_ATTACHMENTS_CODE': '0',
        '_GONIOMETER_RADIUS': '140',
        '_SOLLER_SLITS': '2',
        '_MONOCHROMATOR': '0',
        '; Incident beam monochromator : None': '',
        '_SOLLER_SLITS_2': '2',
        '_BETA_FILTER': 'N',
        '_ANALYZER_CODE': '0',
        '; Received beam analyzer : None': '',
        '_DATEMEASURED': '26-Aug-2018 15:22:22',
        '_RUNTIME': '16.45212',
        '_WL_UNIT': 'A',
        '_WL1': '1.54001',
        '_WL2': '1.54402',
        '_WL3': '1.39203',
        '_WLRATIO': '0.5',
        '_ANODE': 'Cu',
        '_V4_INF_USER': 'Lab Manager',
        '_V4_INF_SAMPLEID': 'Commander Sample ID',
        '_V4_INF_CREATOR': 'V5Converter',
        '_V4_INF_CREATOR_VERSION': '3.1.23.0',
        '; Data for range 1': '',
        '_DRIVE': 'COUPLED',
        '_STEPTIME': '57.1',
        '_STEPSIZE': '0.020312',
        '_STEPMODE': 'C',
        '_START': '12',
        '_THETA': '6',
        '_2THETA': '12',
        '_DETECTORSLIT': 'out',
        '_AUX1': '0',
        '_AUX2': '0',
        '_TIMESTARTED': '0',
        '_ROTATION_SPEED': '10',
        '_KV': '40',
        '_MA': '20',
        '_RANGE_WL': '1.5406',
        '_3DPLANE': '0',
        '_V4_PSD2THETA': '9999',
        '_V4_PSDCHANNEL1': '0',
        '_V4_PSDAPERTURE': '2.932812',
        '_V4_PSDTYPE': '5',
        '_V4_PSDFIXED': '0',
        '_V4_COUNTERS_MASK': '1',
        '_V4_DRIVES_MASK': '0',
        '_V4_ENCODERS_MASK': '0',
        '_2THETACOUNTS': '1'
    }


@pytest.fixture
def metadata_def(tmp_path):
    """サンプルのmetadata-def.json"""
    metadata_def = {
        "uxd.comment": {
            "name": {
                "ja": "コメント",
                "en": "Comment"
            },
            "schema": {
                "type": "string"
            },
            "order": 1,
            "mode": "uxd形式",
            "originalName": ";contentof",
            "variable": 1
        },
        "uxd.selected_detector_name": {
            "name": {
                "ja": "使用検出器名称",
                "en": "Selected Detector Name"
            },
            "schema": {
                "type": "string"
            },
            "order": 2,
            "mode": "uxd形式",
            "originalName": ";Goniometer",
            "variable": 1
        },
        "uxd.x-ray_target_material": {
            "name": {
                "ja": "X線ターゲットの材質",
                "en": "X-ray Target Material"
            },
            "schema": {
                "type": "string"
            },
            "order": 3,
            "mode": "uxd形式",
            "originalName": "_ANODE",
            "variable": 1
        },
        "uxd.k_alpha_1_wavelength": {
            "name": {
                "ja": "K_alpha1の波長",
                "en": "K_alpha_1 Wavelength"
            },
            "schema": {
                "type": "number"
            },
            "order": 4,
            "mode": "uxd形式",
            "originalName": "_WL1",
            "variable": 1
        },
        "uxd.k_alpha_2_wavelength": {
            "name": {
                "ja": "K_alpha2の波長",
                "en": "K_alpha_2 Wavelength"
            },
            "schema": {
                "type": "number"
            },
            "order": 5,
            "mode": "uxd形式",
            "originalName": "_WL2",
            "variable": 1
        },
        "uxd.ratio_k_alpha_2/k_alpha_1": {
            "name": {
                "ja": "K_alpha2/K_alpha1の比率",
                "en": "Ratio K_Alpha_2/K_Alpha_1"
            },
            "schema": {
                "type": "number"
            },
            "order": 6,
            "mode": "uxd形式",
            "originalName": "_WLRATIO",
            "variable": 1
        },
        "uxd.x-ray_tube_current": {
            "name": {
                "ja": "X線管電流",
                "en": "X-ray Tube Current"
            },
            "schema": {
                "type": "number"
            },
            "order": 7,
            "unit": "mA",
            "mode": "uxd形式",
            "originalName": "_MA",
            "variable": 1
        },
        "uxd.x-ray_tube_voltage": {
            "name": {
                "ja": "X線管電圧",
                "en": "X-ray Tube Voltage"
            },
            "schema": {
                "type": "number"
            },
            "order": 8,
            "unit": "kV",
            "mode": "uxd形式",
            "originalName": "_KV",
            "variable": 1
        },
        "uxd.scan_mode": {
            "name": {
                "ja": "スキャンモード",
                "en": "Scan Mode"
            },
            "schema": {
                "type": "string"
            },
            "order": 9,
            "mode": "uxd形式",
            "originalName": "_STEPMODE",
            "variable": 1
        },
        "uxd.scan_step_size": {
            "name": {
                "ja": "スキャンステップサイズ",
                "en": "Scan Step Size"
            },
            "schema": {
                "type": "number"
            },
            "order": 10,
            "mode": "uxd形式",
            "originalName": "_STEPSIZE",
            "variable": 1
        },
        "uxd.scan_starting_position": {
            "name": {
                "ja": "スキャン開始位置",
                "en": "Scan Starting Position"
            },
            "schema": {
                "type": "number"
            },
            "order": 11,
            "mode": "uxd形式",
            "originalName": "_START",
            "variable": 1
        },
        "uxd.monochromator": {
            "name": {
                "ja": "分光器",
                "en": "Monochromator"
            },
            "schema": {
                "type": "string"
            },
            "order": 12,
            "mode": "uxd形式",
            "originalName": ";Incident",
            "variable": 1
        },
        "uxd.aperture_width_of_1d_position_sensitive_detector(deg)": {
            "name": {
                "ja": "1次元検出器 開口幅（度）",
                "en": "Aperture width of 1D Position Sensitive Detector(deg)"
            },
            "schema": {
                "type": "number"
            },
            "order": 13,
            "unit": "deg",
            "mode": "uxd形式",
            "originalName": "_V4_PSDAPERTURE",
            "variable": 1
        },
        "uxd.measurement_instrument_name": {
            "name": {
                "ja": "測定装置名",
                "en": "Measurement Instrument name"
            },
            "schema": {
                "type": "string"
            },
            "order": 14,
            "mode": "uxd形式",
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
    """サンプルの入力メタデータ"""
    return {
        ';content of 2018 08 25 Hoge 150 12h.raw - (Diff Plus V4 file)': '',
        '_FILEVERSION': '3',
        '_SAMPLE': 'Commander Sample ID',
        '_USER': 'Lab Manager',
        '_GONIOMETER_CODE': '14',
        '_STAGE_CODE': '7',
        '; Goniometer : D8 theta/theta, stage : Chi drive': '',
        '_SAMPLE_CHANGER_CODE': '0',
        '_ATTACHMENTS_CODE': '0',
        '_GONIOMETER_RADIUS': '140',
        '_SOLLER_SLITS': '2',
        '_MONOCHROMATOR': '0',
        '; Incident beam monochromator : None': '',
        '_SOLLER_SLITS_2': '2',
        '_BETA_FILTER': 'N',
        '_ANALYZER_CODE': '0',
        '; Received beam analyzer : None': '',
        '_DATEMEASURED': '26-Aug-2018 15:22:22',
        '_RUNTIME': '16.45212',
        '_WL_UNIT': 'A',
        '_WL1': '1.54001',
        '_WL2': '1.54402',
        '_WL3': '1.39203',
        '_WLRATIO': '0.5',
        '_ANODE': 'Cu',
        '_V4_INF_USER': 'Lab Manager',
        '_V4_INF_SAMPLEID': 'Commander Sample ID',
        '_V4_INF_CREATOR': 'V5Converter',
        '_V4_INF_CREATOR_VERSION': '3.1.23.0',
        '; Data for range 1': '',
        '_DRIVE': 'COUPLED',
        '_STEPTIME': '57.1',
        '_STEPSIZE': '0.020312',
        '_STEPMODE': 'C',
        '_START': '12',
        '_THETA': '6',
        '_2THETA': '12',
        '_DETECTORSLIT': 'out',
        '_AUX1': '0',
        '_AUX2': '0',
        '_TIMESTARTED': '0',
        '_ROTATION_SPEED': '10',
        '_KV': '40',
        '_MA': '20',
        '_RANGE_WL': '1.5406',
        '_3DPLANE': '0',
        '_V4_PSD2THETA': '9999',
        '_V4_PSDCHANNEL1': '0',
        '_V4_PSDAPERTURE': '2.932812',
        '_V4_PSDTYPE': '5',
        '_V4_PSDFIXED': '0',
        '_V4_COUNTERS_MASK': '1',
        '_V4_DRIVES_MASK': '0',
        '_V4_ENCODERS_MASK': '0',
        '_2THETACOUNTS': '1'
    }


@pytest.fixture
def parse_meta():
    """サンプルの出力メタデータ"""
    return {
        ';contentof': ['2018 08 25 Hoge 150 12h.raw - (Diff Plus V4 file)'],
        '_FILEVERSION': ['3'],
        '_SAMPLE': ['Commander Sample ID'],
        '_USER': ['Lab Manager'],
        '_GONIOMETER_CODE': ['14'],
        '_STAGE_CODE': ['7'],
        ';Goniometer': [': D8 theta/theta, stage : Chi drive'],
        '_SAMPLE_CHANGER_CODE': ['0'],
        '_ATTACHMENTS_CODE': ['0'],
        '_GONIOMETER_RADIUS': ['140'],
        '_SOLLER_SLITS': ['2'],
        '_MONOCHROMATOR': ['0'],
        ';Incident': ['beam monochromator : None'],
        '_SOLLER_SLITS_2': ['2'],
        '_BETA_FILTER': ['N'],
        '_ANALYZER_CODE': ['0'],
        '': ['', ''],  # MEMO: Not applicable to output.(Received beam analyzer, Data for range)
        '_DATEMEASURED': ['26-Aug-2018 15:22:22'],
        '_RUNTIME': ['16.45212'],
        '_WL_UNIT': ['A'],
        '_WL1': ['1.54001'],
        '_WL2': ['1.54402'],
        '_WL3': ['1.39203'],
        '_WLRATIO': ['0.5'],
        '_ANODE': ['Cu'],
        '_V4_INF_USER': ['Lab Manager'],
        '_V4_INF_SAMPLEID': ['Commander Sample ID'],
        '_V4_INF_CREATOR': ['V5Converter'],
        '_V4_INF_CREATOR_VERSION': ['3.1.23.0'],
        '_DRIVE': ['COUPLED'],
        '_STEPTIME': ['57.1'],
        '_STEPSIZE': ['0.020312'],
        '_STEPMODE': ['C'],
        '_START': ['12'],
        '_THETA': ['6'],
        '_2THETA': ['12'],
        '_DETECTORSLIT': ['out'],
        '_AUX1': ['0'],
        '_AUX2': ['0'],
        '_TIMESTARTED': ['0'],
        '_ROTATION_SPEED': ['10'],
        '_KV': ['40'],
        '_MA': ['20'],
        '_RANGE_WL': ['1.5406'],
        '_3DPLANE': ['0'],
        '_V4_PSD2THETA': ['9999'],
        '_V4_PSDCHANNEL1': ['0'],
        '_V4_PSDAPERTURE': ['2.932812'],
        '_V4_PSDTYPE': ['5'],
        '_V4_PSDFIXED': ['0'],
        '_V4_COUNTERS_MASK': ['1'],
        '_V4_DRIVES_MASK': ['0'],
        '_V4_ENCODERS_MASK': ['0'],
        '_2THETACOUNTS': ['1']
    }


@pytest.fixture
def output_meta():
    """ファイル出力後メタデータ"""
    return {
        "constant": {},
        "variable": [{
            'uxd.comment': {'value': '2018 08 25 Hoge 150 12h.raw - (Diff Plus V4 file)'},
            'uxd.selected_detector_name': {'value': ': D8 theta/theta, stage : Chi drive'},
            'uxd.x-ray_target_material': {'value': 'Cu'},
            'uxd.k_alpha_1_wavelength': {'value': 1.54001},
            'uxd.k_alpha_2_wavelength': {'value': 1.54402},
            'uxd.ratio_k_alpha_2/k_alpha_1': {'value': 0.5},
            'uxd.x-ray_tube_current': {'value': 20, 'unit': 'mA'},
            'uxd.x-ray_tube_voltage': {'value': 40, 'unit': 'kV'},
            'uxd.scan_mode': {'value': 'C'},
            'uxd.scan_step_size': {'value': 0.020312},
            'uxd.scan_starting_position': {'value': 12},
            'uxd.monochromator': {'value': 'beam monochromator : None'},
            'uxd.aperture_width_of_1d_position_sensitive_detector(deg)': {'value': 2.932812, 'unit': 'deg'}

        }]
    }


## inputfile_handler

def test_read(read_data, read_meta, temp_dir):
    """ファイル読み込み"""

    # 正常(標準)
    reader = FileReader(RDE_CONFIG_YAML)
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
    assert data['2THETA '].dtypes == 'float64'
    assert data['Intensity '].dtypes == 'float64'


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


def test_split_data_meta(read_data_0, read_meta):
    """データとメタの分離"""
    reader = FileReader(RDE_CONFIG_YAML)

    with open(INPUT_FILE, encoding='cp932') as f:
        reader.data, reader.meta = reader.split_data_meta(f.read().splitlines())
    pd.testing.assert_frame_equal(reader.data['series_value1'], read_data_0, check_dtype=False)
    assert reader.meta['series_meta1'] == read_meta


# meta_handler


def test_parse(input_meta, metadata_def, parse_meta):
    """構文解析"""

    handler = MetaParser(metadata_def_json_path=metadata_def, config=RDE_CONFIG_YAML)
    _, repeated_meta_info = handler.parse(input_meta)
    assert repeated_meta_info == parse_meta


def test_save_meta(temp_dir, class_meta, parse_meta, output_meta):
    """csvファイル出力"""
    metadata_def = temp_dir / "metadata-def.json"
    save_path = temp_dir / "metadata.json"

    repeated_meta_info = parse_meta
    handler = MetaParser(metadata_def_json_path=metadata_def, config=RDE_CONFIG_YAML)
    _ = handler.save_meta(save_path, class_meta, repeated_meta_info=repeated_meta_info)
    assert os.path.exists(save_path)
    with open(save_path, "r", encoding="utf-8") as f:
        contents = json.load(f)
    assert contents == output_meta
    if os.path.exists(save_path):
        os.remove(save_path)
