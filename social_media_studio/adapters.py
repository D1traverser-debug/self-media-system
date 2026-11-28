"""Compatibility facade for the task-bound domain adapter boundary.

New handler ownership lives in social_media_studio.domain_adapters. Existing
callers may keep importing this module while the internal adapter registry is
migrated without changing task, claim, artifact or release contracts.
"""
from .domain_adapters.common import (
    DomainAdapterError, _jsonable, _mapping, _string_tuple, _input_json,
    _input_path, _safe_filename, _write_json,
)
from .domain_adapters.business import *
from .domain_adapters.editorial import *
from .domain_adapters.identity import *
from .domain_adapters.motion import *
from .domain_adapters.lineage import *
from .domain_adapters.media_qa import *
from .domain_adapters.visual import *
from .domain_adapters.registry import (
    DOMAIN_ADAPTERS, SUPPORTED_DOMAIN_ADAPTERS, supports_domain_adapter,
    public_domain_adapter_registry,
)
from .domain_adapters.dispatch import run_claimed_domain_adapter
from .engine import ContractError, StudioEngine, StudioError

# Preserve private helper imports used by existing tests and integrations.
from .domain_adapters.motion import _string_sequence, _model_routing_request
