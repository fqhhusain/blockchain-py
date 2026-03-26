import json
import binascii
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

PRIVATE_KEY_PEM = """-----BEGIN PRIVATE KEY-----
MIGEAgEAMBAGByqGSM49AgEGBSuBBAAKBG0wawIBAQQgbxY35cvlZfoVJsDUGGdL
M0H06TdT/ECTTquZJKSYgcShRANCAAT11TT4AVv9+OvWo5wPQ+7Mrfj1g+fZSQH3
bke0Efzcq/NZsacLXsDOZ08I/pDTNR41VAaxEsnSxzCW4H3zpsld
-----END PRIVATE KEY-----
"""

tx = {"sender": "MFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAE9dU0+AFb", "receiver": "Bob", "amount": 50}
message = json.dumps(tx, sort_keys=True).encode("utf-8")

private_key = serialization.load_pem_private_key(
    PRIVATE_KEY_PEM.encode(), password=None, backend=default_backend()
)
sig_bytes = private_key.sign(message, ec.ECDSA(hashes.SHA256()))
print("signature:", binascii.hexlify(sig_bytes).decode())