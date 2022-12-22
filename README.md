# Git Gateway

Run a simple git http server.


```bash
docker run -d --rm -it -p 8000:8000 ghcr.io/tizz98/git-gateway
git remote set local http://localhost:8000/test/test
git push local -u main
```
