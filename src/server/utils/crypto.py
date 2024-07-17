from datetime import datetime, timedelta, timezone

from hashlib import sha256
import jwt
from secrets import token_hex
import jwt

ACCESS_TOKEN_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES_IN = 20


def hash_password(username: str, password: str) -> str:
    """
    Hash the password using the SHA-256 algorithm.

    Applies a backward string of the username as a salt.

    Args:
        username (str): The username of the user.
        password (str): The password of the user.

    Returns:
        str: The hashed password.
    """
    password_hash = sha256(password.encode("utf-8"))
    password_hash.update(username[::-1].encode("utf-8"))

    return password_hash.hexdigest()

def generate_secret_key() -> str:
    """
    Generate a secret key for the user.

    The key is a random hex string of byte length 256.

    Returns:
        str: The secret key.
    """
    return token_hex(256)

def get_access_token(username: str, secret: str) -> str:
    """
    Generate a jwt access token for the user.

    Args:
        username (str): The username of the user.
        secret (str): The secret key of the user. Do not confuse this with the
            password.

    Returns:
        str: The access token.
    """
    iat = datetime.now(timezone.utc) # Issued at.
    payload = {
        "iss": "valotracker",
        "iat": iat,
        "sub": username,
        "exp": iat + timedelta(seconds=ACCESS_TOKEN_EXPIRES_IN)
    }
    return jwt.encode(payload, secret, ACCESS_TOKEN_ALGORITHM)

def decode_access_token(username: str, secret: str, access_token: str) -> tuple:
    """
    Decode the jwt access token.

    Args:
        username (str): The username of the user.
        secret (str): The secret key of the user. Do not confuse this with the
            password.
        access_token (str): The jwt access token to decode.

    Returns:
        tuple: True if the token is valid, False otherwise, along with the error,
            or '' if successful.
    """
    return jwt.decode(access_token, secret, algorithms=[ACCESS_TOKEN_ALGORITHM])

def is_access_token_valid(username: str, secret: str, access_token: str) -> tuple:
    try:
        decode_access_token(username, secret, access_token)
        return True, ''
    except jwt.ExpiredSignatureError:
        return False, 'expired'
    except jwt.DecodeError:
        return False, 'invalid'
