import os
import pytest
from pathlib import Path
import yaml

from rdetoolkit.exceptions import StructuredError
from rdetoolkit.models.rde2types import RdeOutputResourcePath

from dynamic_factory import DynamicFactory, get_classes, get_scale_types
from file_formats.file import ScaleType
from file_formats.ras_rigaku_file import FileReader as RasFileReader
from file_formats.ras_rigaku_file import MetaParser as RasMetaParser
from file_formats.rasx_rigaku_file import FileReader as RasxFileReader
from file_formats.rasx_rigaku_file import MetaParser as RasxMetaParser
from file_formats.txt_rigaku_file import FileReader as TxtFileReader
from file_formats.txt_rigaku_file import MetaParser as TxtMetaParser
#from file_formats.uxd_bruker_file import FileReader as UxdFileReader
#from file_formats.uxd_bruker_file import MetaParser as UxdMetaParser


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
def resource_paths(temp_dir):
    return RdeOutputResourcePath(
        raw=Path('tests'),
        nonshared_raw=Path('tests'),
        rawfiles=(Path('tests/inputdata/test.ras'),),
        struct=temp_dir,
        main_image=Path('tests'),
        other_image=Path('tests'),
        meta=Path('tests'),
        thumbnail=Path('tests'),
        logs=Path('tests'),
        invoice=Path('tests'),
        invoice_schema_json=Path('tests'),
        invoice_org=Path('tests')
    )


INPUT_FILE = Path('tests/inputdata/test.ras')


def test_get_config(temp_dir, resource_paths):
    """コンフィグ取得"""

    # 正常
    with open(temp_dir / 'rdeconfig.yaml', 'w') as fw:
        yaml.dump(RDE_CONFIG_YAML, fw, default_flow_style=False)
    config, processing_file = DynamicFactory.get_config(resource_paths, temp_dir)
    assert config == RDE_CONFIG_YAML
    assert processing_file == INPUT_FILE

    # 設定ファイル読み込みエラー
    with open(temp_dir / 'rdeconfig.yaml', 'w') as fe:
        fe.write("!!python/name:module.function")
    with pytest.raises(StructuredError) as e:
        DynamicFactory.get_config(resource_paths, temp_dir)
    assert str(e.value).startswith("Invalid configuration file")

    # 設定ファイルなし
    if os.path.exists(temp_dir / 'rdeconfig.yaml'):
        os.remove(temp_dir / 'rdeconfig.yaml')
    with pytest.raises(StructuredError) as e:
        DynamicFactory.get_config(resource_paths, temp_dir)
    assert str(e.value).startswith("File not found")


def test_get_objects(temp_dir):
    """使用クラス取得"""

    # 正常
    with open(temp_dir / 'rdeconfig.yaml', 'w') as fw:
        yaml.dump(RDE_CONFIG_YAML, fw, default_flow_style=False)
    metadata_def, module = DynamicFactory.get_objects(INPUT_FILE, temp_dir, RDE_CONFIG_YAML)
    assert metadata_def.name == "metadata-def_rigaku_ras.json"
    assert str(module.invoice_writer).startswith('<file_formats.file.BaseInvoiceWriter')
    assert str(module.file_reader).startswith('<file_formats.ras_rigaku_file.FileReader')
    assert str(module.meta_parser).startswith('<file_formats.ras_rigaku_file.MetaParser')
    assert str(module.graph_plotter).startswith('<file_formats.file.BaseGraphPlotter')
    assert str(module.structured_processor).startswith('<file_formats.file.BaseStructuredDataProcessor')

    # 拡張子対象外
    with pytest.raises(StructuredError) as e:
        DynamicFactory.get_objects(Path('tests/inputdata/test.raw'), temp_dir, RDE_CONFIG_YAML)
    assert str(e.value) == "Format Error: Input data extension is incorrect: .raw"


@pytest.mark.parametrize(
    ["manufacturer", "suffix", "expected"],
    [
        ("rigaku", ".ras", (RasFileReader, RasMetaParser)),
        ("rigaku", ".rasx", (RasxFileReader, RasxMetaParser)),
        ("rigaku", ".txt", (TxtFileReader, TxtMetaParser))
    ]
)
def test_get_classes(manufacturer, suffix, expected):
    """使用クラス取得"""

    # 正常
    assert get_classes(manufacturer, suffix) == expected

    # エラー
    with pytest.raises(StructuredError) as e:
        get_classes("unknown_manufacturer", ".raw")
    assert str(e.value) == "Unsupported combination of manufacturer 'unknown_manufacturer' and file extension '.raw'"


@pytest.mark.parametrize(
    ["input", "expected"],
    [
        ("log", (ScaleType.log, ScaleType.linear)),
        (None, (ScaleType.linear, ScaleType.log))
    ]
)
def test_scale_types(input, expected):
    """スケール種別取得"""
    assert get_scale_types(input) == expected
