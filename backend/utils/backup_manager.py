import os
import logging
import shutil
import subprocess
import json
import gzip
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import asyncio
import aioredis
from cryptography.fernet import Fernet
from fastapi import HTTPException

class BackupConfig:
    def __init__(self):
        self.backup_dir = os.getenv('BACKUP_DIR', '/var/backups/quantum_trader')
        self.max_backups = int(os.getenv('MAX_BACKUPS', '7'))
        self.backup_interval = int(os.getenv('BACKUP_INTERVAL', '24'))  # hours
        self.encryption_key = os.getenv('ENCRYPTION_KEY')
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_pool = None
        self.initialize_redis()
    
    async def initialize_redis(self) -> None:
        """Initialize Redis connection"""
        try:
            self.redis_pool = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis_pool.ping()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Redis initialization failed: {str(e)}")

class BackupManager:
    def __init__(self, config: BackupConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.backup_dir = self.config.backup_dir
        self.max_backups = self.config.max_backups
        self.backup_interval = self.config.backup_interval
        self.encryption_key = self.config.encryption_key
        self.redis_pool = self.config.redis_pool
        self.initialize_backup_dir()
    
    def initialize_backup_dir(self) -> None:
        """Create backup directory if it doesn't exist"""
        os.makedirs(self.backup_dir, exist_ok=True)
        self.logger.info(f"Backup directory initialized: {self.backup_dir}")
    
    async def create_backup(self, data: Dict[str, Any]) -> str:
        """Create a new backup"""
        try:
            # Generate backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(self.backup_dir, f'backup_{timestamp}.json.gz')
            
            # Compress and encrypt data
            compressed_data = self._compress_data(data)
            encrypted_data = self._encrypt_data(compressed_data)
            
            # Write to file
            with open(backup_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Store metadata in Redis
            metadata = {
                'timestamp': timestamp,
                'size': os.path.getsize(backup_file),
                'hash': self._calculate_hash(encrypted_data),
                'status': 'completed'
            }
            await self.redis_pool.rpush('backup_metadata', json.dumps(metadata))
            
            # Clean up old backups
            await self.cleanup_old_backups()
            
            return backup_file
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Backup creation failed: {str(e)}")
    
    def _compress_data(self, data: Dict[str, Any]) -> bytes:
        """Compress data using gzip"""
        json_data = json.dumps(data).encode()
        return gzip.compress(json_data)
    
    def _encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data using Fernet"""
        if not self.encryption_key:
            raise HTTPException(status_code=500, detail="Encryption key not configured")
            
        fernet = Fernet(self.encryption_key)
        return fernet.encrypt(data)
    
    def _calculate_hash(self, data: bytes) -> str:
        """Calculate SHA-256 hash of data"""
        return hashlib.sha256(data).hexdigest()
    
    async def restore_backup(self, backup_file: str) -> Dict[str, Any]:
        """Restore from backup"""
        try:
            # Read encrypted data
            with open(backup_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt data
            decrypted_data = self._decrypt_data(encrypted_data)
            
            # Decompress data
            decompressed_data = self._decompress_data(decrypted_data)
            
            # Verify hash
            if not self._verify_hash(encrypted_data, backup_file):
                raise HTTPException(status_code=400, detail="Backup file corrupted")
            
            return json.loads(decompressed_data.decode())
            
        except Exception as e:
            self.logger.error(f"Backup restoration failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Backup restoration failed: {str(e)}")
    
    def _decrypt_data(self, data: bytes) -> bytes:
        """Decrypt data using Fernet"""
        if not self.encryption_key:
            raise HTTPException(status_code=500, detail="Encryption key not configured")
            
        fernet = Fernet(self.encryption_key)
        return fernet.decrypt(data)
    
    def _decompress_data(self, data: bytes) -> bytes:
        """Decompress data using gzip"""
        return gzip.decompress(data)
    
    def _verify_hash(self, data: bytes, backup_file: str) -> bool:
        """Verify backup file integrity"""
        calculated_hash = self._calculate_hash(data)
        metadata = await self.get_backup_metadata(backup_file)
        return calculated_hash == metadata.get('hash')
    
    async def get_backup_metadata(self, backup_file: str) -> Dict[str, Any]:
        """Get backup metadata from Redis"""
        try:
            metadata = await self.redis_pool.lrange('backup_metadata', 0, -1)
            for meta in metadata:
                meta_dict = json.loads(meta)
                if meta_dict['timestamp'] in backup_file:
                    return meta_dict
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to get backup metadata: {str(e)}")
            return {}
    
    async def cleanup_old_backups(self) -> None:
        """Clean up old backups"""
        try:
            # Get list of backup files
            backup_files = [f for f in os.listdir(self.backup_dir) if f.startswith('backup_')]
            
            # Sort by timestamp (newest first)
            backup_files.sort(reverse=True)
            
            # Remove old backups
            for file in backup_files[self.max_backups:]:
                os.remove(os.path.join(self.backup_dir, file))
                self.logger.info(f"Removed old backup: {file}")
            
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {str(e)}")
    
    async def list_backups(self) -> list:
        """List available backups"""
        try:
            backup_files = [f for f in os.listdir(self.backup_dir) if f.startswith('backup_')]
            backups = []
            
            for file in backup_files:
                file_path = os.path.join(self.backup_dir, file)
                metadata = await self.get_backup_metadata(file)
                backups.append({
                    'filename': file,
                    'size': os.path.getsize(file_path),
                    'timestamp': metadata.get('timestamp'),
                    'status': metadata.get('status')
                })
            
            return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to list backups: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")
    
    async def verify_backup_integrity(self, backup_file: str) -> bool:
        """Verify backup file integrity"""
        try:
            with open(backup_file, 'rb') as f:
                data = f.read()
            
            # Verify hash
            if not self._verify_hash(data, backup_file):
                return False
            
            # Try to decrypt and decompress
            decrypted = self._decrypt_data(data)
            decompressed = self._decompress_data(decrypted)
            
            # Verify JSON structure
            try:
                json.loads(decompressed.decode())
                return True
            except json.JSONDecodeError:
                return False
            
        except Exception as e:
            self.logger.error(f"Backup verification failed: {str(e)}")
            return False
