"""Constants for the UrbanHello Remi integration."""

DOMAIN = "urbanhello_remi_unofficial"

API_BASE_URL = "https://remi2.urbanhello.com"
API_APP_ID = "jf1a0bADt5fq"
API_CLIENT_VERSION = "i1.16.0"
API_APP_BUILD_VERSION = "13433"
API_APP_DISPLAY_VERSION = "1.6.9"
API_OS_VERSION = "14.2 (18B92)"
API_USER_AGENT = "Remi/13433 CFNetwork/1206 Darwin/20.1.0"

SCAN_INTERVAL_SECONDS = 60

# Informational firmware metadata is read rarely, and a failing endpoint is
# retried after a cool-down instead of on every poll.
FIRMWARE_METADATA_INTERVAL_SECONDS = 3600
FIRMWARE_METADATA_RETRY_SECONDS = 300

CONF_REMI_ID = "remi_id"
CONF_SESSION_TOKEN = "session_token"
CONF_INSTALLATION_ID = "installation_id"

FACE_DEFINE_TO_NAME = {
    "FACE_OFF": "Off",
    "FACE_DAY": "Awake",
    "FACE_NIGHT": "Sleepy",
    "FACE_SEMI_AWAKE": "Semi-Awake",
    "FACE_SMILY": "Smiley",
}

FACE_OBJECT_ID_TO_DEFINE = {
    "GDaZOVdRqj": "FACE_OFF",
    "fIjF0yWRxX": "FACE_DAY",
    "rnAltoFwYC": "FACE_NIGHT",
    "9faiiPGBVv": "FACE_SEMI_AWAKE",
    "d712mdpZ0v": "FACE_SMILY",
}

FACE_DEFINE_TO_OBJECT_ID = {v: k for k, v in FACE_OBJECT_ID_TO_DEFINE.items()}

MUSIC_MODE_OPTIONS = {
    0: "Normal",
    1: "Single track",
    2: "Repeat track",
    3: "Repeat playlist",
}

# The REMI recurrence array starts on Monday (unlike the legacy service input).
DAYS_OF_WEEK = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
