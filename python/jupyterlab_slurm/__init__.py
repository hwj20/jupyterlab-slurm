from .handlers import setup_handlers
from ._version import __version__

def _jupyter_server_extension_points():
    # 新 API：告诉 jupyter_server 这个包是扩展模块
    return [{"module": "jupyterlab_slurm"}]

def load_jupyter_server_extension(server_app):
    # 兼容旧 API 的函数名（没有下划线！）
    setup_handlers(server_app.web_app)
    server_app.log.info("jupyterlab-slurm | server extension loaded")
