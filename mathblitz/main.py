"""FastAPI application factory and SPA hosting."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .core.cache import Cache
from .core.container import Container
from .core.settings import Settings
from .db.session import initialize_database
from .services import ServiceError


def create_app(settings: Settings | None = None, cache: Cache | None = None) -> FastAPI:
    selected_settings = settings or Settings.from_env()
    container = Container.build(selected_settings, cache)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        initialize_database(container.engine)
        yield
        container.engine.dispose()

    app = FastAPI(
        title="MathBlitz API",
        version="2.0.0",
        description="API-first math practice platform.",
        lifespan=lifespan,
    )
    app.state.container = container
    app.include_router(router, prefix=selected_settings.api_prefix)

    @app.exception_handler(ServiceError)
    async def application_error(_request: Request, exc: ServiceError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; base-uri 'self'; "
            "frame-ancestors 'none'"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    assets_dir = selected_settings.frontend_dir / "assets"
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    index_path = selected_settings.frontend_dir / "index.html"

    @app.get("/", include_in_schema=False)
    def web_root() -> FileResponse:
        return FileResponse(index_path)

    @app.get("/{route:path}", include_in_schema=False)
    def web_routes(route: str) -> FileResponse:
        if route.startswith("api/"):
            return FileResponse(index_path, status_code=404)
        return FileResponse(index_path)

    return app


app = create_app()
