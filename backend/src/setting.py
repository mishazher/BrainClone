from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn

from .config import settings
from .database import PostgresDB, Neo4jDB
# NOTE: this module is an unused duplicate of main.py (the app entrypoint is
# src.main:app). r2r references disabled here for consistency.
from .services import Neo4jService, VectorService  # R2RService disabled (r2r removed)
from .services.mock_data import MockDataService

from .api.routes import graph, search  # documents router disabled (r2r removed)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.log_format == "json"
        else structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

postgres_db = PostgresDB()
neo4j_db = Neo4jDB()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting BrainClone backend", environment=settings.environment)

    try:
        logger.info("Initializing BrainClone with sample memory data")
        mock_data_service = MockDataService()
        app.state.mock_data_service = mock_data_service
        app.state.neo4j_service = None
        app.state.vector_service = None
        app.state.r2r_service = None
        logger.info("BrainClone demo mode initialized with sample memories")

    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise

    yield

    logger.info("Shutting down BrainClone backend")

    try:
        await postgres_db.disconnect()
        if neo4j_db.driver:
            await neo4j_db.disconnect()
        if hasattr(app.state, 'r2r_service') and app.state.r2r_service:
            await app.state.r2r_service.cleanup()
        if hasattr(app.state, 'neo4j_service') and app.state.neo4j_service:
            await app.state.neo4j_service.disconnect()
        if hasattr(app.state, 'vector_service') and app.state.vector_service:
            await app.state.vector_service.disconnect()
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-modal knowledge graph system integrating R2R and Neo4j",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        }
    )


@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "environment": settings.environment,
        "version": settings.app_version,
        "services": {}
    }

    health_status["services"]["postgres"] = "demo_mode"
    health_status["services"]["neo4j"] = "demo_mode"
    health_status["services"]["r2r"] = "demo_mode"
    health_status["services"]["mock_data"] = "active"
    health_status["status"] = "demo_mode"
    health_status["message"] = "BrainClone running with sample memory data"

    return health_status


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "api_docs": "/docs",
        "api_redoc": "/redoc",
        "health": "/health"
    }


app.include_router(
    documents.router,
    prefix=f"{settings.api_v1_prefix}",
    tags=["documents"]
)

app.include_router(
    graph.router,
    prefix=f"{settings.api_v1_prefix}",
    tags=["graph"]
)

app.include_router(
    search.router,
    prefix=f"{settings.api_v1_prefix}",
    tags=["search"]
)


@app.get("/metrics")
async def metrics():
    try:
        from .services import VectorService
        async with VectorService() as vector_service:
            vector_stats = await vector_service.get_statistics()

        from .services import Neo4jService
        async with Neo4jService() as neo4j_service:
            entity_count = await neo4j_service.execute_cypher(
                "MATCH (e:Entity) RETURN count(e) as count"
            )
            relationship_count = await neo4j_service.execute_cypher(
                "MATCH ()-[r]->() RETURN count(r) as count"
            )

        return {
            "vector_embeddings": vector_stats,
            "graph": {
                "entities": entity_count[0]["count"] if entity_count else 0,
                "relationships": relationship_count[0]["count"] if relationship_count else 0
            }
        }
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        return {"error": "Failed to retrieve metrics"}


def run_server():
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers if not settings.debug else 1,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    run_server()