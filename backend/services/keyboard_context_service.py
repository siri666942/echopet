"""Keyboard context aggregation.

This module treats keyboard rhythm as a weak typing-state signal. It never
tries to infer emotions directly and never needs real typed text.
"""

from __future__ import annotations

from collections import defaultdict
from statistics import mean, pstdev
from typing import Any


BACKSPACE_KEYS = {"backspace", "key.backspace", "bksp"}
LONG_PAUSE_SECONDS = 10.0
PAUSE_SECONDS = 3.0


def aggregate_keyboard_features(payload: Any) -> dict:
    """Aggregate raw key events into privacy-preserving behavior features."""

    if payload is None:
        return empty_keyboard_features()

    data = _to_dict(payload)
    window_seconds = float(data.get("window_seconds") or 60)
    if window_seconds <= 0:
        window_seconds = 60.0

    raw_events = data.get("events") or []
    events = sorted(
        (
            _to_dict(event)
            for event in raw_events
            if _to_dict(event).get("type") in {"keydown", "keyup"}
            and _coerce_float(_to_dict(event).get("timestamp")) is not None
        ),
        key=lambda event: float(event["timestamp"]),
    )

    keydowns = [event for event in events if event.get("type") == "keydown"]
    keyups = [event for event in events if event.get("type") == "keyup"]
    key_count = len(keydowns)
    backspace_count = sum(1 for event in keydowns if _is_backspace(event.get("key")))
    backspace_ratio = _safe_div(backspace_count, key_count)

    dwell_values = _calc_dwell_values(events)
    dd_intervals = _intervals([float(event["timestamp"]) for event in keydowns])
    flight_values = _calc_flight_values(keydowns, keyups)
    pauses = [value for value in dd_intervals if value > PAUSE_SECONDS]
    long_pauses = [value for value in dd_intervals if value > LONG_PAUSE_SECONDS]

    return {
        "window_seconds": int(window_seconds) if window_seconds.is_integer() else window_seconds,
        "key_count": key_count,
        "kpm": round(key_count / window_seconds * 60),
        "backspace_count": backspace_count,
        "backspace_ratio": round(backspace_ratio, 4),
        "pause_count": len(pauses),
        "long_pause_count": len(long_pauses),
        "max_pause": round(max(dd_intervals, default=0.0), 4),
        "dwell_mean": _rounded_mean(dwell_values),
        "dwell_std": _rounded_std(dwell_values),
        "flight_mean": _rounded_mean(flight_values),
        "flight_std": _rounded_std(flight_values),
        "dd_interval_mean": _rounded_mean(dd_intervals),
        "dd_interval_std": _rounded_std(dd_intervals),
        "burst_count": _calc_burst_count(dd_intervals),
        "typing_stability": _calc_typing_stability(dd_intervals, flight_values, backspace_ratio),
    }


def empty_keyboard_features() -> dict:
    return {
        "window_seconds": 60,
        "key_count": 0,
        "kpm": 0,
        "backspace_count": 0,
        "backspace_ratio": 0.0,
        "pause_count": 0,
        "long_pause_count": 0,
        "max_pause": 0.0,
        "dwell_mean": 0.0,
        "dwell_std": 0.0,
        "flight_mean": 0.0,
        "flight_std": 0.0,
        "dd_interval_mean": 0.0,
        "dd_interval_std": 0.0,
        "burst_count": 0,
        "typing_stability": 1.0,
    }


def features_from_legacy_context(context: Any) -> dict:
    """Build coarse features from the old kpm/backspace_ratio context fields."""

    features = empty_keyboard_features()
    kpm = int(max(0, getattr(context, "kpm", 0) or 0))
    backspace_ratio = float(max(0.0, min(1.0, getattr(context, "backspace_ratio", 0.0) or 0.0)))
    features.update(
        {
            "key_count": kpm,
            "kpm": kpm,
            "backspace_count": round(kpm * backspace_ratio),
            "backspace_ratio": round(backspace_ratio, 4),
            "typing_stability": round(max(0.0, min(1.0, 1.0 - backspace_ratio * 1.8)), 4),
        }
    )
    return features


def infer_keyboard_state(features: dict, user_baseline: dict | None) -> dict:
    """Infer high-level typing state, not emotion."""

    baseline = {
        "normal_kpm": 120,
        "normal_backspace_ratio": 0.08,
        "normal_flight_mean": 0.18,
        "normal_flight_std": 0.06,
        "normal_pause_count": 4,
    }
    baseline.update(user_baseline or {})

    kpm = float(features.get("kpm") or 0.0)
    backspace_ratio = float(features.get("backspace_ratio") or 0.0)
    flight_mean = float(features.get("flight_mean") or baseline["normal_flight_mean"])
    flight_std = float(features.get("flight_std") or baseline["normal_flight_std"])
    pause_count = float(features.get("pause_count") or 0.0)
    long_pause_count = float(features.get("long_pause_count") or 0.0)
    stability = float(features.get("typing_stability") or 0.0)

    kpm_ratio = _safe_div(kpm, float(baseline["normal_kpm"]) or 120.0)
    backspace_delta = backspace_ratio - float(baseline["normal_backspace_ratio"])
    pause_delta = pause_count - float(baseline["normal_pause_count"])
    flight_std_ratio = _safe_div(flight_std, float(baseline["normal_flight_std"]) or 0.06)
    flight_mean_ratio = _safe_div(flight_mean, float(baseline["normal_flight_mean"]) or 0.18)

    focus = _clamp01(0.25 + min(kpm_ratio, 1.8) * 0.42 + stability * 0.25 - max(pause_delta, 0.0) * 0.04)
    stress = _clamp01(0.18 + max(backspace_delta, 0.0) * 3.2 + max(flight_std_ratio - 1.0, 0.0) * 0.18 + (1.0 - stability) * 0.38)
    fatigue = _clamp01(0.12 + long_pause_count * 0.18 + max(1.0 - kpm_ratio, 0.0) * 0.30 + max(flight_mean_ratio - 1.0, 0.0) * 0.18)

    return {
        "focus": round(focus, 4),
        "stress": round(stress, 4),
        "fatigue": round(fatigue, 4),
        "stability": round(_clamp01(stability), 4),
        "typing_state": _typing_state(focus, stress, fatigue, stability, kpm),
    }


def _typing_state(focus: float, stress: float, fatigue: float, stability: float, kpm: float) -> str:
    if kpm <= 0:
        return "inactive"
    if fatigue >= 0.65:
        return "fatigued_typing"
    if focus >= 0.65 and stress >= 0.6 and stability < 0.7:
        return "high_activity_unstable"
    if focus >= 0.65:
        return "focused_typing"
    if stress >= 0.6:
        return "unstable_typing"
    return "steady_typing" if stability >= 0.65 else "low_activity_unstable"


def _calc_dwell_values(events: list[dict]) -> list[float]:
    down_by_key: dict[str, list[float]] = defaultdict(list)
    dwell_values: list[float] = []
    for event in events:
        key = str(event.get("key") or "")
        timestamp = float(event["timestamp"])
        if event.get("type") == "keydown":
            down_by_key[key].append(timestamp)
        elif event.get("type") == "keyup" and down_by_key[key]:
            started_at = down_by_key[key].pop(0)
            duration = timestamp - started_at
            if duration >= 0:
                dwell_values.append(duration)
    return dwell_values


def _calc_flight_values(keydowns: list[dict], keyups: list[dict]) -> list[float]:
    keyup_times = sorted(float(event["timestamp"]) for event in keyups)
    values: list[float] = []
    previous_keyup: float | None = None
    keyup_index = 0

    for keydown in sorted(keydowns, key=lambda event: float(event["timestamp"])):
        down_time = float(keydown["timestamp"])
        while keyup_index < len(keyup_times) and keyup_times[keyup_index] < down_time:
            previous_keyup = keyup_times[keyup_index]
            keyup_index += 1
        if previous_keyup is not None:
            values.append(down_time - previous_keyup)
    return values


def _intervals(values: list[float]) -> list[float]:
    return [later - earlier for earlier, later in zip(values, values[1:]) if later >= earlier]


def _calc_burst_count(dd_intervals: list[float]) -> int:
    burst_count = 0
    run_length = 1
    in_burst = False
    for interval in dd_intervals:
        if interval <= 0.25:
            run_length += 1
            if run_length >= 5 and not in_burst:
                burst_count += 1
                in_burst = True
        else:
            run_length = 1
            in_burst = False
    return burst_count


def _calc_typing_stability(dd_intervals: list[float], flight_values: list[float], backspace_ratio: float) -> float:
    dd_cv = _coefficient_of_variation(dd_intervals)
    flight_cv = _coefficient_of_variation(flight_values)
    instability = min(dd_cv, 2.0) * 0.32 + min(flight_cv, 2.0) * 0.28 + min(backspace_ratio, 0.5) * 0.8
    return round(_clamp01(1.0 - instability), 4)


def _coefficient_of_variation(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    if avg <= 0:
        return 0.0
    return pstdev(values) / avg


def _rounded_mean(values: list[float]) -> float:
    return round(mean(values), 4) if values else 0.0


def _rounded_std(values: list[float]) -> float:
    return round(pstdev(values), 4) if len(values) > 1 else 0.0


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _is_backspace(key: Any) -> bool:
    return str(key or "").strip().lower() in BACKSPACE_KEYS


def _coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_dict(value: Any) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return {}
