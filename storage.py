import json
import os

FILE = "data.json"

def load_data():
    if not os.path.exists(FILE):
        return {"users": [], "groups": []}
    with open(FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(FILE, "w") as f:
        json.dump(data, f)

def add_user(user_id):
    data = load_data()
    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data(data)

def add_group(group_id):
    data = load_data()
    if group_id not in data["groups"]:
        data["groups"].append(group_id)
        save_data(data)

def get_all():
    return load_data()
