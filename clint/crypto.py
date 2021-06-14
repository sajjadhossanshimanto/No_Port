from functools import reduce
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP
from clint.util import data_store, force_str
from operator import add
from base64 import b64decode


aes_key_size=16

def _aes(key, data:bytes):
    cipher_aes = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher_aes.encrypt_and_digest(data)
    return (cipher_aes.nonce, tag, ciphertext)

def encrypt_aes(data):
    key=get_random_bytes(aes_key_size)
    if isinstance(data, str):
        data=data.encode('utf-8')
    data=key + reduce(add, _aes(key, data))
    return data

def decrypt_aes(io, content_ln=-1):
    key=io.read(aes_key_size)
    nonce, tag=[io.read(16) for _ in range(2)]
    ciphertext = io.read(content_ln)

    try:
        cipher_aes = AES.new(key, AES.MODE_EAX, nonce)
        ciphertext = cipher_aes.decrypt_and_verify(ciphertext, tag)
    except ValueError:# mac check failed
        cipher_aes = AES.new(key, AES.MODE_EAX, nonce)
        ciphertext = cipher_aes.decrypt(ciphertext)
    
    try:
        return ciphertext.decode('utf-8')
    except UnicodeDecodeError:# this should never happen
        return force_str(ciphertext)


pub_key=b64decode(data_store.var.key)
pub_key=pub_key.decode('utf-8')# to str
pub_key=RSA.import_key(pub_key)
cipher_rsa = PKCS1_OAEP.new(pub_key)
def encrypt(data):# rsa
    '''structure: key, nonce, mac_tag, ciphertext '''
    if isinstance(data, str):
        data=data.encode('utf-8')
    session_key=get_random_bytes(aes_key_size)
    nonce, tag, data = _aes(session_key, data)
    
    cipher = [cipher_rsa.encrypt(i) for i in (session_key, nonce, tag)]
    cipher.append(data)
    return reduce(add, cipher)

