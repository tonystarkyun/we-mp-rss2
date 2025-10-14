# Repository Guidelines

## Project Structure & Module Organization
- Backend FastAPI code lives in `core/` and `apis/`; routers map to domain models in `core/models/`, and scheduled jobs sit in `jobs/`.
- `main.py` and `init_sys.py` bootstrap the service, while `web.py` exposes the API and serves the Vue bundle stored in `static/`.
- Front-end source is in `web_ui/src/`; the Vite build pushes compiled assets to `static/` for deployment.
- Container assets live in `compose/` and `Dockerfiles/`, and `build-linux.sh` plus `config.example.yaml` support packaging and configuration.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` installs backend dependencies.
- `python main.py -job True -init True` launches the API with schedulers; use `uvicorn web:app --reload --port 8001` for hot reload.
- `cd web_ui && npm install && npm run dev` runs the Vue client; `npm run build` emits the production bundle.
- `docker compose -f compose/docker-compose.yaml up -d` provisions the stack with MySQL, and `docker-compose-sqlite.yaml` targets the embedded database.
- Add automated cases under `tests/` and run them with `pytest`; keep ad-hoc scripts like `test.py` for local smoke checks.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation; use `PascalCase` for ORM classes and `snake_case` for modules (see `core/models/article.py`).
- Share configuration through `core.config.cfg`; avoid hard-coded paths or inline environment lookups inside handlers.
- Log operational events with helpers in `core/log.py` instead of raw `print`.
- Vue components rely on the composition API with TypeScript; keep filenames in `kebab-case` and scope styles within each component.

## Testing Guidelines
- Group backend `pytest` files by feature (`tests/apis/test_articles.py`, `tests/jobs/test_scheduler.py`) and cover success and failure paths.
- Document manual UI verification steps in the pull request or add component tests; store API mocks in `web_ui/src/api/__mocks__/` when used.

## Commit & Pull Request Guidelines
- Commits use short Chinese summaries (for example `修复定制化爬取reuters`); keep them imperative and reference the touched module or endpoint.
- Each PR must list testing performed, configuration or migration steps, and attach screenshots for visible UI work.
- Link related issues in the PR description and split large features into reviewable slices before requesting review.

## Security & Configuration Tips
- Never commit secrets; copy `config.example.yaml` to `config.yaml` locally and inject keys via environment variables or mounts.
- Review webhook integrations under `core/webhook/` for tokens before shipping changes.
- Generated bundles or installers (`build-linux.sh`) should exclude `data/` and cache folders.
