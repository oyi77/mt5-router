from cryptography.fernet import Fernet
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class EncryptionService:
    def __init__(self):
        key = (
            settings.ENCRYPTION_KEY.encode()
            if isinstance(settings.ENCRYPTION_KEY, str)
            else settings.ENCRYPTION_KEY
        )
        if not key:
            logger.warning("ENCRYPTION_KEY not set, using temporary key")
            key = Fernet.generate_key()
        self.cipher = Fernet(key)

    def encrypt(self, data: str) -> str:
        if isinstance(data, str):
            data = data.encode()
        encrypted = self.cipher.encrypt(data)
        return encrypted.decode()

    def decrypt(self, encrypted_data: str) -> str:
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode()
        decrypted = self.cipher.decrypt(encrypted_data)
        return decrypted.decode()


encryption_service = EncryptionService()
