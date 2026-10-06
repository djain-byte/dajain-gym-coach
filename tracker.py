#!/usr/bin/env python3
"""
Interactive Daily Fitness & Nutrition Tracker for 19.GYM
Run this tool anytime in terminal to log meals, steps, water, and workouts!
Synchronized seamlessly with Telegram Coach state and Indian Standard Time (IST).
"""

import json
import os
import shutil
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_PATH = os.path.join(BASE_DIR, "profile.json")
LOGS_PATH = os.path.join(BASE_DIR, "daily_logs.json")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")
os.makedirs(BACKUPS_DIR, exist_ok=True)

# Standard Indian Standard Time (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    return datetime.now(IST)

def load_profile():
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def load_logs():
    if os.path.exists(LOGS_PATH):
        with open(LOGS_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def save_logs(logs):
    tmp_path = f"{LOGS_PATH}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, LOGS_PATH)
    
    # Create daily backup
    try:
        today_str = now_ist().strftime("%Y%m%d")
        backup_file = os.path.join(BACKUPS_DIR, f"daily_logs.json.{today_str}.bak")
        if not os.path.exists(backup_file):
            shutil.copy2(LOGS_PATH, backup_file)
    except Exception:
        pass

def main():
    profile = load_profile()
    targets = profile.get("targets", {
        "daily_calories": 2050,
        "protein_g": 145,
        "carbohydrates_g": 210,
        "fats_g": 52,
        "water_liters": 3.5,
        "daily_steps": 9000
    })

    while True:
        today = now_ist().strftime("%Y-%m-%d")
        logs = load_logs()

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

        entry = logs[today]
        tot = entry["totals"]
        rem_p = max(0, targets["protein_g"] - tot["protein_g"])
        rem_cal = max(0, targets["daily_calories"] - tot["calories"])

        print("\n" + "=" * 65)
        print(f"🔥 19.GYM CLI FITNESS TRACKER — {today} (IST) 🔥")
        print(f"🎯 Targets: {targets['daily_calories']} kcal | P: {targets['protein_g']}g | C: {targets['carbohydrates_g']}g | F: {targets['fats_g']}g | Steps: {targets['daily_steps']}")
        print("=" * 65)
        print(f"📊 Totals Today : {tot['calories']} / {targets['daily_calories']} kcal (Left: {rem_cal} kcal)")
        print(f"💪 Protein      : {tot['protein_g']}g / {targets['protein_g']}g (Left: {rem_p:.1f}g)")
        print(f"🍞 Carbs / Fats : {tot['carbs_g']}g C | {tot['fats_g']}g F")
        print(f"🚶 Steps / Water: {entry['steps']} / {targets['daily_steps']} steps | {entry['water_l']}L / {targets['water_liters']}L water")
        if entry.get("weight_kg"):
            print(f"⚖️ Weight       : {entry['weight_kg']} kg")
        print("=" * 65)
        print("1. Log Meal (Food name, Calories, Protein, Carbs, Fats)")
        print("2. Update Steps, Water & Weight")
        print("3. Log Workout Completed")
        print("4. View All Meals for Today")
        print("5. Exit")
        print("=" * 65)

        try:
            choice = input("Enter choice (1-5): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting tracker.")
            break

        if choice == "1":
            try:
                name = input("Meal/Food Name: ").strip()
                if not name:
                    print("⚠️ Name cannot be empty.")
                    continue
                cal = int(input("Calories (kcal): ").strip() or "0")
                p = float(input("Protein (g): ").strip() or "0")
                c = float(input("Carbs (g): ").strip() or "0")
                f = float(input("Fats (g): ").strip() or "0")

                entry["meals"].append({
                    "time": now_ist().strftime("%H:%M"),
                    "name": name,
                    "calories": cal,
                    "protein_g": round(p, 1),
                    "carbs_g": round(c, 1),
                    "fats_g": round(f, 1)
                })
                entry["totals"]["calories"] = sum(m["calories"] for m in entry["meals"])
                entry["totals"]["protein_g"] = round(sum(m["protein_g"] for m in entry["meals"]), 1)
                entry["totals"]["carbs_g"] = round(sum(m["carbs_g"] for m in entry["meals"]), 1)
                entry["totals"]["fats_g"] = round(sum(m["fats_g"] for m in entry["meals"]), 1)
                save_logs(logs)
                print(f"✅ Meal '{name}' logged successfully!")
            except ValueError:
                print("⚠️ Invalid number entered.")

        elif choice == "2":
            try:
                s_input = input(f"Steps (Current: {entry['steps']}, press Enter to skip): ").strip()
                if s_input:
                    entry["steps"] = int(s_input)
                w_input = input(f"Water in Liters (Current: {entry['water_l']}L, press Enter to skip): ").strip()
                if w_input:
                    entry["water_l"] = round(float(w_input), 2)
                wt_input = input(f"Weight in kg (Current: {entry.get('weight_kg', 'N/A')}, press Enter to skip): ").strip()
                if wt_input:
                    entry["weight_kg"] = round(float(wt_input), 2)
                save_logs(logs)
                print("✅ Metrics updated successfully!")
            except ValueError:
                print("⚠️ Invalid number format.")

        elif choice == "3":
            w_done = input("Workout completed summary: ").strip()
            if w_done:
                entry["workout_done"] = w_done
                save_logs(logs)
                print("✅ Workout recorded successfully!")

        elif choice == "4":
            print("\n📋 Today's Logged Meals:")
            if not entry["meals"]:
                print("No meals logged yet today.")
            else:
                for i, m in enumerate(entry["meals"], 1):
                    print(f"  {i}. [{m['time']}] {m['name']} — {m['protein_g']}g P | {m['calories']} kcal | {m['carbs_g']}g C | {m['fats_g']}g F")
            input("\nPress Enter to return to menu...")

        elif choice == "5":
            print("Keep pushing Darshan! See you on Telegram Coach.")
            break
        else:
            print("⚠️ Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    main()
