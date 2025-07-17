from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI()

class PredictionRequest(BaseModel):
    drivers: List[str]
    teams: List[str]
    track: str
    weather: str = "dry"
    qualifying: Dict[str, int] = {}
    recent_results: Dict[str, List[str]] = {}

@app.post("/predict")
def predict_race(request: PredictionRequest):
    # Placeholder: scoring logic will be added later
    return {"message": "Prediction endpoint is working!", "input": request.dict()} 