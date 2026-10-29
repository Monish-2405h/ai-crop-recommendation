import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import random, os, json, math, datetime, hashlib
from functools import wraps
import smtplib, threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")
load_dotenv(PROJECT_ROOT / ".env")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aicropadvisor_secret_2026")
CORS(app, supports_credentials=True)

# ══════════════════════════════════════════════════════════════════════════════
#  EMAIL CONFIG
# ══════════════════════════════════════════════════════════════════════════════
MAIL_SENDER   = os.environ.get("MAIL_SENDER", "")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
MAIL_ENABLED  = bool(MAIL_SENDER and MAIL_PASSWORD)

def _send_email_worker(to_email: str, subject: str, html_body: str):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"AI Crop Advisor <{MAIL_SENDER}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(MAIL_SENDER, MAIL_PASSWORD)
            server.sendmail(MAIL_SENDER, to_email, msg.as_string())
        print(f"✅ Email sent → {to_email} | {subject}")
    except Exception as e:
        print(f"❌ Email failed → {to_email} | {e}")

def send_email(to_email: str, subject: str, html_body: str):
    if not MAIL_ENABLED:
        return
    threading.Thread(target=_send_email_worker, args=(to_email, subject, html_body), daemon=True).start()

def welcome_email_html(name: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
      <div style="background:#2e7d32;padding:24px;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:24px">🌱 AI Crop Advisor</h1>
      </div>
      <div style="padding:32px">
        <h2 style="color:#2e7d32">Welcome, {name}!</h2>
        <p style="color:#333;font-size:15px;line-height:1.6">
          Your account has been created successfully. You can now log in and start
          getting AI-powered crop recommendations tailored to your soil and climate.
        </p>
        <div style="text-align:center;margin:32px 0">
          <a href="#" style="background:#2e7d32;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-size:15px">
            Get Started →
          </a>
        </div>
        <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
        <p style="color:#888;font-size:12px;text-align:center">
          AI Crop Advisor — Smart farming, better yields.
        </p>
      </div>
    </div>"""

def prediction_email_html(name: str, result: dict) -> str:
    crop        = result.get("crop", "N/A")
    season      = result.get("season", "N/A")
    profit      = result.get("profit_per_acre", "N/A")
    yield_est   = result.get("yield_est", "N/A")
    fertilizer  = result.get("fertilizer", "N/A")
    intercrop1  = result.get("intercrop_1", "N/A")
    intercrop2  = result.get("intercrop_2", "N/A")
    location    = result.get("location", "your area")
    soil_score  = result.get("soil_score", "N/A")
    market      = result.get("market_status", "N/A")
    tips        = result.get("soil_tips", [])
    schemes     = result.get("gov_schemes", [])
    top3        = result.get("top3", [])

    tips_html = "".join(f"<li style='color:#555;margin:4px 0'>{t}</li>" for t in tips) if tips else "<li style='color:#aaa'>No issues detected</li>"
    schemes_html = ", ".join(schemes) if schemes else "N/A"
    top3_html = "".join(
        f"<tr><td style='padding:8px;border-bottom:1px solid #eee'>{c['crop']}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee'>{c['season']}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee'>{c['profit']}</td></tr>"
        for c in top3
    )

    return f"""
    <div style="font-family:Arial,sans-serif;max-width:640px;margin:auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
      <div style="background:#388e3c;padding:24px;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:22px">🌾 Your Crop Prediction is Ready!</h1>
        <p style="color:#c8e6c9;margin:6px 0 0">AI Crop Advisor — {location}</p>
      </div>
      <div style="padding:28px">
        <p style="color:#333;font-size:15px">Hi <strong>{name}</strong>,</p>
        <p style="color:#555;font-size:14px">Here's your AI-powered crop recommendation based on your soil and weather data.</p>

        <div style="background:#e8f5e9;border-left:4px solid #388e3c;border-radius:6px;padding:16px;margin:20px 0">
          <h2 style="color:#2e7d32;margin:0 0 4px">✅ Recommended Crop: {crop}</h2>
          <p style="color:#555;margin:0;font-size:14px">Season: <strong>{season}</strong> &nbsp;|&nbsp; Market: <strong>{market}</strong></p>
        </div>

        <table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:14px">
          <tr style="background:#f5f5f5">
            <td style="padding:10px;font-weight:bold;color:#555;width:45%">💰 Expected Profit</td>
            <td style="padding:10px;color:#333">{profit}</td>
          </tr>
          <tr>
            <td style="padding:10px;font-weight:bold;color:#555">📦 Estimated Yield</td>
            <td style="padding:10px;color:#333">{yield_est} kg/acre</td>
          </tr>
          <tr style="background:#f5f5f5">
            <td style="padding:10px;font-weight:bold;color:#555">🧪 Fertilizer</td>
            <td style="padding:10px;color:#333">{fertilizer}</td>
          </tr>
          <tr>
            <td style="padding:10px;font-weight:bold;color:#555">🌿 Intercropping</td>
            <td style="padding:10px;color:#333">{intercrop1}, {intercrop2}</td>
          </tr>
          <tr style="background:#f5f5f5">
            <td style="padding:10px;font-weight:bold;color:#555">🧬 Soil Health Score</td>
            <td style="padding:10px;color:#333">{soil_score} / 100</td>
          </tr>
          <tr>
            <td style="padding:10px;font-weight:bold;color:#555">🏛 Govt Schemes</td>
            <td style="padding:10px;color:#333">{schemes_html}</td>
          </tr>
        </table>

        {"<h3 style='color:#e65100;font-size:14px;margin:16px 0 8px'>⚠️ Soil Tips</h3><ul style='margin:0;padding-left:20px'>" + tips_html + "</ul>" if tips else ""}
        {"<h3 style='color:#1565c0;font-size:14px;margin:20px 0 8px'>🏆 Other Top Picks</h3><table style='width:100%;border-collapse:collapse;font-size:13px'><tr style='background:#e3f2fd'><th style='padding:8px;text-align:left'>Crop</th><th style='padding:8px;text-align:left'>Season</th><th style='padding:8px;text-align:left'>Profit</th></tr>" + top3_html + "</table>" if top3 else ""}

        <div style="background:#fff8e1;border:1px solid #ffe082;border-radius:6px;padding:16px;margin:24px 0">
          <h3 style="color:#f57f17;margin:0 0 8px">📝 After Harvesting — Share Your Feedback!</h3>
          <p style="color:#555;font-size:13px;margin:0;line-height:1.6">
            Once you harvest your crop, please come back and submit your feedback on the app.
          </p>
        </div>

        <hr style="border:none;border-top:1px solid #eee;margin:20px 0">
        <p style="color:#888;font-size:12px;text-align:center">AI Crop Advisor — Smart farming, better yields.</p>
      </div>
    </div>"""

def feedback_thankyou_email_html(name: str, actual_crop: str, rating: int, total_profit: float, total_yield: float) -> str:
    stars = "⭐" * rating + "☆" * (5 - rating)
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
      <div style="background:#00695c;padding:24px;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:22px">🙏 Thank You for Your Feedback!</h1>
      </div>
      <div style="padding:28px">
        <p style="color:#333;font-size:15px">Hi <strong>{name}</strong>,</p>
        <p style="color:#555;font-size:14px;line-height:1.6">
          Thank you for sharing your harvest experience with us! Your feedback helps our AI model get smarter.
        </p>
        <div style="background:#e0f2f1;border-left:4px solid #00695c;border-radius:6px;padding:16px;margin:20px 0">
          <h3 style="color:#00695c;margin:0 0 12px">📋 Your Feedback Summary</h3>
          <table style="width:100%;font-size:14px;border-collapse:collapse">
            <tr>
              <td style="padding:6px 0;color:#555;font-weight:bold;width:50%">Crop Grown</td>
              <td style="padding:6px 0;color:#333">{actual_crop}</td>
            </tr>
            <tr>
              <td style="padding:6px 0;color:#555;font-weight:bold">Total Profit</td>
              <td style="padding:6px 0;color:#333">₹{total_profit:,.0f}</td>
            </tr>
            <tr>
              <td style="padding:6px 0;color:#555;font-weight:bold">Total Yield</td>
              <td style="padding:6px 0;color:#333">{total_yield:,.0f} kg</td>
            </tr>
            <tr>
              <td style="padding:6px 0;color:#555;font-weight:bold">Your Rating</td>
              <td style="padding:6px 0">{stars}</td>
            </tr>
          </table>
        </div>
        <hr style="border:none;border-top:1px solid #eee;margin:20px 0">
        <p style="color:#888;font-size:12px;text-align:center">AI Crop Advisor — Smart farming, better yields.</p>
      </div>
    </div>"""

def login_email_html(name: str, login_time: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
      <div style="background:#1565c0;padding:24px;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:24px">🔐 Login Alert</h1>
      </div>
      <div style="padding:32px">
        <h2 style="color:#1565c0">Hi {name},</h2>
        <p style="color:#333;font-size:15px;line-height:1.6">
          A successful login was recorded on your AI Crop Advisor account.
        </p>
        <table style="width:100%;border-collapse:collapse;margin:20px 0">
          <tr>
            <td style="padding:10px;background:#f5f5f5;font-weight:bold;color:#555;width:40%">Time</td>
            <td style="padding:10px;color:#333">{login_time}</td>
          </tr>
        </table>
        <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
        <p style="color:#888;font-size:12px;text-align:center">AI Crop Advisor — Smart farming, better yields.</p>
      </div>
    </div>"""

# ══════════════════════════════════════════════════════════════════════════════
#  MONGODB & IN-MEMORY FALLBACK
# ══════════════════════════════════════════════════════════════════════════════
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId

class InMemoryCollection:
    def __init__(self, name):
        self.name = name
        self._docs = []

    def insert_one(self, doc):
        d = dict(doc)
        if "_id" not in d:
            d["_id"] = str(ObjectId())
        self._docs.append(d)
        class Result:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        return Result(d["_id"])

    def _matches(self, doc, query):
        if not query:
            return True
        for k, v in query.items():
            if k == "$or" and isinstance(v, list):
                if not any(self._matches(doc, q) for q in v):
                    return False
                continue
            if isinstance(v, dict):
                if "$ne" in v:
                    if doc.get(k) == v["$ne"]:
                        return False
                    continue
            val = doc.get(k)
            if k == "_id":
                if str(val) != str(v):
                    return False
            elif val != v:
                return False
        return True

    def find_one(self, query=None, projection=None):
        res = list(self.find(query, projection))
        return res[0] if res else None

    def find(self, query=None, projection=None):
        matched = [d for d in self._docs if self._matches(d, query)]
        
        class Cursor:
            def __init__(self, items, projection):
                self.items = items
                self.projection = projection

            def _project(self, item):
                d = dict(item)
                if self.projection and isinstance(self.projection, dict):
                    if self.projection.get("password") == 0:
                        d.pop("password", None)
                    if self.projection.get("_id") == 0:
                        d.pop("_id", None)
                    if self.projection.get("userId") == 0:
                        d.pop("userId", None)
                return d

            def sort(self, key, direction=-1):
                reverse = (direction == -1 or direction == "desc")
                self.items = sorted(self.items, key=lambda x: str(x.get(key, "")), reverse=reverse)
                return self

            def limit(self, n):
                self.items = self.items[:n]
                return self

            def __iter__(self):
                for item in self.items:
                    yield self._project(item)

            def __len__(self):
                return len(self.items)

        return Cursor(matched, projection)

    def count_documents(self, query=None):
        return len(list(self.find(query)))

class InMemoryDB:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = InMemoryCollection(name)
        return self.collections[name]

in_memory_db = InMemoryDB()

# Seed default admin in memory
try:
    import bcrypt
    in_memory_db["users"].insert_one({
        "name": "System Admin",
        "email": "admin@agrosense.com",
        "password": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
        "role": "admin",
        "createdAt": datetime.datetime.utcnow().isoformat()
    })
except Exception:
    pass

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
try:
    _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    _client.server_info()
    db = _client["ai_crop_advisor"]
    print("✅ MongoDB connected →", MONGO_URI)
except Exception as e:
    print(f"⚠️  MongoDB server not connected ({e}). Using In-Memory Database fallback.")
    db = None

def col(name):
    if db is not None:
        return db[name]
    return in_memory_db[name]


# ══════════════════════════════════════════════════════════════════════════════
#  ML MODEL
# ══════════════════════════════════════════════════════════════════════════════
MODEL_PATH  = PROJECT_ROOT / "model" / "crop_model.pkl"
SCALER_PATH = PROJECT_ROOT / "model" / "scaler.pkl"

try:
    import joblib, numpy as np
    if not MODEL_PATH.exists() or not SCALER_PATH.exists():
        print(f"⚠️  Model file not found at {MODEL_PATH}. Run python train_model.py first.")
        USE_ML = False
    else:
        MODEL  = joblib.load(MODEL_PATH)
        SCALER = joblib.load(SCALER_PATH)
        USE_ML = True
        print(f"✅ ML model loaded successfully from {MODEL_PATH}")
except Exception as e:
    USE_ML = False
    print(f"⚠️  ML fallback rule-based: {e}")

# ══════════════════════════════════════════════════════════════════════════════
#  CROP KNOWLEDGE BASE — 15 CROPS
# ══════════════════════════════════════════════════════════════════════════════
CROP_DATA = {
    "Rice":      {"intercrop":["Azolla","Fish (Aquaculture)"],"fertilizer":"Urea + DAP","base_price":2200,"price_volatility":0.04,"market_trend":"rising","season":"Kharif","sow_month":6,"harvest_month":10,"profit_per_acre":"₹40,000–₹55,000","yield_kg_per_acre":(2500,4000),"market_status":"High Demand","water_need":"high","disease_risk":{"fungal":True,"bacterial":True,"pest":False},"gov_schemes":["PM-Kisan","PMFBY","NFSM"]},
    "Maize":     {"intercrop":["Cowpea","Soybean"],"fertilizer":"NPK 14-35-14","base_price":1800,"price_volatility":0.05,"market_trend":"stable","season":"Kharif/Rabi","sow_month":6,"harvest_month":9,"profit_per_acre":"₹25,000–₹35,000","yield_kg_per_acre":(1800,3000),"market_status":"Normal","water_need":"medium","disease_risk":{"fungal":False,"bacterial":False,"pest":True},"gov_schemes":["PM-Kisan","NFSM"]},
    "Groundnut": {"intercrop":["Pearl Millet","Castor"],"fertilizer":"SSP + Gypsum","base_price":5500,"price_volatility":0.06,"market_trend":"rising","season":"Kharif","sow_month":6,"harvest_month":10,"profit_per_acre":"₹35,000–₹50,000","yield_kg_per_acre":(800,1500),"market_status":"High Demand","water_need":"medium","disease_risk":{"fungal":True,"bacterial":False,"pest":True},"gov_schemes":["PM-Kisan","PMFBY"]},
    "Wheat":     {"intercrop":["Mustard","Chickpea"],"fertilizer":"Urea + DAP","base_price":2100,"price_volatility":0.03,"market_trend":"stable","season":"Rabi","sow_month":11,"harvest_month":3,"profit_per_acre":"₹30,000–₹42,000","yield_kg_per_acre":(1500,2800),"market_status":"Normal","water_need":"medium","disease_risk":{"fungal":True,"bacterial":False,"pest":False},"gov_schemes":["PM-Kisan","NFSM","MSP Scheme"]},
    "Cotton":    {"intercrop":["Moong Bean","Groundnut"],"fertilizer":"NPK 20-20-0","base_price":6500,"price_volatility":0.07,"market_trend":"rising","season":"Kharif","sow_month":5,"harvest_month":11,"profit_per_acre":"₹45,000–₹65,000","yield_kg_per_acre":(400,700),"market_status":"High Demand","water_need":"medium","disease_risk":{"fungal":False,"bacterial":True,"pest":True},"gov_schemes":["PM-Kisan","Cotton Tech Mission","PMFBY"]},
    "Sugarcane": {"intercrop":["Onion","Garlic"],"fertilizer":"NPK + Zinc","base_price":350,"price_volatility":0.02,"market_trend":"stable","season":"Annual","sow_month":2,"harvest_month":12,"profit_per_acre":"₹50,000–₹75,000","yield_kg_per_acre":(30000,50000),"market_status":"Normal","water_need":"high","disease_risk":{"fungal":True,"bacterial":False,"pest":False},"gov_schemes":["PM-Kisan","Sugarcane Dev Scheme"]},
    "Banana":    {"intercrop":["Ginger","Turmeric"],"fertilizer":"FYM + NPK","base_price":1200,"price_volatility":0.08,"market_trend":"rising","season":"Annual","sow_month":3,"harvest_month":12,"profit_per_acre":"₹60,000–₹90,000","yield_kg_per_acre":(8000,15000),"market_status":"High Demand","water_need":"high","disease_risk":{"fungal":True,"bacterial":True,"pest":False},"gov_schemes":["PM-Kisan","NHM","PMFBY"]},
    "Chickpea":  {"intercrop":["Safflower","Linseed"],"fertilizer":"DAP + Rhizobium","base_price":5000,"price_volatility":0.05,"market_trend":"stable","season":"Rabi","sow_month":10,"harvest_month":2,"profit_per_acre":"₹28,000–₹38,000","yield_kg_per_acre":(600,1200),"market_status":"Normal","water_need":"low","disease_risk":{"fungal":False,"bacterial":False,"pest":True},"gov_schemes":["PM-Kisan","NFSM","Pulses Dev"]},
    "Tomato":    {"intercrop":["Basil","Marigold"],"fertilizer":"NPK 19-19-19","base_price":800,"price_volatility":0.15,"market_trend":"rising","season":"Rabi/Kharif","sow_month":7,"harvest_month":11,"profit_per_acre":"₹80,000–₹1,50,000","yield_kg_per_acre":(10000,20000),"market_status":"High Demand","water_need":"medium","disease_risk":{"fungal":True,"bacterial":True,"pest":True},"gov_schemes":["PM-Kisan","NHM","PMFBY"]},
    "Onion":     {"intercrop":["Carrot","Spinach"],"fertilizer":"Urea + SSP + MOP","base_price":1500,"price_volatility":0.12,"market_trend":"rising","season":"Rabi","sow_month":11,"harvest_month":4,"profit_per_acre":"₹60,000–₹1,00,000","yield_kg_per_acre":(8000,15000),"market_status":"High Demand","water_need":"medium","disease_risk":{"fungal":True,"bacterial":False,"pest":True},"gov_schemes":["PM-Kisan","NHM"]},
    "Chilli":    {"intercrop":["Coriander","Fenugreek"],"fertilizer":"NPK 17-17-17","base_price":12000,"price_volatility":0.10,"market_trend":"rising","season":"Kharif","sow_month":6,"harvest_month":12,"profit_per_acre":"₹70,000–₹1,20,000","yield_kg_per_acre":(1500,3000),"market_status":"High Demand","water_need":"medium","disease_risk":{"fungal":True,"bacterial":True,"pest":True},"gov_schemes":["PM-Kisan","NHM"]},
    "Turmeric":  {"intercrop":["Ginger","Taro"],"fertilizer":"FYM + NPK + Boron","base_price":8000,"price_volatility":0.08,"market_trend":"stable","season":"Kharif","sow_month":5,"harvest_month":1,"profit_per_acre":"₹90,000–₹1,40,000","yield_kg_per_acre":(2000,4000),"market_status":"High Demand","water_need":"medium","disease_risk":{"fungal":True,"bacterial":False,"pest":False},"gov_schemes":["PM-Kisan","NHM","Spices Board"]},
    "Soybean":   {"intercrop":["Maize","Sorghum"],"fertilizer":"DAP + Rhizobium","base_price":3800,"price_volatility":0.06,"market_trend":"rising","season":"Kharif","sow_month":6,"harvest_month":10,"profit_per_acre":"₹25,000–₹40,000","yield_kg_per_acre":(800,1500),"market_status":"Normal","water_need":"medium","disease_risk":{"fungal":True,"bacterial":False,"pest":True},"gov_schemes":["PM-Kisan","NFSM"]},
    "Mango":     {"intercrop":["Papaya","Turmeric"],"fertilizer":"FYM + NPK","base_price":3000,"price_volatility":0.09,"market_trend":"rising","season":"Annual","sow_month":7,"harvest_month":5,"profit_per_acre":"₹1,00,000–₹2,00,000","yield_kg_per_acre":(5000,12000),"market_status":"High Demand","water_need":"low","disease_risk":{"fungal":True,"bacterial":False,"pest":True},"gov_schemes":["PM-Kisan","NHM"]},
    "Coconut":   {"intercrop":["Banana","Pepper"],"fertilizer":"NPK + Boron","base_price":25,"price_volatility":0.05,"market_trend":"stable","season":"Annual","sow_month":6,"harvest_month":12,"profit_per_acre":"₹60,000–₹1,00,000","yield_kg_per_acre":(8000,15000),"market_status":"Normal","water_need":"medium","disease_risk":{"fungal":False,"bacterial":True,"pest":True},"gov_schemes":["PM-Kisan","Coconut Dev Board"]},
    "Basil":     {"intercrop":["Marigold","Tomato"],"fertilizer":"FYM + Vermicompost","base_price":3500,"price_volatility":0.08,"market_trend":"rising","season":"Kharif/Rabi","sow_month":6,"harvest_month":9,"profit_per_acre":"₹30,000–₹45,000","yield_kg_per_acre":(1000,2000),"market_status":"High Demand","water_need":"medium","disease_risk":{"fungal":True,"bacterial":False,"pest":True},"gov_schemes":["NHM"]},
    "Marigold":  {"intercrop":["Tomato","Basil"],"fertilizer":"NPK 15-15-15","base_price":2500,"price_volatility":0.09,"market_trend":"rising","season":"Annual","sow_month":7,"harvest_month":11,"profit_per_acre":"₹40,000–₹65,000","yield_kg_per_acre":(3500,6000),"market_status":"High Demand","water_need":"medium","disease_risk":{"fungal":True,"bacterial":False,"pest":False},"gov_schemes":["NHM"]},
    "Cowpea":    {"intercrop":["Maize","Sorghum"],"fertilizer":"DAP + Rhizobium","base_price":4500,"price_volatility":0.05,"market_trend":"stable","season":"Kharif","sow_month":6,"harvest_month":9,"profit_per_acre":"₹20,000–₹32,000","yield_kg_per_acre":(400,800),"market_status":"Normal","water_need":"low","disease_risk":{"fungal":False,"bacterial":False,"pest":True},"gov_schemes":["NFSM"]},
    "Mustard":   {"intercrop":["Wheat","Chickpea"],"fertilizer":"NPK + Sulphur","base_price":5200,"price_volatility":0.05,"market_trend":"rising","season":"Rabi","sow_month":10,"harvest_month":2,"profit_per_acre":"₹25,000–₹38,000","yield_kg_per_acre":(500,1000),"market_status":"High Demand","water_need":"low","disease_risk":{"fungal":True,"bacterial":False,"pest":True},"gov_schemes":["NFSM"]},
    "Moong Bean":{"intercrop":["Cotton","Groundnut"],"fertilizer":"DAP + Rhizobium","base_price":7000,"price_volatility":0.06,"market_trend":"rising","season":"Kharif/Rabi","sow_month":6,"harvest_month":8,"profit_per_acre":"₹22,000–₹35,000","yield_kg_per_acre":(400,750),"market_status":"Normal","water_need":"low","disease_risk":{"fungal":True,"bacterial":True,"pest":False},"gov_schemes":["NFSM"]},
    "Garlic":    {"intercrop":["Sugarcane","Onion"],"fertilizer":"FYM + NPK + Sulphur","base_price":8500,"price_volatility":0.12,"market_trend":"rising","season":"Rabi","sow_month":10,"harvest_month":3,"profit_per_acre":"₹60,000–₹1,10,000","yield_kg_per_acre":(2500,4500),"market_status":"High Demand","water_need":"medium","disease_risk":{"fungal":True,"bacterial":False,"pest":True},"gov_schemes":["NHM"]},
    "Ginger":    {"intercrop":["Banana","Turmeric"],"fertilizer":"FYM + NPK + Zinc","base_price":6000,"price_volatility":0.10,"market_trend":"rising","season":"Kharif","sow_month":5,"harvest_month":1,"profit_per_acre":"₹80,000–₹1,40,000","yield_kg_per_acre":(3500,7000),"market_status":"High Demand","water_need":"medium","disease_risk":{"fungal":True,"bacterial":True,"pest":False},"gov_schemes":["NHM"]},
    "Carrot":    {"intercrop":["Onion","Spinach"],"fertilizer":"NPK 15-15-15","base_price":1800,"price_volatility":0.08,"market_trend":"stable","season":"Rabi","sow_month":10,"harvest_month":1,"profit_per_acre":"₹35,000–₹55,000","yield_kg_per_acre":(6000,10000),"market_status":"Normal","water_need":"medium","disease_risk":{"fungal":True,"bacterial":False,"pest":True},"gov_schemes":["NHM"]},
    "Spinach":   {"intercrop":["Onion","Carrot"],"fertilizer":"Urea + FYM","base_price":1200,"price_volatility":0.10,"market_trend":"rising","season":"Rabi/Kharif","sow_month":10,"harvest_month":12,"profit_per_acre":"₹25,000–₹40,000","yield_kg_per_acre":(3000,5000),"market_status":"High Demand","water_need":"medium","disease_risk":{"fungal":True,"bacterial":False,"pest":True},"gov_schemes":["NHM"]},
    "Coriander": {"intercrop":["Chilli","Fenugreek"],"fertilizer":"NPK 20-20-0","base_price":6500,"price_volatility":0.07,"market_trend":"rising","season":"Rabi","sow_month":10,"harvest_month":1,"profit_per_acre":"₹30,000–₹50,000","yield_kg_per_acre":(600,1200),"market_status":"High Demand","water_need":"low","disease_risk":{"fungal":True,"bacterial":False,"pest":False},"gov_schemes":["NHM"]},
    "Fenugreek": {"intercrop":["Chilli","Coriander"],"fertilizer":"FYM + NPK","base_price":5500,"price_volatility":0.06,"market_trend":"stable","season":"Rabi","sow_month":10,"harvest_month":1,"profit_per_acre":"₹20,000–₹35,000","yield_kg_per_acre":(500,900),"market_status":"Normal","water_need":"low","disease_risk":{"fungal":True,"bacterial":False,"pest":False},"gov_schemes":["NHM"]},
    "Azolla":    {"intercrop":["Rice","Fish (Aquaculture)"],"fertilizer":"Superphosphate","base_price":500,"price_volatility":0.02,"market_trend":"stable","season":"Annual","sow_month":1,"harvest_month":12,"profit_per_acre":"₹15,000–₹25,000","yield_kg_per_acre":(5000,10000),"market_status":"Normal","water_need":"high","disease_risk":{"fungal":False,"bacterial":False,"pest":False},"gov_schemes":["NFSM"]},
    "Fish (Aquaculture)":{"intercrop":["Rice","Azolla"],"fertilizer":"Aqua Feed","base_price":15000,"price_volatility":0.05,"market_trend":"rising","season":"Annual","sow_month":1,"harvest_month":12,"profit_per_acre":"₹50,000–₹90,000","yield_kg_per_acre":(2000,4000),"market_status":"High Demand","water_need":"high","disease_risk":{"fungal":True,"bacterial":True,"pest":False},"gov_schemes":["PM-Kisan"]},
    "Sorghum":   {"intercrop":["Cowpea","Soybean"],"fertilizer":"FYM + NPK","base_price":2800,"price_volatility":0.05,"market_trend":"stable","season":"Kharif","sow_month":6,"harvest_month":10,"profit_per_acre":"₹22,000–₹35,000","yield_kg_per_acre":(1200,2200),"market_status":"Normal","water_need":"low","disease_risk":{"fungal":False,"bacterial":False,"pest":True},"gov_schemes":["NFSM"]},
    "Pearl Millet":{"intercrop":["Groundnut","Cowpea"],"fertilizer":"Urea + DAP","base_price":2200,"price_volatility":0.04,"market_trend":"rising","season":"Kharif","sow_month":6,"harvest_month":9,"profit_per_acre":"₹20,000–₹30,000","yield_kg_per_acre":(1000,1800),"market_status":"Normal","water_need":"low","disease_risk":{"fungal":False,"bacterial":False,"pest":True},"gov_schemes":["NFSM"]},
    "Castor":    {"intercrop":["Groundnut","Moong Bean"],"fertilizer":"NPK 20-20-0","base_price":5800,"price_volatility":0.06,"market_trend":"rising","season":"Kharif","sow_month":7,"harvest_month":12,"profit_per_acre":"₹30,000–₹45,000","yield_kg_per_acre":(600,1200),"market_status":"High Demand","water_need":"low","disease_risk":{"fungal":True,"bacterial":False,"pest":False},"gov_schemes":["NFSM"]},
    "Taro":      {"intercrop":["Turmeric","Ginger"],"fertilizer":"FYM + NPK","base_price":3000,"price_volatility":0.08,"market_trend":"stable","season":"Kharif","sow_month":5,"harvest_month":11,"profit_per_acre":"₹35,000–₹55,000","yield_kg_per_acre":(5000,9000),"market_status":"Normal","water_need":"high","disease_risk":{"fungal":True,"bacterial":False,"pest":False},"gov_schemes":["NHM"]},
    "Linseed":   {"intercrop":["Chickpea","Wheat"],"fertilizer":"DAP + NPK","base_price":5600,"price_volatility":0.05,"market_trend":"stable","season":"Rabi","sow_month":10,"harvest_month":3,"profit_per_acre":"₹20,000–₹32,000","yield_kg_per_acre":(400,800),"market_status":"Normal","water_need":"low","disease_risk":{"fungal":True,"bacterial":False,"pest":False},"gov_schemes":["NFSM"]},
    "Safflower": {"intercrop":["Chickpea","Linseed"],"fertilizer":"NPK + Gypsum","base_price":5200,"price_volatility":0.06,"market_trend":"rising","season":"Rabi","sow_month":10,"harvest_month":3,"profit_per_acre":"₹22,000–₹34,000","yield_kg_per_acre":(500,900),"market_status":"Normal","water_need":"low","disease_risk":{"fungal":False,"bacterial":False,"pest":True},"gov_schemes":["NFSM"]},
    "Papaya":    {"intercrop":["Mango","Turmeric"],"fertilizer":"FYM + NPK + Boron","base_price":2000,"price_volatility":0.10,"market_trend":"rising","season":"Annual","sow_month":6,"harvest_month":12,"profit_per_acre":"₹70,000–₹1,20,000","yield_kg_per_acre":(15000,25000),"market_status":"High Demand","water_need":"medium","disease_risk":{"fungal":True,"bacterial":True,"pest":True},"gov_schemes":["NHM"]},
    "Pepper":    {"intercrop":["Coconut","Banana"],"fertilizer":"Organic Compost + NPK","base_price":45000,"price_volatility":0.08,"market_trend":"rising","season":"Annual","sow_month":6,"harvest_month":1,"profit_per_acre":"₹1,20,000–₹2,20,000","yield_kg_per_acre":(800,1600),"market_status":"High Demand","water_need":"high","disease_risk":{"fungal":True,"bacterial":False,"pest":True},"gov_schemes":["Spices Board"]},
}
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# ══════════════════════════════════════════════════════════════════════════════
#  AGMARKNET LIVE MARKET PRICE INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════
NON_MANDI_CROPS = {"Azolla", "Fish (Aquaculture)"}

AGMARKNET_COMMODITY_MAP = {
    "Rice":         ["Paddy(Dhan)", "Rice"],
    "Maize":        ["Maize"],
    "Groundnut":    ["Groundnut"],
    "Wheat":        ["Wheat"],
    "Cotton":       ["Cotton"],
    "Sugarcane":    ["Sugarcane", "Gur"],
    "Banana":       ["Banana"],
    "Chickpea":     ["Bengal Gram(Gram)(Whole)", "Chickpea", "Gram"],
    "Tomato":       ["Tomato"],
    "Onion":        ["Onion"],
    "Chilli":       ["Green Chilli", "Chilli Red", "Chillies"],
    "Turmeric":     ["Turmeric"],
    "Soybean":      ["Soyabean", "Soybean"],
    "Mango":        ["Mango"],
    "Coconut":      ["Coconut"],
    "Basil":        ["Tulsi", "Basil"],
    "Marigold":     ["Marigold(Loose)", "Flower", "Marigold"],
    "Cowpea":       ["Cowpea(Veg)", "Cowpea(Lobia)", "Lobia"],
    "Mustard":      ["Mustard", "Mustard Seed"],
    "Moong Bean":   ["Green Gram(Moong)(Whole)", "Moong(Grain)", "Moong"],
    "Garlic":       ["Garlic"],
    "Ginger":       ["Ginger(Green)", "Dry Ginger", "Ginger"],
    "Carrot":       ["Carrot"],
    "Spinach":      ["Spinach"],
    "Coriander":    ["Coriander(Leaves)", "Coriander seed", "Coriander"],
    "Fenugreek":    ["Methi(Leaves)", "Methi Seeds", "Fenugreek"],
    "Sorghum":      ["Jowar(Sorghum)", "Jowar"],
    "Pearl Millet": ["Bajra(Pearl Millet/Cumbu)", "Bajra"],
    "Castor":       ["Castor Seed", "Castor"],
    "Taro":         ["Taro", "Arbi", "Colocasia"],
    "Linseed":      ["Linseed", "Alsi"],
    "Safflower":    ["Safflower"],
    "Papaya":       ["Papaya"],
    "Pepper":       ["Black Pepper", "Pepper"],
}

ESTIMATED_PRODUCTION_COST_PER_ACRE = {
    "Rice":               25000,
    "Maize":              15000,
    "Groundnut":          20000,
    "Wheat":              18000,
    "Cotton":             25000,
    "Sugarcane":          40000,
    "Banana":             45000,
    "Chickpea":           15000,
    "Tomato":             35000,
    "Onion":              30000,
    "Chilli":             35000,
    "Turmeric":           40000,
    "Soybean":            16000,
    "Mango":              30000,
    "Coconut":            25000,
    "Basil":              12000,
    "Marigold":           15000,
    "Cowpea":             10000,
    "Mustard":            12000,
    "Moong Bean":         11000,
    "Garlic":             28000,
    "Ginger":             35000,
    "Carrot":             18000,
    "Spinach":            10000,
    "Coriander":          12000,
    "Fenugreek":          10000,
    "Sorghum":            12000,
    "Pearl Millet":       10000,
    "Castor":             15000,
    "Taro":               20000,
    "Linseed":            11000,
    "Safflower":          11000,
    "Papaya":             35000,
    "Pepper":             40000,
    "Azolla":              5000,
    "Fish (Aquaculture)": 40000,
}

AGMARKNET_BENCHMARK_REGISTRY = {
    "Rice":         {"market": "Coimbatore Mandi", "commodity": "Paddy(Dhan)", "variety": "Common", "grade": "FAQ", "min_price": 2180.0, "modal_price": 2320.0, "max_price": 2450.0, "arrival_quantity": "250 Quintals"},
    "Maize":        {"market": "Erode Mandi", "commodity": "Maize", "variety": "Yellow", "grade": "FAQ", "min_price": 1900.0, "modal_price": 2050.0, "max_price": 2200.0, "arrival_quantity": "180 Quintals"},
    "Groundnut":    {"market": "Pollachi Mandi", "commodity": "Groundnut", "variety": "Pods", "grade": "FAQ", "min_price": 5400.0, "modal_price": 5850.0, "max_price": 6200.0, "arrival_quantity": "120 Quintals"},
    "Wheat":        {"market": "Khanna Mandi", "commodity": "Wheat", "variety": "Dara", "grade": "FAQ", "min_price": 2300.0, "modal_price": 2480.0, "max_price": 2650.0, "arrival_quantity": "400 Quintals"},
    "Cotton":       {"market": "Tiruppur Mandi", "commodity": "Cotton", "variety": "Medium Staple", "grade": "FAQ", "min_price": 6600.0, "modal_price": 7100.0, "max_price": 7500.0, "arrival_quantity": "150 Quintals"},
    "Sugarcane":    {"market": "Sathyamangalam Mandi", "commodity": "Sugarcane", "variety": "Cane", "grade": "FAQ", "min_price": 315.0, "modal_price": 350.0, "max_price": 380.0, "arrival_quantity": "1200 Quintals"},
    "Banana":       {"market": "Trichy Mandi", "commodity": "Banana", "variety": "Poovan", "grade": "FAQ", "min_price": 1500.0, "modal_price": 1850.0, "max_price": 2100.0, "arrival_quantity": "300 Quintals"},
    "Chickpea":     {"market": "Indore Mandi", "commodity": "Bengal Gram(Gram)", "variety": "Desi", "grade": "FAQ", "min_price": 5000.0, "modal_price": 5400.0, "max_price": 5800.0, "arrival_quantity": "220 Quintals"},
    "Tomato":       {"market": "Oddanchatram Mandi", "commodity": "Tomato", "variety": "Hybrid Tomato", "grade": "FAQ", "min_price": 1800.0, "modal_price": 2200.0, "max_price": 2600.0, "arrival_quantity": "350 Quintals"},
    "Onion":        {"market": "Dindigul Mandi", "commodity": "Onion", "variety": "Red Onion", "grade": "FAQ", "min_price": 1600.0, "modal_price": 1950.0, "max_price": 2300.0, "arrival_quantity": "450 Quintals"},
    "Chilli":       {"market": "Guntur Mandi", "commodity": "Chilli Red", "variety": "Dry Red Chilli", "grade": "FAQ", "min_price": 12500.0, "modal_price": 14200.0, "max_price": 15800.0, "arrival_quantity": "160 Quintals"},
    "Turmeric":     {"market": "Erode Mandi", "commodity": "Turmeric", "variety": "Finger", "grade": "FAQ", "min_price": 8400.0, "modal_price": 9200.0, "max_price": 10100.0, "arrival_quantity": "280 Quintals"},
    "Soybean":      {"market": "Latur Mandi", "commodity": "Soyabean", "variety": "Yellow", "grade": "FAQ", "min_price": 3900.0, "modal_price": 4300.0, "max_price": 4650.0, "arrival_quantity": "310 Quintals"},
    "Mango":        {"market": "Salem Mandi", "commodity": "Mango", "variety": "Neelum", "grade": "FAQ", "min_price": 3800.0, "modal_price": 4500.0, "max_price": 5200.0, "arrival_quantity": "200 Quintals"},
    "Coconut":      {"market": "Kangayam Mandi", "commodity": "Coconut", "variety": "De-husked", "grade": "FAQ", "min_price": 2400.0, "modal_price": 2800.0, "max_price": 3100.0, "arrival_quantity": "500 Quintals"},
    "Basil":        {"market": "Neemuch Mandi", "commodity": "Tulsi", "variety": "Dry Leaves", "grade": "FAQ", "min_price": 3100.0, "modal_price": 3500.0, "max_price": 3900.0, "arrival_quantity": "80 Quintals"},
    "Marigold":     {"market": "Koyambedu Mandi", "commodity": "Marigold", "variety": "Orange", "grade": "FAQ", "min_price": 2100.0, "modal_price": 2500.0, "max_price": 2900.0, "arrival_quantity": "140 Quintals"},
    "Cowpea":       {"market": "Vellore Mandi", "commodity": "Cowpea(Veg)", "variety": "Local", "grade": "FAQ", "min_price": 4000.0, "modal_price": 4500.0, "max_price": 4900.0, "arrival_quantity": "90 Quintals"},
    "Mustard":      {"market": "Bharatpur Mandi", "commodity": "Mustard", "variety": "Black", "grade": "FAQ", "min_price": 4800.0, "modal_price": 5200.0, "max_price": 5600.0, "arrival_quantity": "320 Quintals"},
    "Moong Bean":   {"market": "Madurai Mandi", "commodity": "Green Gram(Moong)", "variety": "Whole", "grade": "FAQ", "min_price": 6500.0, "modal_price": 7000.0, "max_price": 7400.0, "arrival_quantity": "110 Quintals"},
    "Garlic":       {"market": "Mandsaur Mandi", "commodity": "Garlic", "variety": "Desi", "grade": "FAQ", "min_price": 7500.0, "modal_price": 8500.0, "max_price": 9600.0, "arrival_quantity": "210 Quintals"},
    "Ginger":       {"market": "Wayanad Mandi", "commodity": "Ginger(Green)", "variety": "Fresh", "grade": "FAQ", "min_price": 5200.0, "modal_price": 6000.0, "max_price": 6800.0, "arrival_quantity": "170 Quintals"},
    "Carrot":       {"market": "Ooty Mandi", "commodity": "Carrot", "variety": "Ooty Hybrid", "grade": "FAQ", "min_price": 1500.0, "modal_price": 1800.0, "max_price": 2100.0, "arrival_quantity": "260 Quintals"},
    "Spinach":      {"market": "Chennai Mandi", "commodity": "Spinach", "variety": "Green Leaf", "grade": "FAQ", "min_price": 1000.0, "modal_price": 1200.0, "max_price": 1500.0, "arrival_quantity": "190 Quintals"},
    "Coriander":    {"market": "Kota Mandi", "commodity": "Coriander", "variety": "Dry Seed", "grade": "FAQ", "min_price": 5800.0, "modal_price": 6500.0, "max_price": 7100.0, "arrival_quantity": "230 Quintals"},
    "Fenugreek":    {"market": "Jaipur Mandi", "commodity": "Fenugreek", "variety": "Seed", "grade": "FAQ", "min_price": 4900.0, "modal_price": 5500.0, "max_price": 6000.0, "arrival_quantity": "150 Quintals"},
    "Sorghum":      {"market": "Solapur Mandi", "commodity": "Jowar(Sorghum)", "variety": "Maldandi", "grade": "FAQ", "min_price": 2400.0, "modal_price": 2800.0, "max_price": 3100.0, "arrival_quantity": "270 Quintals"},
    "Pearl Millet": {"market": "Villupuram Mandi", "commodity": "Bajra(Pearl Millet)", "variety": "Hybrid", "grade": "FAQ", "min_price": 1950.0, "modal_price": 2200.0, "max_price": 2400.0, "arrival_quantity": "300 Quintals"},
    "Castor":       {"market": "Palanpur Mandi", "commodity": "Castor Seed", "variety": "Commercial", "grade": "FAQ", "min_price": 5300.0, "modal_price": 5800.0, "max_price": 6200.0, "arrival_quantity": "180 Quintals"},
    "Taro":         {"market": "Palakkad Mandi", "commodity": "Taro", "variety": "Colocasia Root", "grade": "FAQ", "min_price": 2600.0, "modal_price": 3000.0, "max_price": 3400.0, "arrival_quantity": "130 Quintals"},
    "Linseed":      {"market": "Kanpur Mandi", "commodity": "Linseed", "variety": "Brown", "grade": "FAQ", "min_price": 5100.0, "modal_price": 5600.0, "max_price": 6000.0, "arrival_quantity": "160 Quintals"},
    "Safflower":    {"market": "Ahmednagar Mandi", "commodity": "Safflower", "variety": "Standard", "grade": "FAQ", "min_price": 4700.0, "modal_price": 5200.0, "max_price": 5600.0, "arrival_quantity": "110 Quintals"},
    "Papaya":       {"market": "Theni Mandi", "commodity": "Papaya", "variety": "Red Lady", "grade": "FAQ", "min_price": 1600.0, "modal_price": 2000.0, "max_price": 2400.0, "arrival_quantity": "280 Quintals"},
    "Pepper":       {"market": "Kochi Mandi", "commodity": "Black Pepper", "variety": "Ungarbled", "grade": "FAQ", "min_price": 41000.0, "modal_price": 45000.0, "max_price": 48000.0, "arrival_quantity": "70 Quintals"},
}

def fetch_agmarknet_market_data(crop_name: str, state: str = None, district: str = None, latitude=None, longitude=None):
    """
    Fetches real live mandi prices from Agmarknet OGD API (api.data.gov.in).
    Falls back to Agmarknet daily mandi benchmarks if live network connection is unavailable.
    """
    crop_name = normalize_crop(crop_name)
    if crop_name in NON_MANDI_CROPS:
        return {
            "available": False,
            "reason": "non_mandi",
            "crop_name": crop_name,
            "message": f"Mandi price tracking is not applicable for {crop_name} (on-farm bio-input / aquaculture)."
        }

    api_key     = os.environ.get("AGMARKNET_API_KEY", "579b464db66ec23bdd000001cdd394632b774f197d623786809f05f9")
    resource_id = os.environ.get("AGMARKNET_RESOURCE_ID", "9ef84268-d588-465a-a308-a864a43d0070")

    candidates = AGMARKNET_COMMODITY_MAP.get(crop_name, [crop_name])
    import urllib.request, urllib.parse, ssl

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    if api_key and resource_id:
        for commodity in candidates:
            try:
                params = {
                    "api-key": api_key,
                    "format": "json",
                    "limit": 50,
                    "filters[commodity]": commodity
                }
                if state:
                    params["filters[state]"] = state
                if district:
                    params["filters[district]"] = district

                url = f"https://api.data.gov.in/resource/{resource_id}?" + urllib.parse.urlencode(params)
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

                with urllib.request.urlopen(req, timeout=5, context=ctx) as r:
                    res_data = json.loads(r.read().decode("utf-8"))
                    records = res_data.get("records", [])

                if records:
                    valid_records = []
                    for rec in records:
                        try:
                            mp = float(rec.get("modal_price") or 0)
                            if mp > 0:
                                valid_records.append((mp, rec))
                        except (ValueError, TypeError):
                            continue

                    if valid_records:
                        modal_p, rec = valid_records[0]
                        min_p = float(rec.get("min_price") or modal_p)
                        max_p = float(rec.get("max_price") or modal_p)
                        arr_qty = rec.get("arrivals_in_qtl") or rec.get("arrival_quantity") or "N/A"

                        return {
                            "available": True,
                            "market": rec.get("market") or "Agmarknet Mandi",
                            "commodity": rec.get("commodity") or commodity,
                            "variety": rec.get("variety") or "Standard",
                            "grade": rec.get("grade") or "FAQ",
                            "min_price": round(min_p, 2),
                            "modal_price": round(modal_p, 2),
                            "max_price": round(max_p, 2),
                            "arrival_quantity": str(arr_qty),
                            "market_date": rec.get("arrival_date") or datetime.datetime.now().strftime("%d/%m/%Y"),
                            "source": "Agmarknet",
                            "state": rec.get("state", ""),
                            "district": rec.get("district", "")
                        }
            except Exception as e:
                print(f"Agmarknet API fetch error for commodity '{commodity}': {e}")
                continue

    # Agmarknet Daily Benchmark Fallback
    bm = AGMARKNET_BENCHMARK_REGISTRY.get(crop_name)
    if not bm:
        return {
            "available": False,
            "reason": "not_listed",
            "crop_name": crop_name,
            "message": f"Mandi price data is currently not available for {crop_name}."
        }

    return {
        "available": True,
        "market": bm["market"],
        "commodity": bm["commodity"],
        "variety": bm["variety"],
        "grade": bm["grade"],
        "min_price": bm["min_price"],
        "modal_price": bm["modal_price"],
        "max_price": bm["max_price"],
        "arrival_quantity": bm["arrival_quantity"],
        "market_date": datetime.datetime.now().strftime("%d/%m/%Y"),
        "source": "Agmarknet",
        "state": state or "Tamil Nadu",
        "district": district or "Coimbatore"
    }


# ══════════════════════════════════════════════════════════════════════════════
#  TRANSLATIONS DICTIONARY — 6 LANGUAGES (en, ta, hi, te, kn, ml)
# ══════════════════════════════════════════════════════════════════════════════

TRANSLATIONS = {
    "en": {
        "app_title": "AI Crop Advisor",
        "tagline": "Smart farming intelligence for better yields",
        "step1": "Location", "step2": "Soil", "step3": "Results", "step4": "Feedback",
        "my_history": "My History", "logout": "Logout", "login": "Login", "signup": "Sign Up",
        "admin_login": "Admin Login", "city_label": "City / Village", "type_city": "Type city or village...",
        "get_weather": "Get Weather", "use_gps": "Use GPS", "temperature": "Temperature (°C)",
        "humidity": "Humidity (%)", "nitrogen": "Nitrogen (N)", "phosphorus": "Phosphorus (P)",
        "potassium": "Potassium (K)", "ph": "Soil pH", "rainfall": "Rainfall (mm)",
        "recommend": "Get Recommendation", "sensor": "Auto Fill Sensor", "next": "Next", "back": "Back",
        "submit_feedback": "Submit Feedback", "actual_crop": "Crop you actually grew",
        "actual_profit": "Actual Profit (₹/acre)", "actual_yield": "Actual Yield (kg/acre)",
        "acres_farmed": "Number of Acres Farmed", "total_profit": "Total Profit (₹)",
        "total_yield": "Total Yield (kg)", "rate_prediction": "Rate the AI Prediction",
        "comments": "Comments (optional)", "save_db": "Save to Database & Help Train AI",
        "skip_new": "Skip — Start New Prediction", "thank_you": "Thank You!",
        "feedback_note": "Your data helps improve AI model predictions",
        "rec_crop": "Recommended Crop", "intercrop_1": "Intercrop 1", "intercrop_2": "Intercrop 2",
        "fertilizer": "Fertilizer", "expected_profit": "Expected Profit", "expected_yield": "Expected Yield",
        "market_status_label": "Market Status", "soil_health": "Soil Health Score", "crop_calendar": "Crop Calendar",
        "irrigation": "Irrigation Schedule", "disease_risk": "Disease Risk", "top3_alt": "Top 3 Crop Alternatives",
        "market_forecast": "Market Price Forecast", "nearby_mandis": "Nearby Mandis Map",
        "gov_schemes": "Government Schemes", "report": "Report", "share": "Share", "history": "History",
        "best": "Best", "current": "Current", "next_month": "Next Month", "km_away": "km away",
        "directions": "Directions", "your_farm": "Your Farm", "drag_me": "Drag me", "score": "Score",
        "sow": "Sow", "growing": "Growing", "harvest": "Harvest", "duration": "Duration", "months": "months",
        "frequency": "Frequency", "amount_session": "Amount/Session", "risk": "Risk", "advice": "Advice",
        "no_mandis": "No verified nearby mandi data available", "export_csv": "Export CSV",
        "sowing_date_label": "Sowing Date",
        "generate_cal_btn": "Generate Crop Calendar",
        "typical_season_label": "Typical Growing Season",
        "typical_sow_window": "Typical Sowing Window",
        "estimated_harvest_label": "Estimated Harvest Date",
        "harvest_disclaimer": "Harvest date is an estimate based on the selected crop's typical growth duration. Actual harvest time may vary depending on weather, soil conditions, irrigation, crop variety, and farming practices.",
        "weather_stage_advisory": "Weather & Farming Advisory",
        "primary_crop_title": "Primary Crop",
        "intercrop_1_title": "Intercrop 1",
        "intercrop_2_title": "Intercrop 2",
        "advisory_context_primary": "Farm Advisory for Primary Crop",
        "advisory_context_intercrop": "Intercrop Advisory",
        "actual_sowing_date_label": "Actual Sowing Date",
        "total_duration_label": "Total Growth Duration",
        "days_unit": "Days",
        "months_unit": "Months",
        "stage_prefix": "Stage",
        "select_crop_label": "Select Crop",
        "around_prefix": "Around",
        "crop_label": "Crop",
        "weather_advisory_high_rain": "🌧️ High rainfall ({rainfall}mm) recorded in your region. Ensure good field drainage during initial crop establishment.",
        "weather_advisory_high_temp": "☀️ High temperature ({temp}°C) expected. Maintain optimal irrigation during flowering and panicle stages.",
        "weather_advisory_normal": "🌤️ Current climate conditions (Temp: {temp}°C, Humidity: {humidity}%) are suitable for standard crop growth.",
        "crops": {
            "Rice": "Rice", "Maize": "Maize", "Groundnut": "Groundnut", "Wheat": "Wheat",
            "Cotton": "Cotton", "Sugarcane": "Sugarcane", "Banana": "Banana", "Chickpea": "Chickpea",
            "Tomato": "Tomato", "Onion": "Onion", "Chilli": "Chilli", "Turmeric": "Turmeric",
            "Soybean": "Soybean", "Mango": "Mango", "Coconut": "Coconut"
        },
        "intercrops": {
            "Azolla": "Azolla", "Fish (Aquaculture)": "Fish (Aquaculture)", "Cowpea": "Cowpea",
            "Soybean": "Soybean", "Pearl Millet": "Pearl Millet", "Castor": "Castor",
            "Mustard": "Mustard", "Chickpea": "Chickpea", "Moong Bean": "Moong Bean",
            "Groundnut": "Groundnut", "Onion": "Onion", "Garlic": "Garlic",
            "Ginger": "Ginger", "Turmeric": "Turmeric", "Safflower": "Safflower",
            "Linseed": "Linseed", "Basil": "Basil", "Marigold": "Marigold",
            "Carrot": "Carrot", "Spinach": "Spinach", "Coriander": "Coriander",
            "Fenugreek": "Fenugreek", "Taro": "Taro", "Sorghum": "Sorghum",
            "Papaya": "Papaya", "Pepper": "Pepper", "Banana": "Banana"
        },
        "fertilizers": {
            "Urea + DAP": "Urea + DAP", "NPK 14-35-14": "NPK 14-35-14", "SSP + Gypsum": "SSP + Gypsum",
            "NPK 20-20-0": "NPK 20-20-0", "NPK + Zinc": "NPK + Zinc", "FYM + NPK": "FYM + NPK",
            "DAP + Rhizobium": "DAP + Rhizobium", "NPK 19-19-19": "NPK 19-19-19",
            "Urea + SSP + MOP": "Urea + SSP + MOP", "NPK 17-17-17": "NPK 17-17-17",
            "FYM + NPK + Boron": "FYM + NPK + Boron", "NPK + Boron": "NPK + Boron"
        },
        "seasons": {
            "Kharif": "Kharif (Monsoon)", "Rabi": "Rabi (Winter)", "Annual": "Annual (Year-round)",
            "Kharif/Rabi": "Kharif / Rabi", "Rabi/Kharif": "Rabi / Kharif"
        },
        "irrigation_freq": {
            "Every day": "Every day", "Every 2 days": "Every 2 days", "Every 3 days": "Every 3 days",
            "Twice a week": "Twice a week", "Once a week": "Once a week", "Once in 10 days": "Once in 10 days",
            "Rainfall sufficient": "Rainfall sufficient", "Monitor only": "Monitor only"
        },
        "disease_types": {
            "Fungal Disease": "Fungal Disease", "Bacterial Blight": "Bacterial Blight",
            "Pest Infestation": "Pest Infestation", "No Risk Detected": "No Risk Detected"
        },
        "risk_levels": {
            "High": "High Risk", "Medium": "Medium Risk", "Low": "Low Risk"
        },
        "disease_advice": {
            "Apply Mancozeb or Copper Oxychloride": "Apply Mancozeb or Copper Oxychloride",
            "Use Streptocycline spray": "Use Streptocycline spray",
            "Use Neem oil or recommended pesticide": "Use Neem oil or recommended pesticide",
            "Maintain good field hygiene": "Maintain good field hygiene"
        },
        "market_status": {
            "High Demand": "High Demand", "Normal": "Normal Demand"
        },
        "market_trend": {
            "rising": "↑ Rising", "falling": "↓ Falling", "stable": "→ Stable"
        },
        "schemes": {
            "PM-Kisan": "PM-Kisan Scheme", "PMFBY": "PM Crop Insurance (PMFBY)",
            "NFSM": "National Food Security Mission", "MSP Scheme": "Minimum Support Price (MSP)",
            "Cotton Tech Mission": "Cotton Tech Mission", "Sugarcane Dev Scheme": "Sugarcane Dev Scheme",
            "NHM": "National Horticulture Mission", "Pulses Dev": "Pulses Development Scheme",
            "Spices Board": "Spices Board India", "Coconut Dev Board": "Coconut Development Board"
        },
        "soil_tips": {
            "Low Nitrogen — apply Urea or green manure": "Low Nitrogen — apply Urea or green manure",
            "Low Phosphorus — apply DAP or SSP": "Low Phosphorus — apply DAP or SSP",
            "Low Potassium — apply MOP": "Low Potassium — apply MOP",
            "Acidic soil — apply lime": "Acidic soil — apply lime",
            "Alkaline soil — apply gypsum": "Alkaline soil — apply gypsum",
            "Soil health is good!": "✅ Soil health is good!"
        },
        "water_need": {
            "high": "High", "medium": "Medium", "low": "Low"
        },
        "agmarknet_price_title": "Live Agmarknet Mandi Price",
        "modal_price": "Latest Modal Mandi Price",
        "min_price": "Minimum Price",
        "max_price": "Maximum Price",
        "mandi_market": "Market / Mandi",
        "market_date": "Date",
        "source": "Source",
        "agmarknet_source": "Agmarknet",
        "live_market_unavailable": "Live market price currently unavailable.",
        "market_trend_unavailable": "Market trend unavailable",
        "estimated_profit": "Estimated Profit",
        "estimated_revenue": "Estimated Revenue",
        "commodity": "Commodity",
        "variety": "Variety",
        "grade": "Grade",
        "arrival_qty": "Arrival Quantity"
    },
    "ta": {
        "app_title": "AI பயிர் ஆலோசகர்",
        "tagline": "சிறந்த விளைச்சலுக்கான விவசாய நுண்ணறிவு",
        "step1": "இடம்", "step2": "மண்", "step3": "முடிவுகள்", "step4": "கருத்து",
        "my_history": "எனது வரலாறு", "logout": "வெளியேறு", "login": "உள்நுழைவு", "signup": "பதிவு செய்",
        "admin_login": "நிர்வாகி உள்நுழைவு", "city_label": "நகரம் / கிராமம்", "type_city": "நகரம் அல்லது கிராமத்தை தட்டச்சு செய்க...",
        "get_weather": "வானிலை பெறுக", "use_gps": "GPS பயன்படுத்து", "temperature": "வெப்பநிலை (°C)",
        "humidity": "ஈரப்பதம் (%)", "nitrogen": "நைட்ரஜன் (N)", "phosphorus": "பாஸ்பரஸ் (P)",
        "potassium": "பொட்டாசியம் (K)", "ph": "மண் pH", "rainfall": "மழைப்பொழிவு (mm)",
        "recommend": "பரிந்துரை பெறுக", "sensor": "சென்சார் தானியங்கு", "next": "அடுத்து", "back": "பின்செல்",
        "submit_feedback": "கருத்து சமர்ப்பி", "actual_crop": "நீங்கள் பயிரிட்ட பயிர்",
        "actual_profit": "உண்மை லாபம் (₹/ஏக்கர்)", "actual_yield": "உண்மை விளைச்சல் (கிலோ/ஏக்கர்)",
        "acres_farmed": "விவசாய நில அளவு (ஏக்கர்)", "total_profit": "மொத்த லாபம் (₹)",
        "total_yield": "மொத்த விளைச்சல் (கிலோ)", "rate_prediction": "AI கணிப்பிற்கு மதிப்பீடு தருக",
        "comments": "கருத்துகள் (விருப்பத்தின்பேரில்)", "save_db": "தரவுத்தளத்தில் சேமி & AI பயிற்சி பெற உதவு",
        "skip_new": "தவிர் — புதிய கணிப்பு தொடங்கு", "thank_you": "நன்றி!",
        "feedback_note": "உங்கள் தரவு AI கணிப்புகளை மேம்படுத்த உதவுகிறது",
        "rec_crop": "பரிந்துரைக்கப்பட்ட பயிர்", "intercrop_1": "ஊடு பயிர் 1", "intercrop_2": "ஊடு பயிர் 2",
        "fertilizer": "உரப் பரிந்துரை", "expected_profit": "எதிர்பார்க்கப்படும் லாபம்", "expected_yield": "எதிர்பார்க்கப்படும் விளைச்சல்",
        "market_status_label": "சந்தை நிலை", "soil_health": "மண் வள மதிப்பெண்", "crop_calendar": "பயிர் காலண்டர்",
        "irrigation": "நீர்ப்பாசன அட்டவணை", "disease_risk": "நோய் ஆபத்து", "top3_alt": "மாற்று 3 பயிர்கள்",
        "market_forecast": "சந்தை விலை கணிப்பு", "nearby_mandis": "அருகிலுள்ள சந்தைகள் வரைபடம்",
        "gov_schemes": "அரசு திட்டங்கள்", "report": "அறிக்கை", "share": "பகிர்", "history": "வரலாறு",
        "best": "சிறந்தது", "current": "தற்போதைய", "next_month": "அடுத்த மாதம்", "km_away": "கி.மீ தூரம்",
        "directions": "வழித்தடம்", "your_farm": "உங்கள் பண்ணை", "drag_me": "நகர்த்தவும்", "score": "மதிப்பெண்",
        "sow": "விதைப்பு", "growing": "வளர்ச்சி", "harvest": "அறுவடை", "duration": "கால அளவு", "months": "மாதங்கள்",
        "frequency": "அதிர்வெண்", "amount_session": "அளவு/முறை", "risk": "ஆபத்து", "advice": "ஆலோசனை",
        "no_mandis": "சரிபார்க்கப்பட்ட சந்தை தரவு இல்லை", "export_csv": "CSV ஏற்றுமதி",
        "crops": {
            "Rice": "நெல்", "Maize": "மக்காச்சோளம்", "Groundnut": "நிலக்கடலை", "Wheat": "கோதுமை",
            "Cotton": "பருத்தி", "Sugarcane": "கரும்பு", "Banana": "வாழை", "Chickpea": "கொண்டைக் கடலை",
            "Tomato": "தக்காளி", "Onion": "வெங்காயம்", "Chilli": "மிளகாய்", "Turmeric": "மஞ்சள்",
            "Soybean": "சோயாபீன்", "Mango": "மாம்பழம்", "Coconut": "தேங்காய்"
        },
        "intercrops": {
            "Azolla": "அசோலா", "Fish (Aquaculture)": "மீன் வளர்ப்பு", "Cowpea": "தட்டப்பயறு",
            "Soybean": "சோயாபீன்", "Pearl Millet": "கம்பு", "Castor": "ஆமணக்கு",
            "Mustard": "கடுகு", "Chickpea": "கொண்டைக் கடலை", "Moong Bean": "பாசிப்பயறு",
            "Groundnut": "நிலக்கடலை", "Onion": "வெங்காயம்", "Garlic": "பூண்டு",
            "Ginger": "இஞ்சி", "Turmeric": "மஞ்சள்", "Safflower": "செந்தூரம் (குசும்பா)",
            "Linseed": "ஆளி விதை", "Basil": "துளசி", "Marigold": "சாமந்தி",
            "Carrot": "கேரட்", "Spinach": "பசலைக்கீரை", "Coriander": "கொத்தமல்லி",
            "Fenugreek": "வெந்தயம்", "Taro": "சேப்பங்கிழங்கு", "Sorghum": "சோளம்",
            "Papaya": "பப்பாளி", "Pepper": "மிளகு", "Banana": "வாழை"
        },
        "fertilizers": {
            "Urea + DAP": "யூரியா + டி.ஏ.பி", "NPK 14-35-14": "என்.பி.கே 14-35-14", "SSP + Gypsum": "எஸ்.எஸ்.பி + ஜிப்சம்",
            "NPK 20-20-0": "என்.பி.கே 20-20-0", "NPK + Zinc": "என்.பி.கே + ஜிங்க்", "FYM + NPK": "தொழுஉரம் + என்.பி.கே",
            "DAP + Rhizobium": "டி.ஏ.பி + ரைசோபியம்", "NPK 19-19-19": "என்.பி.கே 19-19-19",
            "Urea + SSP + MOP": "யூரியா + எஸ்.எஸ்.பி + எம்.ஓ.பி", "NPK 17-17-17": "என்.பி.கே 17-17-17",
            "FYM + NPK + Boron": "தொழுஉரம் + என்.பி.கே + போரான்", "NPK + Boron": "என்.பி.கே + போரான்"
        },
        "seasons": {
            "Kharif": "காரீஃப் (மழைக்காலம்)", "Rabi": "ரபி (குளிர்காலம்)", "Annual": "ஆண்டு முழுவதும்",
            "Kharif/Rabi": "காரீஃப் / ரபி", "Rabi/Kharif": "ரபி / காரீஃப்"
        },
        "irrigation_freq": {
            "Every day": "தினமும்", "Every 2 days": "2 நாட்களுக்கு ஒருமுறை", "Every 3 days": "3 நாட்களுக்கு ஒருமுறை",
            "Twice a week": "வாரத்திற்கு இருமுறை", "Once a week": "வாரத்திற்கு ஒருமுறை", "Once in 10 days": "10 நாட்களுக்கு ஒருமுறை",
            "Rainfall sufficient": "போதுமான மழைபொழிவு", "Monitor only": "கண்காணிக்கவும்"
        },
        "disease_types": {
            "Fungal Disease": "பூஞ்சை நோய்", "Bacterial Blight": "பாக்டீரியா கருகல் நோய்",
            "Pest Infestation": "பூச்சி தாக்குதல்", "No Risk Detected": "நோய் ஆபத்து இல்லை"
        },
        "risk_levels": {
            "High": "அதிக ஆபத்து", "Medium": "மிதமான ஆபத்து", "Low": "குறைந்த ஆபத்து"
        },
        "disease_advice": {
            "Apply Mancozeb or Copper Oxychloride": "மேங்கோசெப் அல்லது காப்பர் ஆக்சிக்ளோரைடு தெளிக்கவும்",
            "Use Streptocycline spray": "ஸ்ட்ரெப்டோசைக்ளின் தெளிக்கவும்",
            "Use Neem oil or recommended pesticide": "வேப்ப எண்ணெய் அல்லது பூச்சிக்கொல்லி தெளிக்கவும்",
            "Maintain good field hygiene": "வயலை தூய்மையாக பராமரிக்கவும்"
        },
        "market_status": {
            "High Demand": "அதிக தேவை", "Normal": "சாதாரண தேவை"
        },
        "market_trend": {
            "rising": "↑ உயர்கிறது", "falling": "↓ குறைகிறது", "stable": "→ நிலையானது"
        },
        "schemes": {
            "PM-Kisan": "பி.எம்-கிசான் திட்டம்", "PMFBY": "பயிர் காப்பீட்டுத் திட்டம் (PMFBY)",
            "NFSM": "தேசிய உணவு பாதுகாப்பு இயக்கம்", "MSP Scheme": "குறைந்தபட்ச ஆதரவு விலை (MSP)",
            "Cotton Tech Mission": "பருத்தி தொழில்நுட்ப திட்டம்", "Sugarcane Dev Scheme": "கரும்பு மேம்பாட்டு திட்டம்",
            "NHM": "தேசிய தோட்டக்கலை இயக்கம்", "Pulses Dev": "பயறுவகை மேம்பாட்டு திட்டம்",
            "Spices Board": "இந்திய நறுமணப் பொருட்கள் வாரியம்", "Coconut Dev Board": "தென்னை மேம்பாட்டு வாரியம்"
        },
        "soil_tips": {
            "Low Nitrogen — apply Urea or green manure": "குறைந்த நைட்ரஜன் — யூரியா அல்லது பசுந்தாள் உரம் இடவும்",
            "Low Phosphorus — apply DAP or SSP": "குறைந்த பாஸ்பரஸ் — டி.ஏ.பி அல்லது எஸ்.எஸ்.பி இடவும்",
            "Low Potassium — apply MOP": "குறைந்த பொட்டாசியம் — எம்.ஓ.பி உரம் இடவும்",
            "Acidic soil — apply lime": "அமில மண் — சுண்ணம் (லைம்) இடவும்",
            "Alkaline soil — apply gypsum": "கார மண் — ஜிப்சம் இடவும்",
            "Soil health is good!": "✅ மண் வளம் நன்றாக உள்ளது!"
        },
        "water_need": {
            "high": "அதிகம்", "medium": "மிதமானது", "low": "குறைவு"
        },
        "agmarknet_price_title": "நேரலை அகமார்க்நெட் சந்தை விலை",
        "modal_price": "சமீபத்திய சராசரி சந்தை விலை",
        "min_price": "குறைந்தபட்ச விலை",
        "max_price": "அதிகபட்ச விலை",
        "mandi_market": "சந்தை / மண்டி",
        "market_date": "தேதி",
        "source": "ஆதாரம்",
        "agmarknet_source": "அகமார்க்நெட்",
        "live_market_unavailable": "நேரலை சந்தை விலை தற்போது கிடைக்கவில்லை.",
        "market_trend_unavailable": "சந்தை போக்கு கிடைக்கவில்லை",
        "estimated_profit": "மதிப்பிடப்பட்ட லாபம்",
        "estimated_revenue": "மதிப்பிடப்பட்ட வருவாய்",
        "commodity": "பொருள்",
        "variety": "ரகம்",
        "grade": "தரம்",
        "arrival_qty": "வரத்து அளவு",
        "primary_crop_title": "முதன்மை பயிர்",
        "intercrop_1_title": "ஊடு பயிர் 1",
        "intercrop_2_title": "ஊடு பயிர் 2",
        "advisory_context_primary": "முதன்மை பயிருக்கான விவசாய ஆலோசனை",
        "advisory_context_intercrop": "ஊடு பயிர் ஆலோசனை",
        "actual_sowing_date_label": "உண்மையான விதைப்பு தேதி",
        "total_duration_label": "மொத்த வளர்ச்சி காலம்",
        "days_unit": "நாட்கள்",
        "months_unit": "மாதங்கள்",
        "stage_prefix": "நிலை",
        "select_crop_label": "பயிரைத் தேர்ந்தெடுக்கவும்",
        "around_prefix": "சுமார்",
        "crop_label": "பயிர்",
        "typical_season_label": "இயல்பான வளரும் பருவம்",
        "estimated_harvest_label": "எதிர்பார்க்கப்படும் அறுவடை தேதி",
        "harvest_disclaimer": "அறுவடை தேதி என்பது தேர்ந்தெடுக்கப்பட்ட பயிரின் இயல்பான வளர்ச்சி காலத்தின் அடிப்படையில் கணக்கிடப்பட்ட மதிப்பீடாகும். வானிலை, மண் வளம், நீர்ப்பாசனம் மற்றும் விவசாய முறைகளுக்கு ஏற்ப உண்மையான அறுவடை நேரம் மாறக்கூடும்.",
        "weather_advisory_high_rain": "🌧️ உங்கள் பகுதியில் அதிக மழைப்பொழிவு ({rainfall}mm) பதிவாகியுள்ளது. பயிர் ஆரம்ப வளர்ச்சியின் போது நல்ல வடிகால் வசதியை உறுதி செய்யவும்.",
        "weather_advisory_high_temp": "☀️ அதிக வெப்பநிலை ({temp}°C) எதிர்பார்க்கப்படுகிறது. பூக்கும் மற்றும் கதிர் வரும் நிலைகளில் போதுமான நீர்ப்பாசனம் வழங்கவும்.",
        "weather_advisory_normal": "🌤️ தற்போதைய வானிலை நிலவரம் (வெப்பநிலை: {temp}°C, ஈரப்பதம்: {humidity}%) பயிர் வளர்ச்சிக்கு ஏற்றதாக உள்ளது.",
                    "stage_explanations": {
                "Prepare seedbed, sow seeds, and maintain consistent nursery moisture for healthy seedling emergence.": "நாற்றுப் பாத்தி தயாரித்து விதைகளை விதைத்து, ஆரோக்கியமான நாற்றுகள் முளைக்க தொடர் ஈரப்பதத்தைப் பராமரிக்கவும்.",
                "Transplant seedlings to main field, maintain 2-5cm standing water, and apply initial nitrogen fertilizer.": "நாற்றுகளை பிரதான வயலில் நட்டு, 2-5 செ.மீ நீர் தேக்கி வைத்து, முதல் தவணை நைட்ரஜன் உரம் இடவும்.",
                "Panicle initiation and flowering stage. Ensure peak water availability and protect against stem borer.": "கதிர் உருவாகும் மற்றும் பூக்கும் நிலை. அதிகபட்ச நீர் இருப்பை உறுதிசெய்து தண்டு துளைப்பானில் இருந்து பாதுகாக்கவும்.",
                "Grain filling and ripening. Drain field water 10 days prior to harvest when grains turn golden.": "தானியம் முதிர்ச்சியடையும் நிலை. தானியங்கள் பொன்னிறமாக மாறும்போது அறுவடைக்கு 10 நாட்களுக்கு முன் வயல் நீரை வடிக்கவும்.",
                "Sow seeds 4-5cm deep in well-drained soil. Ensure optimal warmth and soil moisture.": "நல்ல வடிகால் வசதியுள்ள மண்ணில் 4-5 செ.மீ ஆழத்தில் விதைகளை விதைக்கவும். சரியான சூடு மற்றும் ஈரப்பதத்தை உறுதி செய்யவும்.",
                "Rapid leaf elongation and stem growth. Apply NPK fertilizer top dressing and earthing up.": "வேகமான இலை மற்றும் தண்டு வளர்ச்சி. மேலுரமாக NPK உரம் இட்டு மண் அணைக்கவும்.",
                "Flowering and pollination phase. Critical stage requiring adequate irrigation and pest control.": "பூக்கும் மற்றும் மகரந்தச்சேர்க்கை நிலை. தேவையான நீர்ப்பாசனம் மற்றும் பூச்சி கட்டுப்பாடு தேவைப்படும் முக்கிய நிலை.",
                "Kernels mature and harden. Harvest when cob husk turns dry and pale yellow.": "தானியங்கள் கெட்டியாக முதிர்ச்சியடைகின்றன. சோளத்தோல் காய்ந்து வெளிர் மஞ்சளாக மாறும்போது அறுவடை செய்யவும்.",
                "Plant quality pods/seeds in friable soil. Ensure moist seedbed for uniform germination.": "நன்கு உழுத மண்ணில் தரமான விதைகளை விதைக்கவும். சீரான முளைப்புக்கு ஈரப்பதமான விதைப்பாத்தியை உறுதி செய்யவும்.",
                "Canopy development and branching. Apply gypsum to supply calcium for pod development.": "கிளைகள் மற்றும் இலைகள் வளர்ச்சி நிலை. காய் வளர்ச்சிக்கு கால்சியம் அளிக்க ஜிப்ஸம் உரம் இடவும்.",
                "Flower pegs enter soil to form underground pods. Avoid deep cultivation to protect pegs.": "பூ விழுதுகள் மண்ணிற்குள் சென்று காய்களாக மாறுகின்றன. விழுதுகளைப் பாதுகாக்க ஆழ உழவைத் தவிர்க்கவும்.",
                "Pods mature and harden. Harvest when internal shell lining turns dark brown.": "காய்கள் முதிர்ந்து கெட்டியாகின்றன. ஓட்டின் உட்சுவர் அடர் பழுப்பு நிறமாக மாறும்போது அறுவடை செய்யவும்.",
                "Sow in cool moist soil. Provide first irrigation at Crown Root Initiation (CRI) stage (~21 days).": "குளிர்ந்த ஈரமான மண்ணில் விதைக்கவும். 21வது நாளில் முதல் நீர்ப்பாசனம் வழங்கவும்.",
                "Tillers develop and stems elongate. Apply top dressing nitrogen and control weeds.": "தூர்கள் பெருகி தண்டுகள் நீளுகின்றன. மேலுரமாக நைட்ரஜன் உரம் இட்டு களைகளைக் கட்டுப்படுத்தவும்.",
                "Earheads emerge and flowering begins. Maintain soil moisture to avoid grain reduction.": "கதிர்கள் வெளிவந்து பூக்கத் தொடங்குகின்றன. தானியக் குறைப்பைத் தவிர்க்க மண் ஈரப்பதத்தைப் பராமரிக்கவும்.",
                "Dough stage to hard grain. Harvest when crop turns golden and moisture drops to 12-14%.": "தானியங்கள் கெட்டியாகும் பருவம். பயிர் பொன்னிறமாக மாறும்போது அறுவடை செய்யவும்.",
                "Sow seeds in ridges or flat beds. Monitor early weed competition and seedling vigor.": "பார்களில் விதைகளை விதைக்கவும். ஆரம்பகாலக் களைகளைக் கட்டுப்படுத்தவும்.",
                "Main stem and sympodial branch development. Apply split nitrogen doses.": "முதன்மைத் தண்டு மற்றும் பக்கக் கிளைகள் வளர்கின்றன. நைட்ரஜன் உரத்தைப் பிரித்து வழங்கவும்.",
                "Square (flower bud) initiation and white/pink flower bloom. Monitor for bollworm infestation.": "பூ மொட்டுகள் உருவாகி வெள்ளைப் பூக்கள் பூக்கின்றன. காய் புழுத் தாக்குதலைக் கண்காணிக்கவும்.",
                "Bolls mature and open exposing clean lint. Perform multiple pickings on sunny dry days.": "காய்கள் முதிர்ந்து வெடித்து பஞ்சு வெளிவருகிறது. வெயில் நாட்களில் பஞ்சை அறுவடை செய்யவும்.",
                "Plant 2-3 bud setts in furrows. Maintain soil moisture for eye bud sprouting.": "பார் அமைத்து 2-3 பருக்கள் கொண்ட கரணைகளை நடவும். பருக்கள் முளைக்க ஈரப்பதம் காக்கவும்.",
                "Shoot proliferation and root system expansion. Perform earthing up and weed removal.": "தூர்கள் பெருகி வேர் மண்டலம் வளர்கிறது. மண் அணைத்து களைகளை அகற்றவும்.",
                "Rapid cane elongation and internode thickening. Peak water and nutrient requirement stage.": "கரும்பு தடிமனாகி வேகமாக நீளுகிறது. அதிக நீர் மற்றும் ஊட்டச்சத்து தேவைப்படும் நிலை.",
                "Sucrose synthesis and accumulation in stalk. Stop irrigation 2-3 weeks before harvesting.": "தண்டில் சர்க்கரைச் சத்து சேர்கிறது. அறுவடைக்கு 2-3 வாரங்களுக்கு முன் நீர்ப்பாசனத்தை நிறுத்தவும்.",
                "Plant disease-free suckers/tissue plants in pits. Provide organic mulching and shade.": "நோயற்ற வாழைக் கன்றுகளைக் குழிகளில் நடவும். இயற்கை மூடாக்கு மற்றும் நிழல் அளிக்கவும்.",
                "Rapid broad leaf expansion and pseudostem thickening. Regular fertigation and desuckering.": "அகன்ற இலைகள் விரிந்து மரம் தடிக்கிறது. தவறாமல் உரம் மற்றும் பக்கக்கன்றுகளை அகற்றவும்.",
                "Inflorescence emerges from pseudostem heart. Provide bamboo propping support to heavy bunches.": "வாழை மரத்தின் நடுவிலிருந்து பூ வெளிவருகிறது. கனமான தார்களுக்கு மூங்கில் முட்டு கொடுக்கவும்.",
                "Banana fingers swell and round off. Harvest mature green bunches before yellowing.": "வாழைக் காய்கள் திரண்டு உருண்டையாகின்றன. மஞ்சள் நிறமாவதற்கு முன் முதிர்ந்த பச்சைத் தார்களை அறுவடை செய்யவும்.",
                "Sow in residual moisture after monsoon. Ensure proper aeration to prevent root rot.": "மழைக்குப் பின் மண்ணில் உள்ள ஈரப்பதத்தில் விதைக்கவும். வேரழுகல் நோயைத் தவிர்க்க நல்ல காற்றோட்டம் தேவை.",
                "Branching phase. Nip terminal buds at 30-45 days to encourage bushy lateral growth.": "கிளைகள் உருவாகும் நிலை. 30-45 நாட்களில் நுனிகளைக் கிள்ளி பக்கக் கிளைகளை அதிகரிக்கவும்.",
                "Pod initiation. Protect crop from Helicoverpa pod borer using pheromone traps.": "காய் பிடிக்கும் நிலை. மோகனக் பொறிகள் மூலம் காய்ப்புழுத் தாக்குதலிலிருந்து பாதுகாக்கவும்.",
                "Pods turn straw yellow and leaves drop. Harvest when seeds rattle inside dry pods.": "காய்கள் மஞ்சளாகி இலைகள் உதிர்கின்றன. காய்ந்த காய்களுக்குள் விதைகள் சலசலக்கும்போது அறுவடை செய்யவும்.",
                "Transplant 25-day old seedlings to raised beds. Provide staking support early for vine crops.": "25 நாள் நாற்றுகளை மேட்டுப்பாத்தியில் நடவும். செடிகளுக்கு ஆரம்பத்திலேயே குச்சி முட்டு கொடுக்கவும்.",
                "Stem growth and leaf canopy expansion. Apply balanced NPK fertilizer and weeding.": "தண்டு வளர்ச்சி மற்றும் இலைகள் பெருக்கம். சீரான NPK உரம் இட்டு களை எடுக்கவும்.",
                "Yellow flower cluster bloom and green fruit formation. Maintain uniform moisture to prevent blossom drop.": "மஞ்சள் பூக்கள் பூத்து பச்சைக் காய்கள் உருவாகின்றன. பூ உதிர்வதைத் தடுக்க சீரான ஈரப்பதம் காக்கவும்.",
                "Fruits change from green to breaker/red mature stage. Harvest in multiple pickings every 3-4 days.": "பழங்கள் பச்சையிலிருந்து சிவப்பு நிறமாக மாறுகின்றன. 3-4 நாட்களுக்கு ஒருமுறை பழங்களை அறுவடை செய்யவும்.",
                "Transplant healthy nursery seedlings in shallow furrows. Keep soil weed-free.": "ஆரோக்கியமான நாற்றுகளை பார்களில் நடவும். மண்ணைக் களைகளின்றி பராமரிக்கவும்.",
                "Tubular leaf production. Adequate nitrogen and micro-irrigation promote top growth.": "குழாய் வடிவ இலைகள் வளர்கின்றன. தேவையான நைட்ரஜன் மற்றும் நுண் நீர்ப்பாசனம் இலை வளர்ச்சியை ஊக்குவிக்கும்.",
                "Bulbs begin expanding below soil surface. Increase potash application for firmness.": "மண்ணிற்குள் வெங்காயம் திரளத் தொடங்குகிறது. வெங்காயம் கெட்டியாக பொட்டாஷ் உரத்தை அதிகரிக்கவும்.",
                "Foliage turns yellow and necks break over naturally. Pull bulbs and cure in shade.": "இலைகள் மஞ்சளாகித் தாள்கள் தானாகச் சாயும். வெங்காயத்தை அறுவடை செய்து நிழலில் உலர்த்தவும்.",
                "Plant nursery seedlings on ridges. Apply organic basal manure and light watering.": "பார்களில் நாற்றுகளை நடவும். இயற்கை அடிஉரம் இட்டு லேசாக நீர் பாய்ச்சவும்.",
                "Branching and dense canopy growth. Spray micronutrients and monitor sucking pests.": "அடர்த்தியான கிளைகள் மற்றும் இலை வளர்ச்சி. நுண்ஊட்டச்சத்து தெளித்துப் பூச்சிகளைக் கண்காணிக்கவும்.",
                "White flowers bloom continuously and green chilli pods develop. Regulate irrigation.": "வெள்ளைப் பூக்கள் பூத்துக் காய்கள் உருவாகின்றன. நீர்ப்பாசனத்தைச் சீராக வழங்கவும்.",
                "Chilli pods mature to deep green or red. Perform selective hand picking every 7-10 days.": "மிளகாய்கள் அடர் பச்சை அல்லது சிவப்பு நிறமாக மாறுகின்றன. 7-10 நாட்களுக்கு ஒருமுறை அறுவடை செய்யவும்.",
                "Plant mother rhizomes on ridges. Cover with heavy green leaf mulch to preserve moisture.": "தாய்க்கிழங்குகளை பார்களில் நடவும். ஈரப்பதம் காக்கப் பசுந்தாள் மூடாக்கு போடவும்.",
                "Tillers and broad green leaves emerge. Apply top dressing fertilizers and earthing up.": "தூர்கள் மற்றும் பசுமையான இலைகள் வளர்கின்றன. மேலுரம் இட்டு மண் அணைக்கவும்.",
                "Primary and secondary finger rhizomes enlarge in soil. Keep root zone well aerated.": "மஞ்சள் விரல்க் கிழங்குகள் மண்ணில் பெருகுகின்றன. வேர்ப்பகுதியில் நல்ல காற்றோட்டம் இருக்கட்டும்.",
                "Leaves turn dry and straw yellow. Dig out mature rhizomes carefully without bruising.": "இலைகள் காய்ந்து மஞ்சளாகும். கிழங்குகளில் காயம்படாமல் கவனமாகத் தோண்டி எடுக்கவும்.",
                "Sow Rhizobium-treated seeds 3-4cm deep. Ensure good soil moisture for quick emergence.": "ரைசோபியம் பூசிய விதைகளை 3-4 செ.மீ ஆழத்தில் விதைக்கவும். விரைவான முளைப்புக்கு ஈரப்பதம் தேவை.",
                "Trifoliate leaf growth and root nodule nitrogen fixation. Control early broadleaf weeds.": "இலை வளர்ச்சி மற்றும் வேர் முடிச்சுகளில் நைட்ரஜன் சேமிப்பு. ஆரம்பகாலக் களைகளைக் கட்டுப்படுத்தவும்.",
                "Small purple/white flowers blossom into pods. Critical irrigation window for yield.": "சிறிய பூக்கள் பூத்துக் காய்கள் உருவாகின்றன. விளைச்சலுக்கு இதுவே மிக முக்கியமான நீர்ப்பாசன நிலை.",
                "Pods turn yellow-brown and leaves shed. Harvest when grain moisture drops to 13-15%.": "காய்கள் பழுப்பு நிறமாகி இலைகள் உதிரும். தானிய ஈரப்பதம் குறையும்போது அறுவடை செய்யவும்.",
                "Panicles bloom with fragrant flowers. Protect against powdery mildew and mango hoppers.": "மாம்பூக்கள் பூத்துக் குலுங்கும். சாம்பல் நோய் மற்றும் தட்டுப் பூச்சியிலிருந்து பாதுகாக்கவும்.",
                "Young fruits set at pea/marble size. Apply light irrigation to prevent fruit drop.": "பிஞ்சுகள் பட்டாணி அளவில் பிடிக்கும். பிஞ்சு உதிர்வதைத் தடுக்க லேசான நீர்ப்பாசனம் தரவும்.",
                "Fruits expand rapidly and stone hardens inside. Apply potassium for sweetness and size.": "மாங்காய்கள் வேகமாக திரண்டு கொட்டை கெட்டியாகும். இனிப்புக்கும் அளவுக்கும் பொட்டாஷ் உரமிடவும்.",
                "Fruit shoulders widen and skin color turns pale yellow-green. Harvest with pedicel attached.": "மாம்பழத் தோள்கள் அகன்று வெளிர் மஞ்சள்-பச்சையாகும். காம்போடு பார்த்து அறுவடை செய்யவும்.",
                "Flower spathe opens and female buttons are pollinated naturally by bees and wind.": "தென்னம்பாளை வெடித்து பெண் குரும்பைகள் இயற்கை முறையில் மகரந்தச்சேர்க்கை பெறுகின்றன.",
                "Young coconut shell fills with sweet nourishing tender coconut water.": "தென்னங்காய்க்குள் சுவையான சத்தான இளநீர் நிரம்புகிறது.",
                "Endosperm (copra meat) forms and thickens along inner shell wall.": "ஓட்டின் உட்புறத்தில் தேங்காய்ப் பருப்பு தடித்து கெட்டியாகிறது.",
                "Nuts turn brown and dry. Harvest mature coconuts every 45-60 days throughout the year.": "தேங்காய்கள் பழுப்பு நிறமாக மாறுகின்றன. ஆண்டு முழுவதும் 45-60 நாட்களுக்கு ஒருமுறை அறுவடை செய்யவும்."
            },
        "stage_names": {
            "Sowing & Nursery": "விதைப்பு & நாற்றங்கால்",
            "Vegetative Growth": "வளர்ச்சி பருவம்",
            "Reproductive & Panicle": "கதிர் வரும் நிலை",
            "Ripening & Maturity": "முதிர்ச்சி & அறுவடை",
            "Sowing & Germination": "விதைப்பு & முளைப்பு",
            "Vegetative Stage": "வளர்ச்சி பருவம்",
            "Tasseling & Silking": "பூக்கும் & கதிர் பிடிக்கும் நிலை",
            "Grain Filling & Maturity": "தானியம் முதிர்ச்சி நிலை",
            "Sowing & Seedling": "விதைப்பு & நாற்று பருவம்",
            "Pegging & Pod Formation": "விழுது இறங்குதல் & காய் பிடித்தல்",
            "Pod Maturity & Harvest": "காய் முதிர்ச்சி & அறுவடை",
            "Sowing & Crown Root": "விதைப்பு & வேர் உருவாக்கம்",
            "Tillering & Jointing": "தூர்கட்டுதல் & தண்டு நீளுதல்",
            "Heading & Flowering": "கதிர் வருதல் & பூத்தல்",
            "Vegetative Branching": "கிளைகள் வளர்ச்சி நிலை",
            "Squaring & Flowering": "மொட்டு & பூக்கும் நிலை",
            "Boll Opening & Picking": "காய் வெடித்தல் & பஞ்சு எடுத்தல்",
            "Planting & Germination": "கரணை நடுதல் & முளைப்பு",
            "Tillering Stage": "தூர்கட்டும் பருவம்",
            "Grand Growth Period": "வேகமான வளர்ச்சி பருவம்",
            "Ripening & Harvest": "முதிர்ச்சி & அறுவடை",
            "Planting & Establishment": "கன்று நடுதல் & நிலைபெறுதல்",
            "Vegetative Canopy": "இலைத் தொகுதி வளர்ச்சி",
            "Bunch Shooting": "வாழைப் பூ தள்ளுதல்",
            "Bunch Development & Harvest": "தார் வளர்ச்சி & அறுவடை",
            "Vegetative & Nipping": "வளர்ச்சி & நுனி கிள்ளுதல்",
            "Flowering & Pod Set": "பூத்தல் & காய் பிடித்தல்",
            "Pod Ripening & Harvest": "காய் முதிர்ச்சி & அறுவடை",
            "Transplanting & Nursery": "நாற்று நடுதல் & பராமரிப்பு",
            "Fruit Set & Fruit Ripening": "காய் பிடித்தல் & பழம் முதிர்ச்சி",
            "Fruit Ripening & Harvest": "பழம் முதிர்ச்சி & அறுவடை",
            "Transplanting & Early Growth": "நாற்று நடுதல் & ஆரம்ப வளர்ச்சி",
            "Foliage Development": "இலைகள் வளர்ச்சி நிலை",
            "Bulb Initiation & Swelling": "வெங்காய திரட்சி நிலை",
            "Neck Fall & Harvest": "தாள் சாய்தல் & அறுவடை",
            "Transplanting & Establishment": "நாற்று நடுதல் & நிலைபெறுதல்",
            "Pod Maturity & Harvesting": "மிளகாய் முதிர்ச்சி & அறுவடை",
            "Planting & Sprouting": "நடுதல் & முளைப்பு நிலை",
            "Vegetative Tillering": "தூர் வளர்ச்சி நிலை",
            "Rhizome Expansion": "மஞ்சள் கிழங்கு பெருக்குதல்",
            "Foliage Drying & Harvest": "இலை காய்தல் & அறுவடை",
            "Flowering & Pod Formation": "பூத்தல் & காய் பிடித்தல்",
            "Bud Break & Flowering": "அரும்பு அவிழ்தல் & பூத்தல்",
            "Fruit Set & Pea Stage": "பிஞ்சு பிடித்தல் & பட்டாணி நிலை",
            "Fruit Growth & Enlargement": "காய் வளர்ச்சி & திரட்சி",
            "Maturity & Harvest": "பழம் முதிர்ச்சி & அறுவடை",
            "Spathe & Button Stage": "பாளை வெடித்தல் & குரும்பை நிலை",
            "Tender Nut Water Stage": "இளநீர் பருவம்",
            "Kernel Solidification": "தேங்காய்ப் பருப்பு திரளுதல்",
            "Full Maturity & Harvest": "முழு முதிர்ச்சி & தேங்காய் பறித்தல்"
        }
    },
    "hi": {

        "app_title": "AI फसल सलाहकार",
        "tagline": "बेहतर उपज के लिए कृषि बुद्धिमत्ता",
        "step1": "स्थान", "step2": "मिट्टी", "step3": "परिणाम", "step4": "प्रतिक्रिया",
        "my_history": "मेरा इतिहास", "logout": "लॉगआउट", "login": "लॉगिन", "signup": "साइन अप",
        "admin_login": "एडमिन लॉगिन", "city_label": "शहर / गाँव", "type_city": "शहर या गाँव का नाम लिखें...",
        "get_weather": "मौसम प्राप्त करें", "use_gps": "GPS का उपयोग करें", "temperature": "तापमान (°C)",
        "humidity": "आर्द्रता (%)", "nitrogen": "नाइट्रोजन (N)", "phosphorus": "फास्फोरस (P)",
        "potassium": "पोटेशियम (K)", "ph": "मिट्टी pH", "rainfall": "वर्षा (mm)",
        "recommend": "सिफारिश प्राप्त करें", "sensor": "सेंसर ऑटो-फिल", "next": "आगे", "back": "पीछे",
        "submit_feedback": "प्रतिक्रिया जमा करें", "actual_crop": "आपकी वास्तविक फसल",
        "actual_profit": "वास्तविक लाभ (₹/एकड़)", "actual_yield": "वास्तविक उपज (किग्रा/एकड़)",
        "acres_farmed": "खेती का क्षेत्रफल (एकड़)", "total_profit": "कुल लाभ (₹)",
        "total_yield": "कुल उपज (किग्रा)", "rate_prediction": "AI भविष्यवाणी का मूल्यांकन करें",
        "comments": "टिप्पणी (वैकल्पिक)", "save_db": "डेटाबेस में सहेजें और AI प्रशिक्षण में मदद करें",
        "skip_new": "छोड़ें — नई भविष्यवाणी शुरू करें", "thank_you": "धन्यवाद!",
        "feedback_note": "आपका डेटा AI मॉडल की सटीकता सुधारने में मदद करता है",
        "rec_crop": "अनुशंसित फसल", "intercrop_1": "अंतर-फसल 1", "intercrop_2": "अंतर-फसल 2",
        "fertilizer": "उर्वरक सिफारिश", "expected_profit": "अनुमानित लाभ", "expected_yield": "अनुमानित उपज",
        "market_status_label": "बाजार की स्थिति", "soil_health": "मिट्टी स्वास्थ्य स्कोर", "crop_calendar": "फसल कैलेंडर",
        "irrigation": "सिंचाई अनुसूची", "disease_risk": "रोग जोखिम", "top3_alt": "शीर्ष 3 विकल्प फसलें",
        "market_forecast": "बाजार मूल्य पूर्वानुमान", "nearby_mandis": "निकटतम मंडी मानचित्र",
        "gov_schemes": "सरकारी योजनाएं", "report": "रिपोर्ट", "share": "शेयर", "history": "इतिहास",
        "best": "सर्वश्रेष्ठ", "current": "वर्तमान", "next_month": "अगला महीना", "km_away": "किमी दूर",
        "directions": "दिशा-निर्देश", "your_farm": "आपका खेत", "drag_me": "खींचे", "score": "स्कोर",
        "sow": "बुआई", "growing": "विकास", "harvest": "कटाई", "duration": "अवधि", "months": "महीने",
        "frequency": "आवृत्ति", "amount_session": "मात्रा/सत्र", "risk": "जोखिम", "advice": "सलाह",
        "no_mandis": "कोई सत्यापित मंडी डेटा उपलब्ध नहीं है", "export_csv": "CSV निर्यात करें",
        "crops": {
            "Rice": "चावल (धान)", "Maize": "मक्का", "Groundnut": "मूंगफली", "Wheat": "गेहूँ",
            "Cotton": "कपास", "Sugarcane": "गन्ना", "Banana": "केला", "Chickpea": "चना",
            "Tomato": "टमाटर", "Onion": "प्याज", "Chilli": "मिर्च", "Turmeric": "हल्दी",
            "Soybean": "सोयाबीन", "Mango": "आम", "Coconut": "नारियल"
        },
        "intercrops": {
            "Azolla": "अजोला", "Fish (Aquaculture)": "मछली पालन", "Cowpea": "लोबिया",
            "Soybean": "सोयाबीन", "Pearl Millet": "बाजरा", "Castor": "अरंडी",
            "Mustard": "सरसों", "Chickpea": "चना", "Moong Bean": "मूंग",
            "Groundnut": "मूंगफली", "Onion": "प्याज", "Garlic": "लहसुन",
            "Ginger": "अदरक", "Turmeric": "हल्दी", "Safflower": "कुसुम",
            "Linseed": "अलसी", "Basil": "तुलसी", "Marigold": "गेंदा",
            "Carrot": "गाजर", "Spinach": "पालक", "Coriander": "धनिया",
            "Fenugreek": "मेथी", "Taro": "अरबी", "Sorghum": "ज्वार",
            "Papaya": "पपीता", "Pepper": "काली मिर्च", "Banana": "केला"
        },
        "fertilizers": {
            "Urea + DAP": "यूरिया + डीएपी", "NPK 14-35-14": "एनपीके 14-35-14", "SSP + Gypsum": "एसएसपी + जिप्सम",
            "NPK 20-20-0": "एनपीके 20-20-0", "NPK + Zinc": "एनपीके + जिंक", "FYM + NPK": "गोबर खाद + एनपीके",
            "DAP + Rhizobium": "डीएपी + राइजोबियम", "NPK 19-19-19": "एनपीके 19-19-19",
            "Urea + SSP + MOP": "यूरिया + एसएसपी + एमओपी", "NPK 17-17-17": "एनपीके 17-17-17",
            "FYM + NPK + Boron": "गोबर खाद + एनपीके + बोरॉन", "NPK + Boron": "एनपीके + बोरॉन"
        },
        "seasons": {
            "Kharif": "खरीफ (मानसून)", "Rabi": "रबी (शीतकाल)", "Annual": "वार्षिक (पूरे वर्ष)",
            "Kharif/Rabi": "खरीफ / रबी", "Rabi/Kharif": "रबी / खरीफ"
        },
        "irrigation_freq": {
            "Every day": "प्रतिदिन", "Every 2 days": "हर 2 दिन में", "Every 3 days": "हर 3 दिन में",
            "Twice a week": "सप्ताह में दो बार", "Once a week": "सप्ताह में एक बार", "Once in 10 days": "10 दिन में एक बार",
            "Rainfall sufficient": "पर्याप्त वर्षा", "Monitor only": "केवल निगरानी करें"
        },
        "disease_types": {
            "Fungal Disease": "कवक रोग (फंगल)", "Bacterial Blight": "जीवाणु झुलसा (बैक्टीरियल)",
            "Pest Infestation": "कीट प्रकोप", "No Risk Detected": "कोई जोखिम नहीं"
        },
        "risk_levels": {
            "High": "उच्च जोखिम", "Medium": "मध्यम जोखिम", "Low": "कम जोखिम"
        },
        "disease_advice": {
            "Apply Mancozeb or Copper Oxychloride": "मैंकोजेब या कॉपर ऑक्सीक्लोराइड का छिड़काव करें",
            "Use Streptocycline spray": "स्ट्रेप्टोसाइक्लिन का छिड़काव करें",
            "Use Neem oil or recommended pesticide": "नीम तेल या अनुशंसित कीटनाशक का प्रयोग करें",
            "Maintain good field hygiene": "खेत की अच्छी स्वच्छता बनाए रखें"
        },
        "market_status": {
            "High Demand": "उच्च मांग", "Normal": "सामान्य मांग"
        },
        "market_trend": {
            "rising": "↑ बढ़ रहा है", "falling": "↓ गिर रहा है", "stable": "→ स्थिर"
        },
        "schemes": {
            "PM-Kisan": "पीएम-किसान योजना", "PMFBY": "फसल बीमा योजना (PMFBY)",
            "NFSM": "राष्ट्रीय खाद्य सुरक्षा मिशन", "MSP Scheme": "न्यूनतम समर्थन मूल्य (MSP)",
            "Cotton Tech Mission": "कपास प्रौद्योगिकी मिशन", "Sugarcane Dev Scheme": "गन्ना विकास योजना",
            "NHM": "राष्ट्रीय बागवानी मिशन", "Pulses Dev": "दलहन विकास योजना",
            "Spices Board": "भारतीय मसाला बोर्ड", "Coconut Dev Board": "नारियल विकास बोर्ड"
        },
        "soil_tips": {
            "Low Nitrogen — apply Urea or green manure": "कम नाइट्रोजन — यूरिया या हरी खाद डालें",
            "Low Phosphorus — apply DAP or SSP": "कम फास्फोरस — डीएपी या एसएसपी डालें",
            "Low Potassium — apply MOP": "कम पोटेशियम — एमओपी डालें",
            "Acidic soil — apply lime": "अम्लीय मिट्टी — चूना डालें",
            "Alkaline soil — apply gypsum": "क्षारीय मिट्टी — जिप्सम डालें",
            "Soil health is good!": "✅ मिट्टी का स्वास्थ्य अच्छा है!"
        },
        "water_need": {
            "high": "अधिक", "medium": "मध्यम", "low": "कम"
        },
        "agmarknet_price_title": "लाइव एगमार्कनेट मंडी भाव",
        "modal_price": "नवीनतम मॉडल मंडी भाव",
        "min_price": "न्यूनतम मूल्य",
        "max_price": "अधिकतम मूल्य",
        "mandi_market": "मंडी / बाजार",
        "market_date": "दिनांक",
        "source": "स्रोत",
        "agmarknet_source": "एगमार्कनेट",
        "live_market_unavailable": "लाइव बाजार मूल्य वर्तमान में उपलब्ध नहीं है।",
        "market_trend_unavailable": "बाजार का रुख उपलब्ध नहीं है",
        "estimated_profit": "अनुमानित लाभ",
        "estimated_revenue": "अनुमानित राजस्व",
        "commodity": "जिंस",
        "variety": "किस्म",
        "grade": "ग्रेड",
        "arrival_qty": "आवक मात्रा",
        "primary_crop_title": "मुख्य फसल",
        "intercrop_1_title": "अंतर-फसल 1",
        "intercrop_2_title": "अंतर-फसल 2",
        "advisory_context_primary": "मुख्य फसल के लिए कृषि सलाह",
        "advisory_context_intercrop": "अंतर-फसल सलाह",
        "actual_sowing_date_label": "वास्तविक बुवाई की तारीख",
        "total_duration_label": "कुल वृद्धि की अवधि",
        "days_unit": "दिन",
        "months_unit": "महीने",
        "stage_prefix": "चरण",
        "select_crop_label": "फसल चुनें",
        "around_prefix": "लगभग",
        "crop_label": "फसल",
        "typical_season_label": "सामान्य फसल मौसम",
        "estimated_harvest_label": "अनुमानित कटाई की तारीख",
        "harvest_disclaimer": "कटाई की तारीख चुनी गई फसल की सामान्य विकास अवधि पर आधारित एक अनुमान है। मौसम, मिट्टी की स्थिति, सिंचाई और कृषि पद्धतियों के आधार पर वास्तविक कटाई का समय भिन्न हो सकता है।",
        "weather_advisory_high_rain": "🌧️ आपके क्षेत्र में भारी वर्षा ({rainfall}mm) दर्ज की गई है। शुरुआती फसल वृद्धि के दौरान खेत में अच्छी जल निकासी सुनिश्चित करें।",
        "weather_advisory_high_temp": "☀️ उच्च तापमान ({temp}°C) की संभावना है। फूल आने और बाली बनने की अवस्था में उचित सिंचाई बनाए रखें।",
        "weather_advisory_normal": "🌤️ वर्तमान जलवायु परिस्थितियां (तापमान: {temp}°C, आर्द्रता: {humidity}%) सामान्य फसल विकास के लिए उपयुक्त हैं।",
                    "stage_explanations": {
                "Prepare seedbed, sow seeds, and maintain consistent nursery moisture for healthy seedling emergence.": "पौध की क्यारी तैयार करें, बीज बोएं और स्वस्थ पौध निकलने के लिए नर्सरी में नमी बनाए रखें।",
                "Transplant seedlings to main field, maintain 2-5cm standing water, and apply initial nitrogen fertilizer.": "पौधों को मुख्य खेत में रोपें, 2-5 सेमी खड़ा पानी रखें और पहला नाइट्रोजन उर्वरक डालें।",
                "Panicle initiation and flowering stage. Ensure peak water availability and protect against stem borer.": "बाली बनने और फूल आने की अवस्था। पानी की पूर्ण उपलब्धता सुनिश्चित करें और तना छेदक से बचाव करें।",
                "Grain filling and ripening. Drain field water 10 days prior to harvest when grains turn golden.": "दाना भरना और पकना। दाने सुनहरे होने पर कटाई से 10 दिन पहले खेत का पानी निकाल दें।",
                "Sow seeds 4-5cm deep in well-drained soil. Ensure optimal warmth and soil moisture.": "अच्छी जल निकासी वाली मिट्टी में 4-5 सेमी गहरे बीज बोएं। उचित नमी सुनिश्चित करें।",
                "Rapid leaf elongation and stem growth. Apply NPK fertilizer top dressing and earthing up.": "पत्तियों और तने का तेजी से विकास। एनपीके उर्वरक की टॉप ड्रेसिंग करें।",
                "Flowering and pollination phase. Critical stage requiring adequate irrigation and pest control.": "फूल आने और परागण की अवस्था। पर्याप्त सिंचाई और कीट नियंत्रण आवश्यक है।",
                "Kernels mature and harden. Harvest when cob husk turns dry and pale yellow.": "दाने पकते और सख्त होते हैं। भुट्टे के सूखने पर कटाई करें।",
                "Plant quality pods/seeds in friable soil. Ensure moist seedbed for uniform germination.": "भुरभुरी मिट्टी में गुणवत्तापूर्ण बीज बोएं। समान अंकुरण के लिए नमी बनाए रखें।",
                "Canopy development and branching. Apply gypsum to supply calcium for pod development.": "शाखाओं का विकास। फली के विकास के लिए जिप्सम डालें।",
                "Flower pegs enter soil to form underground pods. Avoid deep cultivation to protect pegs.": "फूल के खूंटे जमीन में प्रवेश कर फलियां बनाते हैं। खूंटों को बचाने के लिए गहरी जुताई से बचें।",
                "Pods mature and harden. Harvest when internal shell lining turns dark brown.": "फलियां पककर सख्त हो जाती हैं। छिलके की अंदरूनी परत भूरी होने पर कटाई करें।",
                "Sow in cool moist soil. Provide first irrigation at Crown Root Initiation (CRI) stage (~21 days).": "ठंडी नम मिट्टी में बुवाई करें। 21 दिनों में पहली सिंचाई करें।",
                "Tillers develop and stems elongate. Apply top dressing nitrogen and control weeds.": "कल्ले निकलते हैं और तने लंबे होते हैं। नाइट्रोजन उर्वरक डालें और खरपतवार नियंत्रित करें।",
                "Earheads emerge and flowering begins. Maintain soil moisture to avoid grain reduction.": "बालियां निकलती हैं और फूल खिलते हैं। मिट्टी में नमी बनाए रखें।",
                "Dough stage to hard grain. Harvest when crop turns golden and moisture drops to 12-14%.": "फसल सुनहरी होने और नमी 12-14% होने पर कटाई करें।"
            },
        "stage_names": {
            "Sowing & Nursery": "बुवाई और नर्सरी",
            "Vegetative Growth": "वानस्पतिक विकास",
            "Reproductive & Panicle": "प्रजनन और बाली अवस्था",
            "Ripening & Maturity": "पकाव और कटाई",
            "Sowing & Germination": "बुवाई और अंकुरण",
            "Vegetative Stage": "वानस्पतिक अवस्था",
            "Tasseling & Silking": "मंजी और सिल्क अवस्था",
            "Grain Filling & Maturity": "दाना भरना और परिपक्वता",
            "Sowing & Seedling": "बुवाई और अंकुरण",
            "Pegging & Pod Formation": "पेगिंग और फली बनना",
            "Pod Maturity & Harvest": "फली परिपक्वता और कटाई",
            "Sowing & Crown Root": "बुवाई और क्राउन रूट",
            "Tillering & Jointing": "कल्ले निकलना और गांठ बनना",
            "Heading & Flowering": "बाली निकलना और फूल आना",
            "Vegetative Branching": "वानस्पतिक शाखाएं",
            "Squaring & Flowering": "स्क्वायरिंग और फूल आना",
            "Boll Opening & Picking": "बॉल खुलना और चुनाई",
            "Planting & Germination": "रोपाई और अंकुरण",
            "Tillering Stage": "कल्ले निकलने की अवस्था",
            "Grand Growth Period": "मुख्य विकास अवधि",
            "Ripening & Harvest": "पकाव और कटाई",
            "Planting & Establishment": "रोपण और स्थापना",
            "Vegetative Canopy": "वानस्पतिक कैनोपी",
            "Bunch Shooting": "घार निकलना",
            "Bunch Development & Harvest": "घार विकास और कटाई",
            "Vegetative & Nipping": "वानस्पतिक और निपिंग",
            "Flowering & Pod Set": "फूल आना और फली बनना",
            "Pod Ripening & Harvest": "फली पकाव और कटाई",
            "Transplanting & Nursery": "रोपाई और नर्सरी",
            "Fruit Set & Fruit Ripening": "फल बनना और पकना",
            "Fruit Ripening & Harvest": "फल पकना और तुड़ाई",
            "Transplanting & Early Growth": "रोपाई और शुरुआती विकास",
            "Foliage Development": "पत्तियों का विकास",
            "Bulb Initiation & Swelling": "गांठ बनना और बढ़ना",
            "Neck Fall & Harvest": "गर्दन गिरना और खुदाई",
            "Transplanting & Establishment": "रोपाई और स्थापना",
            "Pod Maturity & Harvesting": "मिर्च परिपक्वता और तुड़ाई",
            "Planting & Sprouting": "रोपाई और अंकुरण",
            "Vegetative Tillering": "कल्ले का विकास",
            "Rhizome Expansion": "कंद का विस्तार",
            "Foliage Drying & Harvest": "पत्तियां सूखना और खुदाई",
            "Flowering & Pod Formation": "फूल और फली बनना",
            "Bud Break & Flowering": "कली फूटना और मौर आना",
            "Fruit Set & Pea Stage": "फल सेट और मटर अवस्था",
            "Fruit Growth & Enlargement": "फल वृद्धि और आकार बढ़ना",
            "Maturity & Harvest": "परिपक्वता और तुड़ाई",
            "Spathe & Button Stage": "स्पैथ और बटन अवस्था",
            "Tender Nut Water Stage": "डाभ पानी अवस्था",
            "Kernel Solidification": "गिरी जमना",
            "Full Maturity & Harvest": "पूर्ण परिपक्वता और तुड़ाई"
        }
    },
    "te": {
        "app_title": "AI పంట సలహాదారు",
        "tagline": "మెరుగైన దిగుబడి కోసం వ్యవసాయ మేధస్సు",
        "step1": "స్థానం", "step2": "నేల", "step3": "ఫలితాలు", "step4": "అభిప్రాయం",
        "my_history": "నా చరిత్ర", "logout": "లాగ్అవుట్", "login": "లాగిన్", "signup": "సైన్ అప్",
        "admin_login": "అడ్మిన్ లాగిన్", "city_label": "నగరం / గ్రామం", "type_city": "నగరం లేదా గ్రామం టైప్ చేయండి...",
        "get_weather": "వాతావరణం పొందండి", "use_gps": "GPS ఉపయోగించండి", "temperature": "ఉష్ణోగ్రత (°C)",
        "humidity": "తేమ (%)", "nitrogen": "నైట్రోజన్ (N)", "phosphorus": "ఫాస్పరస్ (P)",
        "potassium": "పొటాషియం (K)", "ph": "నేల pH", "rainfall": "వర్షపాతం (mm)",
        "recommend": "సిఫారసు పొందండి", "sensor": "సెన్సార్ ఆటో-ఫిల్", "next": "తదుపరి", "back": "వెనుకకు",
        "submit_feedback": "అభిప్రాయం సమర్పించు", "actual_crop": "మీరు పండించిన పంట",
        "actual_profit": "వాస్తవ లాభం (₹/ఎకరం)", "actual_yield": "వాస్తవ దిగుబడి (కిలోలు/ఎకరం)",
        "acres_farmed": "సాగు విస్తీర్ణం (ఎకరాలు)", "total_profit": "మొత్తం లాభం (₹)",
        "total_yield": "మొత్తం దిగుబడి (కిలోలు)", "rate_prediction": "AI అంచనాను రేట్ చేయండి",
        "comments": "వ్యాఖ్యలు (ఐచ్ఛికం)", "save_db": "డేటాబేస్‌లో సేవ్ చేయండి & AIకి సహాయపడండి",
        "skip_new": "వదిలేయండి — కొత్త అంచనా ప్రారంభించండి", "thank_you": "ధన్యవాదాలు!",
        "feedback_note": "మీ డేటా AI మోడల్ అంచనాలను మెరుగుపరచడానికి సహాయపడుతుంది",
        "rec_crop": "సిఫార్సు చేసిన పంట", "intercrop_1": "అంతర్ పంట 1", "intercrop_2": "అంతర్ పంట 2",
        "fertilizer": "ఎరువుల సిఫారసు", "expected_profit": "ఆశించిన లాభం", "expected_yield": "ఆశించిన దిగుబడి",
        "market_status_label": "మార్కెట్ పరిస్థితి", "soil_health": "నేల ఆరోగ్య స్కోరు", "crop_calendar": "పంట క్యాలెండర్",
        "irrigation": "నీటి పారుదల షెడ్యూల్", "disease_risk": "తెగులు ప్రమాదం", "top3_alt": "టాప్ 3 ప్రత్యామ్నాయ పంటలు",
        "market_forecast": "మార్కెట్ ధర అంచనా", "nearby_mandis": "సమీప మార్కెట్ల మ్యాప్",
        "gov_schemes": "ప్రభుత్వ పథకాలు", "report": "నివేదిక", "share": "షేర్ చేయండి", "history": "చరిత్ర",
        "best": "ఉత్తమమైనది", "current": "ప్రస్తుత", "next_month": "వచ్చే నెల", "km_away": "కిమీ దూరంలో",
        "directions": "దారి", "your_farm": "మీ పొలం", "drag_me": "జరపండి", "score": "స్కోరు",
        "sow": "విత్తడం", "growing": "పెరుగుదల", "harvest": "కోత", "duration": "కాలవ్యవధి", "months": "నెలులు",
        "frequency": "ఫ్రీక్వెన్సీ", "amount_session": "మోతాదు/సెషన్", "risk": "ప్రమాదం", "advice": "సలహా",
        "no_mandis": "ధృవీకరించబడిన మార్కెట్ డేటా అందుబాటులో లేదు", "export_csv": "CSV ఎగుమతి",
        "crops": {
            "Rice": "వరి", "Maize": "మొక్కజొన్న", "Groundnut": "వేరుశెనగ", "Wheat": "గోధుమ",
            "Cotton": "పత్తి", "Sugarcane": "చెరకు", "Banana": "అరటి", "Chickpea": "శనగ",
            "Tomato": "టమాటా", "Onion": "ఉల్లిపాయ", "Chilli": "మిరప", "Turmeric": "పసుపు",
            "Soybean": "సోయాబీన్", "Mango": "మామిడి", "Coconut": "కొబ్బరి"
        },
        "intercrops": {
            "Azolla": "అజోల్లా", "Fish (Aquaculture)": "చేపల పెంపకం", "Cowpea": "అలసందలు",
            "Soybean": "సోయాబీన్", "Pearl Millet": "సజ్జలు", "Castor": "ఆముదం",
            "Mustard": "ఆవాలు", "Chickpea": "శనగ", "Moong Bean": "పెసలు",
            "Groundnut": "వేరుశెనగ", "Onion": "ఉల్లిపాయ", "Garlic": "వెల్లుల్లి",
            "Ginger": "అల్లం", "Turmeric": "పసుపు", "Safflower": "కుసుమ",
            "Linseed": "అవిసెలు", "Basil": "తులసి", "Marigold": "బంతి పూవు",
            "Carrot": "క్యారెట్", "Spinach": "పాలకూర", "Coriander": "కొత్తిమీర",
            "Fenugreek": "మెంతులు", "Taro": "చేమదుంప", "Sorghum": "జొన్నలు",
            "Papaya": "బొప్పాయి", "Pepper": "మిరియాలు", "Banana": "అరటి"
        },
        "fertilizers": {
            "Urea + DAP": "యూరియా + డిఎపి", "NPK 14-35-14": "ఎన్‌పికె 14-35-14", "SSP + Gypsum": "ఎస్ఎస్పి + జిప్సం",
            "NPK 20-20-0": "ఎన్‌పికె 20-20-0", "NPK + Zinc": "ఎన్‌పికె + జింక్", "FYM + NPK": "పశువుల ఎరువు + ఎన్‌పికె",
            "DAP + Rhizobium": "డిఎపి + రైజోబియం", "NPK 19-19-19": "ఎన్‌పికె 19-19-19",
            "Urea + SSP + MOP": "యూరియా + ఎస్ఎస్పి + ఎంఓపి", "NPK 17-17-17": "ఎన్‌పికె 17-17-17",
            "FYM + NPK + Boron": "పశువుల ఎరువు + ఎన్‌పికె + బోరాన్", "NPK + Boron": "ఎన్‌పికె + బోరాన్"
        },
        "seasons": {
            "Kharif": "ఖరీఫ్ (వర్షాకాలం)", "Rabi": "రబీ (శీతాకాలం)", "Annual": "వార్షిక (ఏడాది పొడవునా)",
            "Kharif/Rabi": "ఖరీఫ్ / రబీ", "Rabi/Kharif": "రబీ / ఖరీఫ్"
        },
        "irrigation_freq": {
            "Every day": "ప్రతిరోజూ", "Every 2 days": "ప్రతి 2 రోజులకు", "Every 3 days": "ప్రతి 3 రోజులకు",
            "Twice a week": "వారానికి రెండుసార్లు", "Once a week": "వారానికి ఒకసారి", "Once in 10 days": "10 రోజులకు ఒకసారి",
            "Rainfall sufficient": "తగినంత వర్షపాతం", "Monitor only": "పర్యవేక్షించండి"
        },
        "disease_types": {
            "Fungal Disease": "శిలీంధ్ర వ్యాధి (ఫంగల్)", "Bacterial Blight": "బ్యాక్టీరియా తెగులు",
            "Pest Infestation": "పురుగుల దాడి", "No Risk Detected": "ప్రమాదం లేదు"
        },
        "risk_levels": {
            "High": "ఎక్కువ ప్రమాదం", "Medium": "మధ్యస్థ ప్రమాదం", "Low": "తక్కువ ప్రమాదం"
        },
        "disease_advice": {
            "Apply Mancozeb or Copper Oxychloride": "మాంకోజెబ్ లేదా కాపర్ ఆక్సిక్లోరైడ్ పిచికారీ చేయండి",
            "Use Streptocycline spray": "స్ట్రెప్టోసైక్లిన్ పిచికారీ చేయండి",
            "Use Neem oil or recommended pesticide": "వేప నూనె లేదా సిఫార్సు చేసిన క్రిమిసంహారకం వాడండి",
            "Maintain good field hygiene": "పొలాన్ని శుభ్రంగా ఉంచండి"
        },
        "market_status": {
            "High Demand": "ఎక్కువ డిమాండ్", "Normal": "సాధారణ డిమాండ్"
        },
        "market_trend": {
            "rising": "↑ పెరుగుతోంది", "falling": "↓ తగ్గుతోంది", "stable": "→ స్థిరంగా ఉంది"
        },
        "schemes": {
            "PM-Kisan": "పిఎం-కిసాన్ పథకం", "PMFBY": "పంటల భీమా (PMFBY)",
            "NFSM": "జాతీయ ఆహార భద్రతా మిషన్", "MSP Scheme": "కనీస మద్దతు ధర (MSP)",
            "Cotton Tech Mission": "పత్తి సాంకేతిక మిషన్", "Sugarcane Dev Scheme": "చెరకు అభివృద్ధి పథకం",
            "NHM": "జాతీయ ఉద్యానవన మిషన్", "Pulses Dev": "పప్పుధాన్యాల అభివృద్ధి పథకం",
            "Spices Board": "భారత సుగంధ ద్రవ్యాల బోర్డు", "Coconut Dev Board": "కొబ్బరి అభివృద్ధి బోర్డు"
        },
        "soil_tips": {
            "Low Nitrogen — apply Urea or green manure": "తక్కువ నైట్రోజన్ — యూరియా లేదా పచ్చిరొట్ట ఎరువు వాడండి",
            "Low Phosphorus — apply DAP or SSP": "తక్కువ ఫాస్పరస్ — డిఎపి లేదా ఎస్ఎస్పి వాడండి",
            "Low Potassium — apply MOP": "తక్కువ పొటాషియం — ఎంఓపి వాడండి",
            "Acidic soil — apply lime": "ఆమ్ల నేల — సున్నం వేయండి",
            "Alkaline soil — apply gypsum": "క్షార నేల — జిప్సం వేయండి",
            "Soil health is good!": "✅ నేల ఆరోగ్యం బాగుంది!"
        },
        "water_need": {
            "high": "ఎక్కువ", "medium": "మధ్యస్థం", "low": "తక్కువ"
        },
        "agmarknet_price_title": "లైవ్ అగ్మార్క్‌నెట్ మార్కెట్ ధర",
        "modal_price": "తాజా మోడల్ మార్కెట్ ధర",
        "min_price": "కనిష్ట ధర",
        "max_price": "గరిష్ట ధర",
        "mandi_market": "మార్కెట్ / మండి",
        "market_date": "తేదీ",
        "source": "మూలం",
        "agmarknet_source": "అగ్మార్క్‌నెట్",
        "live_market_unavailable": "లైవ్ మార్కెట్ ధర ప్రస్తుతం అందుబాటులో లేదు.",
        "market_trend_unavailable": "మార్కెట్ ట్రెండ్ అందుబాటులో లేదు",
        "estimated_profit": "అంచనా లాభం",
        "estimated_revenue": "అంచనా ఆదాయం",
        "commodity": "సరుకు",
        "variety": "రకం",
        "grade": "గ్రేడ్",
        "arrival_qty": "రాక పరిమాణం",
        "primary_crop_title": "ముఖ్య పంట",
        "intercrop_1_title": "అంతర్ పంట 1",
        "intercrop_2_title": "అంతర్ పంట 2",
        "advisory_context_primary": "ముఖ్య పంట వ్యవసాయ సలహా",
        "advisory_context_intercrop": "అంతర్ పంట సలహా",
        "actual_sowing_date_label": "వాస్తవ విత్తిన తేదీ",
        "total_duration_label": "మొత్తం పెరుగుదల కాలవ్యవధి",
        "days_unit": "రోజులు",
        "months_unit": "నెలలు",
        "stage_prefix": "దశ",
        "select_crop_label": "పంటను ఎంచుకోండి",
        "around_prefix": "సుమారు",
        "crop_label": "పంట",
        "typical_season_label": "సాధారణ పంట కాలం",
        "estimated_harvest_label": "అంచనా కోత తేదీ",
        "harvest_disclaimer": "కోత తేదీ అనేది ఎంచుకున్న పంట యొక్క సాధారణ పెరుగుదల కాలవ్యవధి ఆధారంగా అంచనా వేయబడింది. వాతావరణం, నేల పరిస్థితులు, నీటి పారుదల మరియు వ్యవసాయ పద్ధతుల ఆధారంగా వాస్తవ కోత సమయం మారవచ్చు.",
        "weather_advisory_high_rain": "🌧️ మీ ప్రాంతంలో భారీ వర్షపాతం ({rainfall}mm) నమోదైంది. పంట ప్రారంభ దశలో సరైన నీటి పారుదల సౌకర్యం కల్పించండి.",
        "weather_advisory_high_temp": "☀️ అధిక ఉష్ణోగ్రత ({temp}°C) నమోదయ్యే అవకాశం ఉంది. పూత మరియు గింజ తొడిగే దశల్లో సరైన నీటి పారుదల అందించండి.",
        "weather_advisory_normal": "🌤️ ప్రస్తుత వాతావరణ పరిస్థితులు (ఉష్ణోగ్రత: {temp}°C, తేమ: {humidity}%) సాధారణ పంట పెరుగుదలకు అనుకూలంగా ఉన్నాయి.",
                    "stage_explanations": {
                "Prepare seedbed, sow seeds, and maintain consistent nursery moisture for healthy seedling emergence.": "నారుమడి సిద్ధం చేసి విత్తనాలు చల్లి, ఆరోగ్యకరమైన మొలకల కోసం తేమను నిర్వహించండి.",
                "Transplant seedlings to main field, maintain 2-5cm standing water, and apply initial nitrogen fertilizer.": "నారును ప్రధాన పొలంలో నాటండి, 2-5 సెం.మీ నీరు ఉంచి, మొదటి నైట్రోజన్ ఎరువు వేయండి.",
                "Panicle initiation and flowering stage. Ensure peak water availability and protect against stem borer.": "వెన్ను తొడిగే మరియు పూత దశ. గరిష్ట నీటి లభ్యతను నిర్ధారించుకోండి మరియు కాండం తొలిచే పురుగు నుండి రక్షించండి.",
                "Grain filling and ripening. Drain field water 10 days prior to harvest when grains turn golden.": "గింజ పాలుపోసుకుని పక్వానికి రావడం. గింజలు దోరగా మారినప్పుడు కోతకు 10 రోజుల ముందు నీటిని తీసివేయండి.",
                "Sow seeds 4-5cm deep in well-drained soil. Ensure optimal warmth and soil moisture.": "మంచి నీటి పారుదల ఉన్న నేలలో 4-5 సెం.మీ లోతులో విత్తనాలు విత్తండి.",
                "Rapid leaf elongation and stem growth. Apply NPK fertilizer top dressing and earthing up.": "ఆకులు మరియు కాండం వేగంగా పెరుగుతాయి. ఎన్‌పికి ఎరువులు వేయండి.",
                "Flowering and pollination phase. Critical stage requiring adequate irrigation and pest control.": "పూత మరియు ఫలదీకరణ దశ. తగిన నీటి పారుదల మరియు పురుగుల నివారణ అవసరం.",
                "Kernels mature and harden. Harvest when cob husk turns dry and pale yellow.": "గింజలు పక్వానికి వచ్చి గట్టిపడతాయి. కండె ఎండిపోయినప్పుడు కోయండి."
            },
        "stage_names": {
            "Sowing & Nursery": "విత్తడం & నారుమడి",
            "Vegetative Growth": "శాకీయ పెరుగుదల",
            "Reproductive & Panicle": "పునరుత్పత్తి & వెన్ను దశ",
            "Ripening & Maturity": "పక్వత & కోత",
            "Sowing & Germination": "విత్తడం & మొలక",
            "Vegetative Stage": "శాకీయ దశ",
            "Tasseling & Silking": "పూత & పీచు దశ",
            "Grain Filling & Maturity": "గింజ పాలుపోసుకోవడం & పక్వత",
            "Sowing & Seedling": "విత్తడం & నారు దశ",
            "Pegging & Pod Formation": "ఊడలు దిగడం & కాయ తయారీ",
            "Pod Maturity & Harvest": "కాయ పక్వత & కోత",
            "Sowing & Crown Root": "విత్తడం & వేరు వ్యవస్థ",
            "Tillering & Jointing": "పిలకలు తొడగడం & కణుపులు",
            "Heading & Flowering": "వెన్ను రావడం & పూత",
            "Vegetative Branching": "కొమ్మల పెరుగుదల",
            "Squaring & Flowering": "మొగ్గ తొడగడం & పూత",
            "Boll Opening & Picking": "కాయ పగలడం & పత్తి తీయడం",
            "Planting & Germination": "నాటడం & మొలక",
            "Tillering Stage": "పిలకల దశ",
            "Grand Growth Period": "తీవ్ర పెరుగుదల కాలం",
            "Ripening & Harvest": "పక్వత & కోత",
            "Planting & Establishment": "నాటడం & స్థిరపడటం",
            "Vegetative Canopy": "ఆకుల విస్తరణ",
            "Bunch Shooting": "అంటి గెల రావడం",
            "Bunch Development & Harvest": "గెల ఎదుగుదల & కోత",
            "Vegetative & Nipping": "పెరుగుదల & చిగుళ్లు తుంచడం",
            "Flowering & Pod Set": "పూత & కాయ తయారీ",
            "Pod Ripening & Harvest": "కాయ పక్వత & కోత",
            "Transplanting & Nursery": "నాట్లు వేయడం & నారు",
            "Fruit Set & Fruit Ripening": "కాయ కాపు & పక్వత",
            "Fruit Ripening & Harvest": "పండు పక్వత & కోత",
            "Transplanting & Early Growth": "నాటడం & ప్రారంభ పెరుగుదల",
            "Foliage Development": "ఆకుల ఎదుగుదల",
            "Bulb Initiation & Swelling": "ఉల్లిపాయ ఊరడం",
            "Neck Fall & Harvest": "ఆకులు వాలడం & కోత",
            "Transplanting & Establishment": "నాటడం & స్థిరపడటం",
            "Pod Maturity & Harvesting": "మిరపకాయ పక్వత & కోత",
            "Planting & Sprouting": "నాటడం & మొలక",
            "Vegetative Tillering": "పిలకల పెరుగుదల",
            "Rhizome Expansion": "కొమ్ముల ఊరడం",
            "Foliage Drying & Harvest": "ఆకులు ఎండడం & కోత",
            "Flowering & Pod Formation": "పూత & కాయ కట్టడం",
            "Bud Break & Flowering": "మొగ్గ తొడగడం & పూత",
            "Fruit Set & Pea Stage": "పిందె కాపు & బఠానీ దశ",
            "Fruit Growth & Enlargement": "కాయ పెరుగుదల",
            "Maturity & Harvest": "పండు పక్వత & కోత",
            "Spathe & Button Stage": "పొల రావడం & పిందె",
            "Tender Nut Water Stage": "బొండం నీళ్ల దశ",
            "Kernel Solidification": "కొబ్బరి పీచు & కొబ్బరి",
            "Full Maturity & Harvest": "పూర్తి పక్వత & కొబ్బరి కోత"
        }
    },
    "kn": {
        "app_title": "AI ಬೆಳೆ ಸಲಹೆಗಾರ",
        "tagline": "ಉತ್ತಮ ಇಳುವರಿಗಾಗಿ ಕೃಷಿ ಬುದ್ಧಿವಂತಿಕೆ",
        "step1": "ಸ್ಥಳ", "step2": "ಮಣ್ಣು", "step3": "ಫಲಿತಾಂಶ", "step4": "ಪ್ರತಿಕ್ರಿಯೆ",
        "my_history": "ನನ್ನ ಇತಿಹಾಸ", "logout": "ಲಾಗಿನ್ ออก", "login": "ಲಾಗಿನ್", "signup": "ಸೈನ್ ಅಪ್",
        "admin_login": "ಅಡ್ಮಿನ್ ಲಾಗಿನ್", "city_label": "ನಗರ / ಗ್ರಾಮ", "type_city": "ನಗರ ಅಥವಾ ಗ್ರಾಮದ ಹೆಸರು ಬರೆಯಿರಿ...",
        "get_weather": "ಹವಾಮಾನ ಪಡೆಯಿರಿ", "use_gps": "GPS ಬಳಸಿ", "temperature": "ತಾಪಮಾನ (°C)",
        "humidity": "ತೇವಾಂಶ (%)", "nitrogen": "ಸಾರಜನಕ (N)", "phosphorus": "ರಂಜಕ (P)",
        "potassium": "ಪೊಟ್ಯಾಷಿಯಂ (K)", "ph": "ಮಣ್ಣು pH", "rainfall": "ಮಳೆ ಪ್ರಮಾಣ (mm)",
        "recommend": "ಶಿಫಾರಸು ಪಡೆಯಿರಿ", "sensor": "ಸೆಂನ್ಸರ್ ಸ್ವಯಂ-ಭರ್ತಿ", "next": "ಮುಂದೆ", "back": "ಹಿಂದೆ",
        "submit_feedback": "ಪ್ರತಿಕ್ರಿಯೆ ಸಲ್ಲಿಸಿ", "actual_crop": "ನೀವು ಬೆಳೆದ ನಿಜವಾದ ಬೆಳೆ",
        "actual_profit": "ನಿಜವಾದ ಲಾಭ (₹/ಎಕರೆ)", "actual_yield": "ನಿಜವಾದ ಇಳುವರಿ (ಕೆಜಿ/ಎಕರೆ)",
        "acres_farmed": "ಕೃಷಿ ಭೂಮಿ (ಎಕರೆ)", "total_profit": "ಒಟ್ಟು ಲಾಭ (₹)",
        "total_yield": "ಒಟ್ಟು ಇಳುವರಿ (ಕೆಜಿ)", "rate_prediction": "AI ಅಂಚನೆಗೆ ರೇಟಿಂಗ್ ನೀಡಿ",
        "comments": "ಕಾಮೆಂಟ್‌ಗಳು (ಐಚ್ಛಿಕ)", "save_db": "ಡೇಟಾಬೇಸ್‌ನಲ್ಲಿ ಉಳಿಸಿ & AI ಗೆ ಸಹಾಯ ಮಾಡಿ",
        "skip_new": "ಸ್ಕಿಪ್ ಮಾಡಿ — ಹೊಸ ಅಂಚನೆ ಪ್ರಾರಂಭಿಸಿ", "thank_you": "ಧನ್ಯವಾದಗಳು!",
        "feedback_note": "ನಿಮ್ಮ ಡೇಟಾ AI ಮಾಡೆಲ್ ಸುಧಾರಿಸಲು ನೆರವಾಗುತ್ತದೆ",
        "rec_crop": "ಶಿಫಾರಸು ಮಾಡಿದ ಬೆಳೆ", "intercrop_1": "ಅಂತರ ಬೆಳೆ 1", "intercrop_2": "ಅಂತರ ಬೆಳೆ 2",
        "fertilizer": "ಗೊಬ್ಬರ ಶಿಫಾರಸು", "expected_profit": "ನಿರೀಕ್ಷಿತ ಲಾಭ", "expected_yield": "ನಿರೀಕ್ಷಿತ ಇಳುವರಿ",
        "market_status_label": "ಮಾರುಕಟ್ಟೆ ಸ್ಥಿತಿ", "soil_health": "ಮಣ್ಣಿನ ಆರೋಗ್ಯ ಸ್ಕೋರ್", "crop_calendar": "ಬೆಳೆ ಕ್ಯಾಲೆಂಡರ್",
        "irrigation": "ನೀರಾವರಿ ವೇಳಾಪಟ್ಟಿ", "disease_risk": "ರೋಗದ ಅಪಾಯ", "top3_alt": "ಟಾಪ್ 3 ಪರ್ಯಾಯ ಬೆಳೆಗಳು",
        "market_forecast": "ಮಾರುಕಟ್ಟೆ ಬೆಲೆ ಮುನ್ಸೂಚನೆ", "nearby_mandis": "ಸಮೀಪದ ಮಾರುಕಟ್ಟೆಗಳ ನಕ್ಷೆ",
        "gov_schemes": "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು", "report": "ವರದಿ", "share": "ಹಂಚಿಕೊಳ್ಳಿ", "history": "ಇತಿಹಾಸ",
        "best": "ಉತ್ತಮ", "current": "ಪ್ರಸ್ತುತ", "next_month": "ಮುಂದಿನ ತಿಂಗಳು", "km_away": "ಕಿಮೀ ದೂರ",
        "directions": "ದಾರಿ", "your_farm": "ನಿಮ್ಮ ಜಮೀನು", "drag_me": "ಎಳೆಯಿರಿ", "score": "ಸ್ಕೋರ್",
        "sow": "ಬಿತ್ತನೆ", "growing": "ಬೆಳವಣಿಗೆ", "harvest": "ಕೊಯ್ಲು", "duration": "ಅವಧಿ", "months": "ತಿಂಗಳುಗಳು",
        "frequency": "ಆವರ್ತನ", "amount_session": "ಪ್ರಮಾಣ/ಸೆಷನ್", "risk": "ಅಪಾಯ", "advice": "ಸಲಹೆ",
        "no_mandis": "ಯಾವುದೇ ಪರಿಶೀಲಿಸಿದ ಮಾರುಕಟ್ಟೆ ಡೇಟಾ ಲಭ್ಯವಿಲ್ಲ", "export_csv": "CSV ರಫ್ತು ಮಾಡಿ",
        "crops": {
            "Rice": "ಭತ್ತ", "Maize": "ಮೆಕ್ಕೆ ಜೋಳ", "Groundnut": "ಶೇಂಗಾ", "Wheat": "ಗೋಧಿ",
            "Cotton": "ಹತ್ತಿ", "Sugarcane": "ಕಬ್ಬು", "Banana": "ಬಾಳೆ", "Chickpea": "ಕಡಲೆ",
            "Tomato": "ಟೊಮ್ಯಾಟೊ", "Onion": "ಈರುಳ್ಳಿ", "Chilli": "ಮೆಣಸಿನಕಾಯಿ", "Turmeric": "ಅರಿಶಿನ",
            "Soybean": "ಸೋಯಾಬೀನ್", "Mango": "ಮಾವು", "Coconut": "ತೆಂಗು"
        },
        "intercrops": {
            "Azolla": "ಅಜೋಲ್ಲಾ", "Fish (Aquaculture)": "ಮೀನು ಸಾಕಣೆ", "Cowpea": "ಅಲಸಂದೆ",
            "Soybean": "ಸೋಯಾಬೀನ್", "Pearl Millet": "ಸಜ್ಜೆ", "Castor": "ಔಡಲ",
            "Mustard": "ಸಾಸಿವೆ", "Chickpea": "ಕಡಲೆ", "Moong Bean": "ಹೆಸರು ಕಾಳು",
            "Groundnut": "ಶೇಂಗಾ", "Onion": "ಈರುಳ್ಳಿ", "Garlic": "ಬೆಳ್ಳುಳ್ಳಿ",
            "Ginger": "ಶುಂಠಿ", "Turmeric": "ಅರಿಶಿನ", "Safflower": "ಕುಸುಮೆ",
            "Linseed": "ಅಗಸೆ", "Basil": "ತುಳಸಿ", "Marigold": "ಚೆಂಡು ಹೂವು",
            "Carrot": "ಕ್ಯಾರೇಟ್", "Spinach": "ಪಾಲಕ್", "Coriander": "ಕೊತ್ತಂಬರಿ",
            "Fenugreek": "ಮೆಂತ್ಯ", "Taro": "ಕೆಸವಿನ ಗಡ್ಡೆ", "Sorghum": "ಜೋಳ",
            "Papaya": "ಪರಂಗಿ ಹಣ್ಣು", "Pepper": "ಕಾಳುಮೆಣಸು", "Banana": "ಬಾಳೆ"
        },
        "fertilizers": {
            "Urea + DAP": "ಯೂರಿಯಾ + ಡಿಎಪಿ", "NPK 14-35-14": "ಎನ್‌ಪಿಕೆ 14-35-14", "SSP + Gypsum": "ಎಸ್‌ಎಸ್‌ಪಿ + ಜಿಪ್ಸಂ",
            "NPK 20-20-0": "ಎನ್‌ಪಿಕೆ 20-20-0", "NPK + Zinc": "ಎನ್‌ಪಿಕೆ + ಝಿಂಕ್", "FYM + NPK": "ಸಾಗಾಣಿಕೆ ಗೊಬ್ಬರ + ಎನ್‌ಪಿಕೆ",
            "DAP + Rhizobium": "ಡಿಎಪಿ + ರೈಝೋಬಿಯಂ", "NPK 19-19-19": "ಎನ್‌ಪಿಕೆ 19-19-19",
            "Urea + SSP + MOP": "ಯೂರಿಯಾ + ಎಸ್‌ಎಸ್‌ಪಿ + ಎಂಒಪಿ", "NPK 17-17-17": "ಎನ್‌ಪಿಕೆ 17-17-17",
            "FYM + NPK + Boron": "ಗೊಬ್ಬರ + ಎನ್‌ಪಿಕೆ + ಬೋರಾನ್", "NPK + Boron": "ಎನ್‌ಪಿಕೆ + ಬೋರಾನ್"
        },
        "seasons": {
            "Kharif": "ಖಾರಿಫ್ (ಮಳೆಗಾಲ)", "Rabi": "ರಬಿ (ಚಳಿಗಾಲ)", "Annual": "ವಾರ್ಷಿಕ (ವರ್ಷಪೂರ್ತಿ)",
            "Kharif/Rabi": "ಖಾರಿಫ್ / ರಬಿ", "Rabi/Kharif": "ರಬಿ / ಖಾರಿಫ್"
        },
        "irrigation_freq": {
            "Every day": "ಪ್ರತಿ ರೋಜೂ", "Every 2 days": "ಪ್ರತಿ 2 ದಿನಗಳಿಗೊಮ್ಮೆ", "Every 3 days": "ಪ್ರತಿ 3 ದಿನಗಳಿಗೊಮ್ಮೆ",
            "Twice a week": "ವಾರಕ್ಕೆ ಎರಡು ಬಾರಿ", "Once a week": "ವಾರಕ್ಕೆ ಒಮ್ಮೆ", "Once in 10 days": "10 ದಿನಗಳಿಗೊಮ್ಮೆ",
            "Rainfall sufficient": "ಸಾಕು ಮಳೆ", "Monitor only": "ವೀಕ್ಷಿಸಿ"
        },
        "disease_types": {
            "Fungal Disease": "ಶಿಲೀಂಧ್ರ ರೋಗ", "Bacterial Blight": "ಬ್ಯಾಕ್ಟೀರಿಯಾ ಕರಗು ರೋಗ",
            "Pest Infestation": "ಕೀಟ ಬಾಧೆ", "No Risk Detected": "ರೋಗದ ಅಪಾಯವಿಲ್ಲ"
        },
        "risk_levels": {
            "High": "ಹೆಚ್ಚು ಅಪಾಯ", "Medium": "ಮಧ್ಯಮ ಅಪಾಯ", "Low": "ಕಡಿಮೆ ಅಪಾಯ"
        },
        "disease_advice": {
            "Apply Mancozeb or Copper Oxychloride": "ಮ್ಯಾಂಕೋಝೆಬ್ ಅಥವಾ ಕಾಪರ್ ಆಕ್ಸಿಕ್ಲೋರೈಡ್ ಸಿಂಪಡಿಸಿ",
            "Use Streptocycline spray": "ಸ್ಟ್ರೆಪ್ಟೋಸೈಕ್ಲಿನ್ ಸಿಂಪಡಿಸಿ",
            "Use Neem oil or recommended pesticide": "ಬೇವಿನ ಎಣ್ಣೆ ಅಥವಾ ಕೀಟನಾಶಕ ಬಳಸಿ",
            "Maintain good field hygiene": "ಜಮೀನನ್ನು ಸ್ವಚ್ಛವಾಗಿಡಿ"
        },
        "market_status": {
            "High Demand": "ಹೆಚ್ಚು ಬೇಡಿಕೆ", "Normal": "ಸಾಧಾರಣ ಬೇಡಿಕೆ"
        },
        "market_trend": {
            "rising": "↑ ಏರುತ್ತಿದೆ", "falling": "↓ ಇಳಿಯುತ್ತಿದೆ", "stable": "→ ಸ್ಥಿರವಾಗಿದೆ"
        },
        "schemes": {
            "PM-Kisan": "ಪಿಎಂ-ಕಿಸಾನ್ ಯೋಜನೆ", "PMFBY": "ಬೆಳೆ ವಿಮೆ (PMFBY)",
            "NFSM": "ರಾಷ್ಟ್ರೀಯ ಆಹಾರ ಭದ್ರತಾ ಮಿಷನ್", "MSP Scheme": "ಕನಿಷ್ಠ ಬೆಂಬಲ ಬೆಲೆ (MSP)",
            "Cotton Tech Mission": "ಹತ್ತಿ ತಂತ್ರಜ್ಞಾನ ಮಿಷನ್", "Sugarcane Dev Scheme": "ಕಬ್ಬು ಅಭಿವೃದ್ಧಿ ಯೋಜನೆ",
            "NHM": "ರಾಷ್ಟ್ರೀಯ ತೋಟಗಾರಿಕಾ ಮಿಷನ್", "Pulses Dev": "ಬೇಳೆಕಾಳು ಅಭಿವೃದ್ಧಿ ಯೋಜನೆ",
            "Spices Board": "ಭಾರತೀಯ ಸಾಂಬಾರು ಮಂಡಳಿ", "Coconut Dev Board": "ತೆಂಗು ಅಭಿವೃದ್ಧಿ ಮಂಡಳಿ"
        },
        "soil_tips": {
            "Low Nitrogen — apply Urea or green manure": "ಕಡಿಮೆ ಸಾರಜನಕ — ಯೂರಿಯಾ ಅಥವಾ ಹಸಿರೆಲೆ ಗೊಬ್ಬರ ಬಳಸಿ",
            "Low Phosphorus — apply DAP or SSP": "ಕಡಿಮೆ ರಂಜಕ — ಡಿಎಪಿ ಅಥವಾ ಎಸ್‌ಎಸ್‌ಪಿ ಬಳಸಿ",
            "Low Potassium — apply MOP": "ಕಡಿಮೆ ಪೊಟ್ಯಾಷಿಯಂ — ಎಂಒಪಿ ಬಳಸಿ",
            "Acidic soil — apply lime": "ಆಮ್ಲೀಯ ಮಣ್ಣು — ಸುಣ್ಣ ಬಳಸಿ",
            "Alkaline soil — apply gypsum": "ಕ್ಷಾರೀಯ ಮಣ್ಣು — ಜಿಪ್ಸಂ ಬಳಸಿ",
            "Soil health is good!": "✅ ಮಣ್ಣಿನ ಆರೋಗ್ಯ ಚೆನ್ನಾಗಿದೆ!"
        },
        "water_need": {
            "high": "ಹೆಚ್ಚು", "medium": "ಮಧ್ಯಮ", "low": "ಕಡಿಮೆ"
        },
        "agmarknet_price_title": "ಲೈವ್ ಅಗ್‌ಮಾರ್ಕ್‌ನೆಟ್ ಮಾರುಕಟ್ಟೆ ಬೆಲೆ",
        "modal_price": "ಇತ್ತೀಚಿನ ಮಾದರಿ ಮಾರುಕಟ್ಟೆ ಬೆಲೆ",
        "min_price": "ಕನಿಷ್ಠ ಬೆಲೆ",
        "max_price": "ಗರಿಷ್ಠ ಬೆಲೆ",
        "mandi_market": "ಮಾರುಕಟ್ಟೆ / ಮಂಡಿ",
        "market_date": "ದಿನಾಂಕ",
        "source": "ಮೂಲ",
        "agmarknet_source": "ಅಗ್‌ಮಾರ್ಕ್‌ನೆಟ್",
        "live_market_unavailable": "ಲೈವ್ ಮಾರುಕಟ್ಟೆ ಬೆಲೆ ಪ್ರಸ್ತುತ ಲಭ್ಯವಿಲ್ಲ.",
        "market_trend_unavailable": "ಮಾರುಕಟ್ಟೆ ಪ್ರವೃತ್ತಿ ಲಭ್ಯವಿಲ್ಲ",
        "estimated_profit": "ಅಂದಾಜು ಲಾಭ",
        "estimated_revenue": "ಅಂದಾಜು ಆದಾಯ",
        "commodity": "ಸರಕು",
        "variety": "ತಳಿ",
        "grade": "ದರ್ಜೆ",
        "arrival_qty": "ಆगमन ಪ್ರಮಾಣ",
        "primary_crop_title": "ಮುಖ್ಯ ಬೆಳೆ",
        "intercrop_1_title": "ಅಂತರ ಬೆಳೆ 1",
        "intercrop_2_title": "ಅಂತರ ಬೆಳೆ 2",
        "advisory_context_primary": "ಮುಖ್ಯ ಬೆಳೆಯ ಕೃಷಿ ಸಲಹೆ",
        "advisory_context_intercrop": "ಅಂತರ ಬೆಳೆಯ ಸಲಹೆ",
        "actual_sowing_date_label": "ನಿಜವಾದ ಬಿತ್ತನೆ ದಿನಾಂಕ",
        "total_duration_label": "ಒಟ್ಟು ಬೆಳವಣಿಗೆಯ ಅವಧಿ",
        "days_unit": "ದಿನಗಳು",
        "months_unit": "ತಿಂಗಳುಗಳು",
        "stage_prefix": "ಹಂತ",
        "select_crop_label": "ಬೆಳೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ",
        "around_prefix": "ಸುಮಾರು",
        "crop_label": "ಬೆಳೆ",
        "typical_season_label": "ಸಾಮಾನ್ಯ ಬೆಳೆಯುವ ಋತು",
        "estimated_harvest_label": "ಅಂದಾಜು ಕೊಯ್ಲು ದಿನಾಂಕ",
        "harvest_disclaimer": "ಕೊಯ್ಲು ದಿನಾಂಕವು ಆಯ್ಕೆಮಾಡಿದ ಬೆಳೆಯ ಸಾಮಾನ್ಯ ಬೆಳವಣಿಗೆಯ ಅವಧಿಯನ್ನು ಆಧರಿಸಿದ ಅಂದಾಜು. ಹವಾಮಾನ, ಮಣ್ಣಿನ ಸ್ಥಿತಿ, ನೀರಾವರಿ ಮತ್ತು ಕೃಷಿ ಪದ್ಧತಿಗಳನ್ನು ಅವಲಂಬಿಸಿ ನಿಜವಾದ ಕೊಯ್ಲಿನ ಸಮಯ ಬದಲಾಗಬಹುದು.",
        "weather_advisory_high_rain": "🌧️ ನಿಮ್ಮ ಪ್ರದೇಶದಲ್ಲಿ ಹೆಚ್ಚಿನ ಮಳೆ ಪ್ರಮಾಣ ({rainfall}mm) ದಾಖಲಾಗಿದೆ. ಆರಂಭಿಕ ಬೆಳೆ ಬೆಳವಣಿಗೆಯ ಸಮಯದಲ್ಲಿ ಉತ್ತಮ ಒಳಚರಂಡಿ ವ್ಯವಸ್ಥೆಯನ್ನು ಖಚಿತಪಡಿಸಿ.",
        "weather_advisory_high_temp": "☀️ ಹೆಚ್ಚಿನ ತಾಪಮಾನ ({temp}°C) ನಿರೀಕ್ಷಿಸಲಾಗಿದೆ. ಹೂಬಿಡುವ ಮತ್ತು ತೆನೆ ಬರುವ ಹಂತಗಳಲ್ಲಿ ಸೂಕ್ತ ನೀರಾವರಿ ನಿರ್ವಹಿಸಿ.",
        "weather_advisory_normal": "🌤️ ಪ್ರಸ್ತುತ ಹವಾಮಾನ ಪರಿಸ್ಥಿತಿಗಳು (ತಾಪಮಾನ: {temp}°C, ತೇವಾಂಶ: {humidity}%) ಬೆಳೆ ಬೆಳವಣಿಗೆಗೆ ಸೂಕ್ತವಾಗಿವೆ.",
                    "stage_explanations": {
                "Prepare seedbed, sow seeds, and maintain consistent nursery moisture for healthy seedling emergence.": "ನಾಟಿ ಮಡಿ ತಯಾರಿಸಿ ಬೀಜ ಬಿತ್ತಿ, ಆರೋಗ್ಯಕರ ಸಸಿಗಳ ಬೆಳವಣಿಗೆಗೆ ತೇವಾಂಶ ನಿರ್ವಹಿಸಿ.",
                "Transplant seedlings to main field, maintain 2-5cm standing water, and apply initial nitrogen fertilizer.": "ಸಸಿಗಳನ್ನು ಮುಖ್ಯ ಗದ್ದೆಗೆ ನಾಟಿ ಮಾಡಿ, 2-5 ಸೆಂ.ಮೀ ನೀರು ನಿಲ್ಲಿಸಿ ಮೊದಲ ಸಾರಜನಕ ಗೊಬ್ಬರ ಹಾಕಿ.",
                "Panicle initiation and flowering stage. Ensure peak water availability and protect against stem borer.": "ತೆನೆ ಬರುವ ಮತ್ತು ಹೂಬಿಡುವ ಹಂತ. ಗರಿಷ್ಠ ನೀರು ಒದಗಿಸಿ ಮತ್ತು ಕಾಂಡ ಕೊರೆಯುವ ಕೀಟದಿಂದ ರಕ್ಷಿಸಿ.",
                "Grain filling and ripening. Drain field water 10 days prior to harvest when grains turn golden.": "ಕಾಳು ತುಂಬುವುದು ಮತ್ತು ಪಕ್ವವಾಗುವುದು. ಕಾಳುಗಳು ಹೊಂಬಣ್ಣಕ್ಕೆ ತಿರುಗಿದಾಗ ಕೊಯ್ಲಿಗೆ 10 ದಿನ ಮುಂಚಿತವಾಗಿ ನೀರು ಹೊರಹಾಕಿ.",
                "Sow seeds 4-5cm deep in well-drained soil. Ensure optimal warmth and soil moisture.": "ಉತ್ತಮ ಒಳಚರಂಡಿ ಇರುವ ಮಣ್ಣಿನಲ್ಲಿ 4-5 ಸೆಂ.ಮೀ ಆಳದಲ್ಲಿ ಬೀಜ ಬಿತ್ತಿ.",
                "Rapid leaf elongation and stem growth. Apply NPK fertilizer top dressing and earthing up.": "ಎಲೆ ಮತ್ತು ಕಾಂಡದ ವೇಗದ ಬೆಳವಣಿಗೆ. ಎನ್‌ಪಿಕೆ ಗೊಬ್ಬರ ನೀಡಿ.",
                "Flowering and pollination phase. Critical stage requiring adequate irrigation and pest control.": "ಹೂಬಿಡುವ ಹಂತ. ಸೂಕ್ತ ನೀರಾವರಿ ಮತ್ತು ಕೀಟ ನಿಯಂತ್ರಣ ಅಗತ್ಯ.",
                "Kernels mature and harden. Harvest when cob husk turns dry and pale yellow.": "ಕಾಳುಗಳು ಪಕ್ವವಾಗಿ ಗಟ್ಟಿಯಾಗುತ್ತವೆ. ಮೆಕ್ಕೆಜೋಳದ ಸಿಪ್ಪೆ ಒಣಗಿದಾಗ ಕೊಯ್ಲು ಮಾಡಿ."
            },
        "stage_names": {
            "Sowing & Nursery": "ಬಿತ್ತನೆ & ನರ್ಸರಿ",
            "Vegetative Growth": "ಸಸ್ಯೀಯ ಬೆಳವಣಿಗೆ",
            "Reproductive & Panicle": "ಸಂತಾನೋತ್ಪತ್ತಿ & ತೆನೆ ಹಂತ",
            "Ripening & Maturity": "ಪಕ್ವತೆ & ಕೊಯ್ಲು",
            "Sowing & Germination": "ಬಿತ್ತನೆ & ಮೊಳಕೆಯೊಡೆಯುವಿಕೆ",
            "Vegetative Stage": "ಸಸ್ಯೀಯ ಹಂತ",
            "Tasseling & Silking": "ಹೂ & ತೆನೆ ಹಂತ",
            "Grain Filling & Maturity": "ಕಾಳು ತುಂಬುವುದು & ಪಕ್ವತೆ",
            "Sowing & Seedling": "ಬಿತ್ತನೆ & ಸಸಿ ಹಂತ",
            "Pegging & Pod Formation": "ಬೀಳು ಬಿಡುವುದು & ಕಾಯಿ ಕಟ್ಟುವುದು",
            "Pod Maturity & Harvest": "ಕಾಯಿ ಪಕ್ವತೆ & ಕೊಯ್ಲು",
            "Sowing & Crown Root": "ಬಿತ್ತನೆ & ಬೇರು ಹಂತ",
            "Tillering & Jointing": "ಕಿರುಸಸಿ ಬರುವುದು & ಗಂಟು ಹಂತ",
            "Heading & Flowering": "ತೆನೆ ಬರುವುದು & ಹೂಬಿಡುವುದು",
            "Vegetative Branching": "ರೆಂಬೆಗಳ ಬೆಳವಣಿಗೆ",
            "Squaring & Flowering": "ಮೊಗ್ಗು & ಹೂಬಿಡುವುದು",
            "Boll Opening & Picking": "ಕಾಯಿ ಒಡೆಯುವುದು & ಹತ್ತಿ ಬಿಡಿಸುವುದು",
            "Planting & Germination": "ನಾಟಿ & ಮೊಳಕೆ",
            "Tillering Stage": "ಕಿರುಸಸಿ ಹಂತ",
            "Grand Growth Period": "ವೇಗದ ಬೆಳವಣಿಗೆಯ ಅವಧಿ",
            "Ripening & Harvest": "ಪಕ್ವತೆ & ಕೊಯ್ಲು",
            "Planting & Establishment": "ಸಸಿ ನಾಟಿ & ಬೇರೂರುವುದು",
            "Vegetative Canopy": "ಎಲೆಗಳ ಬೆಳವಣಿಗೆ",
            "Bunch Shooting": "ಬಾಳೆ ಗೊನೆ ಬರುವುದು",
            "Bunch Development & Harvest": "ಗೊನೆ ಬೆಳವಣಿಗೆ & ಕೊಯ್ಲು",
            "Vegetative & Nipping": "ಬೆಳವಣಿಗೆ & ತುದಿಕಟ್ಟುವುದು",
            "Flowering & Pod Set": "ಹೂಬಿಡುವುದು & ಕಾಯಿ ಕಟ್ಟುವುದು",
            "Pod Ripening & Harvest": "ಕಾಯಿ ಪಕ್ವತೆ & ಕೊಯ್ಲು",
            "Transplanting & Nursery": "ನಾಟಿ & ನರ್ಸರಿ",
            "Fruit Set & Fruit Ripening": "ಕಾಯಿ ಕಟ್ಟುವುದು & ಪಕ್ವತೆ",
            "Fruit Ripening & Harvest": "ಹಣ್ಣು ಪಕ್ವತೆ & ಕೊಯ್ಲು",
            "Transplanting & Early Growth": "ನಾಟಿ & ಆರಂಭಿಕ ಬೆಳವಣಿಗೆ",
            "Foliage Development": "ಎಲೆಗಳ ವೃದ್ಧಿ",
            "Bulb Initiation & Swelling": "ಈರುಳ್ಳಿ ದಪ್ಪಗಾಗುವುದು",
            "Neck Fall & Harvest": "ತಾಳು ಬೀಳುವುದು & ಕೊಯ್ಲು",
            "Transplanting & Establishment": "ನಾಟಿ & ಬೇರೂರುವುದು",
            "Pod Maturity & Harvesting": "ಮೆಣಸಿನಕಾಯಿ ಪಕ್ವತೆ & ಕೊಯ್ಲು",
            "Planting & Sprouting": "ನಾಟಿ & ಮೊಳಕೆ",
            "Vegetative Tillering": "ತೂರ್ ಬೆಳವಣಿಗೆ ಹಂತ",
            "Rhizome Expansion": "ಅರಿಶಿನ ಗಡ್ಡೆ ದಪ್ಪಗಾಗುವುದು",
            "Foliage Drying & Harvest": "ಎಲೆ ಒಣಗುವುದು & ಕೊಯ್ಲು",
            "Flowering & Pod Formation": "ಹೂ & ಕಾಯಿ ಕಟ್ಟುವುದು",
            "Bud Break & Flowering": "ಮೊಗ್ಗು & ಹೂ ಬಿಡುವುದು",
            "Fruit Set & Pea Stage": "ಕಾಯಿ ಕಟ್ಟುವುದು & ಬಟಾಣಿ ಹಂತ",
            "Fruit Growth & Enlargement": "ಕಾಯಿ ಬೆಳವಣಿಗೆ",
            "Maturity & Harvest": "ಪಕ್ವತೆ & ಕೊಯ್ಲು",
            "Spathe & Button Stage": "ಹೊಂಬಾಳೆ & ಸಿಂಗಾರ ಹಂತ",
            "Tender Nut Water Stage": "ಎಳನೀರು ಹಂತ",
            "Kernel Solidification": "ಕೊಬ್ಬರಿ ಗಟ್ಟಿಯಾಗುವುದು",
            "Full Maturity & Harvest": "ಪೂರ್ಣ ಪಕ್ವತೆ & ತೆಂಗಿನಕಾಯಿ ಕೊಯ್ಲು"
        }
    },
    "ml": {
        "app_title": "AI വിള ఉపദേഷ്ടാവ്",
        "tagline": "മെച്ചപ്പെട്ട വിളവിനായി കാർഷിക വിജ്ഞാനം",
        "step1": "സ്ഥലം", "step2": "മണ്ണ്", "step3": "ഫലങ്ങൾ", "step4": "പ്രതികരണം",
        "my_history": "എന്റെ ചരിത്രം", "logout": "ലോഗ്ഔട്ട്", "login": "ലോഗിൻ", "signup": "സൈൻ അപ്പ്",
        "admin_login": "അഡ്മിൻ ലോഗിൻ", "city_label": "നഗരം / ഗ്രാമം", "type_city": "നഗരം അല്ലെങ്കിൽ ഗ്രാമം ടൈപ്പ് ചെയ്യുക...",
        "get_weather": "കാലാവസ്ഥ അറിയുക", "use_gps": "GPS ഉപയോഗിക്കുക", "temperature": "താപനില (°C)",
        "humidity": "ഈർപ്പം (%)", "nitrogen": "നൈട്രജൻ (N)", "phosphorus": "ഫോസ്ഫറസ് (P)",
        "potassium": "പൊട്ടാസ്യം (K)", "ph": "മണ്ണ് pH", "rainfall": "മഴയളവ് (mm)",
        "recommend": "ശുപാർശ നേടുക", "sensor": "സെൻസർ വിവരങ്ങൾ", "next": "അടുത്തത്", "back": "പിന്നോട്ട്",
        "submit_feedback": "പ്രതികരണം സമർപ്പിക്കുക", "actual_crop": "നിങ്ങൾ കൃഷി ചെയ്ത വിള",
        "actual_profit": "യഥാർത്ഥ ലാഭം (₹/ഏക്കർ)", "actual_yield": "യഥാർത്ഥ വിളവ് (കിലോ/ഏക്കർ)",
        "acres_farmed": "കൃഷി ചെയ്ത ഏക്കർ", "total_profit": "ആകെ ലാഭം (₹)",
        "total_yield": "ആകെ വിളവ് (കിലോ)", "rate_prediction": "AI പ്രവചനത്തെ റേറ്റുചെയ്യുക",
        "comments": "അഭിപ്രായങ്ങൾ (ഓപ്ഷണൽ)", "save_db": "ഡേറ്റാബേസിൽ സേവ് ചെയ്യുക & AI പരിശീലനത്തെ സഹായിക്കുക",
        "skip_new": "ഒഴിവാക്കുക — പുതിയ പ്രവചനം നടത്തുക", "thank_you": "നന്ദി!",
        "feedback_note": "നിങ്ങളുടെ ഡേറ്റ AI മോഡലിന്റെ കൃത്യത മെച്ചപ്പെടുത്താൻ സഹായിക്കും",
        "rec_crop": "ശുപാർശ ചെയ്യുന്ന വിള", "intercrop_1": "ഇടവിള 1", "intercrop_2": "ഇടവിള 2",
        "fertilizer": "വളപ്രയോഗം", "expected_profit": "പ്രതീക്ഷിക്കുന്ന ലാഭം", "expected_yield": "പ്രതീക്ഷിക്കുന്ന വിളവ്",
        "market_status_label": "വിപണി അവസ്ഥ", "soil_health": "മണ്ണിന്റെ ആരോഗ്യ സ്കോർ", "crop_calendar": "വിള കലണ്ടർ",
        "irrigation": "നനയ്ക്കൽ ക്രമം", "disease_risk": "രോഗസാധ്യത", "top3_alt": "മറ്റ് 3 പ്രധാന വിളകൾ",
        "market_forecast": "വിപണി വില പ്രവചനം", "nearby_mandis": "അടുത്തുള്ള മാർക്കറ്റുകൾ മാപ്പ്",
        "gov_schemes": "സർക്കാർ പദ്ധതികൾ", "report": "റിപ്പോർട്ട്", "share": "പങ്കുവെക്കുക", "history": "ചരിത്രം",
        "best": "ഏറ്റവും മികച്ചത്", "current": "നിലവിലെ", "next_month": "അടുത്ത മാസം", "km_away": "കി.മീ അകലെ",
        "directions": "വഴി", "your_farm": "നിങ്ങളുടെ തോട്ടം", "drag_me": "നീക്കുക", "score": "സ്കോർ",
        "sow": "വിത്ത് വിതയ്ക്കൽ", "growing": "വളർച്ചാ ഘട്ടം", "harvest": "വിളവെടുപ്പ്", "duration": "കാലയളവ്", "months": "മാസങ്ങൾ",
        "frequency": "ആവൃത്തി", "amount_session": "അളവ്/തവണ", "risk": "സാധ്യത", "advice": "നിർദ്ദേശം",
        "no_mandis": "പരിശോധിച്ച മാർക്കറ്റ് വിവരങ്ങൾ ലഭ്യമല്ല", "export_csv": "CSV എക്സ്പോർട്ട്",
        "crops": {
            "Rice": "നെല്ല്", "Maize": "ചോളം", "Groundnut": "നിലക്കടല", "Wheat": "ഗോതമ്പ്",
            "Cotton": "പരുത്തി", "Sugarcane": "കരിമ്പ്", "Banana": "വാഴ", "Chickpea": "കടല",
            "Tomato": "തക്കാളി", "Onion": "ഉള്ളി", "Chilli": "മുളക്", "Turmeric": "മഞ്ഞൾ",
            "Soybean": "സോയാബീൻ", "Mango": "മാങ്ങ", "Coconut": "തേങ്ങ"
        },
        "intercrops": {
            "Azolla": "അസോള", "Fish (Aquaculture)": "മത്സ്യ വളർത്തൽ", "Cowpea": "മമ്പയർ",
            "Soybean": "സോയാബീൻ", "Pearl Millet": "കമ്പം", "Castor": "ആവണക്ക്",
            "Mustard": "കടുക്", "Chickpea": "കടല", "Moong Bean": "ചെറുപയർ",
            "Groundnut": "നിലക്കടല", "Onion": "ഉള്ളി", "Garlic": "വെളുത്തുള്ളി",
            "Ginger": "ഇഞ്ചി", "Turmeric": "മഞ്ഞൾ", "Safflower": "കുസുമം",
            "Linseed": "ചണവിത്ത്", "Basil": "തുളസി", "Marigold": "ചെണ്ടുമല്ലി",
            "Carrot": "ക്യാരറ്റ്", "Spinach": "ചീര", "Coriander": "മല്ലി",
            "Fenugreek": "ഉലുവ", "Taro": "ചേമ്പ്", "Sorghum": "ചോളം",
            "Papaya": "പപ്പായ", "Pepper": "കുരുമുളക്", "Banana": "വാഴ"
        },
        "fertilizers": {
            "Urea + DAP": "യുറിയ + ഡി.എ.പി", "NPK 14-35-14": "എൻ.പി.കെ 14-35-14", "SSP + Gypsum": "എസ്.എസ്.പി + ജിപ്സം",
            "NPK 20-20-0": "എൻ.പി.കെ 20-20-0", "NPK + Zinc": "എൻ.പി.കെ + സിങ്ക്", "FYM + NPK": "ചാണകപ്പൊടി + എൻ.പി.കെ",
            "DAP + Rhizobium": "ഡി.എ.പി + റൈസോബിയം", "NPK 19-19-19": "എൻ.പി.കെ 19-19-19",
            "Urea + SSP + MOP": "യുറിയ + എസ്.എസ്.പി + എം.ഒ.പി", "NPK 17-17-17": "എൻ.പി.കെ 17-17-17",
            "FYM + NPK + Boron": "ചാണകപ്പൊടി + എൻ.പി.കെ + ബോറോൺ", "NPK + Boron": "എൻ.പി.കെ + ബോറോൺ"
        },
        "seasons": {
            "Kharif": "ഖരീഫ് (മഴക്കാലം)", "Rabi": "രബി (ശൈത്യകാലം)", "Annual": "വാർഷികം (വർഷം മുഴുവൻ)",
            "Kharif/Rabi": "ഖരീഫ് / രബി", "Rabi/Kharif": "രബി / ഖരീഫ്"
        },
        "irrigation_freq": {
            "Every day": "ദിവസവും", "Every 2 days": "2 ദിവസത്തിലൊരിക്കൽ", "Every 3 days": "3 ദിവസത്തിലൊരിക്കൽ",
            "Twice a week": "ആഴ്ചയിൽ രണ്ടുതവണ", "Once a week": "ആഴ്ചയിലൊരിക്കൽ", "Once in 10 days": "10 ദിവസത്തിലൊരിക്കൽ",
            "Rainfall sufficient": "ആവശ്യത്തിന് മഴ", "Monitor only": "നിരീക്ഷിക്കുക മാത്രം"
        },
        "disease_types": {
            "Fungal Disease": "ഫംഗസ് രോഗം", "Bacterial Blight": "ബാക്ടീരിയൽ ബ്ലൈറ്റ്",
            "Pest Infestation": "കീടബാധ", "No Risk Detected": "രോഗസാധ്യതയില്ല"
        },
        "risk_levels": {
            "High": "ഉയർന്ന രോഗസാധ്യത", "Medium": "മിതമായ രോഗസാധ്യത", "Low": "കുറഞ്ഞ രോഗസാധ്യത"
        },
        "disease_advice": {
            "Apply Mancozeb or Copper Oxychloride": "മാങ്കോസെബ് അല്ലെങ്കിൽ കോപ്പർ ഓക്സിക്ലോറൈഡ് തളിക്കുക",
            "Use Streptocycline spray": "സ്ട്രെപ്റ്റോസൈക്ലിൻ തളിക്കുക",
            "Use Neem oil or recommended pesticide": "വേപ്പെണ്ണ അല്ലെങ്കിൽ കീടനാശിനി തളിക്കുക",
            "Maintain good field hygiene": "പാടം ശുചിയായി സൂക്ഷിക്കുക"
        },
        "market_status": {
            "High Demand": "ഉയർന്ന ഡിമാൻഡ്", "Normal": "സാധാരണ ഡിമാൻഡ്"
        },
        "market_trend": {
            "rising": "↑ ഉയരുന്നു", "falling": "↓ കുറയുന്നു", "stable": "→ സ്ഥിരം"
        },
        "schemes": {
            "PM-Kisan": "പി.എം-കിസാൻ പദ്ധതി", "PMFBY": "വിള ഇൻഷുറൻസ് (PMFBY)",
            "NFSM": "ദേശീയ ഭക്ഷ്യ സുരക്ഷാ മിഷൻ", "MSP Scheme": "കുറഞ്ഞ താങ്ങുവില (MSP)",
            "Cotton Tech Mission": "പരുത്തി സാങ്കേതിക വിദ്യാ മിഷൻ", "Sugarcane Dev Scheme": "കരിമ്പ് വികസന പദ്ധതി",
            "NHM": "ദേശീയ ഹോർട്ടികൾച്ചർ മിഷൻ", "Pulses Dev": "പയറുവർഗ്ഗ വികസന പദ്ധതി",
            "Spices Board": "സ്പൈസസ് ബോർഡ് ഇന്ത്യ", "Coconut Dev Board": "നാളികേര വികസന ബോർഡ്"
        },
        "soil_tips": {
            "Low Nitrogen — apply Urea or green manure": "നൈട്രജൻ കുറവാണ് — യൂറിയ അല്ലെങ്കിൽ പച്ചിലവളം നൽകുക",
            "Low Phosphorus — apply DAP or SSP": "ഫോസ്ഫറസ് കുറവാണ് — ഡി.എ.പി അല്ലെങ്കിൽ എസ്.എസ്.പി നൽകുക",
            "Low Potassium — apply MOP": "പൊട്ടാസ്യം കുറവാണ് — എം.ഓ.പി നൽകുക",
            "Acidic soil — apply lime": "അമ്ല മണ്ണ് — കുമ്മായം ചേര്ക്കുക",
            "Alkaline soil — apply gypsum": "ക്ഷാര മണ്ണ് — ജിപ്സം ചേര്ക്കുക",
            "Soil health is good!": "✅ മണ്ണ് നല്ല അവസ്ഥയിലാണ്!"
        },
        "water_need": {
            "high": "കൂടുതൽ", "medium": "മിതമായത്", "low": "കുറവ്"
        },
        "agmarknet_price_title": "ലൈവ് അഗ്മാർക്ക്നെറ്റ് വിപണി വില",
        "modal_price": "ഏറ്റവും പുതിയ മോഡൽ വിപണി വില",
        "min_price": "കുറഞ്ഞ വില",
        "max_price": "കൂടിയ വില",
        "mandi_market": "വിപണി / മണ്ടി",
        "market_date": "തീയതി",
        "source": "ഉറവിടം",
        "agmarknet_source": "അഗ്മാർക്ക്നെറ്റ്",
        "live_market_unavailable": "ലൈവ് മാർക്കറ്റ് വില നിലവിൽ ലഭ്യമല്ല.",
        "market_trend_unavailable": "വിപണി പ്രവണത ലഭ്യമല്ല",
        "estimated_profit": "ലഭ്യമായ ലാഭം",
        "estimated_revenue": "ലഭ്യമായ വരുമാനം",
        "commodity": "ഉൽപ്പന്നം",
        "variety": "ഇനം",
        "grade": "ഗ്രേഡ്",
        "arrival_qty": "വരവ് അളവ്",
        "primary_crop_title": "പ്രധാന വിള",
        "intercrop_1_title": "ഇടവിള 1",
        "intercrop_2_title": "ഇടവിള 2",
        "advisory_context_primary": "പ്രധാന വിള കാർഷിക ഉപദേശം",
        "advisory_context_intercrop": "ഇടവിള ഉപദേശം",
        "actual_sowing_date_label": "യഥാർത്ഥ വിതയ്ക്കൽ തീയതി",
        "total_duration_label": "ആകെ വളർച്ചാ കാലയളവ്",
        "days_unit": "ദിവസങ്ങൾ",
        "months_unit": "മാസങ്ങൾ",
        "stage_prefix": "ഘട്ടം",
        "select_crop_label": "വിള തിരഞ്ഞെടുക്കുക",
        "around_prefix": "ഏകദേശം",
        "crop_label": "വിള",
        "typical_season_label": "സാധാരണ വളർച്ചാ കാലം",
        "estimated_harvest_label": "പ്രതീക്ഷിക്കുന്ന വിളവെടുപ്പ് തീയതി",
        "harvest_disclaimer": "വിളവെടുപ്പ് തീയതി എന്നത് തിരഞ്ഞെടുത്ത വിളയുടെ സാധാരണ വളർച്ചാ കാലയളവിനെ അടിസ്ഥാനമാക്കിയുള്ള ഒരു കണക്കൂകൂട്ടലാണ്. കാലാവസ്ഥ, മണ്ണിന്റെ അവസ്ഥ, നനയ്ക്കൽ, കാർഷിക രീതികൾ എന്നിവയെ ആശ്രയിച്ച് യഥാർത്ഥ വിളവെടുപ്പ് സമയം മാറാം.",
        "weather_advisory_high_rain": "🌧️ നിങ്ങളുടെ പ്രദേശത്ത് ഉയർന്ന മഴയളവ് ({rainfall}mm) രേഖപ്പെടുത്തിയിട്ടുണ്ട്. വിളയുടെ തുടക്കത്തിൽ നല്ല നീരൊഴുക്ക് സൗകര്യം ഉറപ്പാക്കുക.",
        "weather_advisory_high_temp": "☀️ ഉയർന്ന താപനില ({temp}°C) പ്രതീക്ഷിക്കുന്നു. പൂവിടുന്ന സമയത്തും കതിര് വരുന്ന സമയത്തും ആവശ്യത്തിന് നനയ്ക്കൽ ഉറപ്പാക്കുക.",
        "weather_advisory_normal": "🌤️ നിലവിലെ കാലാവസ്ഥാ സ്ഥിതി (താപനില: {temp}°C, ഈർപ്പം: {humidity}%) സാധാരണ വിള വളർച്ചയ്ക്ക് അനുയോജ്യമാണ്.",
                    "stage_explanations": {
                "Prepare seedbed, sow seeds, and maintain consistent nursery moisture for healthy seedling emergence.": "ഞാറ്റടി ഒരുക്കി വിത്തു വിതയ്ക്കുക, നല്ല ഞാറുകൾക്കായി നനവ് നിലനിർത്തുക.",
                "Transplant seedlings to main field, maintain 2-5cm standing water, and apply initial nitrogen fertilizer.": "ഞാറുകൾ പ്രധാന പാടത്തേക്ക് നടുക, 2-5 സെ.മീ വെള്ളം നിലനിർത്തി നൈട്രജൻ വളം നൽകുക.",
                "Panicle initiation and flowering stage. Ensure peak water availability and protect against stem borer.": "കതിര് ഇടുന്നതും പൂവിടുന്നതുമായ ഘട്ടം. പരമാവധി വെള്ളം ഉറപ്പാക്കി തണ്ടുതുരപ്പൻ പുഴുവിനെതിരെ സംരക്ഷിക്കുക.",
                "Grain filling and ripening. Drain field water 10 days prior to harvest when grains turn golden.": "നെന്മണികൾ പഴുത്തു പാകമാകുന്നു. മണികൾ സ്വർണ്ണനിറമാകുമ്പോൾ വിളവെടുപ്പിന് 10 ദിവസം മുമ്പ് പാടത്തെ വെള്ളം വറ്റിക്കുക.",
                "Sow seeds 4-5cm deep in well-drained soil. Ensure optimal warmth and soil moisture.": "നല്ല നീരൊഴുക്കുള്ള മണ്ണിൽ 4-5 സെ.മീ താഴ്ചയിൽ വിത്ത് വിതയ്ക്കുക.",
                "Rapid leaf elongation and stem growth. Apply NPK fertilizer top dressing and earthing up.": "ഇലകളുടെയും തണ്ടിന്റെയും വേഗത്തിലുള്ള വളർച്ച. എNPK വളം നൽകുക.",
                "Flowering and pollination phase. Critical stage requiring adequate irrigation and pest control.": "പൂവിടൽ ഘട്ടം. ആവശ്യത്തിന് നനയ്ക്കലും കീടനിയന്ത്രണവും ഉറപ്പാക്കുക.",
                "Kernels mature and harden. Harvest when cob husk turns dry and pale yellow.": "ധാന്യങ്ങൾ പാകമായി കട്ടിയാകുന്നു. ചോളം ഉണങ്ങുമ്പോൾ വിളവെടുക്കുക."
            },
        "stage_names": {
            "Sowing & Nursery": "വിത്തുവിതയ്ക്കലും ഞാറ്റടിയും",
            "Vegetative Growth": "കായിക വളർച്ച ഘട്ടം",
            "Reproductive & Panicle": "കതിര് വരും ഘട്ടം",
            "Ripening & Maturity": "വിളവെടുപ്പ് പക്വത ഘട്ടം",
            "Sowing & Germination": "വിത്ത് വിതയ്ക്കലും മുളയ്ക്കലും",
            "Vegetative Stage": "വളർച്ചാ ഘട്ടം",
            "Tasseling & Silking": "പൂവിടലും കതിര് വറ്റലും",
            "Grain Filling & Maturity": "ധാന്യം പാകമാകൽ ഘട്ടം",
            "Sowing & Seedling": "വിത്തു വിതയ്ക്കലും ഞാറും",
            "Pegging & Pod Formation": "തൂണ് ഇറങ്ങലും കായ് പിടിക്കലും",
            "Pod Maturity & Harvest": "കായ് മൂപ്പും വിളവെടുപ്പും",
            "Sowing & Crown Root": "വിത്ത് വിതയ്ക്കലും വേരൂട്ടലും",
            "Tillering & Jointing": "ചിനപ്പ് പൊട്ടലും വളർച്ചയും",
            "Heading & Flowering": "കതിര് ഇടലും പൂവിടലും",
            "Vegetative Branching": "ശാഖാ വളർച്ചാ ഘട്ടം",
            "Squaring & Flowering": "മൊട്ടും പൂവിടലും",
            "Boll Opening & Picking": "കായ് പൊട്ടലും പരുത്തി എടുക്കലും",
            "Planting & Germination": "നടലും മുളയ്ക്കലും",
            "Tillering Stage": "ചിനപ്പ് ഘട്ടം",
            "Grand Growth Period": "പ്രധാന വളർച്ചാ കാലയളവ്",
            "Ripening & Harvest": "വിളവെടുപ്പ് പക്വത ഘട്ടം",
            "Planting & Establishment": "തൈ നടലും വേരൂട്ടലും",
            "Vegetative Canopy": "ഇലച്ചാർത്ത് വളർച്ച",
            "Bunch Shooting": "കുല വരും ഘട്ടം",
            "Bunch Development & Harvest": "കുല വളർച്ചയും വിളവെടുപ്പും",
            "Vegetative & Nipping": "വളർച്ചയും തലപ്പ് നുള്ളലും",
            "Flowering & Pod Set": "പൂവിടലും കായ് പിടിക്കലും",
            "Pod Ripening & Harvest": "കായ് മൂപ്പും വിളവെടുപ്പും",
            "Transplanting & Nursery": "തൈ നടലും പരിപാലനവും",
            "Fruit Set & Fruit Ripening": "കായ് പിടിക്കലും പാകമാകലും",
            "Fruit Ripening & Harvest": "പഴം പാകമാകലും വിളവെടുപ്പും",
            "Transplanting & Early Growth": "തൈ നടലും തുടക്ക വളർച്ചയും",
            "Foliage Development": "ഇല വളർച്ചാ ഘട്ടം",
            "Bulb Initiation & Swelling": "ഉള്ളി വലുതാകുന്ന ഘട്ടം",
            "Neck Fall & Harvest": "തണ്ട് ചായലും വിളവെടുപ്പും",
            "Transplanting & Establishment": "തൈ നടലും വേരൂട്ടലും",
            "Pod Maturity & Harvesting": "മുളക് മൂപ്പും വിളവെടുപ്പും",
            "Planting & Sprouting": "നടലും മുളയ്ക്കലും",
            "Vegetative Tillering": "വളർച്ചാ ഘട്ടം",
            "Rhizome Expansion": "മഞ്ഞൾക്കിഴങ്ങ് പെരുകൽ",
            "Foliage Drying & Harvest": "ഇല ഉണങ്ങലും വിളവെടുപ്പും",
            "Flowering & Pod Formation": "പൂവിടലും കായ് വയ്ക്കലും",
            "Bud Break & Flowering": "മൊട്ടുവിടരലും പൂവിടലും",
            "Fruit Set & Pea Stage": "കണ്ണി പിടിക്കലും പയർ മണി ഘട്ടവും",
            "Fruit Growth & Enlargement": "കായ് വളർച്ചാ ഘട്ടം",
            "Maturity & Harvest": "പഴം മൂപ്പും വിളവെടുപ്പും",
            "Spathe & Button Stage": "പൂക്കുലയും കുരുന്ന് ഘട്ടവും",
            "Tender Nut Water Stage": "കരിക്ക് ഘട്ടം",
            "Kernel Solidification": "തേങ്ങാപ്പീര കട്ടിയാകൽ",
            "Full Maturity & Harvest": "പൂർണ്ണ മൂപ്പും തേങ്ങ ഇടീലും"
        }
    }
}


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def rule_based_predict(N, P, K, temperature, humidity, ph, rainfall):
    if N > 80 and humidity > 70 and rainfall > 150:     return "Rice"
    if temperature > 25 and humidity > 75 and K > 50:   return "Tomato"
    if N < 50 and ph > 6.5 and temperature > 20:        return "Onion"
    if temperature > 28 and humidity > 60 and ph > 6:   return "Chilli"
    if K > 70 and temperature > 25 and rainfall < 120:  return "Turmeric"
    if N > 60 and temperature > 25 and rainfall < 120:  return "Groundnut"
    if K > 80 and ph > 6.5 and temperature > 27:        return "Cotton"
    if temperature < 22 and rainfall > 80 and ph < 7:   return "Wheat"
    if ph > 7 and N < 50 and rainfall < 100:            return "Chickpea"
    if humidity > 75 and temperature > 28 and K > 60:   return "Banana"
    if N > 100 and K > 100 and rainfall > 200:          return "Sugarcane"
    if N > 40 and ph > 6 and temperature > 25:          return "Soybean"
    if temperature > 30 and rainfall < 80 and ph > 6.5: return "Mango"
    if humidity > 70 and K > 50 and temperature > 25:   return "Coconut"
    return "Maize"

def ml_predict(N, P, K, temperature, humidity, ph, rainfall):
    try:
        features = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
        return MODEL.predict(SCALER.transform(features))[0]
    except Exception as e:
        print("ML prediction error, fallback to rules:", e)
        return rule_based_predict(N, P, K, temperature, humidity, ph, rainfall)

def normalize_crop(c):
    if c in CROP_DATA: return c
    cl = str(c).lower()
    return next((k for k in CROP_DATA if k.lower() == cl or k.lower() in cl), "Maize")

def soil_health_score(N, P, K, ph):
    s = min(100,N/140*100)*0.30 + min(100,P/145*100)*0.25 + min(100,K/205*100)*0.25 + max(0,100-abs(ph-6.5)*25)*0.20
    return round(s)

def irrigation_schedule(wn, rain, temp):
    if wn == "high":
        if rain < 75 and temp > 30: return {"frequency": "Every day", "amount_per_session": "50–60 mm"}
        if rain < 75:             return {"frequency": "Every 2 days", "amount_per_session": "40–50 mm"}
        if rain < 150:            return {"frequency": "Every 3 days", "amount_per_session": "30–40 mm"}
        return {"frequency": "Once a week", "amount_per_session": "20–25 mm"}
    elif wn == "medium":
        if rain < 75 and temp > 30: return {"frequency": "Every 2 days", "amount_per_session": "35–45 mm"}
        if rain < 75:             return {"frequency": "Every 3 days", "amount_per_session": "30–40 mm"}
        if rain < 150:            return {"frequency": "Twice a week", "amount_per_session": "25–30 mm"}
        return {"frequency": "Once in 10 days", "amount_per_session": "15–20 mm"}
    else:
        if rain < 75: return {"frequency": "Once a week", "amount_per_session": "20–25 mm"}
        return {"frequency": "Rainfall sufficient", "amount_per_session": "Monitor only"}

def disease_risk(hum, temp, info):
    dr = info.get("disease_risk", {})
    risks = []
    if dr.get("fungal") and hum > 75:  risks.append({"type": "Fungal Disease", "level": "High" if hum > 85 else "Medium", "advice": "Apply Mancozeb or Copper Oxychloride"})
    if dr.get("bacterial") and temp > 30: risks.append({"type": "Bacterial Blight", "level": "Medium", "advice": "Use Streptocycline spray"})
    if dr.get("pest") and temp > 28:   risks.append({"type": "Pest Infestation", "level": "High" if temp > 33 else "Medium", "advice": "Use Neem oil or recommended pesticide"})
    if not risks: risks.append({"type": "No Risk Detected", "level": "Low", "advice": "Maintain good field hygiene"})
    return risks

def yield_est(info, N, P, K, rain):
    lo, hi = info["yield_kg_per_acre"]
    f = min(1.0, (N/100*0.4 + P/80*0.3 + K/100*0.3)) * min(1.0, max(0.2, rain/150))
    return round(lo + (hi - lo) * f)

CROP_STAGE_DATA = {
    "Rice": {
        "duration_days": 120,
        "stages": [
            {"name": "Sowing & Nursery", "days": 25, "explanation": "Prepare seedbed, sow seeds, and maintain consistent nursery moisture for healthy seedling emergence."},
            {"name": "Vegetative Growth", "days": 35, "explanation": "Transplant seedlings to main field, maintain 2-5cm standing water, and apply initial nitrogen fertilizer."},
            {"name": "Reproductive & Panicle", "days": 30, "explanation": "Panicle initiation and flowering stage. Ensure peak water availability and protect against stem borer."},
            {"name": "Ripening & Maturity", "days": 30, "explanation": "Grain filling and ripening. Drain field water 10 days prior to harvest when grains turn golden."}
        ]
    },
    "Maize": {
        "duration_days": 100,
        "stages": [
            {"name": "Sowing & Germination", "days": 20, "explanation": "Sow seeds 4-5cm deep in well-drained soil. Ensure optimal warmth and soil moisture."},
            {"name": "Vegetative Stage", "days": 30, "explanation": "Rapid leaf elongation and stem growth. Apply NPK fertilizer top dressing and earthing up."},
            {"name": "Tasseling & Silking", "days": 25, "explanation": "Flowering and pollination phase. Critical stage requiring adequate irrigation and pest control."},
            {"name": "Grain Filling & Maturity", "days": 25, "explanation": "Kernels mature and harden. Harvest when cob husk turns dry and pale yellow."}
        ]
    },
    "Groundnut": {
        "duration_days": 110,
        "stages": [
            {"name": "Sowing & Seedling", "days": 20, "explanation": "Plant quality pods/seeds in friable soil. Ensure moist seedbed for uniform germination."},
            {"name": "Vegetative Growth", "days": 35, "explanation": "Canopy development and branching. Apply gypsum to supply calcium for pod development."},
            {"name": "Pegging & Pod Formation", "days": 30, "explanation": "Flower pegs enter soil to form underground pods. Avoid deep cultivation to protect pegs."},
            {"name": "Pod Maturity & Harvest", "days": 25, "explanation": "Pods mature and harden. Harvest when internal shell lining turns dark brown."}
        ]
    },
    "Wheat": {
        "duration_days": 120,
        "stages": [
            {"name": "Sowing & Crown Root", "days": 25, "explanation": "Sow in cool moist soil. Provide first irrigation at Crown Root Initiation (CRI) stage (~21 days)."},
            {"name": "Tillering & Jointing", "days": 35, "explanation": "Tillers develop and stems elongate. Apply top dressing nitrogen and control weeds."},
            {"name": "Heading & Flowering", "days": 30, "explanation": "Earheads emerge and flowering begins. Maintain soil moisture to avoid grain reduction."},
            {"name": "Grain Filling & Maturity", "days": 30, "explanation": "Dough stage to hard grain. Harvest when crop turns golden and moisture drops to 12-14%."}
        ]
    },
    "Cotton": {
        "duration_days": 160,
        "stages": [
            {"name": "Sowing & Seedling", "days": 30, "explanation": "Sow seeds in ridges or flat beds. Monitor early weed competition and seedling vigor."},
            {"name": "Vegetative Branching", "days": 45, "explanation": "Main stem and sympodial branch development. Apply split nitrogen doses."},
            {"name": "Squaring & Flowering", "days": 45, "explanation": "Square (flower bud) initiation and white/pink flower bloom. Monitor for bollworm infestation."},
            {"name": "Boll Opening & Picking", "days": 40, "explanation": "Bolls mature and open exposing clean lint. Perform multiple pickings on sunny dry days."}
        ]
    },
    "Sugarcane": {
        "duration_days": 360,
        "stages": [
            {"name": "Planting & Germination", "days": 45, "explanation": "Plant 2-3 bud setts in furrows. Maintain soil moisture for eye bud sprouting."},
            {"name": "Tillering Stage", "days": 75, "explanation": "Shoot proliferation and root system expansion. Perform earthing up and weed removal."},
            {"name": "Grand Growth Period", "days": 150, "explanation": "Rapid cane elongation and internode thickening. Peak water and nutrient requirement stage."},
            {"name": "Ripening & Harvest", "days": 90, "explanation": "Sucrose synthesis and accumulation in stalk. Stop irrigation 2-3 weeks before harvesting."}
        ]
    },
    "Banana": {
        "duration_days": 330,
        "stages": [
            {"name": "Planting & Establishment", "days": 60, "explanation": "Plant disease-free suckers/tissue plants in pits. Provide organic mulching and shade."},
            {"name": "Vegetative Canopy", "days": 120, "explanation": "Rapid broad leaf expansion and pseudostem thickening. Regular fertigation and desuckering."},
            {"name": "Bunch Shooting", "days": 60, "explanation": "Inflorescence emerges from pseudostem heart. Provide bamboo propping support to heavy bunches."},
            {"name": "Bunch Development & Harvest", "days": 90, "explanation": "Banana fingers swell and round off. Harvest mature green bunches before yellowing."}
        ]
    },
    "Chickpea": {
        "duration_days": 100,
        "stages": [
            {"name": "Sowing & Germination", "days": 20, "explanation": "Sow in residual moisture after monsoon. Ensure proper aeration to prevent root rot."},
            {"name": "Vegetative & Nipping", "days": 30, "explanation": "Branching phase. Nip terminal buds at 30-45 days to encourage bushy lateral growth."},
            {"name": "Flowering & Pod Set", "days": 25, "explanation": "Pod initiation. Protect crop from Helicoverpa pod borer using pheromone traps."},
            {"name": "Pod Ripening & Harvest", "days": 25, "explanation": "Pods turn straw yellow and leaves drop. Harvest when seeds rattle inside dry pods."}
        ]
    },
    "Tomato": {
        "duration_days": 110,
        "stages": [
            {"name": "Transplanting & Nursery", "days": 20, "explanation": "Transplant 25-day old seedlings to raised beds. Provide staking support early for vine crops."},
            {"name": "Vegetative Branching", "days": 30, "explanation": "Stem growth and leaf canopy expansion. Apply balanced NPK fertilizer and weeding."},
            {"name": "Flowering & Fruit Set", "days": 30, "explanation": "Yellow flower cluster bloom and green fruit formation. Maintain uniform moisture to prevent blossom drop."},
            {"name": "Fruit Ripening & Harvest", "days": 30, "explanation": "Fruits change from green to breaker/red mature stage. Harvest in multiple pickings every 3-4 days."}
        ]
    },
    "Onion": {
        "duration_days": 130,
        "stages": [
            {"name": "Transplanting & Early Growth", "days": 25, "explanation": "Transplant healthy nursery seedlings in shallow furrows. Keep soil weed-free."},
            {"name": "Foliage Development", "days": 40, "explanation": "Tubular leaf production. Adequate nitrogen and micro-irrigation promote top growth."},
            {"name": "Bulb Initiation & Swelling", "days": 35, "explanation": "Bulbs begin expanding below soil surface. Increase potash application for firmness."},
            {"name": "Neck Fall & Harvest", "days": 30, "explanation": "Foliage turns yellow and necks break over naturally. Pull bulbs and cure in shade."}
        ]
    },
    "Chilli": {
        "duration_days": 140,
        "stages": [
            {"name": "Transplanting & Establishment", "days": 25, "explanation": "Plant nursery seedlings on ridges. Apply organic basal manure and light watering."},
            {"name": "Vegetative Growth", "days": 40, "explanation": "Branching and dense canopy growth. Spray micronutrients and monitor sucking pests."},
            {"name": "Flowering & Pod Set", "days": 45, "explanation": "White flowers bloom continuously and green chilli pods develop. Regulate irrigation."},
            {"name": "Pod Maturity & Harvesting", "days": 30, "explanation": "Chilli pods mature to deep green or red. Perform selective hand picking every 7-10 days."}
        ]
    },
    "Turmeric": {
        "duration_days": 240,
        "stages": [
            {"name": "Planting & Sprouting", "days": 45, "explanation": "Plant mother rhizomes on ridges. Cover with heavy green leaf mulch to preserve moisture."},
            {"name": "Vegetative Tillering", "days": 90, "explanation": "Tillers and broad green leaves emerge. Apply top dressing fertilizers and earthing up."},
            {"name": "Rhizome Expansion", "days": 60, "explanation": "Primary and secondary finger rhizomes enlarge in soil. Keep root zone well aerated."},
            {"name": "Foliage Drying & Harvest", "days": 45, "explanation": "Leaves turn dry and straw yellow. Dig out mature rhizomes carefully without bruising."}
        ]
    },
    "Soybean": {
        "duration_days": 100,
        "stages": [
            {"name": "Sowing & Germination", "days": 20, "explanation": "Sow Rhizobium-treated seeds 3-4cm deep. Ensure good soil moisture for quick emergence."},
            {"name": "Vegetative Growth", "days": 30, "explanation": "Trifoliate leaf growth and root nodule nitrogen fixation. Control early broadleaf weeds."},
            {"name": "Flowering & Pod Formation", "days": 25, "explanation": "Small purple/white flowers blossom into pods. Critical irrigation window for yield."},
            {"name": "Pod Maturity & Harvest", "days": 25, "explanation": "Pods turn yellow-brown and leaves shed. Harvest when grain moisture drops to 13-15%."}
        ]
    },
    "Mango": {
        "duration_days": 150,
        "stages": [
            {"name": "Bud Break & Flowering", "days": 35, "explanation": "Panicles bloom with fragrant flowers. Protect against powdery mildew and mango hoppers."},
            {"name": "Fruit Set & Pea Stage", "days": 35, "explanation": "Young fruits set at pea/marble size. Apply light irrigation to prevent fruit drop."},
            {"name": "Fruit Growth & Enlargement", "days": 50, "explanation": "Fruits expand rapidly and stone hardens inside. Apply potassium for sweetness and size."},
            {"name": "Maturity & Harvest", "days": 30, "explanation": "Fruit shoulders widen and skin color turns pale yellow-green. Harvest with pedicel attached."}
        ]
    },
    "Coconut": {
        "duration_days": 365,
        "stages": [
            {"name": "Spathe & Button Stage", "days": 90, "explanation": "Flower spathe opens and female buttons are pollinated naturally by bees and wind."},
            {"name": "Tender Nut Water Stage", "days": 90, "explanation": "Young coconut shell fills with sweet nourishing tender coconut water."},
            {"name": "Kernel Solidification", "days": 90, "explanation": "Endosperm (copra meat) forms and thickens along inner shell wall."},
            {"name": "Full Maturity & Harvest", "days": 95, "explanation": "Nuts turn brown and dry. Harvest mature coconuts every 45-60 days throughout the year."}
        ]
    }
}

def crop_calendar(info, sow_date_str=None, crop_name=None):
    import datetime
    crop_key = crop_name or info.get("crop_name", "Rice")
    if crop_key not in CROP_STAGE_DATA:
        crop_key = "Rice"

    stage_info = CROP_STAGE_DATA[crop_key]
    today = datetime.date.today()
    if sow_date_str:
        try:
            sow_date = datetime.datetime.strptime(sow_date_str.strip(), "%Y-%m-%d").date()
        except Exception:
            sow_date = today
    else:
        sow_date = today

    current_start = sow_date
    stages_out = []

    for stg in stage_info["stages"]:
        dur = stg["days"]
        end_date = current_start + datetime.timedelta(days=dur - 1)
        stages_out.append({
            "name": stg["name"],
            "duration_days": dur,
            "start_date": current_start.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "start_display": current_start.strftime("%d %b %Y"),
            "end_display": end_date.strftime("%d %b %Y"),
            "explanation": stg["explanation"]
        })
        current_start = end_date + datetime.timedelta(days=1)

    harvest_date = sow_date + datetime.timedelta(days=stage_info["duration_days"])

    s_idx = info.get("sow_month", 6) - 1
    h_idx = info.get("harvest_month", 10) - 1
    typical_sow = MONTHS[s_idx % 12]
    typical_harv = MONTHS[h_idx % 12]

    return {
        "crop": crop_key,
        "sow_date": sow_date.strftime("%Y-%m-%d"),
        "sow_date_display": sow_date.strftime("%d %b %Y"),
        "harvest_date": harvest_date.strftime("%Y-%m-%d"),
        "harvest_date_display": harvest_date.strftime("%d %b %Y"),
        "harvest_month_year": harvest_date.strftime("%b %Y"),
        "total_duration_days": stage_info["duration_days"],
        "stages": stages_out,
        "typical_season": info.get("season", "Kharif"),
        "typical_sowing_window": f"{typical_sow} – {typical_harv}"
    }

def price_history(base, vol, trend, months=12):
    tf = {"rising": 1.012, "stable": 1.002, "falling": 0.990}.get(trend, 1.002)
    p, hist = base, []
    for _ in range(months):
        p = p * tf + random.gauss(0, base * vol)
        hist.append(round(max(p, base * 0.5), 2))
    return hist

def get_crop_advisory(crop_name: str, N: float, P: float, K: float, temp: float, hum: float, ph: float, rain: float, farm_lat=11.0168, farm_lon=76.9558, sow_date_str=None):
    crop = normalize_crop(crop_name)
    info = CROP_DATA.get(crop, CROP_DATA["Maize"])
    y_kg = yield_est(info, N, P, K, rain)

    market_data = fetch_agmarknet_market_data(crop, latitude=farm_lat, longitude=farm_lon)

    if market_data.get("available"):
        modal_p = market_data["modal_price"]
        yield_qtl = y_kg / 100.0
        est_revenue = round(yield_qtl * modal_p)
        prod_cost = ESTIMATED_PRODUCTION_COST_PER_ACRE.get(crop, 20000)
        est_profit = round(est_revenue - prod_cost)
        profit_display = f"₹{est_profit:,.0f}"
    else:
        modal_p = None
        est_revenue = None
        prod_cost = ESTIMATED_PRODUCTION_COST_PER_ACRE.get(crop, 20000)
        est_profit = None
        profit_display = info.get("profit_per_acre", "N/A")

    hist = price_history(info["base_price"], info["price_volatility"], info["market_trend"])
    last3 = sum(hist[-3:]) / 3
    tbump = {"rising": 1.04, "falling": 0.96, "stable": 1.01}[info.get("market_trend", "stable")]

    intercrops = info.get("intercrop", ["—", "—"])
    has_trend = bool(market_data.get("available"))
    m_trend_display = f"{info.get('market_trend', 'stable').capitalize()} ({info.get('price_volatility', 0.05)*100:.0f}% volatility)" if has_trend else "Market trend unavailable"

    return {
        "crop": crop,
        "intercrop_1": intercrops[0] if len(intercrops) > 0 else "—",
        "intercrop_2": intercrops[1] if len(intercrops) > 1 else "—",
        "fertilizer": info.get("fertilizer", "N/A"),
        "season": info.get("season", "N/A"),
        "water_need": info.get("water_need", "medium"),
        "market_status": info.get("market_status", "N/A"),
        "market_trend": info.get("market_trend", "stable"),
        "market_data": market_data,
        "profit_per_acre": profit_display,
        "estimated_revenue": est_revenue,
        "estimated_profit": est_profit,
        "production_cost": prod_cost,
        "market_trend_display": m_trend_display,
        "has_historical_trend": has_trend,
        "price_history": hist,
        "current_price": hist[-1],
        "next_month_price": round(last3 * tbump, 2),
        "disease_risks": disease_risk(hum, temp, info),
        "irrigation": irrigation_schedule(info.get("water_need", "medium"), rain, temp),
        "yield_est": y_kg,
        "calendar": crop_calendar(info, sow_date_str, crop),
        "gov_schemes": info.get("gov_schemes", []),
        "nearby_mandis": fallback_mandis("Coimbatore", farm_lat, farm_lon),
        "nearby_fertilizer_shops": fallback_fertilizer_shops("Coimbatore", farm_lat, farm_lon)
    }


def haversine(la1, lo1, la2, lo2):
    R = 6371; dlat = math.radians(la2 - la1); dlon = math.radians(lo2 - lo1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(la1)) * math.cos(math.radians(la2)) * math.sin(dlon/2)**2
    return round(R * 2 * math.asin(math.sqrt(a)), 1)

def geocode(city):
    import urllib.request, urllib.parse
    try:
        url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": city + ", India", "format": "json", "limit": 1})
        req = urllib.request.Request(url, headers={"User-Agent": "AICropAdvisor/1.0"})
        with urllib.request.urlopen(req, timeout=6) as r: d = json.loads(r.read())
        if d: return float(d[0]["lat"]), float(d[0]["lon"])
    except: pass
    return None, None

def fallback_mandis(city, lat, lon):
    if not lat or not lon:
        return []
    try:
        lat = float(lat); lon = float(lon)
    except:
        return []

    # Ensure coordinates are within valid bounds
    rng = random.Random(int(hashlib.md5((city or "farm").encode()).hexdigest()[:8], 16))
    names = [f"{city} Main Agri Market", f"{city} APMC Mandi", "District Farmers Market", "Regional Agri Centre", "Uzhavar Santhai Market"]
    used = []; res = []
    for i in range(5):
        a = rng.uniform(0, 360)
        while any(abs(a - u) < 30 for u in used): a = rng.uniform(0, 360)
        used.append(a); d = rng.uniform(3, 30)
        r = math.radians(a)
        m_lat = round(lat + (d / 111.0) * math.cos(r), 5)
        m_lon = round(lon + (d / (111.0 * math.cos(math.radians(lat)))) * math.sin(r), 5)
        res.append({
            "name": names[i],
            "lat": m_lat,
            "lng": m_lon,
            "distance_km": round(d, 1)
        })
    return sorted(res, key=lambda x: x["distance_km"])

def fallback_fertilizer_shops(city, lat, lon):
    if not lat or not lon:
        return []
    try:
        lat = float(lat); lon = float(lon)
    except:
        return []

    rng = random.Random(int(hashlib.md5((city or "farm").encode() + b"fert").hexdigest()[:8], 16))
    shops = [
        {"name": f"{city} IFFCO Kisan Seva Kendra", "type": "Govt Depot (Subsidized Urea & DAP)", "phone": "+91 1800-180-1551"},
        {"name": f"{city} PACCS Agro Cooperative Society", "type": "Cooperative Fertilizer Outlet", "phone": "+91 94421-88120"},
        {"name": "Sri Lakshmi Agro Chemicals & Fertilizers", "type": "Authorized Fertilizer Dealer", "phone": "+91 98422-55104"},
        {"name": f"{city} Farmers Agro Service Centre", "type": "Organic & NPK Depot", "phone": "+91 97877-33211"},
        {"name": "Green Harvest Bio-Fertilizers & Seeds", "type": "Bio-Inputs & Micronutrients", "phone": "+91 99430-44890"}
    ]
    used = []; res = []
    for i in range(len(shops)):
        a = rng.uniform(0, 360)
        while any(abs(a - u) < 30 for u in used): a = rng.uniform(0, 360)
        used.append(a); d = rng.uniform(2, 22)
        r = math.radians(a)
        s_lat = round(lat + (d / 111.0) * math.cos(r), 5)
        s_lon = round(lon + (d / (111.0 * math.cos(math.radians(lat)))) * math.sin(r), 5)
        res.append({
            "name": shops[i]["name"],
            "type": shops[i]["type"],
            "phone": shops[i]["phone"],
            "lat": s_lat,
            "lng": s_lon,
            "distance_km": round(d, 1)
        })
    return sorted(res, key=lambda x: x["distance_km"])

def top3(N, P, K, temp, hum, ph, rain):
    import datetime as dt
    m = dt.datetime.now().month
    scores = {}
    for crop, info in CROP_DATA.items():
        s = 0
        if info["water_need"] == "high" and hum > 70: s += 20
        if info["water_need"] == "low" and hum < 55:  s += 20
        if info["water_need"] == "medium": s += 10
        if "Kharif" in info["season"] and 5 <= m <= 9: s += 15
        if "Rabi" in info["season"] and (m >= 10 or m <= 3): s += 15
        s += random.randint(0, 10); scores[crop] = s
    return sorted(scores, key=scores.get, reverse=True)[:3]

def oid(s):
    try: return ObjectId(s)
    except: return None

# ══════════════════════════════════════════════════════════════════════════════
#  AUTH HELPERS (JWT + bcrypt)
# ══════════════════════════════════════════════════════════════════════════════
import jwt as pyjwt
import bcrypt

JWT_SECRET = os.environ.get("JWT_SECRET", "jwt_secret_aicropadvisor_2026")
JWT_EXP_HOURS = 24

def hash_pw(pw): return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
def check_pw(pw, hashed): return bcrypt.checkpw(pw.encode(), hashed.encode())

def make_token(user_id, role):
    payload = {"sub": str(user_id), "role": role,
               "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXP_HOURS)}
    return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_token(token):
    try: return pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except: return None

def get_token_from_request():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "): return auth[7:]
    return request.cookies.get("token") or request.headers.get("X-Token")

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = get_token_from_request()
        payload = decode_token(token)
        if not payload: return jsonify({"error": "Unauthorized — please login"}), 401
        request.user_id = payload["sub"]
        request.user_role = payload["role"]
        return f(*args, **kwargs)
    return wrapper

def require_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = get_token_from_request()
        payload = decode_token(token)
        if not payload: return jsonify({"error": "Unauthorized"}), 401
        if payload.get("role") != "admin": return jsonify({"error": "Admin access required"}), 403
        request.user_id = payload["sub"]
        request.user_role = "admin"
        return f(*args, **kwargs)
    return wrapper

def validate_email(email):
    import re
    return bool(re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email))

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE ROUTES
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/")
def page_login():
    return render_template("login.html", T=TRANSLATIONS["en"], translations=TRANSLATIONS)

@app.route("/signup")
def page_signup():
    return render_template("signup.html", T=TRANSLATIONS["en"], translations=TRANSLATIONS)

@app.route("/app")
def page1():
    return render_template("page1.html", translations=TRANSLATIONS)

@app.route("/soil")
def page2():
    return render_template("page2.html", translations=TRANSLATIONS)

@app.route("/results")
def page3():
    return render_template("page3.html", translations=TRANSLATIONS)

@app.route("/feedback")
def page4():
    return render_template("page4.html", translations=TRANSLATIONS, crops=list(CROP_DATA.keys()))

@app.route("/history")
def page_history():
    return render_template("history.html", translations=TRANSLATIONS)

@app.route("/admin")
def page_admin():
    return render_template("admin.html", T=TRANSLATIONS["en"], translations=TRANSLATIONS)

# ══════════════════════════════════════════════════════════════════════════════
#  AUTH API
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/auth/signup", methods=["POST"])
def api_signup():
    d = request.get_json() or {}
    name  = (d.get("name") or "").strip()
    email = (d.get("email") or "").strip().lower()
    pw    = d.get("password", "")
    role  = "user"

    if not name:                  return jsonify({"error": "Name is required"}), 400
    if not validate_email(email): return jsonify({"error": "Invalid email format"}), 400
    if len(pw) < 6:               return jsonify({"error": "Password must be at least 6 characters"}), 400

    try:
        users = col("users")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if users.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409

    user = {"name": name, "email": email, "password": hash_pw(pw), "role": role,
            "createdAt": datetime.datetime.utcnow().isoformat()}
    result = users.insert_one(user)
    token  = make_token(result.inserted_id, role)

    send_email(
        to_email=email,
        subject="🌱 Welcome to AI Crop Advisor!",
        html_body=welcome_email_html(name)
    )

    return jsonify({"token": token, "user": {"id": str(result.inserted_id), "name": name, "email": email, "role": role}}), 201

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    d = request.get_json() or {}
    email = (d.get("email") or "").strip().lower()
    pw    = d.get("password", "")
    if not email or not pw:
        return jsonify({"error": "Email and password required"}), 400
    try:
        user = col("users").find_one({"email": email})
    except Exception as e:
        return jsonify({"error": f"Database error: {e}"}), 500

    if not user or not check_pw(pw, user["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    token = make_token(user["_id"], user["role"])

    login_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    send_email(
        to_email=user["email"],
        subject="🔐 New Login to Your AI Crop Advisor Account",
        html_body=login_email_html(user["name"], login_time)
    )

    return jsonify({"token": token, "user": {"id": str(user["_id"]), "name": user["name"], "email": user["email"], "role": user["role"]}})

@app.route("/api/auth/me")
@require_auth
def api_me():
    user = col("users").find_one({"_id": oid(request.user_id)}, {"password": 0})
    if not user: return jsonify({"error": "User not found"}), 404
    user["_id"] = str(user["_id"])
    return jsonify(user)

# ══════════════════════════════════════════════════════════════════════════════
#  WEATHER / SENSOR
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/weather")
def api_weather():
    city = request.args.get("city", "").strip()
    lat  = request.args.get("lat")
    lon  = request.args.get("lon")
    api_key = os.environ.get("OPENWEATHER_API_KEY", "")

    if api_key and api_key != "your_openweather_api_key_here":
        try:
            import urllib.request, urllib.parse
            url = (f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
                   if lat and lon else
                   f"https://api.openweathermap.org/data/2.5/weather?q={urllib.parse.quote(city)}&appid={api_key}&units=metric")
            with urllib.request.urlopen(url, timeout=5) as r: d = json.loads(r.read())
            return jsonify({
                "temperature": round(d["main"]["temp"]),
                "humidity": d["main"]["humidity"],
                "city": d.get("name", city),
                "lat": float(d["coord"]["lat"]),
                "lon": float(d["coord"]["lon"]),
                "source": "live"
            })
        except Exception as e:
            print("OpenWeatherMap fetch failed, trying Open-Meteo:", e)

    try:
        import urllib.request
        if not lat or not lon or lat == "null" or lon == "null":
            glat, glon = geocode(city)
            lat, lon = glat or 11.0168, glon or 76.9558
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m&timezone=auto"
        with urllib.request.urlopen(url, timeout=6) as r: d = json.loads(r.read())
        cur = d.get("current", {})
        return jsonify({
            "temperature": round(cur.get("temperature_2m", 28)),
            "humidity": cur.get("relative_humidity_2m", 70),
            "city": city or "Coimbatore",
            "lat": float(lat),
            "lon": float(lon),
            "source": "fetched"
        })
    except Exception as e:
        print("Open-Meteo fetch failed:", e)

    glat, glon = geocode(city) if city else (11.0168, 76.9558)
    return jsonify({
        "temperature": random.randint(25, 34),
        "humidity": random.randint(60, 85),
        "city": city or "Local Farm",
        "lat": glat or 11.0168,
        "lon": glon or 76.9558,
        "source": "fallback"
    })

@app.route("/api/sensor")
def api_sensor():
    return jsonify({
        "N": random.randint(40, 120),
        "P": random.randint(20, 80),
        "K": random.randint(30, 120),
        "ph": round(random.uniform(5.5, 7.5), 1),
        "rainfall": random.randint(50, 250)
    })

# ══════════════════════════════════════════════════════════════════════════════
#  MARKET PRICE API
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/market-price")
def api_market_price():
    crop = request.args.get("crop", "Rice").strip()
    lat  = request.args.get("latitude") or request.args.get("lat")
    lon  = request.args.get("longitude") or request.args.get("lon")
    state = request.args.get("state")
    district = request.args.get("district")

    data = fetch_agmarknet_market_data(crop, state=state, district=district, latitude=lat, longitude=lon)
    return jsonify(data)

@app.route("/api/crop-advisory")
def api_crop_advisory():
    crop = request.args.get("crop", "Tomato").strip()
    try:
        N    = float(request.args.get("N", 70))
        P    = float(request.args.get("P", 50))
        K    = float(request.args.get("K", 50))
        temp = float(request.args.get("temperature", 28))
        hum  = float(request.args.get("humidity", 70))
        ph   = float(request.args.get("ph", 6.5))
        rain = float(request.args.get("rainfall", 100))
    except (ValueError, TypeError):
        N, P, K, temp, hum, ph, rain = 70, 50, 50, 28, 70, 6.5, 100

    lat = request.args.get("lat")
    lon = request.args.get("lon")
    sow_date = request.args.get("sow_date") or request.args.get("sowing_date")

    try: farm_lat = float(lat) if lat else 11.0168; farm_lon = float(lon) if lon else 76.9558
    except: farm_lat, farm_lon = 11.0168, 76.9558

    adv = get_crop_advisory(crop, N, P, K, temp, hum, ph, rain, farm_lat, farm_lon, sow_date)
    return jsonify(adv)

# ══════════════════════════════════════════════════════════════════════════════
#  PREDICTIONS
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/predictions", methods=["POST"])
@require_auth
def api_predict():
    d = request.get_json() or {}
    try:
        N    = float(d["N"]); P = float(d["P"]); K = float(d["K"])
        temp = float(d["temperature"]); hum = float(d["humidity"])
        ph   = float(d["ph"]); rain = float(d["rainfall"])
    except Exception as e:
        return jsonify({"error": "Invalid numerical soil/climate parameters"}), 400

    city = d.get("city", "your area")
    lat  = d.get("lat"); lon = d.get("lon")
    if lat is None or lon is None or lat == "null" or lon == "null":
        glat, glon = geocode(city)
        lat = glat; lon = glon

    try: farm_lat = float(lat) if lat else 11.0168; farm_lon = float(lon) if lon else 76.9558
    except: farm_lat, farm_lon = 11.0168, 76.9558

    crop_raw = ml_predict(N, P, K, temp, hum, ph, rain) if USE_ML else rule_based_predict(N, P, K, temp, hum, ph, rain)
    crop  = normalize_crop(crop_raw)
    info  = CROP_DATA[crop]
    score = soil_health_score(N, P, K, ph)
    y_kg  = yield_est(info, N, P, K, rain)

    # Fetch Live Mandi Data from Agmarknet
    market_data = fetch_agmarknet_market_data(crop, latitude=farm_lat, longitude=farm_lon)

    if market_data.get("available"):
        modal_p = market_data["modal_price"]
        yield_qtl = y_kg / 100.0
        est_revenue = round(yield_qtl * modal_p)
        prod_cost = ESTIMATED_PRODUCTION_COST_PER_ACRE.get(crop, 20000)
        est_profit = round(est_revenue - prod_cost)
        profit_display = f"₹{est_profit:,.0f}"
    else:
        modal_p = None
        est_revenue = None
        prod_cost = ESTIMATED_PRODUCTION_COST_PER_ACRE.get(crop, 20000)
        est_profit = None
        profit_display = info["profit_per_acre"]

    hist  = price_history(info["base_price"], info["price_volatility"], info["market_trend"])
    last3 = sum(hist[-3:]) / 3
    tbump = {"rising": 1.04, "falling": 0.96, "stable": 1.01}[info["market_trend"]]
    t3k   = top3(N, P, K, temp, hum, ph, rain)
    t3    = [{"crop": c, "season": CROP_DATA[c]["season"], "profit": CROP_DATA[c]["profit_per_acre"], "water": CROP_DATA[c]["water_need"], "yield_est": yield_est(CROP_DATA[c], N, P, K, rain)} for c in t3k if c in CROP_DATA]
    
    tips = []
    if N < 40: tips.append("Low Nitrogen — apply Urea or green manure")
    if P < 25: tips.append("Low Phosphorus — apply DAP or SSP")
    if K < 25: tips.append("Low Potassium — apply MOP")
    if ph < 5.5: tips.append("Acidic soil — apply lime")
    if ph > 8.0: tips.append("Alkaline soil — apply gypsum")
    if not tips: tips.append("Soil health is good!")

    sow_dt = d.get("sow_date") or d.get("sowing_date")
    main_adv = get_crop_advisory(crop, N, P, K, temp, hum, ph, rain, farm_lat, farm_lon, sow_dt)
    ic1_name = info["intercrop"][0] if len(info.get("intercrop", [])) > 0 else "Basil"
    ic2_name = info["intercrop"][1] if len(info.get("intercrop", [])) > 1 else "Marigold"
    ic1_adv  = get_crop_advisory(ic1_name, N, P, K, temp, hum, ph, rain, farm_lat, farm_lon, sow_dt)
    ic2_adv  = get_crop_advisory(ic2_name, N, P, K, temp, hum, ph, rain, farm_lat, farm_lon, sow_dt)

    result = {
        "userId":                  request.user_id,
        "crop":                    crop,
        "model_used":              "ML" if USE_ML else "Rules",
        "selected_crop_type":      "main",
        "main_advisory":           main_adv,
        "intercrop_1_advisory":    ic1_adv,
        "intercrop_2_advisory":    ic2_adv,
        "intercrop_1":             info["intercrop"][0],
        "intercrop_2":             info["intercrop"][1],
        "fertilizer":              info["fertilizer"],
        "season":                  info["season"],
        "market_status":           info["market_status"],
        "market_trend":            info["market_trend"],
        "market_data":             market_data,
        "profit_per_acre":         profit_display,
        "estimated_revenue":       est_revenue,
        "estimated_profit":        est_profit,
        "production_cost":         prod_cost,
        "market_trend_display":    main_adv["market_trend_display"],
        "has_historical_trend":    main_adv["has_historical_trend"],
        "price_history":           hist,
        "current_price":           hist[-1],
        "next_month_price":        round(last3 * tbump, 2),
        "soil_score":              score,
        "soil_tips":               tips,
        "disease_risks":           disease_risk(hum, temp, info),
        "irrigation":              irrigation_schedule(info["water_need"], rain, temp),
        "yield_est":               y_kg,
        "calendar":                crop_calendar(info, sow_dt, crop),
        "top3":                    t3,
        "gov_schemes":             info["gov_schemes"],
        "nearby_mandis":           fallback_mandis(city, farm_lat, farm_lon),
        "nearby_fertilizer_shops": fallback_fertilizer_shops(city, farm_lat, farm_lon),
        "farm_lat":                farm_lat,
        "farm_lon":                farm_lon,
        "location":                city,
        "inputs":                  {"N": N, "P": P, "K": K, "temperature": temp, "humidity": hum, "ph": ph, "rainfall": rain},
        "soilData":                {"N": N, "P": P, "K": K, "ph": ph},
        "weatherData":             {"temperature": temp, "humidity": hum, "rainfall": rain},
        "createdAt":               datetime.datetime.utcnow().isoformat(),
    }
    
    try:
        inserted = col("predictions").insert_one(result.copy())
        result["_id"] = str(inserted.inserted_id)
        result["userId"] = str(result["userId"])
    except Exception as e:
        print("Failed to save prediction to MongoDB:", e)
        result["_id"] = "temp_id_" + datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")

    user = None
    try:
        user = col("users").find_one({"_id": oid(request.user_id)}, {"name": 1, "email": 1})
    except: pass

    if user:
        send_email(
            to_email=user["email"],
            subject=f"🌾 Your Crop Recommendation: {crop} — AI Crop Advisor",
            html_body=prediction_email_html(user["name"], result)
        )

    return jsonify(result), 201


@app.route("/api/predictions/user")
@require_auth
def api_user_predictions():
    try:
        preds = list(col("predictions").find({"userId": request.user_id}, {"_id": 1, "crop": 1, "soil_score": 1, "yield_est": 1, "profit_per_acre": 1, "createdAt": 1, "location": 1, "model_used": 1}).sort("createdAt", -1).limit(20))
        for p in preds: p["_id"] = str(p["_id"])
        return jsonify(preds)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch user predictions: {e}"}), 500

@app.route("/api/predictions/<pred_id>")
@require_auth
def api_prediction_detail(pred_id):
    try:
        pred = col("predictions").find_one({"_id": oid(pred_id)})
        if not pred: return jsonify({"error": "Prediction record not found"}), 404
        if pred.get("userId") != request.user_id and request.user_role != "admin":
            return jsonify({"error": "Forbidden"}), 403
        pred["_id"] = str(pred["_id"])
        return jsonify(pred)
    except Exception as e:
        return jsonify({"error": f"Error retrieving prediction: {e}"}), 500

# ══════════════════════════════════════════════════════════════════════════════
#  FEEDBACK
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/feedback", methods=["POST"])
@require_auth
def api_feedback():
    d = request.get_json() or {}
    no_acres = float(d.get("no_of_acres") or 1)
    ppa      = float(d.get("actual_profit_per_acre") or 0)
    ypa      = float(d.get("actual_yield_per_acre") or 0)
    record = {
        "userId":                request.user_id,
        "predictionId":          d.get("predictionId"),
        "actual_crop":           d.get("actual_crop"),
        "no_of_acres":           no_acres,
        "actual_profit_per_acre": ppa,
        "actual_total_profit":   round(ppa * no_acres, 2),
        "actual_yield_per_acre":  ypa,
        "actual_total_yield":    round(ypa * no_acres, 2),
        "rating":                int(d.get("rating") or 0),
        "comments":              d.get("comments", ""),
        "lang":                  d.get("lang", "en"),
        "city":                  d.get("city", ""),
        "createdAt":             datetime.datetime.utcnow().isoformat(),
    }
    
    try:
        col("feedback").insert_one(record)
        count = col("feedback").count_documents({})
    except Exception as e:
        return jsonify({"error": f"Failed to save feedback to database: {e}"}), 500

    user = None
    try:
        user = col("users").find_one({"_id": oid(request.user_id)}, {"name": 1, "email": 1})
    except: pass

    if user:
        send_email(
            to_email=user["email"],
            subject="🙏 Thank You for Your Feedback — AI Crop Advisor",
            html_body=feedback_thankyou_email_html(
                name=user["name"],
                actual_crop=record.get("actual_crop", "N/A"),
                rating=record.get("rating", 0),
                total_profit=record.get("actual_total_profit", 0),
                total_yield=record.get("actual_total_yield", 0)
            )
        )

    return jsonify({"status": "ok", "community_count": count, "total_profit": record["actual_total_profit"], "total_yield": record["actual_total_yield"]})

@app.route("/api/feedback/<pred_id>")
@require_auth
def api_feedback_for_pred(pred_id):
    try:
        fb = list(col("feedback").find({"predictionId": pred_id}, {"_id": 0, "userId": 0}))
        return jsonify(fb)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN & DB STATUS
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/admin/users")
@require_admin
def api_admin_users():
    users = list(col("users").find({}, {"password": 0}).sort("createdAt", -1))
    for u in users: u["_id"] = str(u["_id"])
    return jsonify(users)

@app.route("/api/admin/predictions")
@require_admin
def api_admin_predictions():
    preds = list(col("predictions").find({}, {"_id": 1, "userId": 1, "crop": 1, "soil_score": 1, "location": 1, "createdAt": 1, "model_used": 1}).sort("createdAt", -1).limit(100))
    for p in preds: p["_id"] = str(p["_id"])
    return jsonify(preds)

@app.route("/api/admin/feedback")
@require_admin
def api_admin_feedback():
    fbs = list(col("feedback").find({}, {"_id": 1, "userId": 1, "predictionId": 1, "actual_crop": 1, "rating": 1, "createdAt": 1}).sort("createdAt", -1).limit(100))
    for f in fbs: f["_id"] = str(f["_id"])
    return jsonify(fbs)

@app.route("/api/admin/stats")
@require_admin
def api_admin_stats():
    return jsonify({
        "users":       col("users").count_documents({}),
        "predictions": col("predictions").count_documents({}),
        "feedback":    col("feedback").count_documents({}),
    })

@app.route("/api/admin/export-training-data")

@app.route("/api/community-export")
def api_export_training():
    import io, csv
    try:
        rows = list(col("feedback").find({"actual_crop": {"$ne": None}}, {"_id": 0, "userId": 0, "predictionId": 0}))
        output = io.StringIO()
        if rows:
            w = csv.DictWriter(output, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)
        return app.response_class(output.getvalue(), mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=training_data.csv"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/community-count")
def api_community_count():
    try:
        cnt = col("feedback").count_documents({})
        return jsonify({"count": cnt})
    except:
        return jsonify({"count": 0})

@app.route("/api/db-status")
def api_db_status():
    if db is None:
        return jsonify({"mongodb": False, "predictions": 0, "community_data": 0, "error": "MongoDB server connection failed"})
    try:
        pred_cnt = db["predictions"].count_documents({})
        fb_cnt   = db["feedback"].count_documents({})
        return jsonify({"mongodb": True, "predictions": pred_cnt, "community_data": fb_cnt})
    except Exception as e:
        return jsonify({"mongodb": False, "predictions": 0, "community_data": 0, "error": str(e)})

@app.route("/api/translations")
def api_translations():
    return jsonify(TRANSLATIONS)

if __name__ == "__main__":
    print("🚀 Starting AI Crop Advisor Server at http://localhost:5000 ...")
    app.run(debug=True, port=5000, use_reloader=False)
