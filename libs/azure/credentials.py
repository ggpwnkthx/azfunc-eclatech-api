import time
import os
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
CREDENTIAL = None
CREDENTIAL_WAIT = False


def AccountToken(scope):
    global CREDENTIAL_WAIT, CREDENTIAL
    if CREDENTIAL is not None:
        return CREDENTIAL.get_token(scope)
    elif CREDENTIAL_WAIT:
        while CREDENTIAL is None:
            time.sleep(0.1)
        return AccountToken(scope)
    else:
        CREDENTIAL_WAIT = True
        if(os.environ.get("MSI_SECRET")):
            CREDENTIAL = DefaultAzureCredential(additionally_allowed_tenants = ["*"])
        else:
            CREDENTIAL = InteractiveBrowserCredential(additionally_allowed_tenants = ["*"])
        return CREDENTIAL.get_token(scope)
