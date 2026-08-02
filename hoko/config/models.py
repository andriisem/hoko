from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field
from ruamel.yaml import YAML

CONFIG_FILENAME = "hoko.yaml"

_yaml = YAML()
_yaml.preserve_quotes = True


class HokoConfig(BaseModel):
    version: int = 1
    capabilities: list[str] = Field(default_factory=list)

    def add_capability(self, name: str) -> None:
        if name not in self.capabilities:
            self.capabilities.append(name)

    def remove_capability(self, name: str) -> None:
        if name in self.capabilities:
            self.capabilities.remove(name)

    @classmethod
    def load(cls, path: Path | None = None) -> "HokoConfig":
        path = path or Path(CONFIG_FILENAME)
        if not path.exists():
            return cls()
        with path.open() as handle:
            data = _yaml.load(handle) or {}
        return cls(**data)

    def save(self, path: Path | None = None) -> None:
        path = path or Path(CONFIG_FILENAME)
        with path.open("w") as handle:
            _yaml.dump(self.model_dump(), handle)

    def export_preset(self, path: Path) -> None:
        self.save(path)

    @classmethod
    def import_preset(cls, path: Path) -> "HokoConfig":
        return cls.load(path)
