from azure.keyvault.secrets import SecretClient
from .credentials import *


def KeyVaultClient(vault_name):
    """
    Access the Azure Key Vault to load needed secret tokens.
    """
    global CREDENTIAL
    if CREDENTIAL == None:
        AccountToken("https://database.windows.net/.default")
    secret_client = SecretClient(
        vault_url=f"https://{vault_name}.vault.azure.net/",
        credential=CREDENTIAL
    )
    return secret_client
