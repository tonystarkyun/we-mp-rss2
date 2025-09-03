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
- **Development server**: `cd web_ui && yarn dev` (runs on port 3000, proxies API calls to backend)
- **Build frontend**: `cd web_ui && yarn build` (or use `web_ui/build.sh` on Unix / `web_ui/build.bat` on Windows)
- **Install dependencies**: `cd web_ui && yarn install` (or `npm install`)

### Testing Commands
- **Run integration tests**: `python test_integration.py`
- **Test article processing**: `python test_article.py`
- **Test crawler functionality**: `python test_crawler.py`
- **Test notifications**: `python test.py`

### Build Commands
- **Linux executable**: `./build-linux.sh` (PyInstaller + frontend build)
- **Windows executable**: `build.bat` or `build-standalone.bat`
- **Simple builds**: `./build-simple-linux.sh` or `build-simple.bat`
- **Frontend only**: `web_ui/build.sh` (Unix) / `web_ui/build.bat` (Windows)

### Docker Development
- **Development (SQLite)**: `docker-compose -f compose/docker-compose-sqlite.yaml up`
- **Production (MySQL)**: `docker-compose -f compose/docker-compose.yaml up`
- **Quick start**: `docker run -d --name we-mp-rss -p 8001:8001 -v ./data:/app/data ghcr.io/rachelos/we-mp-rss:latest`

## Architecture Overview

### Backend Structure
- **Entry point**: `main.py` - starts FastAPI server with uvicorn, optionally starts APScheduler background jobs
- **Web framework**: `web.py` - FastAPI app configuration with CORS, static file serving, JWT authentication, and API routing
- **Configuration**: `core/config.py` - YAML-based configuration with `${VAR:-default}` environment variable syntax and encryption support
- **Database**: SQLAlchemy ORM with models in `core/models/` (SQLite default, MySQL configurable)
- **APIs**: 17 RESTful endpoint modules in `apis/` directory (`/api/v1/` prefix)
- **Background jobs**: APScheduler-based task system in `jobs/` directory (article fetching, notifications, webhooks)
- **Core services**: Business logic modules in `core/` directory (RSS generation, WeChat integration, article processing)

### Frontend Structure
- **Framework**: Vue 3 + Vite + TypeScript
- **UI Library**: Arco Design Vue + Ant Design Vue
- **Build output**: Copies to `static/` directory for backend to serve
- **API client**: Axios-based HTTP client in `src/api/`

### Key Components
- **WeChat Authentication Flow**: QR code login via Selenium (`driver/wx.py`) → cookie persistence → session management
- **Article Processing Pipeline**: WeChat content fetching (`core/wx/`) → content parsing (`core/article_lax.py`) → RSS generation (`core/rss.py`)
- **Job System**: APScheduler-based background tasks initialized from `jobs/__init__.py` with modules for account management, article fetching, and notifications
- **Browser Automation**: Firefox + Geckodriver integration for WeChat authentication (requires manual driver setup)
- **Multi-format Notifications**: DingTalk, Feishu, WeChat webhook support via `core/notice/`

### Configuration
- **Config file**: `config.yaml` (copy from `config.example.yaml`) with 50+ configurable parameters
- **Environment variables**: Full `${VAR:-default}` syntax support (key vars: `DB`, `PORT`, `USERNAME`, `PASSWORD`)
- **Encryption support**: Sensitive data encryption via `FileCrypto` class
- **Key settings**: Database connection, notification webhooks, RSS settings, APScheduler job configuration

### Data Storage
- **Database**: SQLite by default (`data/db.db`), configurable to MySQL
- **Static files**: `static/` directory for frontend assets
- **Cache**: `data/cache/` directory for temporary files
- **Driver files**: `driver/` directory contains WebDriver for browser automation

## Development Notes

### Build System
- **Multiple PyInstaller specs**: `WeRSS-Linux.spec`, `WeRSS-Standalone.spec`, `WeRSS-Standalone-Safe.spec` for different deployment scenarios
- **Frontend proxy**: Development server on port 3000 proxies API calls to backend (typically port 8001)
- **Build artifacts**: Executables generated in `dist/` directory, frontend assets copied to `../static/`

### Browser Automation Requirements
- **Firefox + Geckodriver**: Required for WeChat QR code authentication (manual installation guide: `driver/geckodriver_manual_install.md`)
- **WebDriver management**: Selenium-based automation with cookie persistence for session management

### Development Workflow
- **Database handling**: First run initializes database, subsequent runs preserve existing data
- **Job system**: Optional background task scheduling (use `-job True` flag to enable)
- **Live reload**: Frontend development server supports hot module replacement via Vite
- **Testing approach**: Manual test execution (no formal test framework configured)