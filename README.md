# 🌾 AI Crop Advisor v4
## AI-Based Crop Recommendation System Using IoT Sensors, Machine Learning, and Market Trend Analysis

AI Crop Advisor is an intelligent agricultural advisory application designed for farmers. It combines soil parameters (Nitrogen, Phosphorus, Potassium, pH), climate data (Temperature, Humidity, Rainfall), Random Forest Machine Learning, continuous community feedback learning, market trend forecasting, geospatial mandi mapping, and full multilingual support.

---

## 🌟 Key Features

1. **AI Crop Prediction**: Random Forest model trained on 15 crops (`Rice`, `Maize`, `Groundnut`, `Wheat`, `Cotton`, `Sugarcane`, `Banana`, `Chickpea`, `Tomato`, `Onion`, `Chilli`, `Turmeric`, `Soybean`, `Mango`, `Coconut`).
2. **Complete 6-Language Multilingual Advisory**: Full support for English, Tamil (தமிழ்), Hindi (हिंदी), Telugu (తెలుగు), Kannada (ಕನ್ನಡ), and Malayalam (മലയാളം). Translates UI, crop names, intercrops, fertilizers, seasons, irrigation schedules, disease advice, market trends, and government schemes.
3. **Geospatial Location & Mandi Map**: Location geocoding via Nominatim & Leaflet map display. Shows verified nearby agricultural mandis, calculates Haversine distance, and provides Google Maps direction links.
4. **Soil Health & Irrigation Advisory**: Calculates Soil Health Score (0-100), provides soil improvement tips (e.g. lime, gypsum, organic fertilizers), and suggests irrigation frequency.
5. **Disease Risk Alert**: Detects fungal, bacterial, or pest risks based on humidity and temperature thresholds and provides preventative advice.
6. **Market Forecast & Crop Calendar**: Visual Chart.js price trend forecast and crop sowing/harvest timeline.
7. **Continuous Learning via MongoDB**: Farmer feedback (actual crop grown, actual yield, profit, rating) is recorded in MongoDB and exported for Random Forest model retraining (`retrain_model.py`).
8. **JWT Authentication & Security**: Secure user signup/login, password hashing with `bcrypt`, admin dashboard, and optional SMTP email alerts.

---

## 💻 Prerequisites & Requirements

- **Operating System**: Windows 10/11 (or Linux/macOS)
- **Python**: Python 3.10+ (Python 3.10, 3.11, 3.12 supported)
- **Database**: MongoDB Community Server installed locally OR MongoDB Atlas cloud URI
- **Web Browser**: Chrome, Edge, Firefox, or Safari

---

## 🚀 Step-by-Step Windows Setup Guide

### Step 1: Open Terminal in Project Root
Open PowerShell or Command Prompt in the project folder:
```powershell
cd c:\Users\monish\Downloads\ai-crop-recommendation7\ai-crop-recommendation7
```

### Step 2: Create Virtual Environment
```powershell
python -m venv venv
```

### Step 3: Activate Virtual Environment
**PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```
*(If PowerShell execution policy blocks script execution, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

**Command Prompt (cmd):**
```cmd
venv\Scripts\activate.bat
```

### Step 4: Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables
Copy `backend/.env.example` to `backend/.env`:
```powershell
copy backend\.env.example backend\.env
```
*(Optionally open `backend/.env` in Notepad or VS Code to update `MONGO_URI`, `JWT_SECRET`, `SECRET_KEY`, or `OPENWEATHER_API_KEY`).*

### Step 6: Start MongoDB Database
If running MongoDB locally as a Windows service:
```cmd
net start MongoDB
```
*(If MongoDB is already running, you will see a message indicating it is started).*

### Step 7: Train Machine Learning Model
Train the initial Random Forest model (creates `model/crop_model.pkl` and `model/scaler.pkl`):
```powershell
python train_model.py
```

### Step 8: Create Admin Account
Create your admin user account:
```powershell
python create_admin.py
```
*Follow the interactive prompts to enter Admin Name, Email, and Password (min 6 characters).*

### Step 9: Start the Application Server
Change into the `backend` directory and start Flask:
```powershell
cd backend
python app.py
```

### Step 10: Open Application in Browser
Open your browser and navigate to:
```
http://localhost:5000
```

---

## 🧪 Testing the Application

### Sample Test Inputs:
1. **Sign Up / Login**: Register a user account and log in.
2. **Step 1 — Location**: Enter `Coimbatore` in the city field and click **Get Weather**.
3. **Step 2 — Soil Inputs**:
   - **Nitrogen (N)**: `90`
   - **Phosphorus (P)**: `45`
   - **Potassium (K)**: `40`
   - **Temperature**: `28`
   - **Humidity**: `80`
   - **Soil pH**: `6.2`
   - **Rainfall**: `200`
   - Click **Get Recommendation**.
4. **Step 3 — Results Page**:
   - Verify Recommended Crop (`Rice`), Intercrops (`Azolla`, `Fish`), Fertilizer (`Urea + DAP`), Soil Score, Crop Calendar, Mandis Map.
5. **Language Switch Test (Tamil)**:
   - Select **தமிழ்** from the language dropdown at top right.
   - Verify that all headings, crop names, intercrops, fertilizers, seasons, disease advice, soil health tips, market trends, map labels, buttons, and chart titles switch immediately to Tamil.
6. **Step 4 — Farmer Feedback**:
   - Enter actual farm size (e.g. `2.5` acres), profit, yield, rating, and submit feedback to save to MongoDB.
7. **Admin Dashboard**:
   - Visit `http://localhost:5000/admin` to view user accounts, prediction records, feedback logs, and export training CSV.

---

## 🔁 Continuous Learning & Retraining Model

Periodically retrain the Random Forest model using accumulated farmer feedback:
```powershell
python retrain_model.py
```

---

## 📂 Project Structure

```
ai-crop-recommendation7/
├── backend/
│   ├── app.py                # Main Flask REST API & Web Server
│   ├── .env.example          # Environment variables template
│   ├── templates/            # HTML templates
│   │   ├── login.html        # Login Page
│   │   ├── signup.html       # Sign Up Page
│   │   ├── page1.html        # Step 1: Location & Weather
│   │   ├── page2.html        # Step 2: Soil Parameters
│   │   ├── page3.html        # Step 3: Recommendation Results
│   │   ├── page4.html        # Step 4: Farmer Feedback
│   │   ├── history.html      # Prediction History
│   │   └── admin.html        # Admin Dashboard
│   └── static/
│       ├── css/              # Unified stylesheets (style.css, auth.css)
│       └── js/               # Shared Auth & I18n helper (auth.js)
├── dataset/                  # Training data (crop_dataset.csv)
├── model/                    # ML model (crop_model.pkl & scaler.pkl)
├── train_model.py            # Model training script
├── retrain_model.py          # Continuous learning retraining script
├── create_admin.py           # Admin account creation CLI
├── requirements.txt          # Python package requirements
└── README.md                 # System Documentation & Setup Guide
```
