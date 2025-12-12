from fastapi import FastAPI
from app.routes import problems, run, submit, auth, admin

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AlgoVerse API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(problems.router)
app.include_router(run.router)
app.include_router(submit.router)
app.include_router(auth.router)
app.include_router(admin.router)
