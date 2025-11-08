# Technology Stack

## Build System & Package Management

- **Package Manager**: UV (modern Python package manager)
- **Python Version**: 3.12+ (Python 3.13 supported)
- **Configuration**: `pyproject.toml` for dependencies and tool configuration

## Core Dependencies

### LLM & AI
- `openai>=1.66.3` - Azure OpenAI API with Structured Outputs
- `pydantic>=2.10.6` - Data validation and type-safe LLM responses

### Data Processing & Visualization
- `pandas>=2.2.3` - Data manipulation
- `matplotlib>=3.7.0` - Plotting (manual Japanese font configuration)
- `seaborn>=0.12.0` - Statistical visualizations
- `scipy>=1.11.0` - Scientific computing and statistical analysis

### Code Execution
- `ipython>=8.0.0` - IPython kernel for code execution
- `jupyter-client>=8.0.0` - Jupyter protocol communication

### Templating & Rendering
- `jinja2>=3.1.6` - Template engine for prompts and reports
- `markdown>=3.5` - Markdown processing

### Utilities
- `python-dotenv>=1.0.1` - Environment variable management
- `loguru>=0.7.3` - Logging
- `pillow>=11.1.0` - Image processing

## Development Tools

- `pytest>=8.3.4` - Testing framework
- `ruff>=0.7.2` - Linter and formatter (replaces black, flake8, isort)
- `mypy>=1.13.0` - Static type checker
- `pandas-stubs>=2.2.0` - Type stubs for pandas

## Common Commands

### Setup
```bash
# Install dependencies
uv sync

# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### Running
```bash
# Execute main workflow
python scripts/simple_workflow.py
```

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test suites
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/e2e/ -v
```

### Code Quality
```bash
# Format and lint with ruff
ruff check .
ruff format .

# Type checking
mypy src/
```

## Environment Variables

Required in `.env` file:

```env
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
SANDBOX_TIMEOUT=600
DEBUG=True
```

## Key Technical Decisions

- **No japanize_matplotlib**: Manual font configuration for Python 3.13 compatibility
- **Escape Sequence Handling**: Azure OpenAI returns `\\n` which requires decoding
- **Structured Outputs**: Type-safe LLM responses using Pydantic models
- **IPython Kernel**: Persistent kernel for efficient multi-step code execution
