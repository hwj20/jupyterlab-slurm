import json
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
from tornado import web
from nbformat import read, write, v4 as nbf

USE_REST = bool(os.environ.get("SLURM_USE_REST", ""))
SLURMREST_URL = os.environ.get("SLURMREST_URL", "")
SLURMREST_TOKEN = os.environ.get("SLURMREST_TOKEN", "")

class SlurmSubmitHandler(APIHandler):
    @web.authenticated
    async def post(self):
        payload = self.get_json_body() or {}
        try:
            # Optionally crop notebook to selected cells
            mode = payload.get("mode", "shell")
            if mode == "notebook" and payload.get("selectedCells"):
                src = payload["notebookPath"]
                run_dir = Path(payload.get("runDir", "."))
                run_dir.mkdir(parents=True, exist_ok=True)
                sub_nb = run_dir / "selected_cells.ipynb"
                make_sub_notebook(src, payload["selectedCells"], str(sub_nb))
                payload["notebookPath"] = str(sub_nb)

            script = build_sbatch_script(payload)
            out = await submit_job(script, payload)
            self.finish({"ok": True, **out})
        except Exception as e:
            self.set_status(500)
            self.finish({"ok": False, "error": str(e)})

class SlurmQueueHandler(APIHandler):
    @web.authenticated
    async def get(self):
        try:
            fmt = "%.18i %.9P %.8j %.8u %.2t %.10M %.6D %R"
            cmd = ["squeue", "-o", fmt]
            res = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.finish({"ok": True, "text": res.stdout})
        except Exception as e:
            self.set_status(500)
            self.finish({"ok": False, "error": str(e)})

class SlurmCancelHandler(APIHandler):
    @web.authenticated
    async def post(self):
        payload = self.get_json_body() or {}
        job_id = str(payload.get("job_id", "")).strip()
        try:
            if not job_id:
                raise ValueError("job_id required")
            subprocess.run(["scancel", job_id], check=True)
            self.finish({"ok": True, "job_id": job_id})
        except Exception as e:
            self.set_status(500)
            self.finish({"ok": False, "error": str(e)})

def setup_handlers(web_app):
    host_pattern = ".*"
    base_url = web_app.settings.get("base_url", "/")
    route = url_path_join(base_url, "jupyterlab-slurm")
    handlers = [
        (url_path_join(route, "submit"), SlurmSubmitHandler),
        (url_path_join(route, "queue"), SlurmQueueHandler),
        (url_path_join(route, "cancel"), SlurmCancelHandler),
    ]
    web_app.add_handlers(host_pattern, handlers)

# ---------- helpers ----------

def make_sub_notebook(src_path: str, cells_idx: List[int], out_path: str):
    nb = read(src_path, as_version=4)
    cells = [nb.cells[i] for i in cells_idx if i is not None and 0 <= i < len(nb.cells)]
    if not cells:
        cells = nb.cells
    sub = nbf.new_notebook(cells=cells, metadata=nb.metadata)
    write(sub, out_path)

def build_sbatch_script(cfg: Dict[str, Any]) -> str:
    job_name    = cfg.get("jobName", "jl-job")
    partition   = cfg.get("partition")
    account     = cfg.get("account")
    qos         = cfg.get("qos")
    time_lim    = cfg.get("time", "01:00:00")
    nodes       = cfg.get("nodes", 1)
    gpus        = cfg.get("gpus", 0)
    cpus        = cfg.get("cpus", 4)
    mem         = cfg.get("mem", "8G")
    conda_env   = cfg.get("condaEnv")
    workdir     = cfg.get("workdir", "${SLURM_SUBMIT_DIR}")
    export_envs = cfg.get("exportEnvs", [])

    lines = [
        "#!/bin/bash",
        f"#SBATCH -J {job_name}",
        f"#SBATCH -t {time_lim}",
        f"#SBATCH -N {nodes}",
        f"#SBATCH --cpus-per-task={cpus}",
        f"#SBATCH --mem={mem}",
    ]
    if partition: lines.append(f"#SBATCH -p {partition}")
    if account:   lines.append(f"#SBATCH -A {account}")
    if qos:       lines.append(f"#SBATCH --qos={qos}")
    if gpus:      lines.append(f"#SBATCH --gpus={gpus}")

    lines += [
        "set -euo pipefail",
        f"cd {workdir}",
        'echo "[Slurm] job: $SLURM_JOB_ID node: $(hostname)"',
    ]

    if conda_env:
        lines += [
            f'echo "[Slurm] activating conda: {conda_env}"',
            "source ~/.bashrc || true",
            f"conda activate {conda_env} || source activate {conda_env} || true",
        ]

    for kv in export_envs:
        lines.append(f"export {kv}")

    mode = cfg.get("mode", "shell")
    if mode == "notebook":
        nb_path = cfg.get("notebookPath")
        out_ipynb = cfg.get("outputNotebook", "output.ipynb")
        out_html  = cfg.get("outputHtml", "output.html")
        pm_params = cfg.get("parameters", {})
        pm_args = " ".join([f"-p {k} {json.dumps(v)}" for k, v in pm_params.items()])
        lines += [
            'echo "[Slurm] running papermill"',
            f"papermill {nb_path} {out_ipynb} {pm_args}",
            'echo "[Slurm] exporting HTML"',
            f"jupyter nbconvert --to html {out_ipynb} --output {out_html}",
        ]
    else:
        command = cfg.get("command", "echo 'hello from slurm'")
        lines.append(command)

    return "\\n".join(lines) + "\\n"

async def submit_job(script_text: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    run_dir = Path(cfg.get("runDir", "."))
    run_dir.mkdir(parents=True, exist_ok=True)
    script_path = run_dir / "job.sbatch"
    script_path.write_text(script_text)
    res = subprocess.run(["sbatch", str(script_path)], check=True, capture_output=True, text=True)
    job_id = res.stdout.strip().split()[-1]
    return {"job_id": job_id, "stdout": res.stdout}
