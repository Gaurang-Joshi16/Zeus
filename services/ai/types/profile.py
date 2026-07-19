from dataclasses import dataclass, field
from typing import List, Optional

from services.ai.models.types import ModelCategory, ModelFramework


@dataclass
class CapabilityDescriptor:
    capability_name: str
    supported_languages: List[str] = field(default_factory=list)
    streaming_support: bool = False
    batch_processing: bool = False
    gpu_support: bool = False
    cpu_support: bool = True
    maximum_context: int = 0
    supported_formats: List[str] = field(default_factory=list)
    sample_rates: List[int] = field(default_factory=list)
    provides_confidence_scores: bool = False
    version: str = "1.0.0"


@dataclass
class ProviderProfile:
    performance_tier: str = "balanced"
    memory_usage_mb: int = 0
    latency_ms_estimate: int = 0
    accuracy_tier: str = "standard"
    offline_support: bool = True
    cloud_support: bool = False
    gpu_requirement: str = "optional"
    recommended_use_case: str = "general"


@dataclass
class ProviderCompatibility:
    required_model_category: Optional[ModelCategory] = None
    required_framework: Optional[ModelFramework] = None
    min_runtime_version: str = "0.0.1"
    supported_platforms: List[str] = field(
        default_factory=lambda: ["windows", "linux", "darwin"]
    )
