#!/usr/bin/env python3
"""
19.GYM Telegram Coach Bot & Continuous Learning Engine
- Multi-Image Album Support (media_group_id buffering for front/back product scans and multi-plate meals).
- Nutrition Label OCR Scanner (reads Protein, Carbs, Fats, Calories from package back labels).
- Live Internet Food Search (OpenFoodFacts API integration) for continuous product learning.
- Stores learned products permanently in learned_products.json.
- Workout Media Intake & Progressive Overload PR Tracker.
- Long-Term Behavioral Memory (memory.json) with slip detection and habit streaks.
- 6:30 AM Workout Notification & 9:30 PM Evening Reflection.
- Built-in HTTP server for 100% FREE Render Web Service deployment.
"""

import os
import re
import sys
import time
import json
import threading
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FOOD_IMAGES_DIR = os.path.join(BASE_DIR, "food_images")
WORKOUT_MEDIA_DIR = os.path.join(BASE_DIR, "workout_media")
PROFILE_PATH = os.path.join(BASE_DIR, "profile.json")
LOGS_PATH = os.path.join(BASE_DIR, "daily_logs.json")
PRS_PATH = os.path.join(BASE_DIR, "exercise_prs.json")
MEMORY_PATH = os.path.join(BASE_DIR, "memory.json")
PRODUCTS_PATH = os.path.join(BASE_DIR, "learned_products.json")
ENV_PATH = os.path.join(BASE_DIR, ".env")

os.makedirs(FOOD_IMAGES_DIR, exist_ok=True)
os.makedirs(WORKOUT_MEDIA_DIR, exist_ok=True)

TESSERACT_BIN = "/opt/homebrew/bin/tesseract" if os.path.exists("/opt/homebrew/bin/tesseract") else "tesseract"

# ----------------- HTTP Health Server (For Free Render Hosting) -----------------
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"DJ Gym Coach Bot is LIVE and Healthy 24/7!\n")

    def log_message(self, format, *args):
        pass

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        print(f"🌐 Cloud Health Check Server running on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"Health server note: {e}")

# ----------------- Workout Schedule -----------------
WORKOUT_SCHEDULE = {
    0: {
        "name": "Push Day A (Chest, Front/Side Delts, Triceps)",
        "icon": "💥",
        "focus": "Upper Chest Fullness & 3D Delts",
        "exercises": [
            "1. Incline Dumbbell Press (30°): 3 sets x 8-10 reps (Deep stretch)",
            "2. Flat Barbell or Machine Press: 3 sets x 8-10 reps",
            "3. Standing DB Lateral Raises: 4 sets x 12-15 reps (Strict, no swing)",
            "4. Cable Chest Flyes: 3 sets x 12-15 reps (1s squeeze at peak)",
            "5. Cable Tricep Rope Pushdowns: 3 sets x 10-12 reps",
            "6. Overhead Tricep Extension (DB/Cable): 3 sets x 10-12 reps"
        ]
    },
    1: {
        "name": "Pull Day A (Lats, Upper Back, Rear Delts, Biceps)",
        "icon": "🦅",
        "focus": "Wide V-Taper (Makes waist look tighter)",
        "exercises": [
            "1. Lat Pulldown (Neutral/Wide Grip): 3 sets x 8-10 reps",
            "2. Chest-Supported DB or T-Bar Row: 3 sets x 8-10 reps",
            "3. Seated Cable Row (Close Grip): 3 sets x 10-12 reps",
            "4. Face Pulls (Rope to eye level): 4 sets x 15 reps",
            "5. Incline DB Bicep Curls: 3 sets x 10-12 reps (Full stretch)",
            "6. Hammer Curls (DB or Rope): 3 sets x 10-12 reps (Forearm/Arm thickness)"
        ]
    },
    2: {
        "name": "Legs & Core Day (Heavy Lower Body & Abs)",
        "icon": "🦵",
        "focus": "Quad Sweep, Posterior Chain & Deep Abdominal Bracing",
        "exercises": [
            "1. Barbell Back Squats or Hack Squats: 3 sets x 8-10 reps (3m rest)",
            "2. Romanian Deadlifts (RDLs): 3 sets x 8-10 reps (Hamstring stretch)",
            "3. Leg Press: 3 sets x 10-12 reps",
            "4. Lying or Seated Leg Curls: 3 sets x 12-15 reps",
            "5. Standing Calf Raises: 4 sets x 15-20 reps (2s pause at bottom)",
            "6. Hanging Knee/Leg Raises: 3 sets x 12-15 reps",
            "7. Cable Woodchoppers or Ab Crunches: 3 sets x 15 reps"
        ]
    },
    3: {
        "name": "Active Recovery & Mobility Day (REST)",
        "icon": "🧘",
        "focus": "CNS Restoration, Muscle Repair & NEAT Steps",
        "exercises": [
            "1. Target 8,000 - 10,000 Steps (Brisk walk outdoors or treadmill)",
            "2. 15 mins Full-Body Stretching & Foam Rolling",
            "3. Drink 3.5L+ water to flush metabolic fatigue",
            "Note: Muscles grow during rest! Do not lift today."
        ]
    },
    4: {
        "name": "Upper Body Hypertrophy (Chest, Back, Shoulders, Arms)",
        "icon": "⚔️",
        "focus": "Overall Upper Body Density & Arm Thickness",
        "exercises": [
            "1. DB Flat Bench Press: 3 sets x 8-10 reps",
            "2. Single-Arm DB Rows: 3 sets x 10 reps each side",
            "3. Seated DB Overhead Shoulder Press: 3 sets x 8-10 reps",
            "4. Cable Lateral Raises: 4 sets x 12-15 reps each",
            "5. Preacher or Cable Bicep Curls: 3 sets x 10-12 reps",
            "6. Dips (Assisted/BW) or Skull Crushers: 3 sets x 10-12 reps"
        ]
    },
    5: {
        "name": "Lower Body & Abs + LISS Cardio",
        "icon": "🔥",
        "focus": "Leg Hypertrophy, Core & Fat Oxidation",
        "exercises": [
            "1. Bulgarian Split Squats (DBs): 3 sets x 8-10 reps per leg",
            "2. Leg Extensions: 3 sets x 12-15 reps (Strict squeeze)",
            "3. Seated Hamstring Curls: 3 sets x 12-15 reps",
            "4. Standing Calf Raises: 4 sets x 15 reps",
            "5. Decline Weighted Crunches: 3 sets x 15 reps",
            "6. Plank Hold: 3 sets x 45-60 seconds",
            "7. Cardio: 15 mins Incline Treadmill Walk (10-12% incline, speed 4.0-4.5 km/h)"
        ]
    },
    6: {
        "name": "Complete Rest Day",
        "icon": "💤",
        "focus": "Full Rejuvenation & Weekly Reset",
        "exercises": [
            "1. Zero lifting. Sleep 8+ hours.",
            "2. Keep protein at 145g (Muscle synthesis continues on rest days).",
            "3. Weekly weigh-in & photo progress check."
        ]
    }
}

# ----------------- Persistence Helpers -----------------
def load_env():
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip("'\"")
    for k in ["TELEGRAM_BOT_TOKEN", "PORT"]:
        if k in os.environ:
            env[k] = os.environ[k]
    return env

def load_profile():
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r") as f:
            return json.load(f)
    return {
        "targets": {
            "daily_calories": 2050,
            "protein_g": 145,
            "carbohydrates_g": 210,
            "fats_g": 52,
            "water_liters": 3.5,
            "daily_steps": 9000
        }
    }

def save_profile(profile):
    with open(PROFILE_PATH, "w") as f:
        json.dump(profile, f, indent=2)

def load_logs():
    if os.path.exists(LOGS_PATH):
        with open(LOGS_PATH, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def save_logs(logs):
    with open(LOGS_PATH, "w") as f:
        json.dump(logs, f, indent=2)

def load_prs():
    if os.path.exists(PRS_PATH):
        with open(PRS_PATH, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def save_prs(prs):
    with open(PRS_PATH, "w") as f:
        json.dump(prs, f, indent=2)

def load_memory():
    if os.path.exists(MEMORY_PATH):
        with open(MEMORY_PATH, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {
        "user_name": "Dajain",
        "streaks": {"clean_diet_days": 1, "workout_adherence_days": 1, "water_target_days": 0, "zero_sweets_days": 1},
        "behavioral_patterns": [],
        "timeline_learnings": []
    }

def save_memory(mem):
    with open(MEMORY_PATH, "w") as f:
        json.dump(mem, f, indent=2)

def load_products():
    if os.path.exists(PRODUCTS_PATH):
        with open(PRODUCTS_PATH, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def save_products(prods):
    with open(PRODUCTS_PATH, "w") as f:
        json.dump(prods, f, indent=2)

def get_today_entry(logs):
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in logs:
        logs[today] = {
            "date": today,
            "weight_kg": None,
            "steps": 0,
            "water_l": 0.0,
            "workout_done": "",
            "workout_sets": [],
            "meals": [],
            "totals": {
                "calories": 0,
                "protein_g": 0.0,
                "carbs_g": 0.0,
                "fats_g": 0.0
            }
        }
    if "workout_sets" not in logs[today]:
        logs[today]["workout_sets"] = []
    return logs[today], today

# ----------------- OCR & Continuous Learning Engine -----------------
def run_ocr(image_path):
    """Extracts text from image using tesseract"""
    try:
        res = subprocess.run([TESSERACT_BIN, image_path, "stdout"], capture_output=True, text=True, timeout=10)
        return res.stdout
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""

def parse_nutrition_label(ocr_text):
    """Detects and parses nutrition facts from back label OCR"""
    text = ocr_text.lower()
    is_nutrition_label = any(k in text for k in ["nutritional information", "nutrition facts", "per 100g", "per serve", "energy (kcal)", "protein (g)"])
    if not is_nutrition_label:
        return None

    data = {"calories": 0, "protein_g": 0.0, "carbs_g": 0.0, "fats_g": 0.0, "serving_size": "1 serving"}

    # Extract Protein
    p_match = re.search(r"protein\s*(?:\(g\))?[\s:]*(\d+(?:\.\d+)?)", text)
    if p_match:
        data["protein_g"] = float(p_match.group(1))

    # Extract Energy / Calories
    cal_match = re.search(r"(?:energy|calories)\s*(?:\(kcal\))?[\s:]*(\d+(?:\.\d+)?)", text)
    if cal_match:
        data["calories"] = round(float(cal_match.group(1)))

    # Extract Fat
    f_match = re.search(r"(?:total fat|fat)\s*(?:\(g\))?[\s:]*(\d+(?:\.\d+)?)", text)
    if f_match:
        data["fats_g"] = float(f_match.group(1))

    # Extract Carbs
    c_match = re.search(r"(?:total carbohydrates|carbohydrates|carbs)\s*(?:\(g\))?[\s:]*(\d+(?:\.\d+)?)", text)
    if c_match:
        data["carbs_g"] = float(c_match.group(1))

    # Extract serving size
    serve_match = re.search(r"per\s*(\d+\s*(?:g|ml|scoop))", text)
    if serve_match:
        data["serving_size"] = serve_match.group(1)

    return data

def search_openfoodfacts(query):
    """Live internet search for food products and macros"""
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={query}&search_simple=1&action=process&json=1"
    try:
        r = requests.get(url, headers={"User-Agent": "DJGymCoachBot/2.0"}, timeout=6).json()
        products = r.get("products", [])
        if products:
            p = products[0]
            nutr = p.get("nutriments", {})
            cal = nutr.get("energy-kcal_100g", nutr.get("energy-kcal_serving", 0))
            prot = nutr.get("proteins_100g", nutr.get("proteins_serving", 0))
            carbs = nutr.get("carbohydrates_100g", nutr.get("carbohydrates_serving", 0))
            fat = nutr.get("fat_100g", nutr.get("fat_serving", 0))

            return {
                "name": p.get("product_name", query),
                "brand": p.get("brands", "Verified Brand"),
                "serving_size": p.get("serving_size", "100g"),
                "calories": round(float(cal)),
                "protein_g": round(float(prot), 1),
                "carbs_g": round(float(carbs), 1),
                "fats_g": round(float(fat), 1)
            }
    except Exception as e:
        print(f"Internet search error: {e}")
    return None

# ----------------- Macro Parsing -----------------
NUTRITION_DB = {
    "low fat paneer": {"unit": "100g", "cal": 150, "p": 25.0, "c": 3.0, "f": 4.0},
    "paneer": {"unit": "100g", "cal": 265, "p": 18.0, "c": 3.5, "f": 20.8},
    "whey": {"unit": "1 scoop", "cal": 120, "p": 24.0, "c": 3.0, "f": 1.5},
    "soya chunks": {"unit": "50g raw", "cal": 172, "p": 26.0, "c": 16.5, "f": 0.5},
    "curd": {"unit": "100g", "cal": 65, "p": 3.5, "c": 4.5, "f": 3.5},
    "roti": {"unit": "1 medium", "cal": 85, "p": 2.8, "c": 16.0, "f": 1.0},
    "chilla": {"unit": "1 piece", "cal": 125, "p": 7.0, "c": 15.0, "f": 3.5},
    "rice": {"unit": "1 cup", "cal": 195, "p": 4.0, "c": 44.0, "f": 0.5},
    "oats": {"unit": "50g", "cal": 190, "p": 6.5, "c": 33.0, "f": 3.5},
    "dal": {"unit": "1 bowl", "cal": 135, "p": 8.0, "c": 20.0, "f": 2.5},
    "sabji": {"unit": "1 bowl", "cal": 110, "p": 2.5, "c": 12.0, "f": 5.5},
    "salad": {"unit": "1 plate", "cal": 35, "p": 1.5, "c": 7.0, "f": 0.2},
    "banana": {"unit": "1 medium", "cal": 105, "p": 1.2, "c": 27.0, "f": 0.3},
    "apple": {"unit": "1 medium", "cal": 95, "p": 0.5, "c": 25.0, "f": 0.3},
    "peanut butter": {"unit": "1 tbsp (16g)", "cal": 102, "p": 4.8, "c": 2.9, "f": 7.8},
    "almonds": {"unit": "10 pcs", "cal": 70, "p": 2.5, "c": 2.5, "f": 6.0},
    "walnuts": {"unit": "2 pcs", "cal": 65, "p": 1.5, "c": 1.4, "f": 6.5},
}

def parse_meal_text(text):
    text_lower = text.lower()
    total_cal = 0
    total_p = 0.0
    total_c = 0.0
    total_f = 0.0
    found_items = []

    # Check in learned_products.json first!
    learned = load_products()
    for prod_name, pdata in learned.items():
        if prod_name in text_lower or (pdata.get("brand", "").lower() in text_lower and any(w in text_lower for w in prod_name.split())):
            total_cal += pdata["calories"]
            total_p += pdata["protein_g"]
            total_c += pdata["carbs_g"]
            total_f += pdata["fats_g"]
            found_items.append(f"{prod_name.title()} ({pdata.get('serving_size', '1 serving')})")
            break

    # Check for paneer
    paneer_match = re.search(r"(\d+)\s*(?:g|gms|gram|grams)?\s*(low\s*fat\s*paneer|paneer)", text_lower)
    if paneer_match:
        qty = float(paneer_match.group(1))
        is_low_fat = "low" in paneer_match.group(2)
        key = "low fat paneer" if is_low_fat else "paneer"
        item = NUTRITION_DB[key]
        ratio = qty / 100.0
        total_cal += item["cal"] * ratio
        total_p += item["p"] * ratio
        total_c += item["c"] * ratio
        total_f += item["f"] * ratio
        found_items.append(f"{qty:.0f}g {key.title()}")
    elif "low fat paneer" in text_lower:
        item = NUTRITION_DB["low fat paneer"]
        total_cal += item["cal"] * 1.5
        total_p += item["p"] * 1.5
        total_c += item["c"] * 1.5
        total_f += item["f"] * 1.5
        found_items.append("150g Low Fat Paneer")
    elif "paneer" in text_lower and not any("paneer" in f.lower() for f in found_items):
        item = NUTRITION_DB["paneer"]
        total_cal += item["cal"]
        total_p += item["p"]
        total_c += item["c"]
        total_f += item["f"]
        found_items.append("100g Paneer")

    # Check for rotis
    roti_match = re.search(r"(\d+)\s*(?:roti|rotis|phulka|phulkas|chapati|chapatis)", text_lower)
    if roti_match:
        count = float(roti_match.group(1))
        item = NUTRITION_DB["roti"]
        total_cal += item["cal"] * count
        total_p += item["p"] * count
        total_c += item["c"] * count
        total_f += item["f"] * count
        found_items.append(f"{int(count)} Rotis")
    elif any(w in text_lower for w in ["roti", "phulka", "chapati"]):
        item = NUTRITION_DB["roti"]
        total_cal += item["cal"] * 2
        total_p += item["p"] * 2
        total_c += item["c"] * 2
        total_f += item["f"] * 2
        found_items.append("2 Rotis")

    if "dal" in text_lower:
        item = NUTRITION_DB["dal"]
        total_cal += item["cal"]
        total_p += item["p"]
        total_c += item["c"]
        total_f += item["f"]
        found_items.append("1 Bowl Dal")

    if any(w in text_lower for w in ["sabji", "subji", "bhindi", "lauki", "turai", "capsicum", "cabbage"]):
        item = NUTRITION_DB["sabji"]
        total_cal += item["cal"]
        total_p += item["p"]
        total_c += item["c"]
        total_f += item["f"]
        found_items.append("1 Bowl Sabji")

    if "salad" in text_lower:
        item = NUTRITION_DB["salad"]
        total_cal += item["cal"]
        total_p += item["p"]
        total_c += item["c"]
        total_f += item["f"]
        found_items.append("Salad")

    if any(w in text_lower for w in ["whey", "protein shake", "gold standard"]) and not any("whey" in f.lower() for f in found_items):
        item = NUTRITION_DB["whey"]
        total_cal += item["cal"]
        total_p += item["p"]
        total_c += item["c"]
        total_f += item["f"]
        found_items.append("1 Scoop Whey Protein")

    if not found_items:
        # Check internet search
        online = search_openfoodfacts(text)
        if online:
            total_cal = online["calories"]
            total_p = online["protein_g"]
            total_c = online["carbs_g"]
            total_f = online["fats_g"]
            found_items.append(f"{online['name']} ({online.get('serving_size', '100g')})")
            # Save into memory
            learned[online["name"].lower()] = online
            save_products(learned)
        else:
            total_cal = 450
            total_p = 25.0
            total_c = 50.0
            total_f = 12.0
            found_items.append(text[:30])

    return {
        "description": ", ".join(found_items),
        "calories": round(total_cal),
        "protein_g": round(total_p, 1),
        "carbs_g": round(total_c, 1),
        "fats_g": round(total_f, 1)
    }

def analyze_behavior_and_habits(text, meal_data=None):
    text_lower = text.lower()
    mem = load_memory()
    feedback_notes = []

    sweet_words = ["sweet", "mithai", "chocolate", "ice cream", "sugar", "gulab jamun", "halwa", "pastry", "cake"]
    found_sweet = any(w in text_lower for w in sweet_words)
    if found_sweet:
        mem["streaks"]["zero_sweets_days"] = 0
        mem["timeline_learnings"].append({
            "timestamp": datetime.now().isoformat(),
            "type": "slip_sugar",
            "learning": f"Sweet/sugar detected in meal: '{text[:40]}'. Reminded that sugar triggers love-handle fat storage."
        })
        feedback_notes.append("⚠️ *Habit Slip Alert:* Sweets detected! Remember our root analysis: sugar triggers acute insulin spikes that store straight on your lower flanks. Let's reset and keep dinner zero-sugar.")
    else:
        mem["streaks"]["zero_sweets_days"] = mem["streaks"].get("zero_sweets_days", 0) + 1

    if "peanut butter" in text_lower and datetime.now().hour < 9:
        feedback_notes.append("⚠️ *Memory Reminder:* You ate Peanut Butter in the morning window. Remember our rule: PB is 70% fat and blunts your gym pumps. Move it to 4:30 PM snack!")

    if meal_data and meal_data.get("protein_g", 0) >= 30:
        feedback_notes.append("🎯 *Coach Win:* 30g+ high-protein meal logged! Excellent execution on breaking your old habit of underdosing protein.")

    save_memory(mem)
    return feedback_notes

def parse_workout_text(text):
    text_lower = text.lower()
    wt_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilo|kilos)", text_lower)
    weight_kg = float(wt_match.group(1)) if wt_match else None

    reps_match = re.search(r"(\d+)\s*(?:reps|rep)", text_lower)
    reps = int(reps_match.group(1)) if reps_match else None

    sets_match = re.search(r"(\d+)\s*(?:sets|set)", text_lower)
    sets = int(sets_match.group(1)) if sets_match else 1

    exercise_name = "Gym Exercise"
    exercises = [
        "incline dumbbell press", "incline db press", "flat bench press", "chest press",
        "lateral raise", "cable fly", "tricep pushdown", "overhead tricep", "skull crusher",
        "lat pulldown", "barbell row", "t-bar row", "cable row", "face pull",
        "bicep curl", "hammer curl", "preacher curl",
        "squat", "hack squat", "leg press", "romanian deadlift", "rdl", "leg curl", "leg extension", "calf raise",
        "bulgarian split squat", "hanging leg raise", "ab crunch", "plank"
    ]
    for ex in exercises:
        if ex in text_lower:
            exercise_name = ex.title()
            break
    if exercise_name == "Gym Exercise" and text.strip():
        clean = re.sub(r"\d+\s*(?:kg|kgs|reps|rep|sets|set)", "", text, flags=re.I).strip()
        if clean:
            exercise_name = clean[:35].title()

    return {
        "exercise": exercise_name,
        "weight_kg": weight_kg,
        "reps": reps,
        "sets": sets
    }

def is_workout_message(text, is_video=False):
    if is_video:
        return True
    text_lower = text.lower()
    workout_keywords = [
        "kg", "reps", "rep", "sets", "set", "squat", "bench", "press", "curl",
        "pulldown", "row", "deadlift", "rdl", "lateral", "extension", "workout", "form check",
        "exercise", "dumbbell", "barbell", "hack squat", "flyes", "calves"
    ]
    return any(w in text_lower for w in workout_keywords)

def format_workout_message(day_offset=0):
    target_date = datetime.fromtimestamp(time.time() + (day_offset * 86400))
    weekday_idx = target_date.weekday()
    day_name = target_date.strftime("%A, %d %B %Y")
    data = WORKOUT_SCHEDULE.get(weekday_idx, WORKOUT_SCHEDULE[6])

    exercises_text = "\n".join(data["exercises"])
    is_today = (day_offset == 0)
    prefix = "🌅 *TODAY'S WORKOUT PROTOCOL (6:30 AM)*" if is_today else f"📅 *WORKOUT PREVIEW FOR TOMORROW ({day_name})*"

    msg = (
        f"{prefix}\n\n"
        f"🗓 *{day_name}*\n"
        f"{data['icon']} *{data['name']}*\n"
        f"🎯 *Focus:* {data['focus']}\n\n"
        f"🏋️‍♂️ *Exercise Breakdown:*\n{exercises_text}\n\n"
        f"⚡ *Pre-Workout Fuel (6:30 AM - 6:45 AM):*\n"
        f"• 1 Medium Ripe Banana\n"
        f"• 1 Sachet (2g) Nescafe Black Coffee in 150ml water\n"
        f"• 300ml water + 1 pinch Himalayan Pink Rock Salt (For insane pump!)\n"
        f"• ❌ *STRICTLY NO PEANUT BUTTER BEFORE LIFTING.*\n\n"
        f"🔥 Target gym window: 7:00 AM – 8:15 AM. Let's conquer it!"
    )
    return msg

def format_evening_review(entry, targets, mem):
    tot = entry["totals"]
    p_pct = (tot["protein_g"] / targets["protein_g"]) * 100
    cal_diff = tot["calories"] - targets["daily_calories"]

    verdict = "🔥 EXCELLENT EXECUTION" if p_pct >= 90 and abs(cal_diff) <= 150 else "⚠️ NEEDS COURSE CORRECTION"

    review_msg = (
        f"🌙 *DAILY COACH REFLECTION & HABIT AUDIT (9:30 PM)*\n\n"
        f"Verdict: *{verdict}*\n\n"
        f"📊 *Scorecard:*\n"
        f"• Protein Hit: `{tot['protein_g']}g / {targets['protein_g']}g` ({p_pct:.0f}%)\n"
        f"• Calories: `{tot['calories']} / {targets['daily_calories']} kcal`\n"
        f"• Steps: `{entry['steps']} / {targets['daily_steps']}`\n"
        f"• Water: `{entry['water_l']}L / {targets['water_liters']}L`\n\n"
        f"🧠 *Learnings & Streaks:*\n"
        f"• Clean Diet Streak: `{mem['streaks'].get('clean_diet_days', 1)} days`\n"
        f"• Zero Sugar Streak: `{mem['streaks'].get('zero_sweets_days', 1)} days`\n\n"
        f"Sleep 8 hours tonight to allow muscle protein synthesis to rebuild your fibers. Tomorrow 6:30 AM routine is ready!"
    )
    return review_msg

# ----------------- Telegram Bot Class with Media Group Buffering -----------------
class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self.last_morning_date = None
        self.last_evening_date = None
        self.media_groups = {}  # group_id -> {"timer": ..., "messages": [...]}
        self.group_lock = threading.Lock()

    def send_message(self, chat_id, text, parse_mode="Markdown"):
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        try:
            r = requests.post(url, json=payload, timeout=10)
            return r.json()
        except Exception as e:
            print(f"Error sending message: {e}")
            return None

    def download_file(self, file_id, dest_path):
        url = f"{self.base_url}/getFile?file_id={file_id}"
        r = requests.get(url, timeout=10).json()
        if r.get("ok"):
            file_path = r["result"]["file_path"]
            download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
            img_data = requests.get(download_url, timeout=60).content
            with open(dest_path, "wb") as f:
                f.write(img_data)
            return True
        return False

    def schedule_checker(self):
        print("⏰ Proactive scheduler thread active (6:30 AM & 9:30 PM)...")
        while True:
            try:
                now = datetime.now()
                today_str = now.strftime("%Y-%m-%d")
                profile = load_profile()
                chat_id = profile.get("telegram_chat_id")

                if now.hour == 6 and now.minute in [30, 31]:
                    if self.last_morning_date != today_str and chat_id:
                        msg = format_workout_message(day_offset=0)
                        self.send_message(chat_id, msg)
                        self.last_morning_date = today_str

                if now.hour == 21 and now.minute in [30, 31]:
                    if self.last_evening_date != today_str and chat_id:
                        logs = load_logs()
                        entry, _ = get_today_entry(logs)
                        mem = load_memory()
                        msg = format_evening_review(entry, profile["targets"], mem)
                        self.send_message(chat_id, msg)
                        self.last_evening_date = today_str
            except Exception as e:
                print(f"Error in scheduler: {e}")
            time.sleep(30)

    def process_media_group(self, group_id):
        """Processes buffered multi-image albums (front + back product scan)"""
        with self.group_lock:
            group_data = self.media_groups.pop(group_id, None)
        if not group_data:
            return

        messages = group_data["messages"]
        chat_id = messages[0]["chat"]["id"]
        caption = next((m.get("caption") for m in messages if m.get("caption")), "")

        print(f"📦 Processing Multi-Image Album ({len(messages)} photos) for chat {chat_id}...")

        downloaded_paths = []
        for i, m in enumerate(messages):
            photos = m.get("photo", [])
            if photos:
                best = photos[-1]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest = os.path.join(FOOD_IMAGES_DIR, f"album_{group_id}_{i}_{timestamp}.jpg")
                if self.download_file(best["file_id"], dest):
                    downloaded_paths.append(dest)

        # Run OCR on all images to detect nutrition label and product details
        ocr_texts = [run_ocr(p) for p in downloaded_paths]
        nutrition_found = None
        for txt in ocr_texts:
            parsed_label = parse_nutrition_label(txt)
            if parsed_label and parsed_label.get("protein_g", 0) > 0:
                nutrition_found = parsed_label
                break

        profile = load_profile()
        targets = profile["targets"]
        logs = load_logs()
        entry, today = get_today_entry(logs)
        learned = load_products()

        if nutrition_found:
            # Successfully read nutrition label!
            product_name = caption if caption else "Scanned Protein/Fitness Product"
            learned[product_name.lower()] = {
                "name": product_name,
                "serving_size": nutrition_found["serving_size"],
                "calories": nutrition_found["calories"],
                "protein_g": nutrition_found["protein_g"],
                "carbs_g": nutrition_found["carbs_g"],
                "fats_g": nutrition_found["fats_g"],
                "learned_from": "front_back_label_scan"
            }
            save_products(learned)

            # Log 1 single serving!
            entry["meals"].append({
                "time": datetime.now().strftime("%H:%M"),
                "name": f"{product_name} ({nutrition_found['serving_size']})",
                "image": os.path.basename(downloaded_paths[0]) if downloaded_paths else None,
                "calories": nutrition_found["calories"],
                "protein_g": nutrition_found["protein_g"],
                "carbs_g": nutrition_found["carbs_g"],
                "fats_g": nutrition_found["fats_g"]
            })

            entry["totals"]["calories"] = sum(m["calories"] for m in entry["meals"])
            entry["totals"]["protein_g"] = round(sum(m["protein_g"] for m in entry["meals"]), 1)
            entry["totals"]["carbs_g"] = round(sum(m["carbs_g"] for m in entry["meals"]), 1)
            entry["totals"]["fats_g"] = round(sum(m["fats_g"] for m in entry["meals"]), 1)
            save_logs(logs)

            tot = entry["totals"]
            rem_p = max(0, targets["protein_g"] - tot["protein_g"])
            rem_cal = max(0, targets["daily_calories"] - tot["calories"])

            feedback = (
                f"🧠 *New Product Learned & Logged as 1 Item!* (📸 {len(downloaded_paths)} Photos Analyzed)\n\n"
                f"📦 *Product:* {product_name}\n"
                f"📋 *Extracted Label Facts ({nutrition_found['serving_size']}):*\n"
                f"• Calories: `{nutrition_found['calories']} kcal`\n"
                f"• Protein: `{nutrition_found['protein_g']}g`\n"
                f"• Carbs: `{nutrition_found['carbs_g']}g`\n"
                f"• Fats: `{nutrition_found['fats_g']}g`\n\n"
                f"✅ *Saved to permanent memory!* I will recognize this product automatically in the future.\n\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 *Today's Total ({today}):*\n"
                f"• Calories: `{tot['calories']} / {targets['daily_calories']} kcal` (Left: `{rem_cal} kcal`)\n"
                f"• Protein: `{tot['protein_g']}g / {targets['protein_g']}g` (Left: `{rem_p:.1f}g`)"
            )
            self.send_message(chat_id, feedback)
        else:
            # Multi-dish meal photos (e.g. plate + salad + bowl)
            meal_input = caption or "Combined Meal Plates"
            parsed = parse_meal_text(meal_input)
            entry["meals"].append({
                "time": datetime.now().strftime("%H:%M"),
                "name": parsed["description"],
                "image": os.path.basename(downloaded_paths[0]) if downloaded_paths else None,
                "calories": parsed["calories"],
                "protein_g": parsed["protein_g"],
                "carbs_g": parsed["carbs_g"],
                "fats_g": parsed["fats_g"]
            })
            entry["totals"]["calories"] = sum(m["calories"] for m in entry["meals"])
            entry["totals"]["protein_g"] = round(sum(m["protein_g"] for m in entry["meals"]), 1)
            entry["totals"]["carbs_g"] = round(sum(m["carbs_g"] for m in entry["meals"]), 1)
            entry["totals"]["fats_g"] = round(sum(m["fats_g"] for m in entry["meals"]), 1)
            save_logs(logs)

            tot = entry["totals"]
            rem_p = max(0, targets["protein_g"] - tot["protein_g"])
            rem_cal = max(0, targets["daily_calories"] - tot["calories"])

            feedback = (
                f"✅ *Multi-Photo Meal Logged as 1 Combined Item!* (📸 {len(downloaded_paths)} Photos)\n\n"
                f"🍽 *Items:* {parsed['description']}\n"
                f"🔥 *Calories:* `{parsed['calories']} kcal`\n"
                f"💪 *Protein:* `{parsed['protein_g']}g`\n"
                f"🍞 *Carbs:* `{parsed['carbs_g']}g`\n"
                f"🥑 *Fats:* `{parsed['fats_g']}g`\n\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 *Today's Total ({today}):*\n"
                f"• Calories: `{tot['calories']} / {targets['daily_calories']} kcal` (Left: `{rem_cal} kcal`)\n"
                f"• Protein: `{tot['protein_g']}g / {targets['protein_g']}g` (Left: `{rem_p:.1f}g`)"
            )
            self.send_message(chat_id, feedback)

    def handle_update(self, update):
        message = update.get("message")
        if not message:
            return

        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        caption = message.get("caption", "")
        photos = message.get("photo")
        video = message.get("video") or message.get("video_note")
        media_group_id = message.get("media_group_id")

        # 1. Handle Multi-Image Album / Media Group Buffering
        if media_group_id and photos:
            with self.group_lock:
                if media_group_id not in self.media_groups:
                    self.media_groups[media_group_id] = {
                        "messages": [message],
                        "timer": threading.Timer(1.5, self.process_media_group, args=[media_group_id])
                    }
                    self.media_groups[media_group_id]["timer"].start()
                else:
                    self.media_groups[media_group_id]["messages"].append(message)
            return

        profile = load_profile()
        if profile.get("telegram_chat_id") != chat_id:
            profile["telegram_chat_id"] = chat_id
            save_profile(profile)

        targets = profile["targets"]
        logs = load_logs()
        entry, today = get_today_entry(logs)
        prs = load_prs()
        mem = load_memory()

        # Commands
        if text.startswith("/start"):
            welcome = (
                f"🔥 *Namaste Darshan! Your 19.GYM AI Coach & Learning Engine is ONLINE* 🔥\n\n"
                f"I continuously learn your personal habits, scan product labels, research new foods online, and engineer you into the aesthetic physique in Image 4.\n\n"
                f"🧠 *Smart Features Active:*\n"
                f"• Multi-Image Support: Send front & back of protein powders or multiple plates together!\n"
                f"• Nutrition Facts Label Scanner (OCR)\n"
                f"• Live Internet Food Search\n"
                f"• Continuous Behavioral Memory (`memory.json`)\n"
                f"• Exercise Video & Progressive Overload Tracking\n"
                f"• 6:30 AM Workout Notification & 9:30 PM Reflection\n\n"
                f"Commands:\n"
                f"• `/products` - View all products I have learned so far\n"
                f"• `/habits` - View your behavioral streaks and learnings\n"
                f"• `/prs` - View your personal best weights across all lifts\n"
                f"• `/workout` - Today's complete routine\n"
                f"• `/status` - Today's full macros, calories & logged sets\n"
                f"• `/water 0.5` | `/steps 8000` | `/weight 67`"
            )
            self.send_message(chat_id, welcome)
            return

        if text.startswith("/products"):
            learned = load_products()
            if not learned:
                self.send_message(chat_id, "📦 No custom products learned yet. Send front and back photos of any food item to teach me!")
            else:
                lines = [f"• *{p.title()}:* `{d['protein_g']}g P` | `{d['calories']} kcal` ({d.get('serving_size', '1 serving')})" for p, d in learned.items()]
                self.send_message(chat_id, "🧠 *Learned Product Knowledge Base:*\n\n" + "\n".join(lines))
            return

        if text.startswith("/habits") or text.startswith("/memory"):
            patterns = mem.get("behavioral_patterns", [])
            pattern_lines = [f"• *{p['id'].replace('_', ' ').title()}:* {p['coach_rule']}" for p in patterns[:5]]
            streaks = mem.get("streaks", {})
            h_msg = (
                f"🧠 *AI Coach Long-Term Memory for Darshan*\n\n"
                f"🔥 *Current Streaks:*\n"
                f"• Clean Diet: `{streaks.get('clean_diet_days', 1)} days`\n"
                f"• Zero Sugar/Sweets: `{streaks.get('zero_sweets_days', 1)} days`\n"
                f"• Workout Adherence: `{streaks.get('workout_adherence_days', 1)} days`\n\n"
                f"📌 *Key Monitored Patterns:*\n" + "\n".join(pattern_lines) + "\n\n"
                f"💡 *Learnings Count:* `{len(mem.get('timeline_learnings', []))} insights stored`."
            )
            self.send_message(chat_id, h_msg)
            return

        if text.startswith("/reflect"):
            msg = format_evening_review(entry, targets, mem)
            self.send_message(chat_id, msg)
            return

        if text.startswith("/workout"):
            if "tomorrow" in text.lower():
                msg = format_workout_message(day_offset=1)
            else:
                msg = format_workout_message(day_offset=0)
            self.send_message(chat_id, msg)
            return

        if text.startswith("/prs"):
            if not prs:
                self.send_message(chat_id, "📈 No exercise weights recorded yet! Record a set or send a video (e.g. 'Incline DB Press 22.5kg 10 reps').")
            else:
                pr_lines = [f"• *{ex}:* `{d['weight_kg']} kg` x `{d.get('reps', '?')} reps` (on {d.get('date', 'recent')})" for ex, d in prs.items()]
                self.send_message(chat_id, "🏆 *Your Current Progressive Overload PRs:*\n\n" + "\n".join(pr_lines))
            return

        if text.startswith("/status") or text.startswith("/today"):
            tot = entry["totals"]
            rem_p = max(0, targets["protein_g"] - tot["protein_g"])
            rem_cal = max(0, targets["daily_calories"] - tot["calories"])
            sets_count = len(entry.get("workout_sets", []))
            stat_msg = (
                f"📊 *Today's Fitness Log ({today})*\n\n"
                f"🔥 *Calories:* `{tot['calories']} / {targets['daily_calories']} kcal` (Left: `{rem_cal} kcal`)\n"
                f"💪 *Protein:* `{tot['protein_g']}g / {targets['protein_g']}g` (Left: `{rem_p:.1f}g`)\n"
                f"🍞 *Carbs:* `{tot['carbs_g']}g / {targets['carbohydrates_g']}g`\n"
                f"🥑 *Fats:* `{tot['fats_g']}g / {targets['fats_g']}g`\n\n"
                f"🏋️ *Workout Sets Logged:* `{sets_count} sets recorded`\n"
                f"🚶‍♂️ *Steps:* `{entry['steps']} / {targets['daily_steps']}`\n"
                f"💧 *Water:* `{entry['water_l']}L / {targets['water_liters']}L`\n\n"
                f"*Meals Today:*\n" + ("\n".join([f"• {m['name']} (~{m['protein_g']}g P, {m['calories']} kcal)" for m in entry["meals"]]) if entry["meals"] else "No meals logged yet.")
            )
            self.send_message(chat_id, stat_msg)
            return

        if text.startswith("/water"):
            parts = text.split()
            if len(parts) > 1:
                try:
                    val = float(parts[1])
                    entry["water_l"] = round(entry["water_l"] + val, 2)
                    save_logs(logs)
                    self.send_message(chat_id, f"💧 Logged +{val}L water! Total today: `{entry['water_l']}L` / {targets['water_liters']}L")
                    return
                except ValueError:
                    pass

        if text.startswith("/steps"):
            parts = text.split()
            if len(parts) > 1:
                try:
                    val = int(parts[1])
                    entry["steps"] = val
                    save_logs(logs)
                    desk_warning = ""
                    if val < 4000 and datetime.now().hour >= 15:
                        desk_warning = "\n⚠️ *Desk Job Trap:* It's past 3 PM and you're under 4,000 steps! Take a 10-minute standing walk between meetings."
                    self.send_message(chat_id, f"🚶‍♂️ Updated steps: `{entry['steps']}` / {targets['daily_steps']}{desk_warning}")
                    return
                except ValueError:
                    pass

        if text.startswith("/weight"):
            parts = text.split()
            if len(parts) > 1:
                try:
                    val = float(parts[1])
                    entry["weight_kg"] = val
                    save_logs(logs)
                    self.send_message(chat_id, f"⚖️ Weight logged: `{val} kg`!")
                    return
                except ValueError:
                    pass

        # Handle Workout Media vs Food Media
        incoming_caption = caption or text
        is_workout = is_workout_message(incoming_caption, is_video=bool(video))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. WORKOUT VIDEO / EXERCISE SET LOGGING
        if is_workout and (video or photos or ("kg" in incoming_caption.lower() or "reps" in incoming_caption.lower())):
            saved_media = None
            media_type = "text"

            if video:
                file_id = video["file_id"]
                filename = f"workout_{timestamp}.mp4"
                dest = os.path.join(WORKOUT_MEDIA_DIR, filename)
                if self.download_file(file_id, dest):
                    saved_media = filename
                    media_type = "video"
            elif photos:
                best_photo = photos[-1]
                file_id = best_photo["file_id"]
                filename = f"workout_{timestamp}.jpg"
                dest = os.path.join(WORKOUT_MEDIA_DIR, filename)
                if self.download_file(file_id, dest):
                    saved_media = filename
                    media_type = "photo"

            parsed_w = parse_workout_text(incoming_caption)
            ex_name = parsed_w["exercise"]
            wt = parsed_w["weight_kg"]
            reps = parsed_w["reps"]
            sets = parsed_w["sets"]

            prev_pr = prs.get(ex_name)
            pr_note = ""
            if wt is not None:
                if not prev_pr:
                    prs[ex_name] = {"weight_kg": wt, "reps": reps or 10, "date": today}
                    pr_note = "⭐ *Baseline Established:* First time recording this lift!"
                elif wt > prev_pr["weight_kg"]:
                    diff = wt - prev_pr["weight_kg"]
                    prs[ex_name] = {"weight_kg": wt, "reps": reps or prev_pr.get("reps", 10), "date": today}
                    pr_note = f"🔥 *NEW PR ALERT!* You increased weight by `+{diff} kg`! That is how muscle hypertrophy happens!"
                else:
                    pr_note = f"📌 Previous best: `{prev_pr['weight_kg']} kg` x `{prev_pr.get('reps', '?')} reps`."
                save_prs(prs)

            entry["workout_sets"].append({
                "time": datetime.now().strftime("%H:%M"),
                "exercise": ex_name,
                "weight_kg": wt,
                "reps": reps,
                "sets": sets,
                "media": saved_media,
                "media_type": media_type
            })
            save_logs(logs)

            media_str = " (🎥 Video Saved)" if media_type == "video" else (" (📸 Photo Saved)" if media_type == "photo" else "")
            reply_msg = (
                f"🏋️‍♂️ *Workout Set & Form Logged!*{media_str}\n\n"
                f"💪 *Exercise:* {ex_name}\n"
                f"⚖️ *Weight:* `{wt} kg`" + (f" | 🔄 *Reps:* `{reps}`" if reps else "") + (f" | 🔢 *Sets:* `{sets}`" if sets > 1 else "") + f"\n\n"
                f"{pr_note}\n\n"
                f"🧠 *Guru Feedback:* Saved for technical review. Keep chest high, control the 2-second negative eccentric, and push close to failure!"
            )
            self.send_message(chat_id, reply_msg)
            return

        # 2. FOOD MEAL LOGGING & HABIT CRITIQUE (Single Photo or Text)
        saved_img_path = None
        if photos:
            best_photo = photos[-1]
            file_id = best_photo["file_id"]
            filename = f"meal_{timestamp}.jpg"
            dest = os.path.join(FOOD_IMAGES_DIR, filename)
            if self.download_file(file_id, dest):
                saved_img_path = dest

        if incoming_caption or photos:
            # Check if this single photo is a nutrition facts label
            if saved_img_path:
                ocr_text = run_ocr(saved_img_path)
                label_data = parse_nutrition_label(ocr_text)
                if label_data and label_data.get("protein_g", 0) > 0:
                    prod_name = incoming_caption or "Product Label"
                    learned = load_products()
                    learned[prod_name.lower()] = {
                        "name": prod_name,
                        "serving_size": label_data["serving_size"],
                        "calories": label_data["calories"],
                        "protein_g": label_data["protein_g"],
                        "carbs_g": label_data["carbs_g"],
                        "fats_g": label_data["fats_g"],
                        "learned_from": "label_scan"
                    }
                    save_products(learned)
                    parsed = {
                        "description": f"{prod_name} ({label_data['serving_size']})",
                        "calories": label_data["calories"],
                        "protein_g": label_data["protein_g"],
                        "carbs_g": label_data["carbs_g"],
                        "fats_g": label_data["fats_g"]
                    }
                else:
                    meal_input = incoming_caption or "Plate photo"
                    parsed = parse_meal_text(meal_input)
            else:
                meal_input = incoming_caption or "Plate photo"
                parsed = parse_meal_text(meal_input)

            habit_feedback = analyze_behavior_and_habits(incoming_caption or parsed["description"], parsed)

            entry["meals"].append({
                "time": datetime.now().strftime("%H:%M"),
                "name": parsed["description"],
                "image": os.path.basename(saved_img_path) if saved_img_path else None,
                "calories": parsed["calories"],
                "protein_g": parsed["protein_g"],
                "carbs_g": parsed["carbs_g"],
                "fats_g": parsed["fats_g"]
            })

            entry["totals"]["calories"] = sum(m["calories"] for m in entry["meals"])
            entry["totals"]["protein_g"] = round(sum(m["protein_g"] for m in entry["meals"]), 1)
            entry["totals"]["carbs_g"] = round(sum(m["carbs_g"] for m in entry["meals"]), 1)
            entry["totals"]["fats_g"] = round(sum(m["fats_g"] for m in entry["meals"]), 1)
            save_logs(logs)

            tot = entry["totals"]
            rem_p = max(0, targets["protein_g"] - tot["protein_g"])
            rem_cal = max(0, targets["daily_calories"] - tot["calories"])

            habit_str = "\n" + "\n".join(habit_feedback) if habit_feedback else ""

            feedback = (
                f"✅ *Meal Logged Successfully!*" + (f" (📸 Photo Saved)" if saved_img_path else "") + f"\n\n"
                f"🍽 *Items:* {parsed['description']}\n"
                f"🔥 *Calories:* `{parsed['calories']} kcal`\n"
                f"💪 *Protein:* `{parsed['protein_g']}g`\n"
                f"🍞 *Carbs:* `{parsed['carbs_g']}g`\n"
                f"🥑 *Fats:* `{parsed['fats_g']}g`\n\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 *Updated Day Total ({today}):*\n"
                f"• Calories: `{tot['calories']} / {targets['daily_calories']} kcal` (Left: `{rem_cal} kcal`)\n"
                f"• Protein: `{tot['protein_g']}g / {targets['protein_g']}g` (Left: `{rem_p:.1f}g`)\n"
                f"{habit_str}\n\n"
                f"Keep pushing! Send your next meal, workout video, or `/status` anytime."
            )
            self.send_message(chat_id, feedback)

    def run(self):
        print("=" * 60)
        print("🤖 19.GYM TELEGRAM COACH & CONTINUOUS LEARNING BOT IS RUNNING...")
        print("📸 Multi-Image Album Buffering: ACTIVE (Groups front/back product scans)")
        print("🔍 Nutrition Facts OCR Scanner: ACTIVE")
        print("🌐 Live Internet Food Search (OpenFoodFacts): ACTIVE")
        print("⏰ Proactive Notifications: 6:30 AM (Workout) & 9:30 PM (Habit Reflection)")
        print(f"📁 Meal Photos: {FOOD_IMAGES_DIR}")
        print(f"📁 Workout Media: {WORKOUT_MEDIA_DIR}")
        print("=" * 60)

        # 1. Proactive scheduler thread
        t_sched = threading.Thread(target=self.schedule_checker, daemon=True)
        t_sched.start()

        # 2. Cloud Health Check Server
        t_http = threading.Thread(target=start_health_server, daemon=True)
        t_http.start()

        # 3. Telegram polling loop
        while True:
            try:
                url = f"{self.base_url}/getUpdates?offset={self.offset}&timeout=20"
                resp = requests.get(url, timeout=30).json()
                if resp.get("ok"):
                    for update in resp.get("result", []):
                        self.offset = update["update_id"] + 1
                        self.handle_update(update)
            except requests.exceptions.RequestException as e:
                time.sleep(3)
            except Exception as e:
                print(f"Error in poll loop: {e}")
                time.sleep(2)

def main():
    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN")

    if not token:
        print("\n⚠️  TELEGRAM_BOT_TOKEN IS MISSING in .env or environment!")
        sys.exit(1)

    bot = TelegramBot(token)
    bot.run()

if __name__ == "__main__":
    main()
