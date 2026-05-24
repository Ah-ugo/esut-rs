from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging

from app.database import connect_db, disconnect_db
from app.routes import auth, users, programmes, courses, students, results, transcripts, admin, audit
from app.middleware.rate_limit import RateLimitMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    logger.info("Database connected")
    yield
    await disconnect_db()
    logger.info("Database disconnected")


app = FastAPI(
    title="ESUT Result Processing System",
    description="University Result Processing and Transcript Generation System for Enugu State University of Science and Technology",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://esut-transcript.vercel.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_middleware(RateLimitMiddleware)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred", "type": type(exc).__name__},
    )


# Register routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(programmes.router, prefix="/api/programmes", tags=["Programmes"])
app.include_router(courses.router, prefix="/api/courses", tags=["Courses"])
app.include_router(students.router, prefix="/api/students", tags=["Students"])
app.include_router(results.router, prefix="/api/results", tags=["Results"])
app.include_router(transcripts.router, prefix="/api/transcripts", tags=["Transcripts"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit Logs"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "ESUT Result Processing System", "version": "1.0.0"}
