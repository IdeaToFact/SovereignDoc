# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

import shutil
from pathlib import Path
from app.config import settings


class StorageManager:
    """Central manager for local workspace directories, vaults, and caches."""

    def __init__(self, base_dir: Path = settings.base_data_dir):
        self.base_dir = Path(base_dir)
        self.vaults_dir = self.base_dir / "vaults"
        self.cache_dir = self.base_dir / "cache"
        self.db_dir = self.base_dir / "db"
        self.initialize_dirs()

    def initialize_dirs(self) -> None:
        """Create necessary local directories if they do not exist."""
        for path in [self.base_dir, self.vaults_dir, self.cache_dir, self.db_dir]:
            try:
                path.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                pass

    def create_vault(self, vault_id: str) -> Path:
        """Create a new vault directory."""
        vault_path = self.get_vault_path(vault_id)
        vault_path.mkdir(parents=True, exist_ok=True)
        return vault_path

    def get_vault_path(self, vault_id: str) -> Path:
        """Get or create path for a specific document vault."""
        vault_path = self.vaults_dir / vault_id
        vault_path.mkdir(parents=True, exist_ok=True)
        return vault_path

    def get_cache_path(self) -> Path:
        """Return the local cache directory."""
        return self.cache_dir

    def cleanup_cache(self) -> None:
        """Clear temporary cache files."""
        if self.cache_dir.exists():
            for item in self.cache_dir.glob("*"):
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)


storage_manager = StorageManager()
