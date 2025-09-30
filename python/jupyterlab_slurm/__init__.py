
from ._version import __version__
from .handlers import setup_handlers

def _jupyter_server_extension_points():
    return [{
        "module": "jupyterlab_slurm",
        "app": "jupyter_server.serverapp.ServerApp",
    }]

def _load_jupyter_server_extension(server_app):
    setup_handlers(server_app.web_app)
    server_app.log.info("jupyterlab-slurm | server extension loaded")
