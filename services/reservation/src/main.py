"""
NekoCafé 预约服务 - 主入口
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
import uuid
import json
import sys

from .routes import router
from .database import init_db, close_db


# ==== 结构化日志配置 ====
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": "reservation",
            "traceId": getattr(record, "traceId", "") or record.__dict__.get("traceId", ""),
        }
        return json.dumps(log_entry, ensure_ascii=False)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger("reservation")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Reservation service starting...")
    await init_db()
    yield
    await close_db()
    logger.info("Reservation service stopped.")


app = FastAPI(
    title="NekoCafé Reservation Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==== 请求追踪中间件 ====
@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    start_time = time.perf_counter()

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start_time) * 1000
    response.headers["X-Trace-Id"] = trace_id

    extra = {"traceId": trace_id, "duration_ms": round(duration_ms, 2)}
    record = logging.LogRecord(
        name="reservation", level=logging.INFO, pathname="", lineno=0,
        msg=f"{request.method} {request.url.path} -> {response.status_code}",
        args=(), exc_info=None
    )
    record.traceId = trace_id
    logger.handle(record)
    return response


app.include_router(router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "reservation", "version": "1.0.0"}
