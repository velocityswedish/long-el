"""VELOCITY LONGFORM - 16:9 chapter lesson, brand and motion constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

TARGET_CHAPTERS = 8
PHRASES_PER_CHAPTER = 7
TARGET_PHRASES = TARGET_CHAPTERS * PHRASES_PER_CHAPTER

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY GREEK"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "GREEK"
HANDLE = "@velocitygreek"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {'code': 'el',
 'name': 'Greek',
 'native_name': 'Ελληνικά',
 'history_key': 'greek',
 'english_voice': 'en-US-AvaNeural',
 'english_fallback_voice': 'en-US-GuyNeural',
 'native_voice': 'el-GR-AthinaNeural',
 'native_fallback_voice': 'el-GR-NestorasNeural',
 'native_engine': 'edge',
 'native_lang_code': 'el',
 'english_rate': '-4%',
 'native_rate': '-10%',
 'english_pitch': '+0Hz',
 'native_pitch': '+0Hz',
 'native_label': 'ΕΛΛΗΝΙΚΑ',
 'translit_label': 'SAY IT LIKE',
 'flag': 'gr',
 'greeting': 'Γεια σας!',
 'encouragement': 'Εξαιρετικά!',
 'rtl': False,
 'char_tiles': False,
 'script_font': '',
 'glyphs': 'ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩαβγδεζηθικλμνξοπρστυφχψω'}
# ==== LANGUAGE PACK END ====

# ==== CATEGORIES START ====
CATEGORIES = {'Motivation': 'Κίνητρο',
 'Love': 'Αγάπη',
 'Success': 'Επιτυχία',
 'Wisdom': 'Σοφία',
 'Happiness': 'Ευτυχία',
 'Self Improvement': 'Αυτοβελτίωση',
 'Gratitude': 'Ευγνωμοσύνη',
 'Friendship': 'Φιλία',
 'Hope': 'Ελπίδα',
 'Creativity': 'Δημιουργικότητα',
 'Inner Peace': 'Εσωτερική Γαλήνη',
 'Confidence': 'Αυτοπεποίθηση',
 'Perseverance': 'Επιμονή',
 'Inspiration': 'Έμπνευση',
 'Positive Life': 'Θετική Ζωή',
 'Courage': 'Θάρρος',
 'Kindness': 'Καλοσύνη',
 'Patience': 'Υπομονή',
 'Forgiveness': 'Συγχώρεση',
 'Strength': 'Δύναμη',
 'Joy': 'Χαρά',
 'Balance': 'Ισορροπία',
 'Growth': 'Ανάπτυξη',
 'Purpose': 'Σκοπός',
 'Mindfulness': 'Ενσυνειδητότητα',
 'Travel & Airport': 'Ταξίδια & Αεροδρόμιο',
 'Ordering Food & Dining': 'Παραγγελίες Φαγητού & Εστιατόρια',
 'Shopping & Prices': 'Αγορές & Τιμές',
 'Asking for Directions': 'Ζητώντας Οδηγίες',
 'Hotel & Accommodation': 'Ξενοδοχείο & Διαμονή',
 'Daily Routine': 'Καθημερινή Ρουτίνα',
 'Meeting People & Greetings': 'Γνωριμίες & Χαιρετισμοί',
 'Emergency & Health': 'Επείγοντα & Υγεία',
 'Public Transportation': 'Μέσα Μαζικής Μεταφοράς',
 'Work & Office': 'Εργασία & Γραφείο',
 'Weather & Small Talk': 'Καιρός & Συζήτηση για τα Πάντα',
 'Coffee Shop & Bakery': 'Καφετέρια & Φούρνος',
 'Family & Home': 'Οικογένεια & Σπίτι',
 'Hobbies & Free Time': 'Χόμπι & Ελεύθερος Χρόνος',
 'Dating & Romance': 'Ραντεβού & Ρομαντισμός',
 'Phone Calls & Messages': 'Τηλεφωνήματα & Μηνύματα',
 'Banking & Money': 'Τράπεζα & Χρήματα',
 'Doctor & Pharmacy': 'Γιατρός & Φαρμακείο',
 'Sports & Fitness': 'Αθλητισμός & Γυμναστική',
 'Celebrations & Parties': 'Γιορτές & Πάρτι',
 'Feelings & Emotions': 'Συναισθήματα & Ένστικτα',
 'Agreeing & Disagreeing': 'Συμφωνία & Διαφωνία',
 'Making Plans': 'Κάνοντας Σχέδια',
 'Common Native Slang': 'Συνήθης Τοπική Αργκό',
 'Cultural Traditions': 'Πολιτιστικές Παραδόσεις'}
# ==== CATEGORIES END ====

CATEGORY_NAMES = list(CATEGORIES.keys())

AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-5.4-nano")
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 7.2
CHAPTER_INTRO_DURATION = 4.4
OUTRO_DURATION = 13.0

EN_CARD_IN = 0.70
GAP_EN_NATIVE = 0.60
NATIVE_CARD_LEAD = 0.40
GAP_BEFORE_REPEAT = 1.00
TAIL_HOLD = 1.30

# ---------------------------------------------------------------- palette

INK = "#30303A"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#7C5CFF"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

# ==== HASHTAGS START ====
HASHTAGS = ['#learngreek',
 '#greeklessons',
 '#greekforbeginners',
 '#languagelearning',
 '#greekvocabulary',
 '#velocitygreek',
 '#dailygreek',
 '#greek',
 '#learnlanguages',
 '#speakgreek']
# ==== HASHTAGS END ====
