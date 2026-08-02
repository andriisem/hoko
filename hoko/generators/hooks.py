from __future__ import annotations

from hoko.capabilities.registry import ANY_ECOSYSTEM, Capability


def hook_ids_for(capability: Capability, ecosystems: list[str]) -> list[str]:
    """Resolve which tool hook ids a capability contributes for a project.

    Ecosystem-specific tools take precedence over the capability's
    ecosystem-agnostic ("*") tools.
    """
    for ecosystem in ecosystems:
        if ecosystem in capability.tools_by_ecosystem:
            return capability.tools_by_ecosystem[ecosystem]
    return capability.tools_by_ecosystem.get(ANY_ECOSYSTEM, [])
