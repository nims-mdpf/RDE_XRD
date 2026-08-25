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
        os.path.join(tasksupport_original_path, "metadata-def_bruker_uxd.json"),
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
    メタデータテスト: XRD.uxd
    """

    input_file: str = "XRD.uxd"

    def test_setup(self):
        setup_inputdata_folder(self.input_file, "bruker", "uxd_basic")

    def test_metadata_constant(self, setup_main, setup_metadatadef_bruker_uxd_json):
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
            constant_meta_key = setup_metadatadef_bruker_uxd_json.get(k)
            assert constant_meta_key

    def test_metadata_variable(self, setup_metadatadef_bruker_uxd_json):
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
            # metadata.json: variable
            variable_meta_key = setup_metadatadef_bruker_uxd_json.get(k)
            # check defined variable = 1
            except_variable_flag = setup_metadatadef_bruker_uxd_json[k].get("variable")

            assert (all(variable_meta_key)) and (except_variable_flag is not None)


class TestOutputCase1:
    """case1
    単一ファイルのテスト: XRD.uxd
    グラフのスケール: linear(default)
    """

    inputdata: Union[str, List[str]] = "XRD.uxd"

    def test_setup(self):
        setup_inputdata_folder(self.inputdata, "bruker", "uxd_basic")
        setup_invoice_json_with_magic_filename("bruker", "uxd_basic")

    def test_raw_data(self, setup_main, data_path):
        assert os.path.exists(os.path.join(data_path, "nonshared_raw", "XRD.uxd"))

    def test_main_image(self, data_path):
        assert os.path.exists(os.path.join(data_path, "main_image", "XRD.png"))

    def test_other_image(self, data_path):
        assert os.path.exists(os.path.join(data_path, "other_image", "XRD_log.png"))

    def test_structured(self, data_path):
        assert os.path.exists(os.path.join(data_path, "structured", "XRD.csv"))
        assert os.path.exists(os.path.join(data_path, "structured", "XRD.html"))

    def test_thumbnail(self, data_path):
        assert os.path.exists(os.path.join(data_path, "thumbnail", "XRD.png"))

    def test_meta(self, data_path):
        assert os.path.exists(os.path.join(data_path, "meta", "metadata.json"))
