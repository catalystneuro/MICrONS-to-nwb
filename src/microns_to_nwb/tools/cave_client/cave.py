import os

from caveclient import CAVEclient
from caveclient.base import AuthException


def get_client():
    try:
        client = CAVEclient("minnie65_public_v343")
    except AuthException:
        # Initialize client without datastack name
        client = CAVEclient()
        # Access token from environment
        assert "CAVE" in os.environ, (
            "The token for CAVE could not be read from the environment."
            "Please set the environment variable named CAVE with the token."
        )
        token = os.environ["CAVE"]
        # Save token at default location used by caveclient
        client.auth.save_token(token=token, overwrite=True)

        # Retry access datastack
        client = CAVEclient("minnie65_public_v343")
    return client


def get_functional_coreg_table(scan_key):
    client = get_client()

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
