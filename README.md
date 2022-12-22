# Git Gateway

Run a simple git http server.


```bash
docker run -d --rm -it -p 8000:8000 ghcr.io/tizz98/git-gateway
git remote set local http://localhost:8000/test/test.git
git push local -u main
```

You can view file contents at http://localhost:8000/test/test/files?path=README.md.
And optionally specify a ref with `?ref=36e5dd55c4a5b3647d0f32d0393a6ddd9774f504`.
