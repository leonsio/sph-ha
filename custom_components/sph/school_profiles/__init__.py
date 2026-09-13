"""Registry and helpers for school-specific profiles."""

from __future__ import annotations

from .base import SchoolProfile
from .kfg import KFGProfile

SCHOOL_PROFILE_NONE = "none"
DEFAULT_SCHOOL_PROFILE = SCHOOL_PROFILE_NONE

_PROFILES: dict[str, SchoolProfile] = {
    SCHOOL_PROFILE_NONE: SchoolProfile(),
    KFGProfile.id: KFGProfile(),
}


def get_school_profile(entry) -> SchoolProfile:
    """Return the configured profile for one child/config entry."""
    name = str(entry.data.get("school_profile", DEFAULT_SCHOOL_PROFILE) or DEFAULT_SCHOOL_PROFILE)
    return _PROFILES.get(name, _PROFILES[SCHOOL_PROFILE_NONE])


def school_profile_options() -> list[dict[str, str]]:
    """Return config-flow selector options."""
    return [
        {"value": profile.id, "label": profile.name}
        for profile in _PROFILES.values()
    ]


def available_school_profiles() -> dict[str, SchoolProfile]:
    """Return a copy of the profile registry for diagnostics/tests."""
    return dict(_PROFILES)


__all__ = [
    "SchoolProfile",
    "SCHOOL_PROFILE_NONE",
    "DEFAULT_SCHOOL_PROFILE",
    "get_school_profile",
    "school_profile_options",
    "available_school_profiles",
]
