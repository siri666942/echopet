"""Tests for keyboard context aggregation."""

from backend.services.keyboard_context_service import (
    aggregate_keyboard_features,
    infer_keyboard_state,
)


def test_aggregate_keyboard_features_from_key_events():
    payload = {
        "window_seconds": 60,
        "events": [
            {"key": "CHAR", "type": "keydown", "timestamp": 0.0},
            {"key": "CHAR", "type": "keyup", "timestamp": 0.1},
            {"key": "CHAR", "type": "keydown", "timestamp": 0.2},
            {"key": "CHAR", "type": "keyup", "timestamp": 0.3},
            {"key": "CHAR", "type": "keydown", "timestamp": 0.4},
            {"key": "CHAR", "type": "keyup", "timestamp": 0.5},
            {"key": "Backspace", "type": "keydown", "timestamp": 4.0},
            {"key": "Backspace", "type": "keyup", "timestamp": 4.1},
            {"key": "CHAR", "type": "keydown", "timestamp": 14.5},
            {"key": "CHAR", "type": "keyup", "timestamp": 14.6},
        ],
    }

    features = aggregate_keyboard_features(payload)

    assert features["key_count"] == 5
    assert features["kpm"] == 5
    assert features["backspace_count"] == 1
    assert features["backspace_ratio"] == 0.2
    assert features["pause_count"] == 2
    assert features["long_pause_count"] == 1
    assert features["max_pause"] == 10.5
    assert features["dwell_mean"] == 0.1
    assert features["dd_interval_mean"] == 3.625
    assert 0 <= features["typing_stability"] <= 1


def test_aggregate_handles_empty_and_unmatched_events():
    empty = aggregate_keyboard_features(None)
    assert empty["key_count"] == 0
    assert empty["typing_stability"] == 1.0

    payload = {
        "window_seconds": 60,
        "events": [
            {"key": "CHAR", "type": "keyup", "timestamp": 1.0},
            {"key": "CHAR", "type": "keydown", "timestamp": 2.0},
        ],
    }
    features = aggregate_keyboard_features(payload)
    assert features["key_count"] == 1
    assert features["dwell_mean"] == 0.0


def test_burst_and_state_inference_use_anonymized_char_keys():
    events = []
    timestamp = 0.0
    for index in range(8):
        events.append({"key": "CHAR", "type": "keydown", "timestamp": timestamp})
        events.append({"key": "CHAR", "type": "keyup", "timestamp": timestamp + 0.05})
        timestamp += 0.12

    features = aggregate_keyboard_features({"window_seconds": 60, "events": events})
    state = infer_keyboard_state(features, None)

    assert features["burst_count"] == 1
    assert "emotion" not in state
    assert state["typing_state"] in {
        "focused_typing",
        "steady_typing",
        "low_activity_unstable",
        "unstable_typing",
        "high_activity_unstable",
    }
