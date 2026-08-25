import json
import os
import shutil
from subprocess import PIPE, run

import pytest


@pytest.fixture
def data_path():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


@pytest.fixture(scope="class")
def setup_main():
    """main.pyを実行するフィクスチャ
    Note:
        scope='module': テストクラスごとに１度だけ実行される
    """
    # setup: テスト準備処理
    basepath_main_script = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if os.name == "nt":
        # windows command
        cmd = ["python", os.path.join(basepath_main_script, "main.py")]
    else:
        # mac / unix command
        pyenv_version = os.getenv("PYENV_VERSION")
        if pyenv_version is not None:
            cmd = ["python", os.path.join(basepath_main_script, "main.py")]
        else:
            cmd = ["python3", os.path.join(basepath_main_script, "main.py")]
            # cmd = ["python3.12", os.path.join(basepath_main_script, "main.py")]

    run(cmd, encoding="utf-8", stdout=PIPE)

    yield

    # teardown:終了処理
    if os.path.exists(os.path.join(basepath_main_script, "data")):
        shutil.rmtree(os.path.join(basepath_main_script, "data"))


@pytest.fixture
def setup_metadatadef_json(hoge):
    print(hoge)
    metadata_filename = "metadata-def.json"

    test_specification_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "tasksupport",
        metadata_filename,
    )

    with open(test_specification_path, mode="r", encoding="utf-8") as f:
        contents = json.load(f)
        print(contents)

    yield contents


@pytest.fixture
def setup_metadatadef_rigaku_ras_json():
    metadata_filename = "metadata-def_rigaku_ras.json"

    test_specification_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "tasksupport",
        metadata_filename,
    )

    with open(test_specification_path, mode="r", encoding="utf-8") as f:
        contents = json.load(f)
        print(contents)

    yield contents


@pytest.fixture
def setup_metadatadef_rigaku_rasx_json():
    metadata_filename = "metadata-def_rigaku_rasx.json"

    test_specification_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "tasksupport",
        metadata_filename,
    )

    with open(test_specification_path, mode="r", encoding="utf-8") as f:
        contents = json.load(f)
        print(contents)

    yield contents


@pytest.fixture
def setup_metadatadef_rigaku_txt_tab_json():
    metadata_filename = "metadata-def_rigaku_txt_tab.json"

    test_specification_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "tasksupport",
        metadata_filename,
    )

    with open(test_specification_path, mode="r", encoding="utf-8") as f:
        contents = json.load(f)
        print(contents)

    yield contents


@pytest.fixture
def setup_metadatadef_rigaku_txt_space_json():
    metadata_filename = "metadata-def_rigaku_txt_space.json"

    test_specification_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "tasksupport",
        metadata_filename,
    )

    with open(test_specification_path, mode="r", encoding="utf-8") as f:
        contents = json.load(f)
        print(contents)

    yield contents


@pytest.fixture
def setup_metadatadef_bruker_uxd_json():
    metadata_filename = "metadata-def_bruker_uxd.json"

    test_specification_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "tasksupport",
        metadata_filename,
    )

    with open(test_specification_path, mode="r", encoding="utf-8") as f:
        contents = json.load(f)
        print(contents)

    yield contents
