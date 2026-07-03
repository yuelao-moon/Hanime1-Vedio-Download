# Repository Guidelines

## Project Structure & Module Organization

This is a local desktop web app: a Python FastAPI backend serves APIs and the static frontend, then PyInstaller packages everything into one Windows executable.

- `python_backend/app/`: backend modules. `main.py` wires routes, `scraper.py` handles remote HTTP and Cloudflare/session behavior, `parser.py` keeps HTML parsing pure, `downloads.py` manages Gopeed-backed downloads, and `local_db.py` stores SQLite state.
- `python_backend/tests/`: pytest coverage for API routes, parsers, cookies, profile actions, cache behavior, and frontend integration assumptions.
- `src/main/resources/static/`: direct-served frontend assets (`index.html`, `app.js`, `style.css`). There is no frontend build step.
- `HanimeMediaCenter.spec`: PyInstaller single-exe packaging recipe.

## Build, Test, and Development Commands

Run commands from the repository root on Windows PowerShell:

```powershell
python -m pip install -r python_backend\requirements.txt
python -m pip install -r python_backend\requirements-dev.txt
python python_backend\run.py
python -m pytest python_backend\tests -q
python -m compileall -q python_backend
node --check src\main\resources\static\app.js
pyinstaller --clean --noconfirm HanimeMediaCenter.spec
```

Use `python_backend\run.py --app-home "D:\HanimeData"` when testing with an isolated data directory. The default app URL is `http://127.0.0.1:58080/`.

## Coding Style & Naming Conventions

Use 4-space indentation for Python and keep FastAPI route logic thin by delegating scraping, parsing, persistence, and download behavior to existing modules. Prefer `snake_case` for Python functions, test names, and files. Keep parser helpers network-free. Frontend code is plain JavaScript/CSS; avoid adding build tooling unless the repository adopts it broadly.

## Testing Guidelines

Add or update focused pytest files under `python_backend/tests/`, named `test_<feature>.py`. Async tests should use `@pytest.mark.asyncio`. Prefer `create_app(..., scraper=FakeScraper())` and temporary app homes for deterministic tests. For live-site or cookie-sensitive fixes, also verify the real user flow: a refresh returning `200` is not enough if downstream browse or action endpoints still fail.

## Commit & Pull Request Guidelines

Recent history uses short imperative summaries such as `Fix comments UI...`, `Wait for valid Cloudflare cookies...`, and occasional Chinese summaries. Keep commits scoped and describe the behavior changed. PRs should include a concise problem/solution summary, commands run, linked issue or repro steps, and screenshots or short recordings for UI changes.

## Security & Configuration Tips

Do not commit local data from `%LOCALAPPDATA%\HanimeMediaCenter\`, cookies, account sessions, or generated `dist/` output. Be careful with endpoint semantics: profile favorite actions and comment actions may require the site's current hidden state, cookies, and CSRF values rather than a simplified desired state.
