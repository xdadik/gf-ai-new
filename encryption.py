# pyre-ignore-all-errors
import os  # type: ignore  # pyre-ignore
import hashlib  # type: ignore  # pyre-ignore
import hmac  # type: ignore  # pyre-ignore
import base64  # type: ignore  # pyre-ignore
import json  # type: ignore  # pyre-ignore
import time  # type: ignore  # pyre-ignore
import secrets  # type: ignore  # pyre-ignore
from typing import Dict, Any, Optional  # type: ignore  # pyre-ignore
from cryptography.fernet import Fernet  # type: ignore  # pyre-ignore
from cryptography.hazmat.primitives import hashes  # type: ignore  # pyre-ignore
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # type: ignore  # pyre-ignore

class SecureChannel:
    def __init__(self, encryption_key: Optional[str] = None):  # type: ignore  # pyre-ignore
        self.key = self._derive_key(encryption_key) if encryption_key else self._generate_key()
        self.fernet = Fernet(self.key)
        self.command_hmac_key = secrets.token_hex(32)
        self._command_log: Dict[str, list] = {}  # type: ignore  # pyre-ignore
        self._rate_limits: Dict[str, Dict] = {}  # type: ignore  # pyre-ignore
        
    def _generate_key(self) -> bytes:  # type: ignore  # pyre-ignore
        key = Fernet.generate_key()
        key_file = ".secure_key"
        if not os.path.exists(key_file):
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
        return key
        
    def _derive_key(self, password: str) -> bytes:  # type: ignore  # pyre-ignore
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'nova_secure_channel_salt',
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def encrypt(self, data: str) -> str:  # type: ignore  # pyre-ignore
        encrypted = self.fernet.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:  # type: ignore  # pyre-ignore
        try:
            decoded = base64.b64decode(encrypted_data.encode())
            return self.fernet.decrypt(decoded).decode()
        except Exception:
            return None  # type: ignore  # pyre-ignore
    
    def sign_command(self, command: str, user_id: str) -> str:  # type: ignore  # pyre-ignore
        timestamp = str(int(time.time()))
        message = f"{user_id}:{command}:{timestamp}"
        signature = hmac.new(
            self.command_hmac_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        log_entry = {
            "command": command,
            "user_id": user_id,
            "timestamp": timestamp,
            "signature": signature
        }
        
        if user_id not in self._command_log:
            self._command_log[user_id] = []
        self._command_log[user_id].append(log_entry)
        
        if len(self._command_log[user_id]) > 100:  # type: ignore  # pyre-ignore
            self._command_log[user_id] = self._command_log[user_id][-100:]  # type: ignore  # pyre-ignore
        
        return f"{signature}:{timestamp}"
    
    def verify_command(self, command: str, user_id: str, signature: str, timestamp: str, max_age: int = 300) -> bool:  # type: ignore  # pyre-ignore
        try:
            cmd_time = int(timestamp)
            current_time = int(time.time())
            
            if current_time - cmd_time > max_age:
                return False
            
            message = f"{user_id}:{command}:{timestamp}"
            expected = hmac.new(
                self.command_hmac_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected)
        except Exception:
            return False
    
    def check_rate_limit(self, user_id: str, operation: str, max_calls: int = 10, window: int = 60) -> bool:  # type: ignore  # pyre-ignore
        current_time = time.time()
        
        if user_id not in self._rate_limits:
            self._rate_limits[user_id] = {}
        
        if operation not in self._rate_limits[user_id]:  # type: ignore  # pyre-ignore
            self._rate_limits[user_id][operation] = []
        
        self._rate_limits[user_id][operation] = [
            t for t in self._rate_limits[user_id][operation]
            if current_time - t < window
        ]
        
        if len(self._rate_limits[user_id][operation]) >= max_calls:  # type: ignore  # pyre-ignore
            return False
        
        self._rate_limits[user_id][operation].append(current_time)
        return True
    
    def get_command_history(self, user_id: str) -> list:  # type: ignore  # pyre-ignore
        return self._command_log.get(user_id, [])
    
    def clear_history(self, user_id: str):
        if user_id in self._command_log:
            self._command_log[user_id] = []

class EncryptedCommand:
    def __init__(self, secure_channel: SecureChannel):
        self.channel = secure_channel
        self.dangerous_ops = {"kill_process", "run_script", "delete_file", "system_shutdown", "system_restart"}
        self.file_extensions_blacklist = {".exe", ".dll", ".bat", ".cmd", ".ps1", ".sh", ".vbs"}
    
    def create_secure_command(self, operation: str, args: dict, user_id: str) -> dict:  # type: ignore  # pyre-ignore
        cmd_data = {
            "op": operation,
            "args": args,
            "timestamp": int(time.time())
        }
        
        signed = self.channel.sign_command(json.dumps(cmd_data), user_id)
        signature, timestamp = signed.split(":")
        
        encrypted_payload = self.channel.encrypt(json.dumps(cmd_data))
        
        return {
            "encrypted": encrypted_payload,
            "signature": signature,
            "timestamp": timestamp,
            "op": operation
        }
    
    def execute_if_verified(self, command: dict, user_id: str) -> tuple[bool, str]:  # type: ignore  # pyre-ignore
        try:
            encrypted = command.get("encrypted", "")
            signature = command.get("signature", "")
            timestamp = command.get("timestamp", "")
            
            if not self.channel.verify_command(encrypted, user_id, signature, timestamp):
                return False, "Command verification failed - signature invalid or expired"
            
            decrypted = self.channel.decrypt(encrypted)
            if not decrypted:
                return False, "Decryption failed"
            
            cmd_data = json.loads(decrypted)
            operation = cmd_data.get("op")
            args = cmd_data.get("args", {})
            
            if not self.channel.check_rate_limit(user_id, operation):
                return False, f"Rate limit exceeded for {operation}"
            
            return True, {"operation": operation, "args": args}
            
        except Exception as e:
            return False, f"Verification error: {str(e)}"
    
    def validate_file_operation(self, filename: str, allowed_dir: str) -> tuple[bool, str]:  # type: ignore  # pyre-ignore
        filename = os.path.basename(filename)
        
        if os.path.dirname(filename):
            return False, "Path traversal not allowed"
        
        full_path = os.path.join(allowed_dir, filename)
        real_allowed = os.path.realpath(allowed_dir)
        real_path = os.path.realpath(full_path)
        
        if not real_path.startswith(real_allowed):
            return False, "Path outside allowed directory"
        
        ext = os.path.splitext(filename)[1].lower()
        if ext in self.file_extensions_blacklist:
            return False, f"File extension {ext} not allowed"
        
        return True, full_path

secure_channel = SecureChannel()
encrypted_commands = EncryptedCommand(secure_channel)

def get_secure_channel() -> SecureChannel:  # type: ignore  # pyre-ignore
    return secure_channel

def get_encrypted_commands() -> EncryptedCommand:  # type: ignore  # pyre-ignore
    return encrypted_commands

