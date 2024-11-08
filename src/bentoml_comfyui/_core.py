import os
import shutil
import subprocess
import sys
from pathlib import Path

import bentoml


# Function to ignore the 'input' and 'output' directories during copy
def _ignore_dirs(src, names):
    ignore_list = ["output", ".venv", ".git", "__pycache__"]
    return [item for item in names if item in ignore_list]


def pack_model(name: str, workspace: str) -> str:
    """Pack the ComfyUI source to a BentoML model

    Args:
        name (str): The name of the BentoML model
        workspace (str): The path to the ComfyUI workspace

    Returns:
        str: Model tag
    """
    with bentoml.models.create(name=name) as model:
        # Copy the entire directory tree from source to destination, ignoring 'input' and 'output'
        shutil.copytree(workspace, model.path, ignore=_ignore_dirs, dirs_exist_ok=True)

        # Create empty output, and output/exp_data directories because they are required by ComfyUI
        os.makedirs(os.path.join(model.path, "output"), exist_ok=True)
        os.makedirs(os.path.join(model.path, "output", "exp_data"), exist_ok=True)

    return str(model.tag)


def _ensure_virtualenv(python: str | None) -> None:
    from bentoml.exceptions import BentoMLConfigException

    if python:
        pyvenv_cfg = Path(python).parent.parent / "pyvenv.cfg"
    else:
        pyvenv_cfg = Path(sys.prefix, "pyvenv.cfg")

    if not pyvenv_cfg.exists():
        raise BentoMLConfigException("ComfyUI must be installed in a virtualenv.")


def get_requirements(python: str | None) -> str:
    _ensure_virtualenv(python)
    freeze_cmd = [
        sys.executable,
        "-m",
        "uv",
        "pip",
        "freeze",
        "--exclude-editable",
        "-p",
        python or sys.executable,
    ]
    output = subprocess.run(
        freeze_cmd, capture_output=True, text=True, check=True
    ).stdout
    # Exclude bentoml from the requirements
    lines = [line for line in output.splitlines() if not line.startswith("bentoml==")]
    return "\n".join(lines)
