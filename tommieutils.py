# 	
#   tommieutils.py : useful crypto functions for using in TommieCoin server and wallet apps
# 
#   Author: Scott Yilek, April 2018
#




from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA


def sign(sk, M):
    """
    Sign string message M with secret key sk using pycrypto library RSA signatures w/
    PKCS1.5 padding and SHA256
    
    sk should be a string and in PEM format
    """
    keyobj = RSA.importKey(sk)
    hobj = SHA256.new(M)
    signobj = PKCS1_v1_5.new(keyobj) 
    sigbytes = signobj.sign(hobj)
    return sigbytes.encode('hex')


def verify(pk, M, S):
    """
    Verify signature.  S is a string of hex that will need to be decoded before actual verification.
    pk should be a string in PEM format

    """
    pubkeyobj = RSA.importKey(pk)
    hobj = SHA256.new(M)
    vfobj = PKCS1_v1_5.new(pubkeyobj) 
    return vfobj.verify(hobj, S.decode('hex'))


def keygen(size):
    """
    Generate an RSA keypair with size bit modulus (e.g., 1024)
    Returns a pair of keys as strings in PEM format
    """
    keyobj = RSA.generate(size)
    pkobj = keyobj.publickey()
    skstr = keyobj.exportKey('PEM')
    pkstr = pkobj.exportKey('PEM')
    return (pkstr, skstr)


def sha256(M):
    """
    Hash input message M using sha256 and return hex string
    """
    hobj = SHA256.new(M)
    return hobj.hexdigest()

