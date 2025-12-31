import os
import time
from typing import Optional
from bson import ObjectId
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi

# Analytics APIs
from analytics.financial_analytics import compute_financial_health
from ml.goal_predictor import generate_plan, goal_probability, should_adjust
from ml.goal_intelligence import compute_goal_intelligence
from agent.financial_agent import run_agent

#Config
env_path = os.path.join(os.path.dirname(__file__), "nosave", ".env")
load_dotenv(dotenv_path=env_path)

MONGO_URI = os.getenv("MONGO_URI", "").strip()
DB_NAME = os.getenv("DB_NAME", "mockDB").strip()
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "userGoals").strip()

app = Flask(__name__, template_folder="Frontend", static_folder="Frontend/static")

# Mongo Connection
def connect_mongo(max_retries: int = 3, delay_sec: float = 1.0) -> MongoClient:
    for attempt in range(1, max_retries + 1):
        print(f"[Mongo] Attempt {attempt}/{max_retries} connecting...")
        client = MongoClient(
            MONGO_URI,
            tls=True,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
        )
        client.admin.command("ping")
        print("[Mongo] Connected successfully.")
        return client

client = connect_mongo()
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Pages
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password required"}), 400

    user = collection.find_one(
        {"email": email, "password": password},
        {"password": 0}
    )

    if not user:
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401

    user["_id"] = str(user["_id"])
    return jsonify({"status": "success", "user": user})

@app.route("/api/signup", methods=["POST"])
def api_signup():
    data = request.get_json(silent=True) or {}

    name = (data.get("Name") or "").strip()
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()

    if not name or not email or not password:
        return jsonify({"status": "error", "message": "Name, Email, and Password are required"}), 400

    if collection.find_one({"email": email}):
        return jsonify({"status": "error", "message": "Email already registered"}), 409

    doc = {
        "_id": ObjectId(),
        "Name": name,
        "email": email,
        "password": password,
        "Age": str(data.get("Age") or ""),
        "employement-status": data.get("employement-status") or "Salaried",

        "Goal": {
            "goal": data.get("Goal", {}).get("goal") or "General",
            "target-amt": {"$numberLong": str(data.get("Goal", {}).get("target-amt", 0))},
            "target-time": {"$numberInt": str(data.get("Goal", {}).get("target-time", 0))},
        },

        "financials": {
            "monthly-income": {"$numberLong": str(data.get("financials", {}).get("monthly-income", 0))},
            "monthly-expenses": {"$numberLong": str(data.get("financials", {}).get("monthly-expenses", 0))},
            "monthly_savings": str(data.get("financials", {}).get("monthly_savings", 0)),
            "debt": {"$numberLong": str(data.get("financials", {}).get("debt", 0))},
            "em-fund-opted": bool(data.get("financials", {}).get("em-fund-opted", False)),
        },

        "investments": {
            "risk-opt": data.get("investments", {}).get("risk-opt", "Moderate"),
            "prefered-mode": data.get("investments", {}).get("prefered-mode", "SIP"),
            "invest-amt": {"$numberLong": str(data.get("investments", {}).get("invest-amt", 0))},
        },

        "progress": {
            "start_date": data.get("progress", {}).get("start_date", ""),
            "tenure": {"$numberInt": str(data.get("progress", {}).get("tenure", 0))},
            "ROR": {"$numberDouble": str(data.get("progress", {}).get("ROR", 0.0))},
            "auto-adjust": bool(data.get("progress", {}).get("auto-adjust", False)),
        }
    }

    collection.insert_one(doc)
    doc.pop("password")
    doc["_id"] = str(doc["_id"])

    return jsonify({"status": "success", "user": doc}), 201

@app.route("/api/user/<email>")
def api_get_user(email):
    user = collection.find_one({"email": email}, {"_id": 0})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    return jsonify({"status": "success", "user": user})

@app.route("/api/analytics/<email>")
def analytics(email):
    user = collection.find_one({"email": email}, {"_id": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"analytics": compute_financial_health(user)})

@app.route("/api/predict/<email>")
def predict(email):
    user = collection.find_one({"email": email}, {"_id": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(goal_probability(user))

@app.route("/api/recommend/<email>")
def recommend(email):
    user = collection.find_one({"email": email}, {"_id": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"recommended_plan": generate_plan(user)})

@app.route("/api/goal-intelligence/<email>")
def goal_intelligence(email):
    user = collection.find_one({"email": email}, {"_id": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404

    intelligence = compute_goal_intelligence(user)
    return jsonify({"goal_intelligence": intelligence})

@app.route("/api/agent/<email>")
def agent_api(email):
    user = collection.find_one({"email": email}, {"_id": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404

    goal_intel = compute_goal_intelligence(user)

    agent_response = run_agent(goal_intel)

    return jsonify({
        "goal_intelligence": goal_intel,
        "agent": agent_response
    })
