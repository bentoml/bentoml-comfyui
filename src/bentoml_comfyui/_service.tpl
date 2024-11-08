from __future__ import annotations

import json
import os
from pathlib import Path

import bentoml
import comfyui_idl
import comfyui_idl.run

REQUEST_TIMEOUT = 360
WORKFLOW_FILE = os.path.join(os.path.dirname(__file__), "workflow.json")

with open(WORKFLOW_FILE, "r") as f:
    workflow = json.load(f)

InputModel = comfyui_idl.generate_input_model(workflow)


@bentoml.service(name={name!r}, traffic={{'timeout': REQUEST_TIMEOUT * 2}})
class ComfyUIService:
    pipeline = bentoml.models.BentoModel({model_tag!r})

    def __init__(self):
        comfy_output_dir = os.path.join(os.getcwd(), "comfy_output")
        comfy_temp_dir = os.path.join(os.getcwd(), "comfy_temp")

        self.comfy_proc = comfyui_idl.run.WorkflowRunner(
            self.pipeline.path,
            comfy_output_dir,
            comfy_temp_dir,
        )
        self.comfy_proc.start()

    @bentoml.api(input_spec=InputModel)
    def generate(
        self,
        *,
        ctx: bentoml.Context,
        **kwargs: t.Any,
    ) -> Path:
        ret = self.comfy_proc.run_workflow(
            workflow, temp_dir=ctx.temp_dir, timeout=REQUEST_TIMEOUT, **kwargs
        )
        if isinstance(ret, list):
            ret = ret[-1]
        return ret

    @bentoml.on_shutdown
    def on_shutdown(self):
        self.comfy_proc.stop()
