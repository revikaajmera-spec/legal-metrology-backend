from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import products

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

# CORS: tells the browser which other websites are allowed to talk to
# this API. Without this, browsers block requests from your React app
# (running on a different address) as a security precaution.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # "*" = allow any website (fine for a light prototype;
                            # tighten this to your real frontend URL before going live for real)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router, prefix=settings.api_v1_prefix)


@app.get("/")
def root():
    return {"status": "ok", "app": settings.app_name}