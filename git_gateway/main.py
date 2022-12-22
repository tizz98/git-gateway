from fastapi import FastAPI

from git_gateway.routers import git_router
from git_gateway.utils.logging_utils import configure_logging

configure_logging()
app = FastAPI()
app.include_router(git_router)
