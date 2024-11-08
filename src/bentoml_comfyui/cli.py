import shutil
import tempfile
from pathlib import Path

import click
import rich
from bentoml_cli.utils import BentoMLCommandGroup


def _check_comfyui_workspace(workspace: str) -> None:
    from bentoml.exceptions import InvalidArgument

    comfy_fingerprints = ["comfy", "comfy_execution", "comfy_extras"]

    for fingerprint in comfy_fingerprints:
        if not Path(workspace, fingerprint).exists():
            raise InvalidArgument(
                f"{workspace!r} does not look like a ComfyUI workspace. Please give a correct path."
            )


@click.group(name="comfyui", cls=BentoMLCommandGroup)
def comfyui_command():
    """ComfyUI Subcommands Groups."""


@comfyui_command.command()
@click.option(
    "--name",
    type=str,
    help="The name of the model, defaults to `comfyui`",
    default="comfyui",
)
@click.option(
    "--version", type=str, help="The version of the model, or generated if not provided"
)
@click.argument("workspace", type=click.Path(exists=True), default=".")
def pack(name: str, version: str | None, workspace: str):
    """Pack the ComfyUI workspace to a BentoML model"""
    from ._core import pack_model

    _check_comfyui_workspace(workspace)

    if version:
        name = f"{name}:{version}"
    tag = pack_model(name, workspace)
    rich.print(
        f"✅ [green]Successfully packed ComfyUI workspace {workspace!r} to BentoML model {tag}[/]"
    )


@comfyui_command.command()
@click.option(
    "--name",
    type=str,
    help="The name of the bento, defaults to `comfyui-service`",
    default="comfyui-service",
)
@click.option(
    "--version", type=str, help="The version of the bento, or generated if not provided"
)
@click.option(
    "--model",
    type=str,
    help="The model tag to use. Defaults to `comfyui`",
    default="comfyui",
)
@click.option(
    "-p",
    "--python",
    type=str,
    help="The Python interpreter path where ComfyUI is running. Defaults to the current Python interpreter",
)
@click.argument("workflow", required=True, type=click.Path(dir_okay=False, exists=True))
def build(
    name: str, version: str | None, model: str, python: str | None, workflow: str
):
    """Build a BentoML service from a ComfyUI workspace"""
    from importlib.resources import read_text

    import bentoml

    from ._core import get_requirements

    service_template = read_text(__package__, "_service.tpl")

    with tempfile.TemporaryDirectory(
        prefix="bentoml-comfyui-", suffix="-bento"
    ) as temp_dir:
        parent = Path(temp_dir)
        rich.print("📂 [blue]Creating requirements.txt[/]")
        with open(parent.joinpath("requirements.txt"), "w") as f:
            f.write(get_requirements(python))
        rich.print("📂 [blue]Creating service.py[/]")
        with open(parent.joinpath("service.py"), "w") as f:
            f.write(service_template.format(name=name, model_tag=model))
        rich.print("📂 [blue]Creating workflow.json[/]")
        shutil.copy2(workflow, parent.joinpath("workflow.json"))
        bento = bentoml.build(
            "service:ComfyUIService",
            name=name,
            version=version,
            build_ctx=temp_dir,
            docker={"system_packages": ["git"]},
            python={"requirements_txt": "requirements.txt", "lock_packages": False},
            include=["service.py", "workflow.json", "requirements.txt"],
        )
    rich.print(
        f"✅ [green]Successfully built Bento {bento.tag} from ComfyUI workflow {workflow!r}[/]"
    )
