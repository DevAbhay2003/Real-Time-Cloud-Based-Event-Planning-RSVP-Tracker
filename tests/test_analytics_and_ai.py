import pytest
from analytics.attendance_model import train_default_model, predict_attendance_probability

def test_attendance_prediction_model():
    model = train_default_model()
    # Feature dictionary: invited_before, rsvp_yes_rate, day_of_week, days_before, role
    test_feature = {
        "invited_before": 3,
        "rsvp_yes_rate": 0.85,
        "day_of_week": "Friday",
        "days_before": 2,
        "role": "speaker"
    }
    prob = predict_attendance_probability(model, test_feature)
    assert 0.0 <= prob <= 1.0
    assert prob > 0.5
