"""
End-to-End Encryption Manager
Provides encryption/decryption for sensitive data with key management.
"""

import os
import json
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import base64


class EncryptionAlgorithm(Enum):
    AES_256_GCM = "aes_256_gcm"
    CHACHA20_POLY1305 = "chacha20_poly1305"


class KeyStatus(Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass
class EncryptionKey:
    key_id: str
    user_id: str
    algorithm: EncryptionAlgorithm
    public_key: str  # Base64 encoded
    private_key: Optional[str] = None  # Base64 encoded (encrypted)
    created_at: str = None
    expires_at: Optional[str] = None
    status: KeyStatus = KeyStatus.ACTIVE
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class EncryptedData:
    data_id: str
    user_id: str
    encrypted_content: str  # Base64 encoded
    algorithm: EncryptionAlgorithm
    key_id: str
    nonce: str  # Base64 encoded
    metadata: Dict[str, Any] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class EncryptionManager:
    def __init__(self, master_password: str = None):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.encryption_dir = os.path.join(self.base_dir, "data", "encryption")
        self.keys_file = os.path.join(self.encryption_dir, "keys.json")
        self.data_file = os.path.join(self.encryption_dir, "encrypted_data.json")
        
        os.makedirs(self.encryption_dir, exist_ok=True)
        
        # Master key derivation
        self.master_password = master_password or os.environ.get('JARVIS_ENCRYPTION_KEY', 'default_key_change_me')
        self.master_key = self._derive_master_key(self.master_password)
        
        # Load data
        self.keys = self._load_keys()
        self.encrypted_data = self._load_encrypted_data()
        
        # Default algorithm
        self.default_algorithm = EncryptionAlgorithm.AES_256_GCM

    def _derive_master_key(self, password: str) -> bytes:
        """Derive master key from password using PBKDF2."""
        try:
            import hashlib
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.backends import default_backend
            
            salt = b'JARVIS_ENCRYPTION_SALT'  # In production, use random salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            return kdf.derive(password.encode())
        except ImportError:
            # Fallback to simple hash if cryptography not available
            return hashlib.sha256(password.encode()).digest()

    def _load_keys(self) -> Dict[str, EncryptionKey]:
        """Load encryption keys from disk."""
        if os.path.exists(self.keys_file):
            try:
                with open(self.keys_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {key_id: EncryptionKey(**key) for key_id, key in data.items()}
            except Exception:
                pass
        return {}

    def _save_keys(self):
        """Save encryption keys to disk."""
        try:
            data = {key_id: asdict(key) for key_id, key in self.keys.items()}
            with open(self.keys_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[EncryptionManager] Failed to save keys: {e}")

    def _load_encrypted_data(self) -> Dict[str, EncryptedData]:
        """Load encrypted data from disk."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {data_id: EncryptedData(**data) for data_id, data in data.items()}
            except Exception:
                pass
        return {}

    def _save_encrypted_data(self):
        """Save encrypted data to disk."""
        try:
            data = {data_id: asdict(data) for data_id, data in self.encrypted_data.items()}
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[EncryptionManager] Failed to save encrypted data: {e}")

    def generate_key_pair(self, user_id: str, algorithm: EncryptionAlgorithm = None) -> EncryptionKey:
        """
        Generate a new encryption key pair for a user.
        
        Args:
            user_id: User ID
            algorithm: Encryption algorithm to use
            
        Returns:
            EncryptionKey with public/private key pair
        """
        algorithm = algorithm or self.default_algorithm
        key_id = f"key_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.backends import default_backend
            
            # Generate RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            public_key = private_key.public_key()
            
            # Serialize keys
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # Encrypt private key with master key
            encrypted_private_key = self._encrypt_with_master_key(private_pem)
            
            key = EncryptionKey(
                key_id=key_id,
                user_id=user_id,
                algorithm=algorithm,
                public_key=base64.b64encode(public_pem).decode('utf-8'),
                private_key=base64.b64encode(encrypted_private_key).decode('utf-8')
            )
            
            self.keys[key_id] = key
            self._save_keys()
            
            return key
            
        except ImportError:
            # Fallback: generate simple symmetric key
            import secrets
            symmetric_key = secrets.token_bytes(32)
            encrypted_key = self._encrypt_with_master_key(symmetric_key)
            
            key = EncryptionKey(
                key_id=key_id,
                user_id=user_id,
                algorithm=algorithm,
                public_key=base64.b64encode(symmetric_key).decode('utf-8'),
                private_key=base64.b64encode(encrypted_key).decode('utf-8')
            )
            
            self.keys[key_id] = key
            self._save_keys()
            
            return key

    def _encrypt_with_master_key(self, data: bytes) -> bytes:
        """Encrypt data with master key."""
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            
            # Generate nonce
            nonce = os.urandom(12)
            
            # Encrypt
            cipher = Cipher(
                algorithms.AES(self.master_key),
                modes.GCM(nonce),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            encrypted = encryptor.update(data) + encryptor.finalize()
            
            # Return nonce + encrypted data + tag
            return nonce + encryptor.tag + encrypted
            
        except ImportError:
            # Fallback: XOR with master key (NOT SECURE, only for fallback)
            key_bytes = self.master_key
            return bytes([data[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(data))])

    def _decrypt_with_master_key(self, encrypted_data: bytes) -> bytes:
        """Decrypt data encrypted with master key."""
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            
            # Extract nonce, tag, and ciphertext
            nonce = encrypted_data[:12]
            tag = encrypted_data[12:28]
            ciphertext = encrypted_data[28:]
            
            # Decrypt
            cipher = Cipher(
                algorithms.AES(self.master_key),
                modes.GCM(nonce, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            return decryptor.update(ciphertext) + decryptor.finalize()
            
        except ImportError:
            # Fallback: XOR with master key
            key_bytes = self.master_key
            return bytes([encrypted_data[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(encrypted_data))])

    def encrypt_data(self, user_id: str, data: str, key_id: str = None,
                    metadata: Dict[str, Any] = None) -> EncryptedData:
        """
        Encrypt data for a user.
        
        Args:
            user_id: User ID
            data: Data to encrypt
            key_id: Key ID to use (auto-select if None)
            metadata: Additional metadata
            
        Returns:
            EncryptedData with encrypted content
        """
        # Select key if not provided
        if key_id is None:
            user_keys = [k for k in self.keys.values() if k.user_id == user_id and k.status == KeyStatus.ACTIVE]
            if not user_keys:
                # Generate new key
                key = self.generate_key_pair(user_id)
                key_id = key.key_id
            else:
                key_id = user_keys[0].key_id
        
        if key_id not in self.keys:
            raise ValueError(f"Key not found: {key_id}")
        
        key = self.keys[key_id]
        
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            
            # Get encryption key
            if key.private_key:
                encrypted_private = base64.b64decode(key.private_key)
                private_key = self._decrypt_with_master_key(encrypted_private)
            else:
                private_key = base64.b64decode(key.public_key)
            
            # Generate nonce
            nonce = os.urandom(12)
            
            # Encrypt
            cipher = Cipher(
                algorithms.AES(private_key),
                modes.GCM(nonce),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            encrypted = encryptor.update(data.encode('utf-8')) + encryptor.finalize()
            
            data_id = f"data_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            encrypted_data = EncryptedData(
                data_id=data_id,
                user_id=user_id,
                encrypted_content=base64.b64encode(nonce + encryptor.tag + encrypted).decode('utf-8'),
                algorithm=key.algorithm,
                key_id=key_id,
                nonce=base64.b64encode(nonce).decode('utf-8'),
                metadata=metadata or {}
            )
            
            self.encrypted_data[data_id] = encrypted_data
            self._save_encrypted_data()
            
            return encrypted_data
            
        except ImportError:
            # Fallback: simple XOR encryption
            key_bytes = private_key if isinstance(private_key, bytes) else base64.b64decode(key.public_key)
            data_bytes = data.encode('utf-8')
            encrypted = bytes([data_bytes[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(data_bytes))])
            
            data_id = f"data_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            encrypted_data = EncryptedData(
                data_id=data_id,
                user_id=user_id,
                encrypted_content=base64.b64encode(encrypted).decode('utf-8'),
                algorithm=key.algorithm,
                key_id=key_id,
                nonce="",
                metadata=metadata or {}
            )
            
            self.encrypted_data[data_id] = encrypted_data
            self._save_encrypted_data()
            
            return encrypted_data

    def decrypt_data(self, data_id: str) -> Optional[str]:
        """
        Decrypt data by ID.
        
        Args:
            data_id: Data ID to decrypt
            
        Returns:
            Decrypted data string or None if failed
        """
        if data_id not in self.encrypted_data:
            return None
        
        encrypted_data = self.encrypted_data[data_id]
        key_id = encrypted_data.key_id
        
        if key_id not in self.keys:
            return None
        
        key = self.keys[key_id]
        
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            
            # Get decryption key
            if key.private_key:
                encrypted_private = base64.b64decode(key.private_key)
                private_key = self._decrypt_with_master_key(encrypted_private)
            else:
                private_key = base64.b64decode(key.public_key)
            
            # Decode encrypted content
            encrypted_bytes = base64.b64decode(encrypted_data.encrypted_content)
            
            # Extract nonce, tag, and ciphertext
            nonce = encrypted_bytes[:12]
            tag = encrypted_bytes[12:28]
            ciphertext = encrypted_bytes[28:]
            
            # Decrypt
            cipher = Cipher(
                algorithms.AES(private_key),
                modes.GCM(nonce, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            decrypted = decryptor.update(ciphertext) + decryptor.finalize()
            
            return decrypted.decode('utf-8')
            
        except ImportError:
            # Fallback: simple XOR decryption
            key_bytes = private_key if isinstance(private_key, bytes) else base64.b64decode(key.public_key)
            encrypted_bytes = base64.b64decode(encrypted_data.encrypted_content)
            decrypted = bytes([encrypted_bytes[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(encrypted_bytes))])
            
            return decrypted.decode('utf-8')

    def revoke_key(self, key_id: str) -> bool:
        """Revoke an encryption key."""
        if key_id not in self.keys:
            return False
        
        self.keys[key_id].status = KeyStatus.REVOKED
        self._save_keys()
        
        return True

    def delete_encrypted_data(self, data_id: str) -> bool:
        """Delete encrypted data."""
        if data_id not in self.encrypted_data:
            return False
        
        del self.encrypted_data[data_id]
        self._save_encrypted_data()
        
        return True

    def get_user_keys(self, user_id: str) -> List[EncryptionKey]:
        """Get all keys for a user."""
        return [key for key in self.keys.values() if key.user_id == user_id]

    def get_user_data(self, user_id: str) -> List[EncryptedData]:
        """Get all encrypted data for a user."""
        return [data for data in self.encrypted_data.values() if data.user_id == user_id]

    def rotate_key(self, old_key_id: str, user_id: str) -> EncryptionKey:
        """
        Rotate encryption key for a user.
        
        Args:
            old_key_id: Old key ID to replace
            user_id: User ID
            
        Returns:
            New EncryptionKey
        """
        # Revoke old key
        self.revoke_key(old_key_id)
        
        # Generate new key
        new_key = self.generate_key_pair(user_id)
        
        # Re-encrypt all data with new key
        user_data = self.get_user_data(user_id)
        for data in user_data:
            if data.key_id == old_key_id:
                # Decrypt with old key
                decrypted = self.decrypt_data(data.data_id)
                if decrypted:
                    # Encrypt with new key
                    self.encrypt_data(user_id, decrypted, new_key.key_id, data.metadata)
                    # Delete old encrypted data
                    self.delete_encrypted_data(data.data_id)
        
        return new_key

    def get_encryption_statistics(self) -> Dict[str, Any]:
        """Get encryption statistics."""
        total_keys = len(self.keys)
        total_data = len(self.encrypted_data)
        
        # Count by status
        by_status = defaultdict(int)
        for key in self.keys.values():
            by_status[key.status.value] += 1
        
        # Count by algorithm
        by_algorithm = defaultdict(int)
        for key in self.keys.values():
            by_algorithm[key.algorithm.value] += 1
        
        return {
            'total_keys': total_keys,
            'total_encrypted_data': total_data,
            'key_status': dict(by_status),
            'algorithms': dict(by_algorithm)
        }

    def export_keys(self, export_path: str) -> Tuple[bool, str]:
        """Export keys (without private keys)."""
        try:
            export_data = {
                'keys': {key_id: {
                    'key_id': key.key_id,
                    'user_id': key.user_id,
                    'algorithm': key.algorithm.value,
                    'public_key': key.public_key,
                    'created_at': key.created_at,
                    'expires_at': key.expires_at,
                    'status': key.status.value
                } for key_id, key in self.keys.items()},
                'exported_at': datetime.now().isoformat(),
                'note': 'Private keys not included for security'
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True, f"Keys exported to {export_path}"
            
        except Exception as e:
            return False, f"Export failed: {str(e)}"

    def hash_data(self, data: str) -> str:
        """Hash data for integrity verification."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def verify_data_integrity(self, data: str, expected_hash: str) -> bool:
        """Verify data integrity against expected hash."""
        return self.hash_data(data) == expected_hash

    def encrypt_file(self, file_path: str, user_id: str, key_id: str = None) -> EncryptedData:
        """
        Encrypt a file.
        
        Args:
            file_path: Path to file to encrypt
            user_id: User ID
            key_id: Key ID to use
            
        Returns:
            EncryptedData with file content
        """
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Convert to base64 string for encryption
            file_b64 = base64.b64encode(file_data).decode('utf-8')
            
            return self.encrypt_data(user_id, file_b64, key_id, 
                                   metadata={'file_path': file_path, 'type': 'file'})
            
        except Exception as e:
            print(f"[EncryptionManager] Failed to encrypt file: {e}")
            raise

    def decrypt_to_file(self, data_id: str, output_path: str) -> bool:
        """
        Decrypt data and write to file.
        
        Args:
            data_id: Data ID to decrypt
            output_path: Output file path
            
        Returns:
            True if successful
        """
        decrypted = self.decrypt_data(data_id)
        if not decrypted:
            return False
        
        try:
            file_data = base64.b64decode(decrypted)
            with open(output_path, 'wb') as f:
                f.write(file_data)
            return True
        except Exception as e:
            print(f"[EncryptionManager] Failed to write decrypted file: {e}")
            return False
