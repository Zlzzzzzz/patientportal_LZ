from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import patients, analytics, ai_summary

app = FastAPI(title="Clinical Trial Portal API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patients.router)
app.include_router(analytics.router)
app.include_router(ai_summary.router)

@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}
