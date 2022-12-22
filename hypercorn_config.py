"""
Forces propagation of Hypercorn loggers so that our structlog configuration applies to them
"""
import logging
import os

accesslog = logging.getLogger("hypercorn.access")
accesslog.setLevel("INFO")

errorlog = logging.getLogger("hypercorn.error")
errorlog.setLevel("INFO")

worker_class = "uvloop"
workers = int(os.environ.get("ASGI_WORKERS", 1))
bind = f"0.0.0.0:{os.environ.get('ASGI_PORT', 8000)}"
