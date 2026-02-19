"""Constants for the UrbanHello Remi integration."""

DOMAIN = "remi"

API_BASE_URL = "https://remi2.urbanhello.com"
API_APP_ID = "jf1a0bADt5fq"
API_CLIENT_VERSION = "i1.16.0"
API_APP_BUILD_VERSION = "13433"
API_APP_DISPLAY_VERSION = "1.6.9"
API_OS_VERSION = "14.2 (18B92)"
API_USER_AGENT = "Remi/13433 CFNetwork/1206 Darwin/20.1.0"

SCAN_INTERVAL_SECONDS = 60

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
    0: "Off",
    1: "Music",
    2: "White Noise",
}

DAYS_OF_WEEK = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]
