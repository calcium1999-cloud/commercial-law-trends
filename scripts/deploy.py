#!/usr/bin/env python3
"""
deploy.py — 部署网页到公网

策略:
1. 如果 git 远程仓库已配置，push 到 GitHub（需在 GitHub Settings 中启用 Pages）
2. 如果未配置远程，启动本地服务器供预览

使用:
    .venv/bin/python scripts/deploy.py              # 自动选择部署方式
    .venv/bin/python scripts/deploy.py --local     # 仅启动本地服务器
    .venv/bin/python scripts/deploy.py --push      # 强制 push 到远程
"""
import sys
import os
import time
import subprocess
from pathlib import Path
from urllib.parse import urlparse

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEPLOY_FILES = ["index.html", "方正小标宋简.TTF"]
MAX_RETRIES = 3


def get_remote_url():
    """Return git remote URL or None."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=str(PROJECT_DIR), capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None


def extract_pages_url(remote):
    """Extract GitHub Pages URL from remote URL (handles token-embedded URLs)."""
    if "github.com" not in remote:
        return None

    parsed = urlparse(remote)
    if parsed.hostname != "github.com":
        return None

    path = parsed.path.lstrip("/").replace(".git", "")
    if "/" in path:
        user, repo = path.split("/", 1)
        return f"https://{user}.github.io/{repo}/"
    return None


def git_push():
    """Stage deploy files and push to remote. Retries on SSL failure."""
    remote = get_remote_url()
    if not remote:
        return False, "未配置 git 远程仓库（请先 git remote add origin <url>）"

    print(f"Git 远程: {remote}")

    for f in DEPLOY_FILES:
        fpath = PROJECT_DIR / f
        if fpath.exists():
            subprocess.run(["git", "add", f], cwd=str(PROJECT_DIR),
                           capture_output=True, timeout=10)

    reports_dir = PROJECT_DIR / "周报"
    if reports_dir.exists():
        subprocess.run(["git", "add", "周报/"], cwd=str(PROJECT_DIR),
                       capture_output=True, timeout=10)

    status = subprocess.run(["git", "status", "--porcelain"],
                           cwd=str(PROJECT_DIR), capture_output=True, text=True, timeout=10)
    if not status.stdout.strip():
        print("无新改动需要提交")
    else:
        import datetime
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        msg = f"Deploy: {ts}"
        commit = subprocess.run(["git", "commit", "-m", msg],
                                cwd=str(PROJECT_DIR), capture_output=True, text=True, timeout=30)
        if commit.returncode != 0:
            return False, f"git commit 失败: {commit.stderr[:200]}"

    for attempt in range(1, MAX_RETRIES + 1):
        result = subprocess.run(["git", "push", "origin", "main"],
                               cwd=str(PROJECT_DIR), capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            pages_url = extract_pages_url(remote)
            return True, pages_url or remote
        print(f"推送第 {attempt}/{MAX_RETRIES} 次失败: {result.stderr[:100]}")
        if attempt < MAX_RETRIES:
            time.sleep(5)
    return False, f"git push 失败（{MAX_RETRIES} 次重试）: {result.stderr[:200]}"


def start_local_server(port=8000):
    """Start a simple HTTP server for local preview."""
    import http.server

    os.chdir(str(PROJECT_DIR))
    handler = http.server.SimpleHTTPRequestHandler
    server = http.server.HTTPServer(("", port), handler)
    url = f"http://localhost:{port}"
    print(f"本地服务器已启动: {url}")
    print("按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
    return True


def main():
    mode = "auto"
    if "--local" in sys.argv:
        mode = "local"
    elif "--push" in sys.argv:
        mode = "push"

    port = 8000
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])

    if mode == "local":
        start_local_server(port)
        return 0

    if mode == "push":
        ok, msg = git_push()
        if ok:
            print(f"部署成功: {msg}")
        else:
            print(f"部署失败: {msg}")
        return 0 if ok else 1

    remote = get_remote_url()
    if remote:
        ok, msg = git_push()
        if ok:
            print(f"部署成功: {msg}")
            return 0
        else:
            print(f"Git 部署失败: {msg}")
            print("启动本地服务器作为替代...")
    else:
        print("未配置 git 远程仓库，无法自动部署到公网")
        print("启动本地服务器...")

    start_local_server(port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
