import json
import os
from pathlib import Path

import pytest
import requests
from sample_api_client import (
    entry_sample,
    find_sample,
    find_sample_detail,
    get_groupid,
    get_token,
    get_url,
    read_payload_file,
)
from rdetoolkit.exceptions import StructuredError


@pytest.fixture
def mock_env(mocker):
    """環境変数をテスト用に設定します."""
    mocker.patch.dict(os.environ, {"ENVNAME": "PRD", "RDE_API_ACCESS_TOKEN": "test_token"})


def test_get_token_env(mock_env):
    """環境変数からトークンが取得できることを確認します."""
    assert get_token() == "test_token"


def test_get_token_file(mocker):
    """環境変数がない場合にファイルからトークンが取得できることを確認します."""
    mocker.patch.dict(os.environ, {}, clear=True)
    mock_path = Path("/app2/data/token.txt")
    mocker.patch.object(Path, "is_file", return_value=True)
    mocker.patch("builtins.open", mocker.mock_open(read_data="file_token\n"))

    assert get_token() == "file_token\n"


def test_get_token_empty(mocker):
    """環境変数もファイルもない場合に空文字が返ることを確認します."""
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch.object(Path, "is_file", return_value=False)

    assert get_token() == ""


def test_get_url_prd(mock_env):
    """PRD環境のURLが正しく返ることを確認します."""
    urls = get_url()
    assert "rde-api.nims.go.jp" in urls["dataset"]
    assert "rde-material-api.nims.go.jp" in urls["material"]


def test_get_url_stg(mocker):
    """STG環境のURLが正しく返ることを確認します."""
    mocker.patch.dict(os.environ, {"ENVNAME": "STG"})
    urls = get_url()
    assert "rde-api.nimsdpf20stg.org" in urls["dataset"]
    assert "rde-material-api.nimsdpf20stg.org" in urls["material"]


def test_get_url_invalid(mocker):
    """不正な環境名が指定された場合にStructuredErrorが発生することを確認します."""
    mocker.patch.dict(os.environ, {"ENVNAME": "INVALID"})
    with pytest.raises(StructuredError, match="There is no such environment"):
        get_url()


def test_get_groupid(mocker, mock_env):
    """データセットIDからグループIDが正しく抽出されることを確認します."""
    mock_response = mocker.Mock()
    mock_response.text = json.dumps({
        "data": {"relationships": {"group": {"data": {"id": "group_123"}}}}
    })
    mock_response.apparent_encoding = "utf-8"
    mocker.patch("requests.get", return_value=mock_response)

    group_id = get_groupid("token", "dataset_id")
    assert group_id == "group_123"


def test_find_sample(mocker, mock_env):
    """試料検索フロー（データセット取得 -> 試料検索）が正しく動作することを確認します."""
    # 1回目のレスポンス (dataset)
    res1 = mocker.Mock()
    res1.text = json.dumps({
        "data": {"relationships": {"group": {"data": {"id": "group_123"}}}}
    })
    res1.apparent_encoding = "utf-8"

    # 2回目のレスポンス (material search)
    res2 = mocker.Mock()
    res2.text = '{"specimen": "found"}'
    res2.apparent_encoding = "utf-8"

    mocker.patch("requests.get", side_effect=[res1, res2])

    result = find_sample("token", "dataset_id", "sample_name")
    assert result == '{"specimen": "found"}'


def test_find_sample_detail(mocker, mock_env):
    """試料詳細情報の取得が正しく動作することを確認します."""
    mock_response = mocker.Mock()
    mock_response.text = '{"detail": "info"}'
    mock_response.apparent_encoding = "utf-8"
    mocker.patch("requests.get", return_value=mock_response)

    result = find_sample_detail("token", "sample_id")
    assert result == '{"detail": "info"}'


def test_entry_sample_success(mocker, mock_env):
    """試料登録が成功した場合にレスポンスが返ることを確認します."""
    mock_response = mocker.Mock()
    mock_response.ok = True
    mock_response.text = "success_response"
    mocker.patch("requests.post", return_value=mock_response)

    payload = {"name": "test_sample"}
    result = entry_sample("token", payload)
    assert result == "success_response"


def test_entry_sample_failure(mocker, mock_env):
    """試料登録が失敗した場合に空文字が返ることを確認します."""
    mock_response = mocker.Mock()
    mock_response.ok = False
    mocker.patch("requests.post", return_value=mock_response)

    payload = {"name": "test_sample"}
    result = entry_sample("token", payload)
    assert result == ""
