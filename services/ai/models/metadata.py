from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from services.ai.models.types import ModelCategory, ModelFramework, ModelStatus


@dataclass
class ModelMetadata:
    id: str
    name: str
    category: ModelCategory
    framework: ModelFramework
    version: str
    sha256: str
    install_path: str
    status: ModelStatus
    description: str = ""
    languages: List[str] = field(default_factory=list)
    author: str = ""
    homepage: str = ""
    license_url: str = ""
    min_zeus_version: str = "0.0.1"
    supported_platforms: List[str] = field(
        default_factory=lambda: ["windows", "linux", "darwin"]
    )
    supported_architectures: List[str] = field(
        default_factory=lambda: ["x86_64", "arm64"]
    )
    tags: List[str] = field(default_factory=list)
    installed_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None


@dataclass
class ModelManifest:
    id: str
    name: str
    version: str
    checksum: str
    framework: ModelFramework
    category: ModelCategory
    entry_file: str
    dependencies: List[str] = field(default_factory=list)
    min_zeus_version: str = "0.0.1"
    supported_platforms: List[str] = field(
        default_factory=lambda: ["windows", "linux", "darwin"]
    )
    supported_architectures: List[str] = field(
        default_factory=lambda: ["x86_64", "arm64"]
    )
    download_url: str = ""
