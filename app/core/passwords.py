import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 260_000


def hash_password(password: str) -> str:
    """Devuelve un hash PBKDF2 con sal aleatoria."""

    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        ITERATIONS,
    )
    return f"{ALGORITHM}${ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    """Comprueba una contraseña contra un hash PBKDF2."""

    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != ALGORITHM:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            int(iterations),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), expected)
