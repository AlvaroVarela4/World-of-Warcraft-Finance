from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import realms, items, market

app = FastAPI(title="WoW Auction Analyzer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(realms.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(market.router, prefix="/api")
