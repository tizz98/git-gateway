from typing import Optional

from fastapi import APIRouter, Request

from git_gateway.git_service import GitService

git_router = APIRouter()


@git_router.get("/{name:path}.git/info/refs")
async def get_refs(name: str, service: str):
    return await GitService.get_refs(name, service)


@git_router.post("/{name:path}.git/{service}")
async def post_refs(name: str, service: str, request: Request):
    return await GitService.post_refs(name, service, request)


@git_router.get("/{name:path}/files")
async def get_file(name: str, path: str, ref: Optional[str] = None):
    return await GitService.get_file(name, path, ref)
