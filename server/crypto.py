from base64 import b64decode
from io import BytesIO, StringIO

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA

from setting import private_key_file

with open(private_key_file, 'r') as f:
    private_key = RSA.import_key(f.read())
cipher_rsa = PKCS1_OAEP.new(private_key)
key_size = private_key.size_in_bytes()
del private_key

def _decrypt(data):# rsa
    '''structure: key, nonce, mac_tag, ciphertext '''
    data=BytesIO(b64decode(data))
    # read and Decrypt the key, nonce and tag with the private RSA key
    session_key, nonce, tag = [cipher_rsa.decrypt(data.read(key_size)) for _ in range(3)]
    ciphertext=data.read()
    del data

    
    # Decrypt the data with the AES session key
    cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
    data = cipher_aes.decrypt_and_verify(ciphertext, tag)
    return data.decode("utf-8")# to str

def decrypt(data:str):
    decoded=StringIO()
    for enc_data in data.splitlines():
        if not enc_data:
            continue
        
        enc_data=_decrypt(enc_data)# decode to str
        decoded.write(enc_data+"\n")# \n is must
    
    decoded.seek(0)
    return decoded.read()
