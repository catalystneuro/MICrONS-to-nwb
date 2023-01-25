import json
from pathlib import Path

from caveclient import CAVEclient
from caveclient.base import AuthException


def get_client(token):

    try:
        client = CAVEclient("minnie65_public_v343")
    except AuthException:
        client = CAVEclient()
        client.auth.save_token(token=token, overwrite=True)

        client = CAVEclient("minnie65_public_v343")
    return client


def get_token_from_external_file(external_file_path):
    """
    Returns the CAVEclient token saved in an external file in JSON format. (e.g. "caveclient_token.json")
    The external file is expected to have a 'token' field with the secret token string.
    For first usage, follow the instructions at https://github.com/seung-lab/CAVEclient/blob/master/CAVEclientExamples.ipynb
    to generate a new token and save it in an external file.
    """
    assert Path(external_file_path).is_file(), f"{external_file_path} does not exist! Please create it."
    with open(external_file_path) as f:
        external_file = json.load(f)
        assert "token" in external_file, f"'token' field is missing from {external_file_path}."

    return external_file["token"]


def get_functional_coreg_table(scan_key, token_file_path):
    token = get_token_from_external_file(token_file_path)
    client = get_client(token=token)

    coreg_table = client.materialize.query_table(
        table="functional_coreg",
        split_positions=True,
    )
    session = scan_key["session"]
    scan = scan_key["scan_idx"]

    coreg_table_for_this_scan = coreg_table[
        (coreg_table["session"] == int(session)) & (coreg_table["scan_idx"] == int(scan))
    ]

    return coreg_table_for_this_scan
