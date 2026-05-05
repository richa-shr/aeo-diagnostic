from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio

from engines import run_all_engines
from search import fetch_competitors
from scorer import generate_report

app = FastAPI(title="AEO Diagnostic API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class DiagnoseRequest(BaseModel):
    product_name: str
    product_description: Optional[str] = ""
    category: Optional[str] = ""
    query: str
    competitors: Optional[List[str]] = []


@app.get("/")
def root():
    return {"status": "AEO Diagnostic API is running"}


@app.post("/diagnose")
async def diagnose(req: DiagnoseRequest):
    try:
        # Step 1: Fetch real competitors from web if not provided
        competitors = req.competitors
        if not competitors:
            competitors = await fetch_competitors(req.query, req.category)

        # Step 2: Run query through all 3 simulated AI engines in parallel
        engine_responses = await run_all_engines(
            query=req.query,
            product_name=req.product_name,
            product_description=req.product_description,
            competitors=competitors,
        )

        # Step 3: Generate report card
        report = await generate_report(
            product_name=req.product_name,
            query=req.query,
            competitors=competitors,
            engine_responses=engine_responses,
        )

        return {"success": True, "report": report}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))