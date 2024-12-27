from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip32Slip10Ed25519, Bip39MnemonicValidator
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from base58 import b58encode
import os


def generate_mnemonic():
    mnemonic_generator = Bip39MnemonicGenerator()
    mnemonic = mnemonic_generator.FromWordsNumber(24) # 24 word phrase
    return mnemonic


def mnemonic_to_seed(mnemonic):
    if not Bip39MnemonicValidator().IsValid(mnemonic):
        raise ValueError("Invalid mnemonic phrase")
    seed_generator = Bip39SeedGenerator(mnemonic)
    return seed_generator.Generate()


def seed_to_private_key(seed):
    bip32_ctx = Bip32Slip10Ed25519.FromSeed(seed)
    derivation_path = "m/44'/4218'/0'/0'/0'"
    private_key = bip32_ctx.DerivePath(derivation_path).PrivateKey().Raw().ToHex()
    return private_key


def sign_data(private_key, data):
    private_key_bytes = bytes.fromhex(private_key)
    private_key_obj = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    signature = private_key_obj.sign(data.encode())
    return signature.hex()


def derive_public_key(private_key):
    private_key_bytes = bytes.fromhex(private_key)
    private_key_obj = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    public_key_obj = private_key_obj.public_key()
    public_key_bytes = public_key_obj.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return public_key_bytes.hex()


def generate_peer_id(public_key):
    prefixed_pub_key_hex = "002408011220" + public_key
    prefixed_pub_key_bytes = bytes.fromhex(prefixed_pub_key_hex)
    peer_id = b58encode(prefixed_pub_key_bytes).decode()
    return peer_id


def verify_signature(public_key, data, signature):
    public_key_bytes = bytes.fromhex(public_key)
    public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
    signature_bytes = bytes.fromhex(signature)
    try:
        public_key_obj.verify(signature_bytes, data.encode())
        return True
    except Exception:
        return False
    

def all_in_one():
    '''
    runs all required steps (functions) to generate a node ID (peer ID)
    return: a list containing the concatenation of the private key with the public key and the corresponding node ID
    '''
    mnemonic = generate_mnemonic()
    seed = mnemonic_to_seed(mnemonic)
    private_key = seed_to_private_key(seed)
    public_key = derive_public_key(private_key)
    priv_pub_key = str(private_key) + str(public_key)
    peer_id = generate_peer_id(public_key)
    return [priv_pub_key, peer_id]
    

# Testing
'''mnemonic = generate_mnemonic()
seed = mnemonic_to_seed(mnemonic)
private_key = seed_to_private_key(seed)
public_key = derive_public_key(private_key)
peer_id = generate_peer_id(public_key)

print("Private Key:", private_key)
print("Public Key:", public_key)
print("Peer ID:", peer_id)'''

#print(all_in_one())

