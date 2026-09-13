"""Dynamic discovery and helpers for school-specific profiles."""

from __future__ import annotations

from importlib import import_module
import logging
from pathlib import Path
import re

from .base import SchoolProfile

_LOGGER = logging.getLogger(__name__)

SCHOOL_PROFILE_NONE = "none"
DEFAULT_SCHOOL_PROFILE = SCHOOL_PROFILE_NONE
_PROFILE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_PROFILE_ROOT = Path(__file__).parent


def _discover_school_profiles() -> dict[str, SchoolProfile]:
    """Discover profile packages from school_profiles/<id>/profile.py."""
    profiles: dict[str, SchoolProfile] = {
        SCHOOL_PROFILE_NONE: SchoolProfile(),
    }

    for directory in sorted(_PROFILE_ROOT.iterdir(), key=lambda item: item.name):
        if not directory.is_dir() or directory.name.startswith((".", "_")):
            continue
        profile_file = directory / "profile.py"
        if not profile_file.is_file():
            continue

        try:
            module = import_module(f"{__name__}.{directory.name}.profile")
        except Exception as err:  # pragma: no cover - defensive runtime isolation
            _LOGGER.exception("Schul-Profil %s konnte nicht geladen werden: %s", directory.name, err)
            continue

        profile = getattr(module, "PROFILE", None)
        if isinstance(profile, type) and issubclass(profile, SchoolProfile):
            profile = profile()
        if not isinstance(profile, SchoolProfile):
            _LOGGER.error(
                "Schul-Profil %s exportiert kein gültiges PROFILE-Objekt",
                directory.name,
            )
            continue

        profile_id = str(profile.id or "").strip()
        if not _PROFILE_ID.fullmatch(profile_id):
            _LOGGER.error("Ungültige Schul-Profil-ID %r in %s", profile_id, profile_file)
            continue
        if profile_id != directory.name:
            _LOGGER.error(
                "Schul-Profil-ID %s muss dem Ordnernamen %s entsprechen",
                profile_id,
                directory.name,
            )
            continue
        if profile_id in profiles:
            _LOGGER.error("Doppelte Schul-Profil-ID %s", profile_id)
            continue

        frontend_module = str(profile.frontend_module or "").strip()
        if frontend_module:
            frontend_file = directory / "frontend" / frontend_module
            if not frontend_file.is_file():
                _LOGGER.error(
                    "Schul-Profil %s verweist auf fehlendes Frontend %s",
                    profile_id,
                    frontend_file,
                )
                continue

        profiles[profile_id] = profile

    return profiles


_PROFILES = _discover_school_profiles()


def get_school_profile(entry) -> SchoolProfile:
    """Return the configured profile for one child/config entry."""
    name = str(entry.data.get("school_profile", DEFAULT_SCHOOL_PROFILE) or DEFAULT_SCHOOL_PROFILE)
    return _PROFILES.get(name, _PROFILES[SCHOOL_PROFILE_NONE])


def school_profile_options() -> list[dict[str, str]]:
    """Return selector options supplied by the discovered profiles."""
    standard = _PROFILES[SCHOOL_PROFILE_NONE]
    others = sorted(
        (profile for key, profile in _PROFILES.items() if key != SCHOOL_PROFILE_NONE),
        key=lambda profile: profile.name.casefold(),
    )
    return [profile.config_option() for profile in (standard, *others)]


def available_school_profiles() -> dict[str, SchoolProfile]:
    """Return a copy of the discovered profile registry."""
    return dict(_PROFILES)


def school_profile_metadata() -> dict[str, dict]:
    """Return profile-owned metadata for diagnostics and generic consumers."""
    return {profile_id: profile.metadata() for profile_id, profile in _PROFILES.items()}


def school_profile_frontend_paths() -> list[tuple[str, Path]]:
    """Return URL ids and frontend directories for profiles with UI assets."""
    result: list[tuple[str, Path]] = []
    for profile_id, profile in _PROFILES.items():
        if profile_id == SCHOOL_PROFILE_NONE or not profile.frontend_module:
            continue
        result.append((profile_id, _PROFILE_ROOT / profile_id / "frontend"))
    return result


__all__ = [
    "SchoolProfile",
    "SCHOOL_PROFILE_NONE",
    "DEFAULT_SCHOOL_PROFILE",
    "get_school_profile",
    "school_profile_options",
    "available_school_profiles",
    "school_profile_metadata",
    "school_profile_frontend_paths",
]
