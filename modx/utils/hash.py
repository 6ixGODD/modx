from __future__ import annotations

import argon2

hasher = argon2.PasswordHasher()


def hash_password(password: str) -> str:
    """
    Hash a password using Argon2.

    Args:
        password (str): The password to hash.

    Returns:
        str: The hashed password.
    """
    return hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a hashed password.

    Args:
        password (str): The password to verify.
        hashed (str): The hashed password to verify against.

    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    try:
        return hasher.verify(hashed, password)
    except argon2.exceptions.VerifyMismatchError:
        return False
