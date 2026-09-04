from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app.routers import products

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

app.include_router(products.router, prefix=settings.api_v1_prefix)


@app.get("/")
def root():
    return {"status": "ok", "app": settings.app_name}