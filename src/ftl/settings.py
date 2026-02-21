import json
from pathlib import Path
from typing import Any, Literal, TypedDict

from platformdirs import user_data_dir

USER_DATA_DIR = Path(user_data_dir("FTL"))
USER_SETTINGS = USER_DATA_DIR / "settings.json"


class ParameterizedTask(TypedDict):
    enabled: bool
    task_type: str
    parameters: dict[str, Any]


class Rule(TypedDict):
    enabled: bool
    name: str
    file_type: Literal["File", "FileSequence"]
    file_patterns: list[str]
    tasks: list[ParameterizedTask]
    description: str
    schema_version: int


class Settings(TypedDict):
    ffmpeg: str | None
    rules: list[Rule]


def default_settings() -> Settings:
    from ftl.rules import default_rules

    return {
        "ffmpeg": None,
        "rules": default_rules(),
    }


def save_settings(data: Settings):
    from ftl.rules import unstructure

    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if rules := data.get("rules"):
        data["rules"] = unstructure(rules)

    USER_SETTINGS.write_text(json.dumps(data))


def get_settings() -> Settings:
    from ftl.rules import Rule, structure

    settings = default_settings()

    if USER_SETTINGS.exists():
        user_settings = json.loads(USER_SETTINGS.read_text())
        if user_rules := user_settings.get("rules"):
            user_settings["rules"] = structure(user_rules, list[Rule])
        settings.update(user_settings)

    return settings


def int_to_sizeStr(value):
    if value <= 0:
        return "original"
    return str(value)


def sizeStr_to_int(value):
    if isinstance(value, str) and value.lower() in ("original", "unchanged"):
        return -1
    return int(value)
