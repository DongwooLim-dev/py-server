# 오늘의 할 일

FastAPI 백엔드 + Streamlit 프론트엔드 + SQLite 저장소.
할 일 추가, 완료 표시, 삭제 및 설치 패키지 조회를 지원합니다.

## 실행 (SSH 서버)

```sh
cd ~/py-server
export PATH="$HOME/.local/bin:$PATH"
uv sync --locked
uv run python run.py
```

두 서버를 함께 시작하며 Ctrl+C로 함께 종료합니다.
가상환경은 `~/py-server/.venv`, 데이터는 `data/tasks.sqlite3`입니다.

## 접속 (내 컴퓨터)

```sh
ssh -N -L 8501:127.0.0.1:8501 -L 8000:127.0.0.1:8000 20.41.105.49
```

- 웹앱: http://localhost:8501/tasks-app/
- 메인페이지 사이드바: http://20.41.105.49/ → 파이썬 할 일 앱
- 사이트 직접 접속: http://20.41.105.49/tasks-app/
- API 문서: http://localhost:8000/docs
- VS Code Remote SSH의 포트 탭에서 8501, 8000을 전달해도 됩니다.

## 통합 패키지 관리

프론트와 백엔드가 하나의 `pyproject.toml`, `uv.lock`, `.venv`를 공유합니다.

```sh
uv add pandas           # 의존성 추가 + lock/환경 갱신
uv remove pandas        # 의존성 제거
uv lock --upgrade       # 버전 갱신
uv sync --locked        # lock 기준 설치
uv tree                 # 의존성 트리
```

패키지 변경 후 앱을 재시작하세요. 화면의 패키지 탭에서 설치 버전을 확인할 수 있습니다.

## 서버 서비스

현재 `py-server.service`로 두 앱을 자동 실행합니다.

```sh
sudo systemctl restart py-server
sudo systemctl status py-server
journalctl -u py-server -n 50
```

Nginx의 `tasks-app.conf`가 `/tasks-app/` HTTP 및 WebSocket 요청을 Streamlit으로 전달합니다.
