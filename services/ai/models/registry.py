import json
import os
import sqlite3
from datetime import datetime
from typing import List, Optional

from core.logging.logger import CoreLogger
from services.ai.models.metadata import ModelMetadata
from services.ai.models.storage import ModelStorage
from services.ai.models.types import ModelCategory, ModelFramework, ModelStatus


class ModelRegistry:
    def __init__(self, storage: ModelStorage):
        self.storage = storage
        self._logger = CoreLogger.get_logger("zeus.models.registry")
        self.db_path = os.path.join(self.storage.get_base_path(), "registry.db")
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS models (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        category TEXT NOT NULL,
                        framework TEXT NOT NULL,
                        version TEXT NOT NULL,
                        sha256 TEXT NOT NULL,
                        install_path TEXT NOT NULL,
                        status TEXT NOT NULL,
                        description TEXT,
                        languages TEXT,
                        author TEXT,
                        homepage TEXT,
                        license_url TEXT,
                        min_zeus_version TEXT,
                        supported_platforms TEXT,
                        supported_architectures TEXT,
                        tags TEXT,
                        installed_date TIMESTAMP,
                        last_updated TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
            self._logger.error(f"Failed to initialize Model Registry DB: {e}")

    def _row_to_metadata(self, row) -> ModelMetadata:
        return ModelMetadata(
            id=row[0],
            name=row[1],
            category=ModelCategory(row[2]),
            framework=ModelFramework(row[3]),
            version=row[4],
            sha256=row[5],
            install_path=row[6],
            status=ModelStatus(row[7]),
            description=row[8],
            languages=json.loads(row[9]) if row[9] else [],
            author=row[10],
            homepage=row[11],
            license_url=row[12],
            min_zeus_version=row[13],
            supported_platforms=json.loads(row[14]) if row[14] else [],
            supported_architectures=json.loads(row[15]) if row[15] else [],
            tags=json.loads(row[16]) if row[16] else [],
            installed_date=datetime.fromisoformat(row[17]) if row[17] else None,
            last_updated=datetime.fromisoformat(row[18]) if row[18] else None,
        )

    def register_model(self, metadata: ModelMetadata) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO models 
                    (id, name, category, framework, version, sha256, install_path, status, description, 
                     languages, author, homepage, license_url, min_zeus_version, supported_platforms, 
                     supported_architectures, tags, installed_date, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        metadata.id,
                        metadata.name,
                        metadata.category.value,
                        metadata.framework.value,
                        metadata.version,
                        metadata.sha256,
                        metadata.install_path,
                        metadata.status.value,
                        metadata.description,
                        json.dumps(metadata.languages),
                        metadata.author,
                        metadata.homepage,
                        metadata.license_url,
                        metadata.min_zeus_version,
                        json.dumps(metadata.supported_platforms),
                        json.dumps(metadata.supported_architectures),
                        json.dumps(metadata.tags),
                        (
                            metadata.installed_date.isoformat()
                            if metadata.installed_date
                            else None
                        ),
                        (
                            metadata.last_updated.isoformat()
                            if metadata.last_updated
                            else None
                        ),
                    ),
                )
                conn.commit()
                self._logger.info(f"Registered model {metadata.id} in registry.")
        except Exception as e:
            self._logger.error(f"Failed to register model {metadata.id}: {e}")

    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM models WHERE id = ?", (model_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_metadata(row)
        except Exception as e:
            self._logger.error(f"Failed to get model {model_id}: {e}")
        return None

    def get_all_models(self) -> List[ModelMetadata]:
        models = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM models")
                for row in cursor:
                    models.append(self._row_to_metadata(row))
        except Exception as e:
            self._logger.error(f"Failed to list all models: {e}")
        return models

    def delete_model(self, model_id: str) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM models WHERE id = ?", (model_id,))
                conn.commit()
                self._logger.info(f"Deleted model {model_id} from registry.")
        except Exception as e:
            self._logger.error(f"Failed to delete model {model_id}: {e}")
