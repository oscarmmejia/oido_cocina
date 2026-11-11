SETTINGS_RESPONSE_EXAMPLE = {
    "id": 1,
    "name": "Test restaurant",
    "time_zone": "Europe/Madrid",
    "is_active": True,
    "courtesy_minutes": 5,
    "slot_minutes": 60,
    "min_break_between_shifts": 30,
    "day_of_week": 5,
    "period": "evening",
    "open_time": "12:00:00",
    "close_time": "23:00:00",
    "kitchen_close_time": "22:00:00",
    "direction": "Example address"
}

SETTINGS_UPDATE_EXAMPLES = {
    "complete": {
        "summary": "Update all editable fields",
        "value": {
            "time_zone": "Europe/Madrid",
            "courtesy_minutes": 10,
            "slot_minutes": 90,
            "min_break_between_shifts": 30,
            "day_of_week": 5,
            "period": "evening",
            "open_time": "20:00:00",
            "close_time": "03:00:00",
            "kitchen_close_time": "02:00:00"
        }
    },
    "partial": {
        "summary": "Update courtesy only",
        "value": {
            "courtesy_minutes": 10
        }
    },
    "overnight": {
        "summary": "Close after midnight",
        "value": {
            "open_time": "20:00:00",
            "close_time": "03:00:00",
            "kitchen_close_time": "02:00:00"
        }
    },
    "negative_courtesy": {
        "summary": "Reject negative courtesy",
        "value": {
            "courtesy_minutes": -1
        }
    },
    "equal_hours": {
        "summary": "Reject equal opening and closing times",
        "value": {
            "open_time": "20:00:00",
            "close_time": "20:00:00",
            "courtesy_minutes": 10
        }
    },
    "kitchen_after_closing": {
        "summary": "Reject kitchen closing after the restaurant",
        "value": {
            "open_time": "20:00:00",
            "close_time": "03:00:00",
            "kitchen_close_time": "04:00:00",
            "courtesy_minutes": 10
        }
    }
}

SETTINGS_SUCCESS_EXAMPLES = {
    name: {
        "summary": example["summary"],
        "value": {**SETTINGS_RESPONSE_EXAMPLE, **example["value"]},
    }
    for name, example in SETTINGS_UPDATE_EXAMPLES.items()
    if name in ("complete", "partial", "overnight")
}

SETTINGS_VALIDATION_EXAMPLES = {
    "negative_courtesy": {
        "summary": "Reject negative courtesy",
        "value": {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Los datos enviados no son válidos."
            }
        }
    },
    "equal_hours": {
        "summary": "Reject equal opening and closing times",
        "value": {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "La hora de cierre debe ser posterior a la apertura; no pueden coincidir."
            }
        }
    },
    "kitchen_after_closing": {
        "summary": "Reject kitchen closing after the restaurant",
        "value": {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "El cierre de cocina no puede ser posterior al cierre del local."
            }
        }
    }
}
