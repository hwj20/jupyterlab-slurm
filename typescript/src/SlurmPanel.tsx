import React, { useState } from 'react';

export const SlurmPanel: React.FC = () => {
  const [cfg, setCfg] = useState<any>({
    jobName: 'jl-job', partition: '', account: '', qos: '', time: '01:00:00',
    nodes: 1, cpus: 4, mem: '8G', gpus: 0, condaEnv: '', workdir: '',
    mode: 'notebook', notebookPath: '', outputNotebook: 'output.ipynb', outputHtml: 'output.html',
    command: '', runDir: './runs', exportEnvs: [], parameters: {}
  });
  const [msg, setMsg] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const post = async (path: string, body?: any) => {
    const base = (window as any).__JUPYTERLAB_BASE_URL__ || '/';
    const url = base.replace(/\/$/,'') + '/jupyterlab-slurm/' + path;
    const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    return res.json();
  };

  const submit = async () => {
    setSubmitting(true); setMsg('');
    try {
      const out = await post('submit', cfg);
      setMsg(out.ok ? `Submitted job ${out.job_id}` : out.error || 'Unknown error');
    } catch (e:any) { setMsg(String(e)); }
    setSubmitting(false);
  };

  const queue = async () => {
    const base = (window as any).__JUPYTERLAB_BASE_URL__ || '/';
    const url = base.replace(/\/$/,'') + '/jupyterlab-slurm/queue';
    const res = await fetch(url);
    const j = await res.json();
    setMsg(j.ok ? j.text : j.error);
  };

  const cancel = async (job_id: string) => {
    const out = await post('cancel', { job_id });
    setMsg(out.ok ? `Canceled ${job_id}` : out.error);
  };

  return (
    <div style={{ padding: 12, maxWidth: 820 }}>
      <h2>Slurm Submitter</h2>
      <section>
        <label>Job Name <input value={cfg.jobName} onChange={e=>setCfg({...cfg, jobName:e.target.value})}/></label>
        <label>Partition <input value={cfg.partition} onChange={e=>setCfg({...cfg, partition:e.target.value})}/></label>
        <label>Time <input value={cfg.time} onChange={e=>setCfg({...cfg, time:e.target.value})}/></label>
        <label>Nodes <input type="number" value={cfg.nodes} onChange={e=>setCfg({...cfg, nodes:Number(e.target.value)})}/></label>
        <label>CPUs <input type="number" value={cfg.cpus} onChange={e=>setCfg({...cfg, cpus:Number(e.target.value)})}/></label>
        <label>Mem <input value={cfg.mem} onChange={e=>setCfg({...cfg, mem:e.target.value})}/></label>
        <label>GPUs <input type="number" value={cfg.gpus} onChange={e=>setCfg({...cfg, gpus:Number(e.target.value)})}/></label>
        <label>Conda Env <input value={cfg.condaEnv} onChange={e=>setCfg({...cfg, condaEnv:e.target.value})}/></label>
        <label>Workdir <input value={cfg.workdir} onChange={e=>setCfg({...cfg, workdir:e.target.value})}/></label>
      </section>
      <section>
        <label>Mode
          <select value={cfg.mode} onChange={e=>setCfg({...cfg, mode:e.target.value})}>
            <option value="notebook">notebook</option>
            <option value="shell">shell</option>
          </select>
        </label>
        {cfg.mode==='notebook' ? (
          <div>
            <label>Notebook Path <input value={cfg.notebookPath} onChange={e=>setCfg({...cfg, notebookPath:e.target.value})}/></label>
            <label>Output .ipynb <input value={cfg.outputNotebook} onChange={e=>setCfg({...cfg, outputNotebook:e.target.value})}/></label>
            <label>Output HTML <input value={cfg.outputHtml} onChange={e=>setCfg({...cfg, outputHtml:e.target.value})}/></label>
          </div>
        ) : (
          <label>Command <input value={cfg.command} onChange={e=>setCfg({...cfg, command:e.target.value})}/></label>
        )}
      </section>
      <section>
        <label>Run Dir <input value={cfg.runDir} onChange={e=>setCfg({...cfg, runDir:e.target.value})}/></label>
      </section>
      <div style={{ marginTop: 8 }}>
        <button disabled={submitting} onClick={submit}>Submit</button>
        <button onClick={queue} style={{ marginLeft: 8 }}>Queue</button>
        <button onClick={()=>{ const id = prompt('Job ID to cancel?'); if (id) cancel(id); }} style={{ marginLeft: 8 }}>Cancel</button>
      </div>
      <pre style={{ marginTop: 12, background: '#1112', padding: 8, whiteSpace: 'pre-wrap' }}>{msg}</pre>
    </div>
  );
};
