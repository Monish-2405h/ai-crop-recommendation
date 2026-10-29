╔══════════════════════════════════════════════════════════╗
║       AI CROP ADVISOR v4 — Full Auth + MongoDB           ║
║       INNOVSENSE 2026 | KPR Institute of Engg & Tech     ║
╚══════════════════════════════════════════════════════════╝

FOLDER STRUCTURE
────────────────
ai-crop-recommendation/
├── backend/
│   ├── app.py                    ← Main Flask app (auth + all APIs)
│   ├── templates/
│   │   ├── login.html            ← Page 0: Login
│   │   ├── signup.html           ← Page 0b: Sign Up
│   │   ├── page1.html            ← Page 1: Location & Weather
│   │   ├── page2.html            ← Page 2: Soil Parameters
│   │   ├── page3.html            ← Page 3: AI Results
│   │   ├── page4.html            ← Page 4: Feedback
│   │   ├── history.html          ← My Prediction History
│   │   └── admin.html            ← Admin Dashboard
│   └── static/
│       ├── css/
│       │   ├── style.css         ← Main design system
│       │   └── auth.css          ← Auth + admin styles
│       └── js/
│           └── auth.js           ← JWT helper (shared by all pages)
├── model/
│   ├── crop_model.pkl            ← Trained ML model (after train_model.py)
│   └── scaler.pkl
├── dataset/
│   └── crop_dataset.csv
├── train_model.py                ← Train 15-crop ML model
├── retrain_model.py              ← Retrain with community data
├── create_admin.py               ← Create first admin account
└── requirements.txt

SETUP INSTRUCTIONS
──────────────────
Step 1 — Install Python libraries
   pip install -r requirements.txt

Step 2 — Install MongoDB (choose one)

   Option A — Local (MongoDB Community):
   → Download: https://www.mongodb.com/try/download/community
   → Install with defaults (runs as Windows service)
   → View data: https://www.mongodb.com/try/download/compass

   Option B — Cloud (MongoDB Atlas FREE):
   → https://www.mongodb.com/atlas/database
   → Create free cluster → Get connection string
   → Windows: set MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/
   → Mac/Linux: export MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/

Step 3 — Train the ML model
   python train_model.py

Step 4 — Create admin account (run once)
   python create_admin.py

Step 5 — Run the app
   cd backend
   python app.py

Step 6 — Open browser
   http://localhost:5000         → Login page
   http://localhost:5000/signup  → Sign Up
   http://localhost:5000/admin   → Admin Dashboard

PAGE FLOW
─────────
/           → Login
/signup     → Sign Up
/app        → Page 1: Location & Weather
/soil       → Page 2: Soil Parameters
/results    → Page 3: AI Results + Map + Charts
/feedback   → Page 4: Farmer Feedback
/history    → My Prediction History
/admin      → Admin Dashboard (admin only)

API ENDPOINTS
─────────────
Auth:
  POST /api/auth/signup           → Register new user
  POST /api/auth/login            → Login (returns JWT)
  GET  /api/auth/me               → Get current user

Predictions (requires login):
  POST /api/predictions           → Save + get prediction
  GET  /api/predictions/user      → Get MY history only
  GET  /api/predictions/<id>      → Get one prediction

Feedback (requires login):
  POST /api/feedback              → Submit feedback
  GET  /api/feedback/<pred_id>    → Get feedback for prediction

Admin only:
  GET  /api/admin/users           → All users
  GET  /api/admin/predictions     → All predictions
  GET  /api/admin/feedback        → All feedback
  GET  /api/admin/stats           → Counts
  GET  /api/admin/export-training-data → Download CSV

ENVIRONMENT VARIABLES
─────────────────────
MONGO_URI            → MongoDB connection (default: localhost:27017)
JWT_SECRET           → JWT signing secret (change in production!)
SECRET_KEY           → Flask session key
OPENWEATHER_API_KEY  → Optional: live weather

SECURITY FEATURES
─────────────────
✅ Passwords hashed with bcrypt (never stored plain)
✅ JWT tokens (expire in 24 hours)
✅ Role-based access (user/admin)
✅ Users can only see their OWN predictions
✅ Admin routes protected with @require_admin decorator
✅ Passwords never returned in API responses
✅ Email validated with regex on signup
