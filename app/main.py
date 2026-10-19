from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, Request, status
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import install_handlers
from app.db.base import Base
from app.db.models import AgentRun, KnowledgeEntry
from app.db.session import create_database_engine, create_session_factory, get_db
from app.knowledge import create_entry, seed_demo_knowledge
from app.schemas import (
    AgentRunResponse,
    DebugRequest,
    KnowledgeCreate,
    KnowledgeRead,
    TraceEvent,
)
from app.service import execute_run, get_run, get_trace


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        resolved.data_dir.mkdir(parents=True, exist_ok=True)
        engine = create_database_engine(resolved.database_url)
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        Base.metadata.create_all(engine)
        with app.state.session_factory() as db:
            seed_demo_knowledge(db)
        yield
        engine.dispose()

    app = FastAPI(
        title="Industrial Debugging Agent",
        version="0.1.0",
        description="Safe, inspectable LangGraph workflow for virtual industrial equipment",
        lifespan=lifespan,
    )
    install_handlers(app)
    api = APIRouter(prefix="/api/v1")
    Database = Annotated[Session, Depends(get_db)]

    @api.get("/health", tags=["health"])
    def health(request: Request) -> dict:
        with request.app.state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        with request.app.state.session_factory() as db:
            run_count = db.scalar(select(func.count(AgentRun.id))) or 0
        return {
            "service": "industrial-debugging-agent",
            "status": "healthy",
            "mode": resolved.app_env,
            "dependencies": {
                "database": "ready",
                "state_cache": "ready" if resolved.app_env == "demo" else "unavailable",
                "llm": "ready" if resolved.app_env == "demo" else "unavailable",
            },
            "run_count": run_count,
        }

    @api.post(
        "/runs",
        response_model=AgentRunResponse,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["agent"],
    )
    def start_run(payload: DebugRequest, db: Database) -> AgentRunResponse:
        return execute_run(db, payload)

    @api.get("/runs/{run_id}", response_model=AgentRunResponse, tags=["agent"])
    def read_run(run_id: UUID, db: Database) -> AgentRunResponse:
        return get_run(db, run_id)

    @api.get("/runs/{run_id}/trace", response_model=list[TraceEvent], tags=["agent"])
    def read_trace(run_id: UUID, db: Database) -> list[TraceEvent]:
        return get_trace(db, run_id)

    @api.post(
        "/knowledge/cases",
        response_model=KnowledgeRead,
        status_code=status.HTTP_201_CREATED,
        tags=["knowledge"],
    )
    def add_knowledge(payload: KnowledgeCreate, db: Database) -> KnowledgeEntry:
        return create_entry(db, payload)

    app.include_router(api)
    return app


app = create_app()
