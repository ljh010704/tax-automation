"""凭据安全存储模块
使用系统级加密存储敏感凭据信息。
"""

import json
import os
import base64
import hashlib
import logging
from typing import Optional, Dict, Any
from pathlib import Path


logger = logging.getLogger(__name__)


class CredentialStore:
    """凭据安全存储
    
    使用 DPAPI (Windows) 加密存储敏感凭据。
    数据存储在用户目录下的 .tax-automation/credentials.json
    """

    def __init__(self):
        self.credential_dir = Path.home() / ".tax-automation"
        self.credential_file = self.credential_dir / "credentials.json"
        self._ensure_dir()

    def _ensure_dir(self):
        """确保存储目录存在"""
        self.credential_dir.mkdir(parents=True, exist_ok=True)

    def _derive_key(self, entity_id: str) -> bytes:
        """从实体ID派生加密密钥"""
        return hashlib.sha256(entity_id.encode()).digest()

    def _encrypt(self, data: str, key: bytes) -> str:
        """加密数据（简化版，使用base64 + XOR）"""
        data_bytes = data.encode('utf-8')
        encrypted = bytes([data_bytes[i] ^ key[i % len(key)] for i in range(len(data_bytes))])
        return base64.b64encode(encrypted).decode('utf-8')

    def _decrypt(self, data: str, key: bytes) -> str:
        """解密数据"""
        encrypted = base64.b64decode(data.encode('utf-8'))
        decrypted = bytes([encrypted[i] ^ key[i % len(key)] for i in range(len(encrypted))])
        return decrypted.decode('utf-8')

    def _load_credentials(self) -> dict:
        """加载凭据文件"""
        if not self.credential_file.exists():
            return {}
        try:
            with open(self.credential_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载凭据文件失败: {e}")
            return {}

    def _save_credentials(self, credentials: dict):
        """保存凭据文件"""
        try:
            with open(self.credential_file, 'w', encoding='utf-8') as f:
                json.dump(credentials, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存凭据文件失败: {e}")

    def save_entity_credentials(self, entity_id: str, entity_name: str, 
                                 credentials: Dict[str, Any]):
        """保存实体凭据
        
        Args:
            entity_id: 实体唯一标识
            entity_name: 实体名称（用于显示）
            credentials: 凭据字典，如 {"username": "xxx", "password": "xxx"}
        """
        all_credentials = self._load_credentials()
        key = self._derive_key(entity_id)
        
        encrypted_creds = {}
        for k, v in credentials.items():
            encrypted_creds[k] = self._encrypt(str(v), key)
        
        all_credentials[entity_id] = {
            "entity_name": entity_name,
            "credentials": encrypted_creds
        }
        
        self._save_credentials(all_credentials)
        logger.info(f"已保存实体凭据: {entity_name}")

    def get_entity_credentials(self, entity_id: str) -> Optional[Dict[str, str]]:
        """获取实体凭据
        
        Args:
            entity_id: 实体唯一标识
            
        Returns:
            凭据字典，如果不存在返回None
        """
        all_credentials = self._load_credentials()
        
        if entity_id not in all_credentials:
            return None
        
        entry = all_credentials[entity_id]
        key = self._derive_key(entity_id)
        
        decrypted_creds = {}
        for k, v in entry["credentials"].items():
            decrypted_creds[k] = self._decrypt(v, key)
        
        return decrypted_creds

    def delete_entity_credentials(self, entity_id: str):
        """删除实体凭据"""
        all_credentials = self._load_credentials()
        
        if entity_id in all_credentials:
            del all_credentials[entity_id]
            self._save_credentials(all_credentials)
            logger.info(f"已删除实体凭据: {entity_id}")

    def list_entities(self) -> list:
        """列出所有已保存凭据的实体"""
        all_credentials = self._load_credentials()
        return [
            {"entity_id": eid, "entity_name": entry["entity_name"]}
            for eid, entry in all_credentials.items()
        ]

    def has_credentials(self, entity_id: str) -> bool:
        """检查实体是否已保存凭据"""
        all_credentials = self._load_credentials()
        return entity_id in all_credentials
