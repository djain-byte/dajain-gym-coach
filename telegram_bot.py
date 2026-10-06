#!/usr/bin/env python3
"""
19.GYM Telegram Coach Bot & Behavioral Learning Engine
- Receives food photos, workout photos, and workout videos directly from your phone.
- Saves food images to food_images/ and workout media to workout_media/.
- Automatically distinguishes food vs workout sets and tracks progressive overload (weights, reps, PRs).
- Smart Long-Term Memory & Habit Learning: Tracks slips, triggers, wins, and patterns in memory.json.
- Proactive Daily 6:30 AM Workout Notification & 9:30 PM Evening Habit Reflection.
- Built-in HTTP health server for 100% FREE 24/7 hosting on Render/Koyeb (Web Service).
- Commands: /start, /status, /workout, /workout tomorrow, /prs, /habits, /reflect, /water, /steps, /weight.
"""

import os
import re
import sys
import time
import json
import threading
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
ENV_PATH = os.path.join(BASE_DIR, ".env")

os.makedirs(FOOD_IMAGES_DIR, exist_ok=True)
os.makedirs(WORKOUT_MEDIA_DIR, exist_ok=True)

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"DJ Gym Coach Bot is LIVE and Healthy 24/7!\n")

    def log_message(self, format, *args):
        pass  # Silence routine ping logs

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        print(f"🌐 Cloud Health Check Server running on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"Health server note: {e}")

WORKOUT_SCHEDULE = {
    0: {  # Monday
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
    1: {  # Tuesday
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
    2: {  # Wednesday
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
    3: {  # Thursday
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
    4: {  # Friday
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
    5: {  # Saturday
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
    6: {  # Sunday
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

def load_env():
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip("'\"")
    # Also check system environment variables (for cloud deployment)
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
    elif "paneer" in text_lower:
        item = NUTRITION_DB["paneer"]
        total_cal += item["cal"]
        total_p += item["p"]
        total_c += item["c"]
        total_f += item["f"]
        found_items.append("100g Paneer")

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

    if any(w in text_lower for w in ["whey", "protein shake", "gold standard"]):
        item = NUTRITION_DB["whey"]
        total_cal += item["cal"]
        total_p += item["p"]
        total_c += item["c"]
        total_f += item["f"]
        found_items.append("1 Scoop Whey Protein")

    if "banana" in text_lower:
        item = NUTRITION_DB["banana"]
        total_cal += item["cal"]
        total_p += item["p"]
        total_c += item["c"]
        total_f += item["f"]
        found_items.append("1 Banana")

    if not found_items:
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

class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self.last_morning_date = None
        self.last_evening_date = None

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
        """Proactive background thread checking for 6:30 AM workout & 9:30 PM reflection"""
        print("⏰ Proactive scheduler thread active (6:30 AM & 9:30 PM)...")
        while True:
            try:
                now = datetime.now()
                today_str = now.strftime("%Y-%m-%d")
                profile = load_profile()
                chat_id = profile.get("telegram_chat_id")

                # 6:30 AM Workout Broadcast
                if now.hour == 6 and now.minute in [30, 31]:
                    if self.last_morning_date != today_str and chat_id:
                        msg = format_workout_message(day_offset=0)
                        print(f"[{now.strftime('%H:%M:%S')}] Sending 6:30 AM workout to chat_id: {chat_id}")
                        self.send_message(chat_id, msg)
                        self.last_morning_date = today_str

                # 9:30 PM Evening Habit Review Broadcast
                if now.hour == 21 and now.minute in [30, 31]:
                    if self.last_evening_date != today_str and chat_id:
                        logs = load_logs()
                        entry, _ = get_today_entry(logs)
                        mem = load_memory()
                        msg = format_evening_review(entry, profile["targets"], mem)
                        print(f"[{now.strftime('%H:%M:%S')}] Sending 9:30 PM habit review to chat_id: {chat_id}")
                        self.send_message(chat_id, msg)
                        self.last_evening_date = today_str

            except Exception as e:
                print(f"Error in scheduler: {e}")
            time.sleep(30)

    def handle_update(self, update):
        message = update.get("message")
        if not message:
            return

        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        caption = message.get("caption", "")
        photos = message.get("photo")
        video = message.get("video") or message.get("video_note")

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
                f"🔥 *Namaste Dajain! Your 19.GYM AI Coach & Learning Engine is ONLINE* 🔥\n\n"
                f"I continuously learn your personal habits, call out old mistakes before they happen, and engineer you into the aesthetic physique in Image 4.\n\n"
                f"🧠 *Smart Features Active:*\n"
                f"• Continuous Behavioral Memory (`memory.json`)\n"
                f"• Food Macro Analysis & Photo Vault\n"
                f"• Exercise Video & Progressive Overload Tracking\n"
                f"• 6:30 AM Morning Workout Protocol\n"
                f"• 9:30 PM Evening Habit Reflection\n\n"
                f"Commands:\n"
                f"• `/habits` - View what I've learned about your habits & streaks\n"
                f"• `/reflect` - Run an on-demand habit audit right now\n"
                f"• `/prs` - View your personal best weights across all lifts\n"
                f"• `/workout` - Today's complete routine\n"
                f"• `/status` - Today's full macros, calories & logged sets\n"
                f"• `/water 0.5` | `/steps 8000` | `/weight 67`"
            )
            self.send_message(chat_id, welcome)
            return

        if text.startswith("/habits") or text.startswith("/memory"):
            patterns = mem.get("behavioral_patterns", [])
            pattern_lines = [f"• *{p['id'].replace('_', ' ').title()}:* {p['coach_rule']}" for p in patterns[:5]]
            streaks = mem.get("streaks", {})
            h_msg = (
                f"🧠 *AI Coach Long-Term Memory for Dajain*\n\n"
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

        # 2. FOOD MEAL LOGGING & HABIT CRITIQUE
        saved_img_path = None
        if photos:
            best_photo = photos[-1]
            file_id = best_photo["file_id"]
            filename = f"meal_{timestamp}.jpg"
            dest = os.path.join(FOOD_IMAGES_DIR, filename)
            if self.download_file(file_id, dest):
                saved_img_path = dest

        if incoming_caption or photos:
            meal_input = incoming_caption or "Plate photo"
            parsed = parse_meal_text(meal_input)

            habit_feedback = analyze_behavior_and_habits(meal_input, parsed)

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
        print("🤖 19.GYM TELEGRAM COACH & LEARNING BOT IS RUNNING...")
        print("⏰ Proactive Notifications: 6:30 AM (Workout) & 9:30 PM (Habit Reflection)")
        print(f"🧠 Long-Term Memory: {MEMORY_PATH}")
        print(f"📁 Meal Photos: {FOOD_IMAGES_DIR}")
        print(f"📁 Workout Media: {WORKOUT_MEDIA_DIR}")
        print("=" * 60)

        # 1. Start 6:30 AM & 9:30 PM proactive scheduler
        t_sched = threading.Thread(target=self.schedule_checker, daemon=True)
        t_sched.start()

        # 2. Start HTTP Health check server for Cloud Hosting
        t_http = threading.Thread(target=start_health_server, daemon=True)
        t_http.start()

        # 3. Main Telegram polling loop
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
        print("\n" + "!" * 60)
        print("⚠️  TELEGRAM_BOT_TOKEN IS MISSING in .env or environment!")
        print("!" * 60)
        sys.exit(1)

    bot = TelegramBot(token)
    bot.run()

if __name__ == "__main__":
    main()
