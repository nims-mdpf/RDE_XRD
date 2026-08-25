import json
import os
import pytest
import pandas as pd
from pathlib import Path
import shutil
from typing import Final

from rdetoolkit.models.rde2types import RdeOutputResourcePath
from rdetoolkit.exceptions import StructuredError

from file_formats.file import BaseFileReader
from file_formats.file import BaseStructuredDataProcessor
from file_formats.file import BaseGraphPlotter
from file_formats.file  import ScaleType
from file_formats.file import BaseInvoiceWriter

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
def input_tab_file(temp_dir):
    """タブ区切りファイル作成"""
    data = [
        "Sample\t202401_MS99",
        "Comments\t ",
        "Filename\tC:\Data\Xrd\2020\202401\202401_MS99_2��_��.raw",
        "Goniometer\tMiniFlex 300/600 +",
        "Attachment\t�W��������",
        "Monochromater\tNone",
        "X\t0",
        "Y\t0",
        "Z\t0",
        "ScanningMode\t2Theta/Theta",
        "ScanningType\tContinuos Scanning",
        "X-Ray\t30kV/10mA",
        "IHS\t10.0mm",
        "DS\t0.625deg",
        "SS\t8.0mm",
        "RS\t13.0mm(Open)",
        "None\t",
        "Start\t10",
        "Stop\t60",
        "Step\t0.01",
        "Speed\t3",
        "Offset\t0",
        "TempUnit\tCelsius",
        "StartTime\t2024/01/31\t14:38:41",
        "StartTemp\t0",
        "StopTime\t2024/01/31\t14:57:15",
        "StopTemp\t0",
        "10\t2740",
        "10.01\t2700",
        "10.02\t2740",
        "10.03\t2705",
        "10.04\t2645",
        "10.05\t2750",
        "10.06\t2770",
        "10.07\t2710",
        "10.08\t2695",
        "10.09\t2730"
    ]

    file_path = temp_dir / "input_tab_file.TXT"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(data))

    yield file_path

    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture
def input_space_file(temp_dir):
    """スペース区切りファイル作成"""
    data = [
        "Sample 202401_MS99",
        "Comments  ",
        "Filename C:\Data\Xrd\2020\202401\202401_MS99_2��_��.raw",
        "Goniometer MiniFlex 300/600 +",
        "Attachment �W��������",
        "Monochromater None",
        "X 0",
        "Y 0",
        "Z 0",
        "ScanningMode 2Theta/Theta",
        "ScanningType Continuos Scanning",
        "X-Ray 30kV/10mA",
        "IHS 10.0mm",
        "DS 0.625deg",
        "SS 8.0mm",
        "RS 13.0mm(Open)",
        "None ",
        "Start 10",
        "Stop 60",
        "Step 0.01",
        "Speed 3",
        "Offset 0",
        "TempUnit Celsius",
        "StartTime 2024/01/31 14:38:41",
        "StartTemp 0",
        "StopTime 2024/01/31 14:57:15",
        "StopTemp 0",
        "10 2740",
        "10.01 2700",
        "10.02 2740",
        "10.03 2705",
        "10.04 2645",
        "10.05 2750",
        "10.06 2770",
        "10.07 2710",
        "10.08 2695",
        "10.09 2730"
    ]

    file_path = temp_dir / "input_space_file.TXT"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(data))

    yield file_path

    if os.path.exists(file_path):
        os.remove(file_path)

@pytest.fixture
def resource_paths_structerd(temp_dir):
    return RdeOutputResourcePath(
        raw=Path('tests'),
        nonshared_raw=Path('tests'),
        rawfiles=(temp_dir,),
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

@pytest.fixture
def resource_paths_graph(temp_dir):
    return RdeOutputResourcePath(
        raw=Path('tests'),
        nonshared_raw=Path('tests'),
        rawfiles=(Path('tests'),),
        struct=temp_dir,
        main_image=temp_dir,
        other_image=temp_dir,
        meta=Path('tests'),
        thumbnail=Path('tests'),
        logs=Path('tests'),
        invoice=Path('tests'),
        invoice_schema_json=Path('tests'),
        invoice_org=Path('tests')
    )

@pytest.fixture
def resource_paths_invoice(temp_dir):
    return RdeOutputResourcePath(
        raw=Path('tests'),
        nonshared_raw=Path('tests'),
        rawfiles=(Path('tests'),),
        struct=Path('tests'),
        main_image=Path('tests'),
        other_image=Path('tests'),
        meta=Path('tests'),
        thumbnail=Path('tests'),
        logs=Path('tests'),
        invoice=temp_dir,
        invoice_schema_json=Path('tests/inputdata/invoice.schema.json'),
        invoice_org=temp_dir / 'invoice.json'
    )

@pytest.fixture
def read_data():
    return pd.DataFrame({
        "2Theta-Theta (deg)": [25.00, 25.01, 25.02, 25.03, 25.04],
        "Intensity (counts)": [13.0, 7.0, 12.0, 6.0, 3.0]
    })

@pytest.fixture
def read_meta():
    """サンプルの出力メタデータ"""
    return {
        'MEAS_SCAN_START_TIME': '11/21/2017 08:32:31'
    }


## inputfile_handler


def test_determine_delimiter(input_tab_file, input_space_file):
    """タブ・スペース区切り判定テスト"""

    assert BaseFileReader.determine_delimiter(input_tab_file) == "\t"
    assert BaseFileReader.determine_delimiter(input_space_file) == " "


## structured_handler


def test_save_csv_ras(temp_dir, resource_paths_structerd, read_data):
    """csv出力(rasファイル向け)"""
    resource_paths_structerd.rawfiles = ((temp_dir / "test.ras"),)
    processor = BaseStructuredDataProcessor()

    processor.save_csv(resource_paths_structerd, resource_paths_structerd.rawfiles[0], read_data, region_num=SINGLE_REGION_NUM)

    df = pd.read_csv(resource_paths_structerd.struct.joinpath("test.csv"), header=0)
    assert df.columns.to_list() == ['2Theta-Theta (deg)', 'Intensity (counts)']
    assert df.iloc[0, :].to_list() == [25.00, 13.0]


def test_save_csv_rasx(temp_dir, resource_paths_structerd, read_data):
    """csv出力(rasxファイル向け)と不随ファイル展開"""
    resource_paths_structerd.rawfiles = ((temp_dir / "test.rasx"),)
    compressd_files: list[str] = ['Data0/Profile0.txt', 'Data0/MesurementConditions0.xml']
    shutil.copy(Path("tests/inputdata/test.rasx"), (temp_dir / "test.rasx"))
    processor = BaseStructuredDataProcessor()

    processor.save_csv(resource_paths_structerd, resource_paths_structerd.rawfiles[0], read_data, region_num=SINGLE_REGION_NUM)
    processor.save_structured_contents(resource_paths_structerd, resource_paths_structerd.rawfiles[0], compressd_files)

    df = pd.read_csv(resource_paths_structerd.struct.joinpath("test.csv"), header=0)
    assert df.columns.to_list() == ['2Theta-Theta (deg)', 'Intensity (counts)']
    assert df.iloc[0, :].to_list() == [25.00, 13.0]
    assert (temp_dir / "Profile0.txt").exists(), "There are no involuntary files."
    assert (temp_dir / "MesurementConditions0.xml").exists(), "There are no involuntary files."


## graph_handler


def test_plot_main(temp_dir, resource_paths_graph, read_data):
    """プロット（シングルリージョン・マルチリージョン）呼び出し元"""
    resource_paths_graph.rawfiles = ((temp_dir / "test.ras"),)
    plotter = BaseGraphPlotter(ScaleType.linear, ScaleType.log)

    # single regsion
    plotter.plot_main(read_data, resource_paths_graph, resource_paths_graph.rawfiles[0], 1)
    main_image = temp_dir / "test.png"
    other_image = temp_dir / "test_log.png"
    html = temp_dir / "test.html"
    assert main_image.exists(), "The plot was not saved correctly."
    assert other_image.exists(), "The plot was not saved correctly."
    assert html.exists(), "The plot was not saved correctly."
    if os.path.exists(main_image):
        os.remove(main_image)
    if os.path.exists(other_image):
        os.remove(other_image)
    if os.path.exists(html):
        os.remove(html)

    # multi regsion
    plotter.plot_main(read_data, resource_paths_graph, resource_paths_graph.rawfiles[0], 2)
    other_image_1 = temp_dir / "test_1.png"
    other_image_1_log = temp_dir / "test_1_log.png"
    html_1 = temp_dir / "test_1.html"
    assert other_image_1.exists(), "The plot was not saved correctly."
    assert other_image_1_log.exists(), "The plot was not saved correctly."
    assert html_1.exists(), "The plot was not saved correctly."
    if os.path.exists(other_image_1):
        os.remove(other_image_1)
    if os.path.exists(other_image_1_log):
        os.remove(other_image_1_log)
    if os.path.exists(html_1):
        os.remove(html_1)


def test_multiplot_main(temp_dir, resource_paths_graph, read_data):
    """マルチリージョン合成プロット呼び出し元"""
    resource_paths_graph.rawfiles = ((temp_dir / "test.ras"),)

    # Scale: linear
    plotter_linear = BaseGraphPlotter(ScaleType.linear, ScaleType.log)
    plotter_linear._set_multi_dataset(read_data)
    plotter_linear._set_multi_dataset(read_data)  # Create a pseudo 'Multi-region'
    plotter_linear.multiplot_main(resource_paths_graph, resource_paths_graph.rawfiles[0])
    main_image_linear = temp_dir / "test.png"
    assert main_image_linear.exists(), "The plot was not saved correctly."
    if os.path.exists(main_image_linear):
        os.remove(main_image_linear)

    # Scale: log
    plotter_log = BaseGraphPlotter(ScaleType.log, ScaleType.linear)
    plotter_log._set_multi_dataset(read_data)
    plotter_log._set_multi_dataset(read_data)  # Create a pseudo 'Multi-region'
    plotter_log.multiplot_main(resource_paths_graph, resource_paths_graph.rawfiles[0])
    main_image_log = temp_dir / "test_log.png"
    assert main_image_log.exists(), "The plot was not saved correctly."
    if os.path.exists(main_image_log):
        os.remove(main_image_log)


def test_plot(temp_dir, read_data):
    """プロット"""
    # Scale: linear
    plotter_linear = BaseGraphPlotter(ScaleType.linear, ScaleType.log)
    html_linear = temp_dir / "test.html"
    main_image_linear = temp_dir / "test.png"
    plotter_linear.plot(read_data, html_linear, main_image_linear, title="Linear", scale=ScaleType.linear)
    assert main_image_linear.exists(), "The plot was not saved correctly."
    assert html_linear.exists(), "The plot was not saved correctly."
    if os.path.exists(main_image_linear):
        os.remove(main_image_linear)

    # Scale: log
    plotter_log = BaseGraphPlotter(ScaleType.linear, ScaleType.log)
    html_log = temp_dir / "HOGE.html"
    main_image_log = temp_dir / "test.png"
    plotter_log.plot(read_data, html_log, main_image_log, title="Linear", scale=ScaleType.log)
    assert main_image_log.exists(), "The plot was not saved correctly."
    if os.path.exists(main_image_log):
        os.remove(main_image_log)


def test_multiplot(temp_dir, read_data):
    """マルチリージョン合成プロット"""
    main_image = temp_dir / "test.png"

    # error (no data)
    plotter = BaseGraphPlotter(ScaleType.linear, ScaleType.log)
    with pytest.raises(StructuredError):
        plotter.multiplot(main_image, title="Multi", scale=ScaleType.log)

    # error (single region)
    plotter._set_multi_dataset(read_data)
    with pytest.raises(StructuredError):
        plotter.multiplot(main_image, title="Multi", scale=ScaleType.log)

    # nomal (multi region)
    plotter._set_multi_dataset(read_data)  # Pseudo 'Multi-region'
    plotter.multiplot(main_image, title="Multi", scale=ScaleType.log)
    assert main_image.exists(), "The plot was not saved correctly."
    if os.path.exists(main_image):
        os.remove(main_image)


def test_set_title_from_filename(temp_dir, resource_paths_graph):
    """タイトル名取得テスト"""
    resource_paths_graph.rawfiles = ((temp_dir / "test.ras"),)
    plotter = BaseGraphPlotter(ScaleType.linear, ScaleType.log)

    assert plotter.set_title_from_filename(resource_paths_graph.main_image.joinpath(f"{resource_paths_graph.rawfiles[0].stem}.png")) == "test"


## invoice_handler


def test_overwrite_invoice_measured_date(resource_paths_invoice, read_meta):
    """計測日上書き"""
    writer = BaseInvoiceWriter(RDE_CONFIG_YAML)
    resource_paths_invoice.rawfiles = (Path('tests/inputdata/test.ras'),)
    data_invoice = {
        'custom': {'measurement_measured_date': None},
        'sample': {'sampleId': 'e3cf4c72-4c2c-4430-9916-3edbddbaeaf5', 'names': ['']}
    }

    # 正常(標準)
    with open(resource_paths_invoice.invoice_org, 'w') as fw:
        json.dump(data_invoice, fw)
    writer.overwrite_invoice_measured_date(resource_paths_invoice, resource_paths_invoice.rawfiles[0].suffix, read_meta, read_meta)
    with open(resource_paths_invoice.invoice.joinpath("invoice.json")) as fr:
        assert json.load(fr) == {
            'custom': {'measurement_measured_date': '2017-11-21'},
            'sample': {'sampleId': 'e3cf4c72-4c2c-4430-9916-3edbddbaeaf5', 'names': ['']}
        }

    # データ変更なし
    with open(resource_paths_invoice.invoice_org, 'w') as fw:
        json.dump(data_invoice, fw)
    writer.overwrite_invoice_measured_date(resource_paths_invoice, resource_paths_invoice.rawfiles[0].suffix, {}, {})
    with open(resource_paths_invoice.invoice.joinpath("invoice.json")) as fr:
        assert json.load(fr) == {
            'custom': {'measurement_measured_date': None},
            'sample': {'sampleId': 'e3cf4c72-4c2c-4430-9916-3edbddbaeaf5', 'names': ['']}
        }

    if os.path.exists(resource_paths_invoice.invoice_org):
        os.remove(resource_paths_invoice.invoice_org)


def test_overwrite_invoice_sample_name(resource_paths_invoice):
    "試料名上書き"
    writer = BaseInvoiceWriter(RDE_CONFIG_YAML)
    with open(resource_paths_invoice.invoice_org, 'w') as fw:
        json.dump({'sample': {'sampleId': 'e3cf4c72-4c2c-4430-9916-3edbddbaeaf5', 'names': ['']}}, fw)

    # 正常(標準)
    resource_paths_invoice.rawfiles = (Path('tests/inputdata/test_material.ras'),)
    writer.overwrite_invoice_sample_name(resource_paths_invoice)
    with open(resource_paths_invoice.invoice.joinpath("invoice.json")) as fr:
        assert json.load(fr) == {'sample': {'sampleId': None, 'names': ['material']}}

    # ファイル名異常
    resource_paths_invoice.rawfiles = (Path('tests/inputdata/test.ras'),)
    with pytest.raises(StructuredError) as e:
        writer.overwrite_invoice_sample_name(resource_paths_invoice)
    assert str(e.value).startswith("Invalid Filename Error: A file without delimiters has been inputted.")

    if os.path.exists(resource_paths_invoice.invoice_org):
        os.remove(resource_paths_invoice.invoice_org)
