# Third-party dependencies · 第三方依赖

Hzhikai 的原创范围为本仓库中的应用代码、集成设计与技术文档。下列框架和工具为独立开源依赖，其作者与版权归属保持不变。

| Dependency | Role | License | Upstream |
| --- | --- | --- | --- |
| FastAPI | REST API and OpenAPI | MIT | [FastAPI](https://github.com/fastapi/fastapi) |
| Uvicorn | ASGI server | BSD-3-Clause | [Uvicorn](https://github.com/Kludex/uvicorn) |
| LangGraph / LangChain Core | State graph and execution primitives | MIT | [LangGraph](https://github.com/langchain-ai/langgraph) · [LangChain](https://github.com/langchain-ai/langchain) |
| Pydantic / pydantic-settings | Data contracts and settings | MIT | [Pydantic](https://github.com/pydantic/pydantic) · [Settings](https://github.com/pydantic/pydantic-settings) |
| SQLAlchemy | ORM and database sessions | MIT | [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) |
| pytest / Ruff | Development tools | MIT | [pytest](https://github.com/pytest-dev/pytest) · [Ruff](https://github.com/astral-sh/ruff) |
| HTTPX | HTTP client and API test support | BSD-3-Clause | [HTTPX](https://github.com/encode/httpx) |
| PyMySQL | Optional database driver | MIT | [PyMySQL](https://github.com/PyMySQL/PyMySQL) |
| redis-py | Optional client dependency | MIT | [redis-py](https://github.com/redis/redis-py) |
| Hatchling | Build backend | MIT | [Hatch](https://github.com/pypa/hatch) |

依赖及版本范围以 [pyproject.toml](pyproject.toml) 为准。许可证应随所安装版本查阅对应发行包与上游文件；可选依赖的列出表示依赖管理范围。

本仓库通过包管理器使用上述组件，未复制第三方完整工程或其源码目录。依赖链接用于来源归属，不将上游框架成果表述为个人原创。
