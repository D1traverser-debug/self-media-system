from __future__ import annotations

import inspect

from social_media_studio.domain_adapters.registry import DOMAIN_ADAPTERS


def test_registered_handlers_receive_only_declared_data_not_engine_authority():
    expected = ["project_id", "packet", "config", "outputs", "output_dir", "attempt", "name"]
    for spec in DOMAIN_ADAPTERS.values():
        parameters = list(inspect.signature(spec.handler).parameters)
        assert parameters == expected
        assert "engine" not in parameters
