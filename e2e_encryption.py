# pyre-ignore-all-errors
import os  # type: ignore  # pyre-ignore
import json  # type: ignore  # pyre-ignore
import base64  # type: ignore  # pyre-ignore
import hashlib  # type: ignore  # pyre-ignore
import secrets  # type: ignore  # pyre-ignore
import logging  # type: ignore  # pyre-ignore
from datetime import datetime  # type: ignore  # pyre-ignore
from typing import Optional, Dict, Tuple  # type: ignore  # pyre-ignore
from cryptography.fernet import Fernet  # type: ignore  # pyre-ignore
from cryptography.hazmat.primitives import hashes, serialization  # type: ignore  # pyre-ignore
from cryptography.hazmat.primitives.asymmetric import rsa, padding  # type: ignore  # pyre-ignore
from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore  # pyre-ignore
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # type: ignore  # pyre-ignore
from cryptography.hazmat.backends import default_backend  # type: ignore  # pyre-ignore

logger = logging.getLogger("E2EEncryption")


class E2EEncryption:
    """End-to-end encryption for user messages and data storage."""

    def __init__(self, user_id: str, key: Optional[str] = None):  # type: ignore  # pyre-ignore
        self.user_id = str(user_id)
        self.key_file = f".e2e_key_{self.user_id}"

        if key:
            self.symmetric_key = self._derive_key(key)
        else:
            self.symmetric_key = self._load_or_create_key()

        self.fernet = Fernet(self.symmetric_key)

    def _derive_key(self, password: str) -> bytes:  # type: ignore  # pyre-ignore
        """Derive a Fernet-compatible key from a password using PBKDF2."""
        salt = f"nova_e2e_{self.user_id}".encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
            backend=default_backend(),
        )
        derived = kdf.derive(password.encode())
        return base64.urlsafe_b64encode(derived)

    def _load_or_create_key(self) -> bytes:  # type: ignore  # pyre-ignore
        """Load an existing key from disk or create a new one."""
        if os.path.exists(self.key_file):
            try:
                with open(self.key_file, "rb") as f:
                    return f.read()
            except Exception:
                pass

        key = Fernet.generate_key()
        try:
            with open(self.key_file, "wb") as f:
                f.write(key)
            # os.chmod with 0o600 is Unix-only; on Windows we skip it gracefully
            if os.name != "nt":
                os.chmod(self.key_file, 0o600)
        except Exception as exc:
            logger.warning(f"Could not secure key file permissions: {exc}")
        return key

    def encrypt_message(self, plaintext: str) -> str:  # type: ignore  # pyre-ignore
        """Encrypt a plaintext string and return a base64-encoded ciphertext."""
        if not plaintext:
            return ""
        try:
            encrypted = self.fernet.encrypt(plaintext.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return plaintext

    def decrypt_message(self, ciphertext: str) -> str:  # type: ignore  # pyre-ignore
        """Decrypt a base64-encoded ciphertext back to plaintext."""
        if not ciphertext:
            return ""
        try:
            decoded = base64.b64decode(ciphertext.encode())
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return ciphertext

    def encrypt_for_storage(self, plaintext: str) -> str:  # type: ignore  # pyre-ignore
        return self.encrypt_message(plaintext)

    def decrypt_from_storage(self, ciphertext: str) -> str:  # type: ignore  # pyre-ignore
        return self.decrypt_message(ciphertext)

    def get_shared_secret(self) -> str:  # type: ignore  # pyre-ignore
        return base64.b64encode(self.symmetric_key).decode()[:32]  # type: ignore  # pyre-ignore


class E2EKeyExchange:
    """RSA-based key exchange for establishing shared secrets."""

    def __init__(self):
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )
        self.public_key = self.private_key.public_key()

    def get_public_key_pem(self) -> str:  # type: ignore  # pyre-ignore
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

    @staticmethod
    def encrypt_with_public_key(public_key_pem: str, data: bytes) -> bytes:  # type: ignore  # pyre-ignore
        public_key = serialization.load_pem_public_key(public_key_pem.encode())
        encrypted = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return base64.b64encode(encrypted)

    def decrypt_with_private_key(self, encrypted_data: bytes) -> bytes:  # type: ignore  # pyre-ignore
        encrypted = base64.b64decode(encrypted_data)
        return self.private_key.decrypt(
            encrypted,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )


class SecureMessageProtocol:
    """Wraps / unwraps messages with E2E encryption markers."""

    ENCRYPT_PREFIX = "\U0001f510"  # 🔐
    CIPHER_PREFIX = "[E2E]"

    def __init__(self, user_id: str, shared_secret: Optional[str] = None):  # type: ignore  # pyre-ignore
        self.user_id = str(user_id)
        self.encryption = E2EEncryption(self.user_id, shared_secret)
        self._message_history: list = []  # type: ignore  # pyre-ignore

    def wrap_outgoing(self, message: str) -> str:  # type: ignore  # pyre-ignore
        if not message or len(message) < 2:
            return message
        if message.startswith(self.CIPHER_PREFIX):
            return message

        encrypted = self.encryption.encrypt_message(message)
        wrapped = f"{self.CIPHER_PREFIX}{encrypted}"

        self._message_history.append(
            {
                "direction": "out",
                "timestamp": datetime.now().isoformat(),
                "preview": message[:50],  # type: ignore  # pyre-ignore
            }
        )
        return wrapped

    def unwrap_incoming(self, message: str) -> str:  # type: ignore  # pyre-ignore
        if not message:
            return message
        if message.startswith(self.CIPHER_PREFIX):
            encrypted = message[len(self.CIPHER_PREFIX) :]  # type: ignore  # pyre-ignore
            return self.encryption.decrypt_message(encrypted)
        return message

    def wrap_for_storage(self, messages: list) -> str:  # type: ignore  # pyre-ignore
        encrypted = self.encryption.encrypt_for_storage(json.dumps(messages))
        return encrypted

    def unwrap_from_storage(self, encrypted_data: str) -> list:  # type: ignore  # pyre-ignore
        try:
            decrypted = self.encryption.decrypt_from_storage(encrypted_data)
            return json.loads(decrypted)
        except Exception:
            return []


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

_encryption_cache: Dict[str, E2EEncryption] = {}  # type: ignore  # pyre-ignore


def create_user_encryption(user_id: str, secret: Optional[str] = None) -> E2EEncryption:  # type: ignore  # pyre-ignore
    return E2EEncryption(user_id, secret)


def get_user_encryption(user_id: str) -> E2EEncryption:  # type: ignore  # pyre-ignore
    return E2EEncryption(user_id)


def get_or_create_encryption(user_id: str, secret: Optional[str] = None) -> E2EEncryption:  # type: ignore  # pyre-ignore
    user_id = str(user_id)
    if user_id not in _encryption_cache:
        _encryption_cache[user_id] = E2EEncryption(user_id, secret)
    return _encryption_cache[user_id]


class EncryptedMessage:
    """High-level helper: encrypt / decrypt messages for a specific user."""

    def __init__(self, user_id: str):
        self.user_id = str(user_id)
        self.crypto = get_or_create_encryption(user_id)

    def encrypt(self, text: str) -> str:  # type: ignore  # pyre-ignore
        if not text:
            return ""
        try:
            encrypted = self.crypto.fernet.encrypt(text.encode())
            return f"[E2E]{base64.b64encode(encrypted).decode()}"
        except Exception as e:
            logger.error(f"E2E encrypt error: {e}")
            return text

    def decrypt(self, text: str) -> str:  # type: ignore  # pyre-ignore
        if not text or not text.startswith("[E2E]"):  # type: ignore  # pyre-ignore
            return text
        try:
            encoded = text[5:]  # type: ignore  # pyre-ignore
            decoded = base64.b64decode(encoded.encode())
            decrypted = self.crypto.fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"E2E decrypt error: {e}")
            return text

    def encrypt_for_db(self, text: str) -> str:  # type: ignore  # pyre-ignore
        return self.encrypt(text)

    def decrypt_from_db(self, text: str) -> str:  # type: ignore  # pyre-ignore
        return self.decrypt(text)

