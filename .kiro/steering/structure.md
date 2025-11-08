# Project Structure

## Architecture Pattern

Clean Architecture with strict layer separation and dependency inversion.

## Directory Layout

```
src/
├── domain/              # Domain Layer (core business logic)
│   ├── entities/        # Business entities (Plan, Program, Review, DataThread)
│   └── repositories/    # Repository interfaces (abstract base classes)
├── application/         # Application Layer (use cases)
│   └── use_cases/       # Business logic orchestration
├── infrastructure/      # Infrastructure Layer (implementations)
│   ├── repositories/    # Repository implementations (OpenAI, Jupyter)
│   ├── renderers/       # Report renderers (HTML, Markdown)
│   ├── kernel/          # Jupyter kernel management
│   ├── services/        # External service integrations
│   └── di_container.py  # Dependency injection container
├── llms/                # LLM utilities
│   ├── llm_response.py  # Response handling
│   └── load_template.py # Jinja2 template loading
├── prompts/             # Jinja2 prompt templates
│   ├── describe_dataframe.jinja
│   ├── generate_code.jinja
│   ├── generate_plan.jinja
│   ├── generate_report.jinja
│   └── generate_review.jinja
└── static/              # Static assets (CSS, fonts)

scripts/                 # Executable workflows
tests/
├── unit/               # Unit tests (isolated components)
├── integration/        # Integration tests (multiple components)
└── e2e/                # End-to-end tests (full workflows)

data/                   # Input data files (CSV)
output/                 # Generated reports and visualizations
docs/                   # Documentation and planning
```

## Layer Dependencies

```
Presentation (scripts/) 
    ↓
Application (use_cases/)
    ↓
Domain (entities/ + repositories/)
    ↑
Infrastructure (repositories/ implementations)
```

**Rule**: Dependencies flow inward. Domain layer has no dependencies on outer layers.

## Key Components

### Domain Layer
- **Entities**: `Plan`, `Program`, `Review`, `DataThread` - immutable business objects
- **Repository Interfaces**: `LLMRepository`, `SandboxRepository` - abstract contracts

### Application Layer
- **Use Cases**: Single-responsibility business operations
  - `DescribeDataframeUseCase` - Data analysis
  - `GeneratePlanUseCase` - Task planning
  - `GenerateCodeUseCase` - Code generation
  - `ExecuteCodeUseCase` - Code execution
  - `GenerateReviewUseCase` - Result review
  - `GenerateReportUseCase` - Report generation

### Infrastructure Layer
- **OpenAILLMRepository**: Azure OpenAI integration with Structured Outputs
- **JupyterSandboxRepository**: IPython kernel for code execution
- **HTMLRenderer / MarkdownRenderer**: Report formatting
- **DIContainer**: Centralized dependency management with lazy initialization

## Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Methods**: `snake_case()`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_leading_underscore`

## Code Organization Rules

1. **Use Cases**: One use case per file, single responsibility
2. **Repositories**: Interface in `domain/`, implementation in `infrastructure/`
3. **Dependency Injection**: Always use `DIContainer` for instantiation
4. **Type Hints**: Required on all function signatures (enforced by mypy)
5. **Pydantic Models**: Use for all LLM request/response schemas
6. **Jinja2 Templates**: Store all prompts in `src/prompts/`

## Testing Structure

- **Unit tests**: Mock all external dependencies
- **Integration tests**: Test component interactions
- **E2E tests**: Full workflow validation with real services

## Output Structure

```
output/{session_id}/
├── report.html              # HTML report
├── analysis_report.md       # Markdown report
├── style.css                # Styling
└── *.png                    # Generated visualizations
```

Session ID format: `YYYYMMDD_HHMMSS`

## Configuration Files

- `.env` - Environment variables (never commit)
- `.env.example` - Template for required variables
- `pyproject.toml` - Dependencies and tool configuration
- `.gitignore` - Excludes `output/`, `data/`, `docs/`, `.env`
