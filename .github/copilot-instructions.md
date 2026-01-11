# AnkiBrain Development Guide

## Project Overview
AnkiBrain is an Anki addon that integrates AI-powered features (chat, card generation, topic explanation) into Anki's desktop client. It uses a **dual-architecture** with a PyQt6-based Python backend embedded in Anki and a React frontend served via QWebEngine.

## Architecture

### Dual-Mode Operation
The addon supports two user modes (`util.UserMode` enum):
- **LOCAL**: AI runs in a local Python 3.9.13 venv with LangChain/OpenAI (requires C++ build tools)
- **SERVER**: AI operations delegated to remote server (uses bundled httpx in `user_files/bundled_dependencies/`)

### Key Components
1. **Anki Integration** (`__init__.py`, `boot.py`): Entry point via Anki's `profileLoaded` hook. Bootstraps by inserting `ChatAI/`, venv site-packages, and bundled deps into `sys.path`.
2. **AnkiBrainModule** (`AnkiBrainModule.py`): Main singleton (`mw.ankiBrain`) managing lifecycle, PyQt signals (`GUIThreadSignaler`), and UI setup.
3. **React Frontend** (`webview/`): Built React app loaded from `webview/build/index.html` into `SidePanel` (QDockWidget with QWebEngineView).
4. **Python↔React Bridge** (`ReactBridge.py`, `WebEnginePage.py`): Bidirectional JSON communication via `pyqtSignal(str)` and JS `window.pywebview.send()`.
5. **ChatAI Module** (`ChatAI/`): Subprocess-based LangChain wrapper. Runs as external script via `ExternalScriptManager` using venv Python interpreter (`project_paths.python_path`).
6. **InterprocessCommand** (`InterprocessCommand.py`): Shared enum for command-based IPC between Python layers and React (e.g., `EXPLAIN_TOPIC`, `GENERATE_CARDS`).

### Critical Data Flows
- **User selects text in Anki card** → `card_injection.py` injects JS → `pycmd` → `AnkiBrainModule.handle_anki_card_webview_pycmd()` → `ReactBridge` → React UI
- **React requests AI action** → `PythonBridge/index.js` sends JSON → `WebEnginePage.react_data_received` signal → `ReactBridge.a_handle_react_data_received()` (async) → `ChatAIModuleAdapter` → `ExternalScriptManager` (subprocess I/O) → `ChatAI/__init__.py`
- **Async threading**: ChatAI operations run in `AnkiBrain.loop` (asyncio event loop). Use `GUIThreadSignaler` signals to update Qt UI from async threads (e.g., `sendToJSFromAsyncThreadSignal.emit()`).

## Development Workflows

### Frontend Development
- **Build**: `cd webview && yarn build` (outputs to `webview/build/`)
- **Hot reload**: Run `yarn start` for standalone dev server, then modify React app to connect to Anki's Python backend
- **Debugging**: React DevTools won't work in QWebEngine; use `console.log()` and check Anki's debug console

### Backend Development
- **Testing changes**: Restart Anki after modifying Python files (no hot reload)
- **Debugging ChatAI subprocess**: Add `print()` statements in `ChatAI/__init__.py`; output appears in Anki console
- **Venv location**: `user_files/venv/` (not root `venv/`—old location auto-deleted in `boot.run_boot_checks()`)

### Installation & Dependencies
- **Local mode setup**: OS-specific scripts (`win-install.bat`, `linux-install.sh`, `macos-install.sh`) install pyenv, Python 3.9.13, create venv, install requirements
- **Requirements**: Platform-specific (`windows_requirements.txt`, `linux_requirements.txt`) include PyQt6, LangChain, OpenAI, ChromaDB
- **Update handling**: `PostUpdateDialog` shown on version bump (tracked via `.ankibrain-version`), prompts dependency reinstall

### Path Management
All paths use `project_paths.py` constants:
- `root_project_dir`: Addon root
- `venv_site_packages_path`: OS-specific venv lib path
- `ChatAI_module_dir`: For subprocess script
- `dotenv_path`: `user_files/.env` for OpenAI key

## Coding Conventions

### Python
- **Signal-based UI updates**: Always use `GUIThreadSignaler` signals when updating Qt UI from async/non-GUI threads. Direct widget manipulation causes crashes.
- **Async patterns**: Use `asyncio.run_coroutine_threadsafe(coro, mw.ankiBrain.loop)` to schedule async tasks from sync contexts (e.g., Qt slots).
- **Settings persistence**: `SettingsManager` (`settings.py`) uses JSON file at `settings_path`. Call `mw.settingsManager.get(key)` / `mw.settingsManager.set(key, value)`.
- **Menu actions**: Use `add_ankibrain_menu_item(label, callback)` and track refs in `mw.menu_actions` for cleanup.

### React/JS
- **Command pattern**: All Python↔React IPC uses `InterprocessCommand` enum values (must match between `InterprocessCommand.py` and `InterprocessCommand.js`).
- **State management**: Redux (`@reduxjs/toolkit`) with slices in `webview/src/api/redux/slices/`.
- **Python bridge**: Import `pyEditSetting`, `pySendCommand` from `api/PythonBridge/senders/`. Responses handled in `handlePythonDataReceived()` switch.

### File Organization
- Root-level files: Anki-specific UI components (Dialogs, Buttons, WebView wrappers)
- `ChatAI/`: Isolated LangChain module (runs as subprocess)
- `webview/`: Complete React app (do NOT edit `build/` directly)
- `user_files/`: Runtime data (venv, .env, settings, bundled deps)

## Common Pitfalls
1. **PyQt threading**: Never call Qt methods from async tasks without signals. Use `GUIThreadSignaler`.
2. **Subprocess limits**: `ExternalScriptManager` sets 1GB buffer limit for subprocess I/O. Large responses may hang.
3. **Path assumptions**: Always use `project_paths.py` constants; hardcoded paths break on different OSes.
4. **Venv isolation**: ChatAI subprocess uses venv Python (`python_path`), main Anki uses Anki's embedded Python.
5. **InterprocessCommand sync**: When adding new commands, update enum in BOTH `InterprocessCommand.py` and `webview/src/api/PythonBridge/InterprocessCommand.js`.

## Key Files Reference
- [__init__.py](__init__.py): Addon entry, version tracking, sys.path setup
- [boot.py](boot.py): Mode detection, module loading logic
- [AnkiBrainModule.py](AnkiBrainModule.py): Main app class, UI setup, signals
- [ReactBridge.py](ReactBridge.py): Command dispatcher for React↔Python IPC
- [ChatAIModuleAdapter.py](ChatAIModuleAdapter.py): Wrapper for subprocess-based AI module
- [ExternalScriptManager.py](ExternalScriptManager.py): Generic subprocess stdin/stdout JSON RPC
- [project_paths.py](project_paths.py): Centralized path constants (OS-aware)
- [webview/src/api/PythonBridge/index.js](webview/src/api/PythonBridge/index.js): React-side bridge handler
