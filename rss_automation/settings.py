"""Settings loading, validation, path resolution, and folder setup."""

from __future__ import annotations

import ctypes
import json
import os
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

from rss_automation.constants import DEFAULT_SETTINGS, PATH_SETTING_KEYS

FOLDERID_DOWNLOADS = UUID("374DE290-123F-4565-9164-39C4925E467B")


class WindowsGUID(ctypes.Structure):
    """ctypes representation of the Windows GUID structure."""

    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]


def guid_from_uuid(value: UUID) -> WindowsGUID:
    """Convert a Python UUID into a Windows GUID structure."""

    data4 = (ctypes.c_ubyte * 8).from_buffer_copy(value.bytes[8:])
    return WindowsGUID(value.time_low, value.time_mid, value.time_hi_version, data4)


def get_project_root() -> Path:
    """Return the repository/project root, assuming this package lives under it."""

    return Path(__file__).resolve().parent.parent


def get_downloads_folder() -> Path:
    """Return the current Windows Downloads known folder, with safe fallbacks."""

    if sys.platform == "win32":
        try:
            return get_windows_known_folder(FOLDERID_DOWNLOADS)
        except OSError:
            pass

    return Path.home() / "Downloads"


def get_windows_known_folder(folder_id: UUID) -> Path:
    """Read a Windows known-folder path through SHGetKnownFolderPath."""

    guid = guid_from_uuid(folder_id)
    path_ptr = ctypes.c_wchar_p()
    result = ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(path_ptr))

    if result != 0 or path_ptr.value is None:
        raise OSError(f"SHGetKnownFolderPath failed with HRESULT {result:#x}")

    try:
        return Path(path_ptr.value)
    finally:
        ctypes.windll.ole32.CoTaskMemFree(path_ptr)


def resolve_settings_path(settings_path: Path, project_root: Path) -> Path:
    """Resolve a settings path relative to the project root when needed."""

    if settings_path.is_absolute():
        return settings_path
    return project_root / settings_path


def replace_path_tokens(value: str, project_root: Path, downloads_folder: Path, root_folder: str | None = None) -> str:
    """Replace supported folder tokens inside one path string."""

    expanded = value
    replacements = {
        "${project_root}": str(project_root),
        "{project_root}": str(project_root),
        "$PROJECT_ROOT": str(project_root),
        "%PROJECT_ROOT%": str(project_root),
        "${downloads_folder}": str(downloads_folder),
        "{downloads_folder}": str(downloads_folder),
        "$DOWNLOADS_FOLDER": str(downloads_folder),
        "%DOWNLOADS_FOLDER%": str(downloads_folder),
    }

    if root_folder is not None:
        replacements.update(
            {
                "${root_folder}": root_folder,
                "{root_folder}": root_folder,
                "$ROOT_FOLDER": root_folder,
                "%ROOT_FOLDER%": root_folder,
            }
        )

    for token, replacement in replacements.items():
        expanded = expanded.replace(token, replacement)

    return expanded


def resolve_path_value(
    value: str,
    project_root: Path,
    downloads_folder: Path | None = None,
    root_folder: str | None = None,
) -> str:
    """Resolve supported path variables and return an absolute path string."""

    downloads_folder = downloads_folder or get_downloads_folder()
    expanded = replace_path_tokens(value, project_root, downloads_folder, root_folder)

    # Allow normal Windows and shell environment variables as well.
    expanded = os.path.expandvars(expanded)

    path = Path(expanded).expanduser()
    if not path.is_absolute():
        path = project_root / path

    return str(path.resolve())


def resolve_configured_paths(settings: dict[str, Any], project_root: Path) -> dict[str, Any]:
    """Resolve all path settings to absolute path strings."""

    resolved = dict(settings)
    downloads_folder = get_downloads_folder()

    resolved["project_root"] = str(project_root)
    resolved["downloads_folder"] = str(downloads_folder)
    resolved["root_folder"] = resolve_path_value(str(resolved["root_folder"]), project_root, downloads_folder)

    for key in PATH_SETTING_KEYS - {"root_folder"}:
        resolved[key] = resolve_path_value(str(resolved[key]), project_root, downloads_folder, str(resolved["root_folder"]))

    return resolved


def load_settings(settings_path: Path, project_root: Path) -> dict[str, Any]:
    """Load settings.json, merge defaults, validate values, and resolve paths."""

    settings_path = resolve_settings_path(settings_path, project_root)

    if not settings_path.exists():
        settings_path.write_text(json.dumps(DEFAULT_SETTINGS, indent=4, ensure_ascii=False), encoding="utf-8")
        settings = dict(DEFAULT_SETTINGS)
    else:
        with settings_path.open("r", encoding="utf-8-sig") as file_handle:
            loaded = json.load(file_handle)
        settings = dict(DEFAULT_SETTINGS)
        settings.update(loaded)

    validate_settings(settings)
    return resolve_configured_paths(settings, project_root)


def validate_settings(settings: dict[str, Any]) -> None:
    """Raise ValueError when settings contain unsupported values."""

    prefer = str(settings.get("prefer_download_type", "magnet")).lower().strip()
    if prefer not in {"magnet", "torrent"}:
        raise ValueError('settings.json: "prefer_download_type" must be "magnet" or "torrent".')

    match_mode = str(settings.get("match_mode", "contains")).lower().strip()
    if match_mode not in {"contains", "exact", "regex"}:
        raise ValueError('settings.json: "match_mode" must be "contains", "exact", or "regex".')

    magnet_format = str(settings.get("write_magnet_format", "title_and_magnet")).lower().strip()
    if magnet_format not in {"magnet_only", "title_and_magnet"}:
        raise ValueError('settings.json: "write_magnet_format" must be "magnet_only" or "title_and_magnet".')

    try:
        max_log_executions = int(settings.get("max_log_executions", 100))
    except (TypeError, ValueError) as exc:
        raise ValueError('settings.json: "max_log_executions" must be an integer.') from exc

    if max_log_executions < 1:
        raise ValueError('settings.json: "max_log_executions" must be at least 1.')


def setup_folders(settings: dict[str, Any]) -> dict[str, Path]:
    """Create required folders and minimal starter config files when absent."""

    paths = {
        "root": Path(settings["root_folder"]),
        "config": Path(settings["config_folder"]),
        "magnet": Path(settings["magnet_output_folder"]),
        "torrent": Path(settings["torrent_output_folder"]),
        "log": Path(settings["log_folder"]),
    }

    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

    rss_file = paths["config"] / str(settings["rss_file"])
    exclude_file = paths["config"] / str(settings["exclude_file"])
    sample_category = paths["config"] / "anime.txt"

    if not rss_file.exists():
        rss_file.write_text("# Put one RSS feed URL per line.\n", encoding="utf-8")
    if not exclude_file.exists():
        exclude_file.write_text("# Put one exclusion keyword per line.\n", encoding="utf-8")
    if not sample_category.exists():
        sample_category.write_text("# Put one title/pattern per line.\n# Example:\n# One Piece\n", encoding="utf-8")

    return paths
