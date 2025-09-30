# jupyterlab-slurm (demo)

Minimal, end-to-end demo for **"click run ➜ submit a Slurm job ➜ free GPU when done"**.

Includes:
- Jupyter **server extension** (Python): `/python/jupyterlab_slurm`
- JupyterLab **front-end** (TypeScript/React) with a simple panel
- **IPython cell magic** `%%slurm` (run cell as a Slurm job)

> This is a minimal demo to get you started quickly. Harden/QA for your environment before production.

## Quickstart

### 0) Requirements on the compute/login node
- Slurm client tools: `sbatch`, `squeue`, `scancel`
- Optional: `papermill`, `jupyter nbconvert`
- Python 3.9+ and JupyterLab 4.x

### 1) Build front-end
```bash
cd typescript
jlpm install
jlpm run build
# copy build outputs to the python package
mkdir -p ../python/jupyterlab_slurm/labextension
cp -r lib/* ../python/jupyterlab_slurm/labextension/
```

### 2) Install server extension
```bash
cd ../python
pip install -e .
# launch Lab
jupyter lab
```

### 3) Use the Slurm panel
- Command Palette ➜ **Slurm: Open Panel**
- Fill partition/time/gpus/cpus etc. ➜ Submit

### 4) Use the IPython cell magic
In a notebook:
```python
%load_ext jupyterlab_slurm.ipython_ext
```
Then in any cell:
```python
%%slurm partition=a100 gpus=1 time=00:20:00 mem=16G cpus=4 conda=pytorch
python train.py --epochs 3
```

The GPU is **only** occupied during the Slurm job.

## Notes
- Set `SLURM_USE_REST`, `SLURMREST_URL`, `SLURMREST_TOKEN` if you want to integrate `slurmrestd`. (The demo stubs raise `NotImplementedError` to keep the sample small.)
- Consider adding policy checks (max GPUs/time) for your cluster.
- For a nicer UI, extend the React panel and parse `squeue` to a table.


## TODO
1. Do we need to support slurmrestd?