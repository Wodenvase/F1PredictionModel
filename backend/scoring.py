# scoring.py
# This module will contain the F1 race scoring logic.

import json
import random
import os
import sys

def load_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def get_team_info(team_name, teams):
    # Try exact match (case-insensitive)
    for team in teams:
        if team_name.strip().lower() == team['name'].strip().lower():
            return team
    # Try partial match (case-insensitive)
    for team in teams:
        if team_name.strip().lower() in team['name'].strip().lower() or team['name'].strip().lower() in team_name.strip().lower():
            return team
    # Try matching by main keyword (e.g., 'Red Bull' in 'Red Bull Racing-Honda RBPT')
    team_keywords = team_name.lower().replace('-', ' ').split()
    for team in teams:
        team_words = team['name'].lower().replace('-', ' ').split()
        if any(word in team_words for word in team_keywords):
            return team
    return None

def get_team_tier_and_luck(team_name):
    # Ordered best → worst matching names in teams.json
    best_to_worst = [
        "McLaren",
        "Ferrari",
        "Mercedes",
        "Red Bull",
        "Williams",
        "Sauber",
        "Racing Bulls",
        "Aston Martin",
        "Haas",
        "Alpine",
    ]
    team_name_lower = team_name.strip().lower()
    if team_name_lower == best_to_worst[0].lower():
        return ("top", 1.0, 2)
    elif team_name_lower in [t.lower() for t in best_to_worst[1:3]]:
        return ("upper-mid", 0.97, 1)
    elif team_name_lower in [t.lower() for t in best_to_worst[3:7]]:
        return ("mid", 0.93, 0)
    else:
        return ("low", 0.9, -1)

def _base_driver_score(driver):
    # Use numeric attributes if present; fall back to sensible defaults
    overall = driver.get("overall", driver.get("ovr", 80))
    pace = driver.get("pace", 80)
    racecraft = driver.get("racecraft", 80)
    awareness = driver.get("awareness", 80)
    experience = driver.get("experience", 80)
    # Weighted blend emphasizing pace and racecraft
    return (
        overall * 0.2 +
        pace * 0.4 +
        racecraft * 0.25 +
        awareness * 0.1 +
        experience * 0.05
    ) / 10.0  # scale down


def calculate_performance_score(driver, team, track, weather="dry", safety_car_chance=0.0, qualifying=None, recent_results=None):
    score = 0
    # Base driver ability component
    score += _base_driver_score(driver)
    # Team trait matches (reduced weight)
    for trait in track['traits']:
        if 'strengths' in team and trait.lower() in [s.lower() for s in team['strengths']]:
            score += 1
        if 'weaknesses' in team and trait.lower() in [w.lower() for w in team['weaknesses']]:
            score -= 1
    # Team tier (reduced weight)
    tier, team_luck_factor, tier_bonus = get_team_tier_and_luck(team['name'])
    score += tier_bonus
    # Driver trait matches (increased weight)
    for trait in track['traits']:
        if 'strengths' in driver and trait.lower() in [s.lower() for s in driver['strengths']]:
            score += 4.5
        if 'weaknesses' in driver and trait.lower() in [w.lower() for w in driver['weaknesses']]:
            score -= 5.5
    # Weather dynamics
    if weather == "wet":
        if "wet weather" in [s.lower() for s in driver.get("strengths", [])]:
            score += 3
        if "wet weather" in [w.lower() for w in driver.get("weaknesses", [])]:
            score -= 3
        # Increase luck/instability in wet
        awareness = driver.get('awareness', 80)
        instability = (100 - awareness) / 100
        luck_base = random.uniform(-1.5, 1.5) * 8 * instability
        luck = luck_base * team_luck_factor
        score += luck
    # Crash penalty and luck
    if "Crash prone" in track['traits']:
        awareness = driver.get('awareness', 80)
        instability = (100 - awareness) / 100
        luck_base = random.uniform(-1, 1) * 6 * instability
        luck = luck_base * team_luck_factor
        score += luck
        # Crash penalty (example: -5 * instability)
        score -= 5 * instability
    # Safety car dynamics
    if safety_car_chance > 0.3:
        awareness = driver.get('awareness', 80)
        score += (awareness - 80) * 0.1  # awareness bonus
        instability = (100 - awareness) / 100
        luck_base = random.uniform(-2, 2) * 10 * instability * safety_car_chance
        score += luck_base

    # Qualifying influence (lower position number is better)
    if qualifying and isinstance(qualifying, dict):
        qpos = qualifying.get(driver.get('name'))
        if isinstance(qpos, int) and 1 <= qpos <= 20:
            score += (21 - qpos) * 0.35

    # Recent momentum: simple +1 per recent top-5, -1 per DNF
    if recent_results and isinstance(recent_results, dict):
        results = recent_results.get(driver.get('name')) or []
        for r in results:
            ru = r.strip().upper()
            if ru.startswith('P'):
                try:
                    pos = int(ru[1:])
                    if pos <= 5:
                        score += 1
                except ValueError:
                    pass
            if 'DNF' in ru:
                score -= 1.5
    # Home GP slight bump
    home_gp = driver.get('home_gp')
    if home_gp and isinstance(track, dict) and home_gp.lower() in track.get('name', '').lower():
        score += 0.75
    return score

def predict_spa_for_all_drivers():
    base_path = os.path.dirname(__file__)
    drivers = load_json(os.path.join(base_path, 'data/drivers.json'))
    teams = load_json(os.path.join(base_path, 'data/teams.json'))
    tracks = load_json(os.path.join(base_path, 'data/tracks.json'))
    spa = next(t for t in tracks if t['code'] == 'BEL')
    results = []
    skipped_drivers = []
    for driver in drivers:
        team = get_team_info(driver['team'], teams)
        if not team:
            skipped_drivers.append(driver['name'] + ' (' + driver['team'] + ')')
            continue
        score = calculate_performance_score(driver, team, spa)
        results.append({"driver": driver['name'], "team": driver['team'], "score": round(score, 2)})
    results.sort(key=lambda x: x['score'], reverse=True)
    if skipped_drivers:
        print("Skipped drivers due to team matching issues:")
        for d in skipped_drivers:
            print("  -", d)
    # Ensure at least 10 drivers are included (add lowest scoring if needed)
    if len(results) < 10:
        all_scored = results.copy()
        for driver in drivers:
            if not any(r['driver'] == driver['name'] for r in results):
                all_scored.append({"driver": driver['name'], "team": driver['team'], "score": 0})
        all_scored.sort(key=lambda x: x['score'], reverse=True)
        results = all_scored[:10]
    return results

def predict_interlagos_for_all_drivers(weather="dry", safety_car_chance=0.0):
    base_path = os.path.dirname(__file__)
    drivers = load_json(os.path.join(base_path, 'data/drivers.json'))
    teams = load_json(os.path.join(base_path, 'data/teams.json'))
    tracks = load_json(os.path.join(base_path, 'data/tracks.json'))
    interlagos = next(t for t in tracks if t['code'] == 'SAP')
    results = []
    for driver in drivers:
        team = get_team_info(driver['team'], teams)
        if not team:
            continue
        score = calculate_performance_score(driver, team, interlagos, weather=weather, safety_car_chance=safety_car_chance)
        results.append({"driver": driver['name'], "team": driver['team'], "score": round(score, 2)})
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

def predict_monza_for_all_drivers(weather="dry", safety_car_chance=0.0):
    base_path = os.path.dirname(__file__)
    drivers = load_json(os.path.join(base_path, 'data/drivers.json'))
    teams = load_json(os.path.join(base_path, 'data/teams.json'))
    tracks = load_json(os.path.join(base_path, 'data/tracks.json'))
    monza = next(t for t in tracks if t['code'] == 'ITA')
    results = []
    for driver in drivers:
        team = get_team_info(driver['team'], teams)
        if not team:
            continue
        score = calculate_performance_score(driver, team, monza, weather=weather, safety_car_chance=safety_car_chance)
        results.append({"driver": driver['name'], "team": driver['team'], "score": round(score, 2)})
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

def predict_for_track(track_code_or_name, weather="dry", safety_car_chance=0.2):
    base_path = os.path.dirname(__file__)
    drivers = load_json(os.path.join(base_path, 'data/drivers.json'))
    teams = load_json(os.path.join(base_path, 'data/teams.json'))
    tracks = load_json(os.path.join(base_path, 'data/tracks.json'))
    # Try to find by code (case-insensitive)
    track = next((t for t in tracks if t['code'].lower() == track_code_or_name.lower()), None)
    if not track:
        # Try to find by name (case-insensitive, partial match)
        track = next((t for t in tracks if track_code_or_name.lower() in t['name'].lower()), None)
    if not track:
        raise ValueError(f"Track '{track_code_or_name}' not found.")
    results = []
    skipped_drivers = []
    for driver in drivers:
        team = get_team_info(driver['team'], teams)
        if not team:
            skipped_drivers.append(driver['name'] + ' (' + driver['team'] + ')')
            continue
        score = calculate_performance_score(driver, team, track, weather=weather, safety_car_chance=safety_car_chance)
        results.append({"driver": driver['name'], "team": driver['team'], "score": round(score, 2)})
    if skipped_drivers:
        print("Skipped drivers due to team matching issues:")
        for d in skipped_drivers:
            print("  -", d)
    # After all matched drivers, fill up to 10 with unmatched drivers (score 0)
    result_names = [r['driver'] for r in results]
    unmatched = [driver for driver in drivers if driver['name'] not in result_names]
    print(f"DEBUG: Drivers in results: {result_names}")
    print(f"DEBUG: Unmatched drivers: {[driver['name'] for driver in unmatched]}")
    while len(results) < 10 and unmatched:
        driver = unmatched.pop(0)
        results.append({"driver": driver['name'], "team": driver['team'], "score": 0})
    results.sort(key=lambda x: x['score'], reverse=True)
    print(f"DEBUG: Number of drivers in results: {len(results)}")
    return results

# For testing: print Spa predictions
if __name__ == "__main__":
    # Allow user to specify track code or name as argument
    if len(sys.argv) > 1:
        track_arg = sys.argv[1]
    else:
        track_arg = "ITA"  # Default to Monza
    predictions = predict_for_track(track_arg, weather="dry", safety_car_chance=0.2)
    points_table = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
    print(f"{'Pos':<4}{'Driver':<22}{'Team':<28}{'Score':<8}{'Points':<6}")
    print("-"*75)
    for i, p in enumerate(predictions):
        points = points_table[i] if i < len(points_table) else 0
        print(f"{i+1:<4}{p['driver']:<22}{p['team']:<28}{p['score']:<8}{points:<6}") 