# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WeRSS (we-mp-rss) is a WeChat public account RSS subscription assistant that allows users to subscribe to and manage WeChat public account content through RSS feeds. The project uses a full-stack architecture with Python/FastAPI backend and Vue.js frontend.

## Development Commands

### Backend Development
- **Start development server**: `python main.py -job True -init True` (enables jobs and initializes database)
- **Start without jobs**: `python main.py -init True`
- **Install dependencies**: `pip install -r requirements.txt`
- **Database initialization**: `python init_sys.py`

### Frontend Development
- **Development server**: `cd web_ui && yarn dev`
- **Build frontend**: `cd web_ui && yarn build` (or use `web_ui/build.bat` on Windows / `web_ui/build.sh` on Unix)
- **Install dependencies**: `cd web_ui && yarn install`

### Build Commands
- **Build executable**: Run `build.bat` (Windows) - creates PyInstaller executable in `dist/` directory
- **Frontend build scripts**: Located in `web_ui/` directory, copies built files to `../static/`

### Docker Development
- **Development**: `docker-compose -f compose/docker-compose-sqlite.yaml up`
- **Production**: `docker-compose -f compose/docker-compose.yaml up`

## Architecture Overview

### Backend Structure
- **Entry point**: `main.py` - starts FastAPI server with uvicorn, optionally starts background jobs
- **Web framework**: `web.py` - FastAPI app configuration with CORS, static file serving, and API routing
- **Configuration**: `core/config.py` - YAML-based configuration with environment variable support and optional encryption
- **Database**: SQLAlchemy models in `core/models/` directory (supports SQLite default, MySQL optional)
- **APIs**: RESTful endpoints in `apis/` directory for auth, articles, RSS feeds, user management, etc.
- **Background jobs**: `jobs/` directory contains scheduled tasks for article fetching and notifications
- **Core services**: `core/` directory contains business logic modules for RSS generation, WeChat integration, notifications, etc.

### Frontend Structure
- **Framework**: Vue 3 + Vite + TypeScript
- **UI Library**: Arco Design Vue + Ant Design Vue
- **Build output**: Copies to `static/` directory for backend to serve
- **API client**: Axios-based HTTP client in `src/api/`

### Key Components
- **RSS Generation**: `core/rss.py` - converts WeChat articles to RSS feeds
- **WeChat Integration**: `core/wx/` - handles WeChat public account authentication and content fetching
- **Article Processing**: `core/article_lax.py` and `jobs/article.py` - content extraction and processing
- **Notification System**: `core/notice/` - supports DingTalk, Feishu, WeChat webhooks
- **Database Models**: `core/models/` - SQLAlchemy models for users, articles, feeds, tasks, etc.

### Configuration
- **Config file**: `config.yaml` (copy from `config.example.yaml`)
- **Environment variables**: Supports `${VAR:-default}` syntax in YAML
- **Key settings**: Database connection, notification webhooks, RSS settings, job scheduling

### Data Storage
- **Database**: SQLite by default (`data/db.db`), configurable to MySQL
- **Static files**: `static/` directory for frontend assets
- **Cache**: `data/cache/` directory for temporary files
- **Driver files**: `driver/` directory contains WebDriver for browser automation

## Development Notes

- The application supports both standalone executable builds (PyInstaller) and containerized deployment
- Frontend development requires Node.js/Yarn, backend requires Python 3.8+
- WeChat authentication uses QR codes and requires browser automation via Selenium
- The system includes comprehensive job scheduling for automated content fetching and notifications
- Configuration supports encryption for sensitive data using `FileCrypto` class