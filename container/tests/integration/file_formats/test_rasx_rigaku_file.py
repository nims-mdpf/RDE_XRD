import json
import os
import shutil
from typing import List, Union


def setup_inputdata_folder(inputdata_name: Union[str, List[str]], manufacturer: str, case_name: str):
    """テスト実行のためのヘルパー関数
    テスト用でdataフォルダ群の作成とrawファイルの準備

    Args:
        inputdata_name (Union[str, List[str]]): rawファイル名
    """
    destination_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
    os.makedirs(destination_path, exist_ok=True)
    os.makedirs(os.path.join(destination_path, "inputdata"), exist_ok=True)
    os.makedirs(os.path.join(destination_path, "invoice"), exist_ok=True)
    inputdata_original_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "inputdata", manufacturer, case_name
    )
    if isinstance(inputdata_name, List):
        for item in inputdata_name:
            shutil.copy(
                os.path.join(inputdata_original_path, item),
                os.path.join(destination_path, "inputdata"),
            )
    else:
        shutil.copy(
            os.path.join(inputdata_original_path, inputdata_name),
            os.path.join(destination_path, "inputdata"),
        )
    shutil.copy(
        os.path.join(inputdata_original_path, "invoice.json"),
        os.path.join(destination_path, "invoice"),
    )

    # tasksupport
    os.makedirs(os.path.join(destination_path, "tasksupport"), exist_ok=True)
    tasksupport_original_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
        "template",
        manufacturer,
        "tasksupport",
    )
    print(tasksupport_original_path)
    shutil.copy(
        os.path.join(tasksupport_original_path, "invoice.schema.json"),
        os.path.join(destination_path, "tasksupport"),
    )
    shutil.copy(
        os.path.join(tasksupport_original_path, "metadata-def_rigaku_rasx.json"),
        os.path.join(destination_path, "tasksupport"),
    )
    shutil.copy(
        os.path.join(tasksupport_original_path, "rdeconfig.yaml"),
        os.path.join(destination_path, "tasksupport"),
    )


def setup_invoice_json_with_magic_filename(manufacturer: str, case_name: str):
    """テスト実行のためのヘルパー関数
    invoice.jsonのdataNameに${filename}を記述したinvoice.jsonを作成する関数
    invoice.jsonはinputからコピーして生成する
    """
    destination_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
    os.makedirs(destination_path, exist_ok=True)
    os.makedirs(os.path.join(destination_path, "inputdata"), exist_ok=True)
    os.makedirs(os.path.join(destination_path, "invoice"), exist_ok=True)
    inputdata_original_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "inputdata", manufacturer, case_name
    )
    with open(os.path.join(inputdata_original_path, "invoice.json"), mode="r", encoding="utf-8") as f:
        contents = json.load(f)
    contents["basic"]["dataName"] = "${filename}"
    contents["sample"]["names"] = [""]

    with open(os.path.join(inputdata_original_path, "invoice.json"), mode="w", encoding="utf-8") as f:
        json.dump(contents, f, indent=4, ensure_ascii=False)

    shutil.copy(
        os.path.join(inputdata_original_path, "invoice.json"),
        os.path.join(destination_path, "invoice"),
    )


class TestMeta1:
    """case1
    メタデータテスト: 89-1_P.rasx
    """

    input_file: str = "89-1_P.rasx"

    def test_setup(self):
        setup_inputdata_folder(self.input_file, "rigaku", "rasx_basic")

    def test_metadata_constant(self, setup_main, setup_metadatadef_rigaku_rasx_json):
        """constメタのテスト
        metadata.jsonに記載されているkeyをmetadata-def.jsonに定義されているか確認する
        """
        metadata = "metadata.json"
        result_metadata_filepath = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "meta", metadata
        )

        with open(result_metadata_filepath, mode="r", encoding="utf-8") as f:
            contents = json.load(f)

        for k in contents["constant"].keys():
            constant_meta_key = setup_metadatadef_rigaku_rasx_json.get(k)
            assert constant_meta_key

    def test_metadata_variable(self, setup_metadatadef_rigaku_rasx_json):
        """variableメタのテスト
        metadata.jsonに記載されているkeyをmetadata-def.jsonに定義されているか確認する
        単位が抽出されているかテスト(一つも単位が検出されていない場合、テスト失敗)
        """
        metadata = "metadata.json"
        result_metadata_filepath = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "meta", metadata
        )

        with open(result_metadata_filepath, mode="r", encoding="utf-8") as f:
            contents = json.load(f)

        extract_unit_keys = [v.get("unit") for item in contents["variable"] for v in item.values() if v.get("unit")]
        assert len(extract_unit_keys) > 0

        result_variable_keys = [k for item in contents["variable"] for k in item.keys()]
        for k in result_variable_keys:
            print(k)
            # metadata.json: variable
            variable_meta_key = setup_metadatadef_rigaku_rasx_json.get(k)
            # check defined variable = 1
            except_variable_flag = setup_metadatadef_rigaku_rasx_json[k].get("variable")

            assert (all(variable_meta_key)) and (except_variable_flag is not None)


class TestOutputCase1:
    """case1
    単一ファイルのテスト: 89-1_P.rasx
    グラフのスケール: linear(default)
    """

    inputdata: Union[str, List[str]] = "89-1_P.rasx"

    def test_setup(self):
        setup_inputdata_folder(self.inputdata, "rigaku", "rasx_basic")
        setup_invoice_json_with_magic_filename("rigaku", "rasx_basic")

    def test_raw_data(self, setup_main, data_path):
        assert os.path.exists(os.path.join(data_path, "nonshared_raw", "89-1_P.rasx"))

    def test_main_image(self, data_path):
        assert os.path.exists(os.path.join(data_path, "main_image", "89-1_P.png"))

    def test_other_image(self, data_path):
        assert os.path.exists(os.path.join(data_path, "other_image", "89-1_P_log.png"))

    def test_structured(self, data_path):
        assert os.path.exists(os.path.join(data_path, "structured", "89-1_P.csv"))
        assert os.path.exists(os.path.join(data_path, "structured", "Profile0.txt"))
        assert os.path.exists(os.path.join(data_path, "structured", "MesurementConditions0.xml"))

    def test_thumbnail(self, data_path):
        assert os.path.exists(os.path.join(data_path, "thumbnail", "89-1_P.png"))

    def test_meta(self, data_path):
        assert os.path.exists(os.path.join(data_path, "meta", "metadata.json"))


class TestOutputCase2:
    """case2
    エクセルインボイスのテスト:
        "input1.zip"
        "hot_extrusion_excel_invoice.xlsx"
    グラフのスケール: log
    """

    inputdata: Union[str, List[str]] = [
        "input1.zip",
        "hot_extrusion_excel_invoice.xlsx"
    ]

    def test_setup(self):
        setup_inputdata_folder(self.inputdata, "rigaku", "rasx_excel_invoice")
        setup_invoice_json_with_magic_filename("rigaku", "rasx_excel_invoice")

    def test_raw_data(self, setup_main, data_path):
        assert os.path.exists(os.path.join(data_path, "nonshared_raw", "89-1_P.rasx"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "nonshared_raw", "89-3_P.rasx"))
        assert os.path.exists(os.path.join(data_path, "divided", "0002", "nonshared_raw", "89-5_P.rasx"))
        assert os.path.exists(os.path.join(data_path, "divided", "0003", "nonshared_raw", "89-7_P.rasx"))
        assert os.path.exists(os.path.join(data_path, "divided", "0004", "nonshared_raw", "89-10_P.rasx"))

    def test_main_image(self, data_path):
        assert os.path.exists(os.path.join(data_path, "main_image", "89-1_P.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "main_image", "89-3_P.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0002", "main_image", "89-5_P.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0003", "main_image", "89-7_P.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0004", "main_image", "89-10_P.png"))

    def test_other_image(self, data_path):
        assert os.path.exists(os.path.join(data_path, "other_image", "89-1_P_log.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "other_image", "89-3_P_log.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0002", "other_image", "89-5_P_log.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0003", "other_image", "89-7_P_log.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0004", "other_image", "89-10_P_log.png"))

    def test_structured(self, data_path):
        assert os.path.exists(os.path.join(data_path, "structured", "89-1_P.csv"))
        assert os.path.exists(os.path.join(data_path, "structured", "Profile0.txt"))
        assert os.path.exists(os.path.join(data_path, "structured", "MesurementConditions0.xml"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "structured", "89-3_P.csv"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "structured", "Profile0.txt"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "structured", "MesurementConditions0.xml"))
        assert os.path.exists(os.path.join(data_path, "divided", "0002", "structured", "89-5_P.csv"))
        assert os.path.exists(os.path.join(data_path, "divided", "0002", "structured", "Profile0.txt"))
        assert os.path.exists(os.path.join(data_path, "divided", "0002", "structured", "MesurementConditions0.xml"))
        assert os.path.exists(os.path.join(data_path, "divided", "0003", "structured", "89-7_P.csv"))
        assert os.path.exists(os.path.join(data_path, "divided", "0003", "structured", "Profile0.txt"))
        assert os.path.exists(os.path.join(data_path, "divided", "0003", "structured", "MesurementConditions0.xml"))
        assert os.path.exists(os.path.join(data_path, "divided", "0004", "structured", "89-10_P.csv"))
        assert os.path.exists(os.path.join(data_path, "divided", "0004", "structured", "Profile0.txt"))
        assert os.path.exists(os.path.join(data_path, "divided", "0004", "structured", "MesurementConditions0.xml"))

    def test_thumbnail(self, data_path):
        assert os.path.exists(os.path.join(data_path, "thumbnail", "89-1_P.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "thumbnail", "89-3_P.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0002", "thumbnail", "89-5_P.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0003", "thumbnail", "89-7_P.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0004", "thumbnail", "89-10_P.png"))

    def test_meta(self, data_path):
        assert os.path.exists(os.path.join(data_path, "meta", "metadata.json"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "meta", "metadata.json"))
        assert os.path.exists(os.path.join(data_path, "divided", "0002", "meta", "metadata.json"))
        assert os.path.exists(os.path.join(data_path, "divided", "0003", "meta", "metadata.json"))
        assert os.path.exists(os.path.join(data_path, "divided", "0004", "meta", "metadata.json"))
