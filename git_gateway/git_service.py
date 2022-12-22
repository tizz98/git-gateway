import asyncio
import os
import tempfile
from functools import partial
from pathlib import Path
from typing import Optional

import structlog
from fastapi import HTTPException, Response, Request
from pygit2 import Repository, init_repository
from starlette import status

logger = structlog.get_logger(__name__)
tmp_dir = tempfile.TemporaryDirectory()


def get_packet_length(packet):
    """
    Returns length of the given packet in a 4 byte hex string.
    This string is placed at the beginning of the response body.
    e.g.
        001e
    """

    chars = "0123456789abcdef"
    length = len(packet) + 4
    prefix = chars[int((length >> 12) & 0xF)]
    prefix = prefix + chars[int((length >> 8) & 0xF)]
    prefix = prefix + chars[int((length >> 4) & 0xF)]
    prefix = prefix + chars[int(length & 0xF)]

    return prefix


def get_response_first_line(service: str):
    """
    Sets first line of git response that includes length and requested service.
    e.g.
        001f# service=git-receive-pack
    """

    first_line = "# service={0}\n".format(service)
    prefix = get_packet_length(first_line)
    return "{0}{1}0000".format(prefix, first_line)


class GitService:
    @classmethod
    async def ensure_repo(cls, name: str) -> Path:
        all_repos_dir = Path(os.environ.get("GIT_REPO_DIR", tmp_dir.name))
        all_repos_dir.mkdir(parents=True, exist_ok=True)
        path = all_repos_dir / name
        if not path.exists():
            await asyncio.get_event_loop().run_in_executor(
                None, partial(init_repository, path, bare=True)
            )
            logger.info(f"Initialized repository at {path}")
        return path

    @classmethod
    async def get_refs(cls, name: str, service: str):
        repo_path = await cls.ensure_repo(name)
        proc = await asyncio.create_subprocess_exec(
            service,
            "--stateless-rpc",
            "--advertise-refs",
            repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.error("Error running git command", stderr=stderr.decode())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=stderr.decode(),
            )

        first_line = get_response_first_line(service)
        return Response(
            first_line.encode() + stdout,
            media_type=f"application/x-{service}-advertisement",
        )

    @classmethod
    async def post_refs(cls, name: str, service: str, request: Request):
        repo_path = await cls.ensure_repo(name)
        data = await request.body()

        proc = await asyncio.create_subprocess_exec(
            service,
            "--stateless-rpc",
            repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate(data)

        if proc.returncode != 0:
            logger.error("Error running git command", stderr=stderr.decode())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=stderr.decode(),
            )

        return Response(stdout, media_type=f"application/x-{service}-result")

    @classmethod
    async def get_file(cls, name: str, path: str, ref: Optional[str] = None):
        repo_path = await cls.ensure_repo(name)
        repo = Repository(repo_path)
        if ref is None:
            ref = repo.head.target.hex

        try:
            ref, _ = repo.resolve_refish(ref)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ref not found"
            )

        try:
            blob = repo[ref.tree[path].id]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
            )

        return Response(blob.data)
