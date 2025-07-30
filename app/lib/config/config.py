import logging
import os
from pathlib import Path
from typing import Optional, Type, MutableMapping, List, TypeVar

from ruamel.yaml import YAML

T = TypeVar("T")

logger = logging.getLogger(__name__)


def find_upwards(cwd: Path, file: Path) -> Optional[Path]:
    if cwd == Path(cwd.root):
        return None

    fullpath = Path(cwd, file)

    return fullpath if fullpath.exists() else find_upwards(cwd.parent, file)


def merge_dicts(x: dict, y: dict) -> dict:
    """
    Update two dicts of dicts recursively,
    if either mapping has leaves that are non-dicts,
    the second's leaf overwrites the first's.
    """
    for k, v in x.items():
        if k in y:
            if all(isinstance(e, MutableMapping) for e in (v, y[k])):
                y[k] = merge_dicts(v, y[k])

    ret = x.copy()
    ret.update(y)
    return ret


def load_config(path: Path | List[Path], name: str | None, model: Type[T]) -> T:
    """
    Load the YML files, merging common and app settings and ensuring they validate
    :param path: Name(s) of config file(s)
    :param name: Name of app. If none we lookup config from the root
    :param model: Model to validate against
    :return:
    """

    if not isinstance(path, list):
        path = [path]

    merged = {}

    for config_file in path:
        if not config_file.exists():
            continue
        with config_file.open() as f:
            yaml: dict = YAML(typ="safe").load(f)

        if yaml is not None:
            if name is not None:
                # Merge common and the specific app config
                data = merge_dicts(
                    yaml["common"] if "common" in yaml else {},
                    yaml[name] if name in yaml else {},
                )
            else:
                data = yaml

            # Merge with previous config
            merged = merge_dicts(merged, data)

    return model(**merged)


def get_config(section: str) -> T:
    # Look for config file in our directory and every parent directory if not passed in via the environment
    # variable APP_CONFIG

    if "APP_CONFIG" in os.environ:
        config_path = [Path(s) for s in os.environ.get("APP_CONFIG").split(",")]
    else:
        config_path = [
            x
            for x in [
                find_upwards(Path.cwd(), Path("config", "default.yml")),
                find_upwards(Path.cwd(), Path("config", "config.yml")),
            ]
            if x is not None
        ]

    return load_config(config_path, section, T)
