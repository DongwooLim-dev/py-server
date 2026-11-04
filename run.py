"""Start both services with: uv run python run.py."""

import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


def main():
    children = []

    def stop(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    root = Path(__file__).resolve().parent
    try:
        children.append(subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=root,
        ))
        for _ in range(100):
            if children[0].poll() is not None:
                raise RuntimeError("FastAPI 시작 실패")
            try:
                with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=1):
                    break
            except OSError:
                time.sleep(0.1)
        else:
            raise RuntimeError("FastAPI 시작 시간 초과")
        children.append(subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
             "--server.address", "127.0.0.1", "--server.port", "8501",
             "--server.baseUrlPath", "tasks-app",
             "--server.headless", "true", "--browser.gatherUsageStats", "false"],
            cwd=root,
            env={**os.environ, "API_BASE_URL": "http://127.0.0.1:8000"},
        ))
        while all(child.poll() is None for child in children):
            time.sleep(0.5)
        raise RuntimeError("웹앱 프로세스가 종료되었습니다.")
    except KeyboardInterrupt:
        pass
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == "__main__":
    main()
