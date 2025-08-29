from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from . import scoring

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

class PredictionRequest(BaseModel):
    track: str
    weather: str = "dry"
    safety_car_chance: float = 0.2
    qualifying: Dict[str, int] = {}
    recent_results: Dict[str, List[str]] = {}

@app.post("/predict")
def predict_race(request: PredictionRequest):
    try:
        results = scoring.predict_for_track(
            request.track,
            weather=request.weather,
            safety_car_chance=request.safety_car_chance,
        )
        # Post-adjust using qualifying and recent_results when provided
        if request.qualifying or request.recent_results:
            adjusted = []
            for r in results:
                driver_name = r["driver"]
                team_name = r["team"]
                base_team = next((t for t in scoring.load_json(scoring.os.path.join(scoring.os.path.dirname(scoring.__file__), 'data/teams.json')) if t['name'] == team_name), None)
                if not base_team:
                    adjusted.append(r)
                    continue
                # Recompute with context
                drivers = scoring.load_json(scoring.os.path.join(scoring.os.path.dirname(scoring.__file__), 'data/drivers.json'))
                driver = next((d for d in drivers if d['name'] == driver_name), None)
                tracks = scoring.load_json(scoring.os.path.join(scoring.os.path.dirname(scoring.__file__), 'data/tracks.json'))
                track_obj = next((t for t in tracks if t['code'].lower() == request.track.lower() or request.track.lower() in t['name'].lower()), None)
                new_score = scoring.calculate_performance_score(
                    driver,
                    base_team,
                    track_obj,
                    weather=request.weather,
                    safety_car_chance=request.safety_car_chance,
                    qualifying=request.qualifying,
                    recent_results=request.recent_results,
                )
                adjusted.append({"driver": driver_name, "team": team_name, "score": round(new_score, 2)})
            results = sorted(adjusted, key=lambda x: x['score'], reverse=True)
        return {"predictions": results}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))