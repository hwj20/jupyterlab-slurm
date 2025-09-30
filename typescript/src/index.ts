import { JupyterFrontEnd, JupyterFrontEndPlugin } from '@jupyterlab/application';
import { ICommandPalette } from '@jupyterlab/apputils';
import { INotebookTracker, NotebookPanel } from '@jupyterlab/notebook';
import { MainAreaWidget, ReactWidget } from '@jupyterlab/apputils';
import * as React from 'react';
import ReactDOM from 'react-dom';
import { Widget } from '@lumino/widgets';
import { SlurmPanel } from './SlurmPanel';

const EXT_ID = 'jupyterlab-slurm:open';

const plugin: JupyterFrontEndPlugin<void> = {
  id: EXT_ID,
  autoStart: true,
  requires: [ICommandPalette, INotebookTracker],
  activate: (app: JupyterFrontEnd, palette: ICommandPalette, tracker: INotebookTracker) => {
    const { commands } = app;

    // Open basic panel
    commands.addCommand(EXT_ID, {
      label: 'Slurm: Open Panel',
      execute: () => {
        const content = document.createElement('div');
        const widget = new MainAreaWidget({ content: new Widget({ node: content }) });
        widget.title.label = 'Slurm Submitter';
        widget.title.closable = true;
        ReactDOM.render(React.createElement(SlurmPanel, {}), content);
        app.shell.add(widget, 'main');
        app.shell.activateById(widget.id);
      }
    });
    palette.addItem({ command: EXT_ID, category: 'Slurm' });

    // Run selected cells on Slurm
    commands.addCommand('slurm:run-selected', {
      label: 'Slurm: Run Selected Cells',
      execute: async () => {
        const current = tracker.currentWidget as NotebookPanel | null;
        if (!current) return;
        await current.context.save();
        const nbPath = current.context.path;
        const selection: number[] = [];
        current.content.widgets.forEach((c, i) => {
          if (current.content.isSelected(c)) selection.push(i);
        });
        await fetch(((window as any).__JUPYTERLAB_BASE_URL__ || '/').replace(/\/$/,'') + '/jupyterlab-slurm/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode: 'notebook', notebookPath: nbPath, selectedCells: selection, runDir: './runs' })
        });
      }
    });
    palette.addItem({ command: 'slurm:run-selected', category: 'Slurm' });
  }
};

export default plugin;
