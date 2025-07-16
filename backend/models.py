from pydantic import BaseModel
from typing import List, Optional

class Driver(BaseModel):
    name: str
    team: str
    ovr: int
    experience: int
    racecraft: int
    awareness: int
    pace: int
    strengths: List[str]
    weaknesses: List[str]
    home_gp: Optional[str] = None
    recent_results: Optional[List[str]] = None  # e.g., ["P1", "P5", "DNF"]
    qualifying_position: Optional[int] = None

class Team(BaseModel):
    name: str
    tier: str  # e.g., "Top", "Upper-Mid", "Mid", "Low"
    strengths: List[str]
    weaknesses: Optional[List[str]] = None

class Track(BaseModel):
    name: str
    traits: List[str]
    crash_risk: float  # e.g., 0.3 for 30%
    country: str
    weather: Optional[str] = None  # e.g., "Dry", "Wet"
    is_street: Optional[bool] = False

class RaceConfig(BaseModel):
    track: Track
    drivers: List[Driver]
    teams: List[Team]
    weather: Optional[str] = None
    qualifying_results: Optional[List[int]] = None
