#!/usr/bin/env python3
"""
Interactive Daily Fitness & Nutrition Tracker for 19.GYM
Run this tool anytime to log your meals, steps, water, and workout!
"""

import json
import os
from datetime import datetime

PROFILE_PATH = os.path.join(os.path.dirname(__file__), "profile.json")
LOGS_PATH = os.path.join(os.path.dirname(__file__), "daily_logs.json")

def load_profile():
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r") as f:
            return json.load(f)
    return {}

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

    today = datetime.now().strftime("%Y-%m-%d")
    logs = load_logs()

    if today not in logs:
        logs[today] = {
            "weight_kg": None,
            "steps": 0,
            "water_l": 0.0,
            "workout_done": "",
            "meals": [],
            "totals": {
                "calories": 0,
                "protein_g": 0,
                "carbs_g": 0,
                "fats_g": 0
            }
        }

    entry = logs[today]
    print("=" * 60)
    print(f"🔥 19.GYM DAILY GURU TRACKER — {today} 🔥")
    print(f"🎯 Targets: {targets['daily_calories']} kcal | P: {targets['protein_g']}g | C: {targets['carbohydrates_g']}g | F: {targets['fats_g']}g | Steps: {targets['daily_steps']}")
    print("=" * 60)
    print(f"Current Totals for Today: {entry['totals']['calories']} kcal | P: {entry['totals']['protein_g']}g | C: {entry['totals']['carbs_g']}g | F: {entry['totals']['fats_g']}g")
    print(f"Steps: {entry['steps']} / {targets['daily_steps']} | Water: {entry['water_l']}L / {targets['water_liters']}L")
    print("=" * 60)
    print("Options:")
    print("1. Log Meal (Food name, Calories, Protein, Carbs, Fats)")
    print("2. Update Steps, Water & Weight")
    print("3. Log Workout Completed")
    print("4. View All Meals for Today")
    print("5. Exit")
    print("=" * 60)

if __name__ == "__main__":
    main()
