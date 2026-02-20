# CLAUDE.md - AI Personal Trainer

Project-specific guidelines, coding standards, and common commands for the AI Personal Trainer assistant.

## Documentation Maintenance

**IMPORTANT: After making project-wide changes, ALWAYS update `README.md` in project root.**

Update README.md when:
- Changing build process or Docker configuration
- Adding/modifying environment variables
- Changing project structure
- Updating tech stack versions
- Modifying startup commands
- Adding new services or dependencies

## Bash Commands
- **Environment Setup**: `python -m venv venv` && `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
- **Install Dependencies**: `pip install -r requirements.txt`
- **Run Application**: `python main.py`
- **Testing**: `pytest`
- **Linting & Formatting**: `black .` or `ruff check . --fix`

## Tech Stack & Architecture
- **Framework**: LangChain using **LCEL (LangChain Expression Language)** via the pipe `|` operator.
- **Storage**:
    - **Vector Store**: Local instance (ChromaDB or FAISS).
    - **Session Memory**: SQLite for persistent conversation history.
- **Integrations**: Google Calendar API for workout scheduling and availability management.
- **Interface**: No UI planned (CLI or backend-only logic).

## Code Style Guidelines
- **Python Standards**: Strictly follow **PEP8**.
- **Type Safety**: Use **Type Hints** for all function signatures and variable declarations (from `typing` module).
- **LangChain Pattern**: Avoid legacy `Chain` classes. Always prefer LCEL syntax for composability.
- **Formatting**: Code must be formatted using `Black` or `Ruff` before submission.
- **Modularity**: Separate concerns into distinct modules:
    - `tools/`: Google Calendar and custom utility functions.
    - `prompts/`: System messages and templates.
    - `database/`: Vector store and SQLite logic.

## Workflow & Best Practices
- **Environment**: Always work within the virtual environment (`venv`).
- **Google Calendar**: When adding calendar features, clearly document the required OAuth scopes and credential paths.
- **Memory**: Ensure conversation state is correctly committed to the SQLite store after each interaction.
- **Testing**: Write unit tests for custom tools and integration tests for the LangChain sequences.