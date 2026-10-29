"""
train_model.py
==============
Initial training script — trains Random Forest on the crop dataset.
Run this ONCE before starting the app or if model files are missing.

Usage:
  python train_model.py
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

import pandas as pd
import numpy as np
import joblib, os
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH  = BASE_DIR / "model" / "crop_model.pkl"
SCALER_PATH = BASE_DIR / "model" / "scaler.pkl"
DATASET_PATH = BASE_DIR / "dataset" / "crop_dataset.csv"

# ── Generate training data for 15 crops ──────────────────────────────────────
print("Generating training dataset for 15 crops...")
np.random.seed(42)

crops = {
    "Rice":      {"N":(60,120),"P":(30,60),"K":(30,60),"T":(20,35),"H":(70,95),"pH":(5.5,7.0),"R":(150,300)},
    "Maize":     {"N":(50,100),"P":(35,75),"K":(35,75),"T":(18,32),"H":(50,75),"pH":(5.5,7.5),"R":(50,130)},
    "Groundnut": {"N":(25,70), "P":(40,85),"K":(30,70),"T":(22,35),"H":(45,75),"pH":(5.5,7.0),"R":(45,110)},
    "Wheat":     {"N":(60,120),"P":(35,80),"K":(35,80),"T":(5,22), "H":(38,65),"pH":(5.5,7.8),"R":(35,110)},
    "Cotton":    {"N":(35,80), "P":(30,65),"K":(60,120),"T":(22,38),"H":(48,70),"pH":(5.8,7.5),"R":(55,115)},
    "Sugarcane": {"N":(90,150),"P":(40,80),"K":(90,150),"T":(22,38),"H":(60,82),"pH":(5.8,7.5),"R":(110,250)},
    "Banana":    {"N":(75,130),"P":(40,75),"K":(55,100),"T":(24,38),"H":(70,90),"pH":(5.5,7.0),"R":(90,200)},
    "Chickpea":  {"N":(20,60), "P":(30,80),"K":(20,60),"T":(15,28),"H":(30,58),"pH":(5.8,8.5),"R":(30,85)},
    "Tomato":    {"N":(80,140),"P":(60,100),"K":(70,120),"T":(20,32),"H":(55,80),"pH":(6.0,7.0),"R":(60,150)},
    "Onion":     {"N":(30,80), "P":(30,70),"K":(40,80),"T":(15,30),"H":(50,75),"pH":(6.0,7.5),"R":(35,100)},
    "Chilli":    {"N":(60,110),"P":(50,90),"K":(60,100),"T":(24,35),"H":(55,80),"pH":(6.0,7.5),"R":(60,130)},
    "Turmeric":  {"N":(50,100),"P":(40,80),"K":(60,110),"T":(22,35),"H":(65,85),"pH":(5.5,7.0),"R":(100,220)},
    "Soybean":   {"N":(30,80), "P":(35,70),"K":(35,70),"T":(20,32),"H":(50,75),"pH":(6.0,7.5),"R":(60,140)},
    "Mango":     {"N":(25,70), "P":(20,55),"K":(40,80),"T":(24,40),"H":(40,70),"pH":(5.5,7.5),"R":(25,100)},
    "Coconut":   {"N":(40,90), "P":(30,65),"K":(50,100),"T":(25,38),"H":(65,85),"pH":(5.5,7.5),"R":(100,220)},
}

rows = []
for crop, r in crops.items():
    for _ in range(500):   # 500 per crop = 7500 rows total
        rows.append({
            "N":          round(np.random.uniform(*r["N"]), 1),
            "P":          round(np.random.uniform(*r["P"]), 1),
            "K":          round(np.random.uniform(*r["K"]), 1),
            "temperature":round(np.random.uniform(*r["T"]), 1),
            "humidity":   round(np.random.uniform(*r["H"]), 1),
            "ph":         round(np.random.uniform(*r["pH"]), 2),
            "rainfall":   round(np.random.uniform(*r["R"]), 1),
            "label":      crop,
        })

df = pd.DataFrame(rows)
print(f"  Dataset: {df.shape[0]} rows, {df['label'].nunique()} crops")

# Save dataset
os.makedirs(DATASET_PATH.parent, exist_ok=True)
df.to_csv(DATASET_PATH, index=False)
print(f"  Dataset saved -> {DATASET_PATH}")

# ── Train ─────────────────────────────────────────────────────────────────────
X = df[["N","P","K","temperature","humidity","ph","rainfall"]].values
y = df["label"].values

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s  = scaler.transform(X_test)

print("\nTraining Random Forest (150 trees, 15 crops)...")
model = RandomForestClassifier(n_estimators=150, random_state=42, n_jobs=-1)
model.fit(X_train_s, y_train)

y_pred = model.predict(X_test_s)
acc    = accuracy_score(y_test, y_pred)
cv     = cross_val_score(model, scaler.transform(X), y, cv=5, scoring="accuracy")

print(f"\n{'='*50}")
print(f"  Accuracy         : {acc*100:.2f}%")
print(f"  Cross-val (mean) : {cv.mean()*100:.2f}%")
print(f"  Cross-val (std)  : {cv.std()*100:.2f}%")
print(f"{'='*50}")
print(f"\nPer-crop results:")
print(classification_report(y_test, y_pred))

# ── Save ──────────────────────────────────────────────────────────────────────
os.makedirs(MODEL_PATH.parent, exist_ok=True)
joblib.dump(model,  MODEL_PATH)
joblib.dump(scaler, SCALER_PATH)
print(f"Model saved -> {MODEL_PATH}")
print(f"Scaler saved -> {SCALER_PATH}")
print("\nTraining complete! Now run: cd backend && python app.py")
