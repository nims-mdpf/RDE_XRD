from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests
from rdetoolkit.exceptions import StructuredError


def get_token() -> str:
    """Obtain a token for RDE API access.

    The system checks for the 'RDE_API_ACCESS_TOKEN' environment variable first.
    if it does not exist, the token is read from the file at the specified path.

    Returns:
        str: Token string for API access.

    """
    token = os.getenv('RDE_API_ACCESS_TOKEN', None)
    if token is None:
        path = Path('/app2/data/token.txt')
        if path.is_file():
            with open(path) as f:
                return f.readlines()[0]
        else:  # Do nothing when testing locally.
            return ""
    else:
        return os.environ.get('RDE_API_ACCESS_TOKEN', 'NONE')

def get_url() -> dict[str, str]:
    """Return the API endpoint URL corresponding to the environment.

    Switches between production (prd) and staging (stg) URLs based on the value of the 'ENVNAME' environment variable.

    Returns:
        dict[str, str]: A URL map with keys 'dataset' and 'material'.

    """
    envname = os.getenv('ENVNAME', default='PRD').lower()
    myurl = {}
    if envname == "prd":
        myurl["dataset"] = 'https://rde-api.nims.go.jp/datasets/'
        myurl["material"] = 'https://rde-material-api.nims.go.jp/samples'
    elif envname == "stg":
        myurl["dataset"] = 'https://rde-api.nimsdpf20stg.org/datasets/'
        myurl["material"] = 'https://rde-material-api.nimsdpf20stg.org/samples'
    else:
        err_msg = f"There is no such environment: {envname}"
        raise StructuredError(err_msg)
    return myurl

def find_sample(_token: str, dataset_id: str, sample_name: str) -> str:
    """Search for a sample using the dataset ID and sample name.

    Args:
        _token (str): Token.
        dataset_id (str): Dataset ID.
        sample_name (str): Sample name.

    Returns:
        str: Response from the API (JSON string).

    """
    token = f'Bearer {_token}'
    geturl = get_url()
    url = geturl["dataset"] + dataset_id
    config = {"ACCEPT": "application/vnd.api+json", "CONTENT_TYPE": "application/vnd.api+json"}
    headers = {'Authorization': token, 'Accept': config['ACCEPT'], 'Content-type': config['CONTENT_TYPE']}
    r = requests.get(url, headers=headers, timeout=(10, 10))

    r.encoding = r.apparent_encoding
    dataset = json.loads(r.text)

    group_id = dataset["data"]["relationships"]["group"]["data"]["id"]
    url = geturl["material"] + '?groupId=' + group_id + '&searchWords=' + sample_name \
        + '&page[offset]=0&page[limit]=1000'
    headers = {'Authorization': token, 'Accept': config['ACCEPT'], 'Content-type': config['CONTENT_TYPE']}
    r = requests.get(url, headers=headers, timeout=(10, 10))

    r.encoding = r.apparent_encoding
    return r.text

def get_groupid(_token: str, dataset_id: str) -> str:
    """Retrieve the group ID associated with the dataset ID.

    Args:
        _token (str): Token.
        dataset_id (str): Dataset ID.

    Returns:
        str: Group ID.

    """
    token = f'Bearer {_token}'
    geturl = get_url()
    url = geturl["dataset"] + dataset_id
    config = {"ACCEPT": "application/vnd.api+json", "CONTENT_TYPE": "application/vnd.api+json"}
    headers = {'Authorization': token, 'Accept': config['ACCEPT'], 'Content-type': config['CONTENT_TYPE']}
    r = requests.get(url, headers=headers, timeout=(10, 10))

    r.encoding = r.apparent_encoding
    dataset = json.loads(r.text)
    return dataset["data"]["relationships"]["group"]["data"]["id"]

def find_sample_detail(_token: str, sample_id: str) -> str:
    """Retrieve detailed information about the sample using the sample ID.

    Args:
        _token (str): Token.
        sample_id (str): Sample ID.

    Returns:
        str: Response from the API (JSON string).

    """
    token = f'Bearer {_token}'
    geturl = get_url()
    url = geturl["material"] + "/" + sample_id
    config = {"ACCEPT": "application/vnd.api+json", "CONTENT_TYPE": "application/vnd.api+json"}
    headers = {'Authorization': token, 'Accept': config['ACCEPT'], 'Content-type': config['CONTENT_TYPE']}
    r = requests.get(url, headers=headers, timeout=(10, 10))

    r.encoding = r.apparent_encoding
    return r.text

def entry_sample(_token: str, _payload: dict[str, Any]) -> str:
    """Register the sample information in RDE.

    Args:
        _token (str): Token.
        _payload (Dict[str, Any]): Payload data.

    Returns:
        str: The response string upon successful registration. Returns an empty string if registration fails.

    """
    token = f'Bearer {_token}'
    config = {"ACCEPT": "application/vnd.api+json", "CONTENT_TYPE": "application/vnd.api+json"}
    geturl = get_url()
    url = geturl["material"]
    headers = {'Authorization': token, 'Accept': config['ACCEPT'], 'Content-type': config['CONTENT_TYPE']}
    r = requests.post(url, headers=headers, json=_payload, timeout=(10, 10))

    return r.text if r.ok else ''

def read_payload_file() -> dict[str, Any]:
    """Load the payload JSON file.

    Returns:
        Dict[str, Any]: JSON data loaded from a file.

    """
    payload_obj: dict
    _payload_file_path = Path(os.path.join("data", "tasksupport", "payload_base.json"))
    with open(_payload_file_path, encoding="utf8") as f:
        payload_obj = json.load(f)
    return payload_obj
