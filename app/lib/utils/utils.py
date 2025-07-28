import os
from pathlib import Path
from typing import List


def override_path(location: Path, override: str|None = None) -> List[Path]:
    if override is None:
        return [location]

    return [Path(override).joinpath(location), location]

def override_str(location: str, override: str|None = None) -> List[str]:
    if override is None:
        return [location]

    return [os.path.join(override, location), location]