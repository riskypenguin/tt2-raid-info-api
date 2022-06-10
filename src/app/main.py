import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from src.app.routers import api
from src.models.Stage import Stage

load_dotenv()

ENV_STAGE = os.getenv('STAGE')

app = FastAPI(
    title=f"TT2 Raid Data API | {ENV_STAGE}",
    version="0.1.0",
    description="""
    API providing access to raid seed data for the mobile game Tap Titans 2.
    You can get raw (unmodified) seeds and enhanced seeds (with useful extra information).
    """,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "tryItOutEnabled": ENV_STAGE != Stage.DEV
    }
)

app.include_router(api.router)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse("/docs")
