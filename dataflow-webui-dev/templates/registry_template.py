"""
DataFlow WebUI 通用 Registry 模板
用法：复制到 backend/app/services/{feature}_registry.py，替换 Feature/feature 占位符
"""
import yaml
import os
from typing import Dict, List, Any
from app.core.config import settings


class FeatureRegistry:
    """Feature 管理类，使用 YAML 平文件持久化"""
    def __init__(self, path: str | None = None):
        self.path = path or settings.FEATURE_REGISTRY  # 在 config.py 中添加对应路径
        self._ensure()

    def _ensure(self):
        if not os.path.exists(self.path):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, 'w') as f:
                yaml.dump({}, f)

    def _get_all(self) -> Dict[str, Any]:
        with open(self.path, 'r') as f:
            data = yaml.safe_load(f)
        return data or {}

    def _get(self, id: str) -> Dict[str, Any] | None:
        data = self._get_all()
        item = data.get(id)
        if not item:
            return None
        item['id'] = id
        return item

    def _set(self, name: str, **kwargs) -> str:
        data = self._get_all()
        new_id = os.urandom(8).hex()
        data[new_id] = {"name": name, **kwargs}
        with open(self.path, 'w') as f:
            yaml.dump(data, f)
        return new_id

    def _update(self, id: str, **kwargs) -> bool:
        data = self._get_all()
        if id not in data:
            return False
        for k, v in kwargs.items():
            if v is not None:
                data[id][k] = v
        with open(self.path, 'w') as f:
            yaml.dump(data, f)
        return True

    def _delete(self, id: str) -> bool:
        data = self._get_all()
        if id not in data:
            return False
        del data[id]
        with open(self.path, 'w') as f:
            yaml.dump(data, f)
        return True
