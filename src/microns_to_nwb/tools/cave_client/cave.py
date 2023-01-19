from caveclient import CAVEclient
from caveclient.base import AuthException


def get_client(token):

    try:
        client = CAVEclient('minnie65_public_v343')
    except AuthException:
        # token should be GitHub secret
        # not sure what is expiration for token
        client = CAVEclient()
        client.auth.save_token(token=token, overwrite=True)

        client = CAVEclient('minnie65_public_v343')
    return client
