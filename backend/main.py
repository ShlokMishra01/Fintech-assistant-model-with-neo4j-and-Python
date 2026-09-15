from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.finance import router as finance_router
from backend.app.api.transactions import router as transactions_router
from backend.app.api.goals import router as goals_router
from backend.app.api.assistant import router as assistant_router
from backend.app.api.auth import router as auth_router
from backend.app.api.portfolio import router as portfolio_router
from backend.app.api.market import router as market_router

app = FastAPI(
    title="Personal Finance AI Assistant API",
    description="Explainable personal finance assistant using Dynamic Knowledge Graphs, Portfolio Intelligence, and LLM-based GraphRAG.",
    version="2.0.0"
)

# Explicit CORS allowed origins for local dev frontend (Vite & React & Streamlit ports)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8501",
    "http://127.0.0.1:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(finance_router)
app.include_router(transactions_router)
app.include_router(goals_router)
app.include_router(assistant_router)
app.include_router(auth_router)
app.include_router(portfolio_router)
app.include_router(market_router)

@app.get("/")
def health_check():
    return {
        "status": "ONLINE",
        "service": "Personal Finance AI Assistant API",
        "database": "Neo4j (finance-ai-antigravity)",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
