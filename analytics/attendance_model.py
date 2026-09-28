import os
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

MODEL_PATH = "attendance_model.pkl"

def train_default_model():
    """Trains a baseline Logistic Regression model using synthetic course event attendance records."""
    synthetic_data = {
        "invited_before": [1, 5, 0, 10, 2, 4, 1, 8, 3, 0],
        "rsvp_yes_rate": [0.5, 0.9, 0.0, 1.0, 0.6, 0.75, 0.2, 0.95, 0.8, 0.1],
        "day_of_week": ["Monday", "Friday", "Saturday", "Wednesday", "Thursday", "Friday", "Tuesday", "Sunday", "Friday", "Monday"],
        "days_before": [7, 2, 14, 1, 5, 3, 10, 1, 4, 12],
        "role": ["student", "speaker", "student", "faculty", "guest", "student", "guest", "faculty", "student", "student"],
        "attended": [0, 1, 0, 1, 1, 1, 0, 1, 1, 0]
    }
    df = pd.DataFrame(synthetic_data)
    X = df[["invited_before", "rsvp_yes_rate", "day_of_week", "days_before", "role"]]
    y = df["attended"]

    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), ["day_of_week", "role"]),
    ], remainder="passthrough")

    pipe = Pipeline([
        ("pre", pre),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))
    ])

    pipe.fit(X, y)
    joblib.dump(pipe, MODEL_PATH)
    return pipe

def get_or_load_model():
    if os.path.exists(MODEL_PATH):
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            return train_default_model()
    return train_default_model()

def predict_attendance_probability(model, feature_dict: dict) -> float:
    df = pd.DataFrame([feature_dict])
    prob = float(model.predict_proba(df)[0][1])
    return round(prob, 4)
