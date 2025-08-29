# F1 Prediction Model

## Run API (FastAPI with Uvicorn/Astra)

Install deps:

```
pip install -r backend/requirements.txt
```

Run API:

```
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Health check: `GET /health`

Predict: `POST /predict` with JSON body:

```
{
  "track": "ITA",
  "weather": "dry",
  "safety_car_chance": 0.2,
  "qualifying": {"Lando Norris": 2, "Max Verstappen": 1},
  "recent_results": {"Lando Norris": ["P2", "P1"], "Lewis Hamilton": ["DNF"]}
}
```

## Run Streamlit UI

```
streamlit run streamlit_app.py
```

# F1 Prediction Model

## Overview
This project predicts Formula 1 race results using a custom scoring system that accounts for driver skills, team strengths, track traits, and more. The backend is written in Python and can be run locally to generate predictions for any race on the calendar.

## How It Works
- Each driver and team is assigned strengths, weaknesses, and stats.
- Each track has a set of traits (e.g., high speed cornering, braking, crash prone).
- The scoring system compares driver/team traits to track traits, applies multipliers, and adds randomness for crash/luck factors.
- The system outputs a ranked list of drivers for a given race, with F1 points assigned to the top 10.

## Running a Prediction (Example: Interlagos/São Paulo)

From the backend directory, run:

```bash
python3 scoring.py
```

This will output the top 10 predicted finishers for the Interlagos (Brazil) race, along with their scores and F1 points.

### Example Output
```
Pos Driver                Team                        Score   Points
---------------------------------------------------------------------------
1   Charles Leclerc       Ferrari                     7       25    
2   Max Verstappen        Red Bull                    6       18    
3   George Russell        Mercedes                    2       15    
4   Kimi Antonelli        Mercedes                    2       12    
5   Lando Norris          McLaren                     1       10    
6   Lewis Hamilton        Ferrari                     1       8     
7   Oscar Piastri         McLaren                     1       6     
8   Carlos Sainz Jr.      Williams                    0       4     
9   Nico Hulkenberg       Sauber                      0       2     
10  Alexander Albon       Williams                    0       1     
```

## Customization
- You can edit `drivers.json`, `teams.json`, and `tracks.json` in `backend/data/` to update stats, teams, or add new tracks.
- The scoring logic is in `backend/scoring.py` and can be adjusted for different weighting or features.

## Requirements
- Python 3.7+

## Next Steps
- Integrate with a FastAPI backend for API access
- Build a frontend dashboard (React or Streamlit)
- Add more advanced features (weather, qualifying, etc.) 
