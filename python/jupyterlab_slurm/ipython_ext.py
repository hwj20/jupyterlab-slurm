from IPython.core.magic import Magics, magics_class, cell_magic
from IPython.display import display, Markdown
import json, time, pathlib, requests, os

BASE = os.environ.get('JLSLURM_BASE', '/jupyterlab-slurm')

@magics_class
class SlurmMagics(Magics):
    @cell_magic
    def slurm(self, line, cell):
        """
        Usage:
        %%slurm partition=a100 gpus=1 time=02:00:00 mem=32G cpus=8 conda=pytorch runDir=./runs
        python your_script.py --arg 1
        """
        opts = dict(kv.split('=') for kv in line.split() if '=' in kv)
        run_dir = opts.pop('runDir', './runs')
        pathlib.Path(run_dir).mkdir(parents=True, exist_ok=True)
        script_path = pathlib.Path(run_dir)/'cell_run.sh'
        script_path.write_text('#!/bin/bash\nset -e\n' + cell + '\n')
        script_path.chmod(0o755)

        payload = {
            'mode': 'shell',
            'command': str(script_path),
            'runDir': run_dir,
            'jobName': opts.get('jobName','cell-job'),
            'partition': opts.get('partition'),
            'time': opts.get('time','01:00:00'),
            'gpus': int(opts.get('gpus','0')),
            'cpus': int(opts.get('cpus','2')),
            'mem': opts.get('mem','4G'),
            'condaEnv': opts.get('conda')
        }
        submit_url = BASE.rstrip('/') + '/submit'
        r = requests.post(submit_url, json=payload)
        r.raise_for_status()
        out = r.json()
        if not out.get('ok'):
            display(Markdown(f"**Submit failed**: {out.get('error')}"))
            return
        job_id = out['job_id']
        display(Markdown(f"Submitted **{job_id}**. Waiting to finish…"))

        # Poll queue
        queue_url = BASE.rstrip('/') + '/queue'
        while True:
            time.sleep(3)
            q = requests.get(queue_url).json()
            if not q.get('ok'):
                break
            if str(job_id) not in q.get('text',''):
                break
        log = pathlib.Path(run_dir)/('slurm-' + str(job_id) + '.out')
        if log.exists():
            display(Markdown('**Job Output:**'))
            display(Markdown('`````\n' + log.read_text() + '\n`````'))
        else:
            display(Markdown('Job finished.'))

def load_ipython_extension(ip):
    ip.register_magics(SlurmMagics)
