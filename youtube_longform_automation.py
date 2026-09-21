"""
YouTube Long-Form Video Automation - Bilingual English/Greek Content Generator
GENERATES 10-MINUTE VIDEOS with improved backgrounds for YouTube
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
LONGFORM_DIR = OUTPUT_DIR / "longform_videos"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR, LONGFORM_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (16:9 horizontal for YouTube long-form)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TARGET_DURATION_MINUTES = 5
TARGET_PHRASES = 120

# English category names
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Greek translations
CATEGORIES_GREEK = {
    "Motivation": "Κίνητρο",
    "Love": "Αγάπη",
    "Success": "Επιτυχία",
    "Wisdom": "Σοφία",
    "Happiness": "Ευτυχία",
    "Self Improvement": "Αυτοβελτίωση",
    "Gratitude": "Ευγνωμοσύνη",
    "Friendship": "Φιλία",
    "Hope": "Ελπίδα",
    "Creativity": "Δημιουργικότητα",
    "Inner Peace": "Εσωτερική Γαλήνη",
    "Confidence": "Αυτοπεποίθηση",
    "Perseverance": "Επιμονή",
    "Inspiration": "Έμπνευση",
    "Positive Life": "Θετική Ζωή",
    "Courage": "Θάρρος",
    "Kindness": "Καλοσύνη",
    "Patience": "Υπομονή",
    "Forgiveness": "Συγχώρεση",
    "Strength": "Δύναμη",
    "Joy": "Χαρά",
    "Balance": "Ισορροπία",
    "Growth": "Ανάπτυξη",
    "Purpose": "Σκοπός",
    "Mindfulness": "Ενσυνειδητότητα",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
LANG_VOICE = "el-GR-AthinaNeural"

# Phrase history file
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Viral hook styles for engagement
VIRAL_STYLES = [
    "surprising fact",
    "common mistake correction",
    "quick tip",
    "must-know phrase",
    "local secret",
    "travel hack",
    "flirty phrase",
    "funny expression",
    "cultural insight",
    "word origin story"
]

# AI Model
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file."
    )


# ============== PHRASE HISTORY MANAGEMENT ==============

def load_phrase_history():
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def is_phrase_similar(new_phrase, used_phrases, similarity_threshold=0.6):
    new_words = set(new_phrase.lower().split())
    if len(new_words) < 3:
        for used in used_phrases:
            if new_phrase.lower() in used.lower() or used.lower() in new_phrase.lower():
                return True
        return False
    for used in used_phrases:
        used_words = set(used.lower().split())
        if len(new_words) == 0 or len(used_words) == 0:
            continue
        intersection = len(new_words.intersection(used_words))
        union = len(new_words.union(used_words))
        similarity = intersection / union if union > 0 else 0
        if similarity >= similarity_threshold:
            return True
    return False


def filter_similar_phrases(phrases, history, similarity_threshold=0.6):
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    unique_phrases = []
    for phrase in phrases:
        english_text = phrase.get("english", "")
        if not is_phrase_similar(english_text, used_phrases, similarity_threshold):
            unique_phrases.append(phrase)
        else:
            print(f"[filter] Skipping similar: {english_text[:50]}...")
    return unique_phrases


def add_phrases_to_history(phrases, category):
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "greek": phrase["greek"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CONTENT GENERATION ==============

def calculate_phrases_needed(target_minutes: int) -> int:
    avg_phrase_duration = 5.0
    total_seconds = target_minutes * 60
    return int(total_seconds / avg_phrase_duration)


def repair_and_parse_json(content: str):
    """Robustly parse JSON from LLM output with truncation repair and regex recovery."""
    import re
    cleaned = content.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()
    
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start:end+1])
        except Exception:
            pass

    if start != -1:
        sub = cleaned[start:]
        last_brace = sub.rfind("}")
        if last_brace != -1:
            try:
                return json.loads(sub[:last_brace+1] + "]")
            except Exception:
                pass

    matches = re.findall(r'\{[^{}]*\"english\"[^{}]*\}', cleaned)
    results = []
    for m in matches:
        try:
            obj = json.loads(m)
            if isinstance(obj, dict) and "english" in obj:
                results.append(obj)
        except Exception:
            continue
    if results:
        return results

    raise ValueError("Could not parse or repair JSON from content")


def generate_phrases_for_longform(category_english: str, num_phrases: int) -> list:
    category_greek = CATEGORIES_GREEK[category_english]
    history = load_phrase_history()
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    viral_style = random.choice(VIRAL_STYLES)
    all_phrases = []
    batch_size = 20
    max_attempts = 5

    for batch_num in range((num_phrases + batch_size - 1) // batch_size):
        remaining = num_phrases - len(all_phrases)
        current_batch_size = min(batch_size, remaining)
        if current_batch_size <= 0:
            break
        for attempt in range(max_attempts):
            try:
                import requests
                url = "https://gen.pollinations.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                    "Content-Type": "application/json"
                }
                exclusion_note = ""
                if used_phrases:
                    recent = used_phrases[-30:] if len(used_phrases) > 30 else used_phrases
                    exclusion_note = f"\n\nAVOID these phrases (already used): {recent}"

                prompt = f"""Create {current_batch_size * 2} unique {category_english} phrases for English speakers learning Greek.

Style: Make each phrase feel like a {viral_style} - something people would want to share!

CRITICAL RULE - ABSOLUTELY ZERO Greek IN ENGLISH FIELD:
The "english" field must contain ONLY English words. NO Greek words at all.
The "greek" field contains the Greek translation in Greek script.
The "pronunciation" field is phonetic English spelling approximating Greek sounds.

These are INSPIRATIONAL PHRASES about the topic, NOT language-learning tips.

WRONG (teaching tip with Greek words): {{"english": "Don't say 'γεια σου,' it means more than 'hello.'", ...}}
WRONG (Greek word in english): {{"english": "Use 'ευχαριστώ' for thank you", ...}}
WRONG (lesson tip): {{"english": "Say 'παρακαλώ' for please", ...}}
CORRECT (pure english phrase): {{"english": "Knowledge is the key to wisdom.", "greek": "Η γνώση είναι το κλειδί για τη σοφία", "pronunciation": "ee gno-see EE-ne to klee-DEE ya tee so-FEE-a"}}
CORRECT: {{"english": "A wise person listens more than they speak.", "greek": "Ένας σοφός άνθρωπος ακούει περισσότερο από ό,τι μιλάει", "pronunciation": "E-nas so-FOS AN-thro-pos a-KOO-ee pe-ri-SO-te-ro a-po o-ti mi-LA-ee"}}

The english field MUST be 100% English words only. Absolutely NO Greek words in the english field.

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Use everyday vocabulary - avoid exotic or rare words
7. Avoid complex grammar - keep it simple and practical
8. Vary sentence structure for natural flow

For each phrase:
1. English phrase (pure English, zero Greek words) with commas for natural pauses
2. Greek translation in Greek script
3. Pronunciation guide (phonetic English spelling)
CRITICAL: Every translation MUST be in Greek. NEVER use German, Spanish, or any other language. Only Greek.

Return as JSON array:
[{{"english": "...", "greek": "...", "pronunciation": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.{exclusion_note}"""

                payload = {
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You create INSPIRATIONAL PHRASES for YouTube language learning videos. CRITICAL: The 'english' field must be PURE ENGLISH with ZERO Greek words - no Greek words at all. These are universal inspirational phrases, NOT language learning tips. Greek goes ONLY in the 'greek' field, written in Greek script."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1.0
                }

                response = requests.post(url, headers=headers, json=payload, timeout=90)
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                phrases = repair_and_parse_json(content)
                filtered_phrases = filter_similar_phrases(phrases, history)
                unique_phrases = []
                for phrase in filtered_phrases:
                    if len(phrase["english"].split()) > 15:
                        continue
                    if not is_phrase_used(phrase["english"]):
                        unique_phrases.append(phrase)
                for phrase in unique_phrases:
                    if len(all_phrases) < num_phrases:
                        all_phrases.append(phrase)
                if len(all_phrases) >= num_phrases:
                    break
            except Exception as e:
                print(f"[content] Batch {batch_num + 1}, Attempt {attempt + 1} failed: {e}")
        if len(all_phrases) < num_phrases:
            import time
            time.sleep(1)

    if not all_phrases:
        print(f"[content] AI generation produced 0 phrases. Loading fresh fallback phrases for '{category_english}'...")
        all_phrases = get_fresh_fallback_phrases(category_english, num_phrases)
    elif len(all_phrases) < num_phrases:
        print(f"[content] Only {len(all_phrases)} phrases generated. Padding with fresh fallback phrases...")
        extras = get_fresh_fallback_phrases(category_english, num_phrases - len(all_phrases))
        for ex in extras:
            if ex not in all_phrases:
                all_phrases.append(ex)

    final_phrases = all_phrases[:num_phrases]
    if final_phrases:
        add_phrases_to_history(final_phrases, category_english)
    print(f"[content] Generated {len(final_phrases)} phrases for long-form video")
    return final_phrases


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    all_fallbacks = {
        "Motivation": [
            {"english": "Believe in yourself.", "greek": "Πίστεψε στον εαυτό σου.", "pronunciation": "PEE-stepse ston eaf-TO sou"},
            {"english": "You are capable of amazing things.", "greek": "Είσαι ικανός για καταπληκτικά πράγματα.", "pronunciation": "EE-se i-ka-NOS ya ka-ta-pli-kti-KA PRA-gma-ta"},
            {"english": "Dream big, start small.", "greek": "Ονειρέψου μεγάλα, ξεκίνα μικρά.", "pronunciation": "o-ni-REP-sou me-GA-la, kse-KEE-na mi-KRA"},
            {"english": "Your future is created by your actions.", "greek": "Το μέλλον σου δημιουργείται από τις πράξεις σου.", "pronunciation": "to MEL-lon sou di-mi-our-YEE-te a-po tis PRA-xeis sou"},
            {"english": "Never give up on your dreams.", "greek": "Μην εγκαταλείπεις ποτέ τα όνειρά σου.", "pronunciation": "min e-ga-ta-LEI-peis po-TE ta o-ni-RA sou"},
            {"english": "Small steps lead to big changes.", "greek": "Μικρά βήματα οδηγούν σε μεγάλες αλλαγές.", "pronunciation": "mi-KRA VI-ma-ta o-di-GOUN se me-GA-les a-la-YES"},
            {"english": "You are stronger than you think.", "greek": "Είσαι πιο δυνατός από ό,τι νομίζεις.", "pronunciation": "EE-se pio di-na-TOS a-po o-ti no-MI-zis"},
        ],
        "Love": [
            {"english": "Love yourself first.", "greek": "Αγάπα τον εαυτό σου πρώτα.", "pronunciation": "a-GA-pa ton eaf-TO sou PRO-ta"},
            {"english": "Love makes everything possible.", "greek": "Η αγάπη κάνει τα πάντα δυνατά.", "pronunciation": "ee a-GA-pi KA-nei ta PAN-ta di-na-TA"},
            {"english": "My heart beats for you.", "greek": "Η καρδιά μου χτυπάει για σένα.", "pronunciation": "ee kar-DIA mou hti-PA-i ya SE-na"},
            {"english": "You are my everything.", "greek": "Είσαι το παν μου.", "pronunciation": "EE-se to PAN mou"},
            {"english": "Together forever, hand in hand.", "greek": "Μαζί για πάντα, χέρι χέρι.", "pronunciation": "ma-ZI ya PAN-da, HE-ri HE-ri"},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "greek": "Η επιτυχία έρχεται από τη σκληρή δουλειά.", "pronunciation": "ee e-pi-ti-HI-a ER-he-te a-po ti skli-RI dou-LYA"},
            {"english": "Keep going, you're getting there.", "greek": "Συνέχισε, πλησιάζεις.", "pronunciation": "si-NE-hi-se, pli-SI-a-zis"},
            {"english": "Winners never quit.", "greek": "Οι νικητές δεν παρατάνε ποτέ.", "pronunciation": "ee ni-ki-TES den pa-ra-TA-ne po-TE"},
            {"english": "Your effort will pay off.", "greek": "Η προσπάθειά σου θα ανταμειφθεί.", "pronunciation": "ee pro-SPA-thia sou tha a-da-mif-THI"},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "greek": "Η γνώση είναι δύναμη.", "pronunciation": "ee GNO-si EE-ne DEE-na-mi"},
            {"english": "Learn from yesterday, live for today.", "greek": "Μάθε από το χθες, ζήσε για το σήμερα.", "pronunciation": "MA-the a-po to hthes, ZEE-se ya to SI-me-ra"},
            {"english": "Think before you act.", "greek": "Σκέψου πριν ενεργήσεις.", "pronunciation": "SKEP-sou prin e-ner-YI-sis"},
            {"english": "Experience is the best teacher.", "greek": "Η εμπειρία είναι ο καλύτερος δάσκαλος.", "pronunciation": "ee em-bi-EE-a EE-ne o ka-LY-te-ros DAS-ka-los"},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "greek": "Η ευτυχία είναι επιλογή.", "pronunciation": "ee ef-ti-HI-a EE-ne e-pi-lo-YI"},
            {"english": "Find joy in the little things.", "greek": "Βρες χαρά στα μικρά πράγματα.", "pronunciation": "vres ha-RA sta mi-KRA PRA-gma-ta"},
            {"english": "Smile, it makes others happy.", "greek": "Χαμογέλα, κάνει τους άλλους χαρούμενους.", "pronunciation": "ha-mo-YE-la, KA-nei tous AL-lous ha-ROU-me-nous"},
            {"english": "Today is a gift.", "greek": "Το σήμερα είναι ένα δώρο.", "pronunciation": "to SI-me-ra EE-ne E-na DO-ro"},
        ],
        "Self Improvement": [
            {"english": "Be better than yesterday.", "greek": "Γίνε καλύτερος από χθες.", "pronunciation": "YEE-ne ka-LY-te-ros a-po hthes"},
            {"english": "Grow through what you go through.", "greek": "Μεγάλωνε μέσα από ό,τι περνάς.", "pronunciation": "me-GA-lo-ne ME-sa a-po o-ti per-NAS"},
            {"english": "Invest in yourself daily.", "greek": "Επένδυσε στον εαυτό σου καθημερινά.", "pronunciation": "e-PEN-dy-se ston eaf-TO sou ka-thi-me-ri-NA"},
        ],
        "Gratitude": [
            {"english": "Thank you for everything.", "greek": "Σε ευχαριστώ για όλα.", "pronunciation": "se ef-ha-ri-STO ya O-la"},
            {"english": "I appreciate your help.", "greek": "Εκτιμώ τη βοήθειά σου.", "pronunciation": "ek-ti-MO ti vo-I-thia sou"},
            {"english": "Grateful for this moment.", "greek": "Ευγνώμων για αυτή τη στιγμή.", "pronunciation": "ev-GNO-mon ya af-TI ti stig-MI"},
        ],
        "Friendship": [
            {"english": "Friends forever, no matter what.", "greek": "Φίλοι για πάντα, ό,τι κι αν γίνει.", "pronunciation": "FI-li ya PAN-da, o-ti ki an YI-ni"},
            {"english": "You are my best friend.", "greek": "Είσαι ο καλύτερός μου φίλος.", "pronunciation": "EE-se o ka-LY-te-ROS mou FI-los"},
            {"english": "True friends stick together.", "greek": "Οι αληθινοί φίλοι μένουν ενωμένοι.", "pronunciation": "ee a-li-thi-NI FI-li ME-noun e-no-ME-ni"},
        ],
        "Hope": [
            {"english": "There is always hope.", "greek": "Υπάρχει πάντα ελπίδα.", "pronunciation": "ee-PAR-hi PAN-da el-PI-da"},
            {"english": "Better days are coming.", "greek": "Καλύτερες μέρες έρχονται.", "pronunciation": "ka-LY-te-res ME-res ER-hon-te"},
            {"english": "Keep faith, keep going.", "greek": "Κράτα την πίστη, συνέχισε.", "pronunciation": "KRA-ta tin PI-sti, si-NE-hi-se"},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "greek": "Δημιούργησε κάτι όμορφο σήμερα.", "pronunciation": "di-MI-our-yi-se KA-ti OM-or-fo SI-me-ra"},
            {"english": "Your imagination is unlimited.", "greek": "Η φαντασία σου είναι απεριόριστη.", "pronunciation": "ee fan-ta-SI-a sou EE-ne a-pe-ri-O-ri-sti"},
            {"english": "Art comes from the heart.", "greek": "Η τέχνη έρχεται από την καρδιά.", "pronunciation": "ee TEH-hni ER-he-te a-po tin kar-DIA"},
            {"english": "Express yourself freely.", "greek": "Εκφράσου ελεύθερα.", "pronunciation": "ek-FRA-sou e-LEF-the-ra"},
            {"english": "Innovation starts with curiosity.", "greek": "Η καινοτομία ξεκινά με την περιέργεια.", "pronunciation": "ee ke-no-to-MI-a kse-ki-NA me tin pe-ri-ER-yi-a"},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "greek": "Βρες γαλήνη μέσα σου.", "pronunciation": "vres ga-LI-ni ME-sa sou"},
            {"english": "Breathe, relax, let go.", "greek": "Ανάπνευσε, χαλάρωσε, άσε το.", "pronunciation": "a-NA-PNEF-se, ha-LA-ro-se, A-se to"},
            {"english": "Calm mind, happy heart.", "greek": "Ήρεμο μυαλό, χαρούμενη καρδιά.", "pronunciation": "EE-re-mo mya-LO, ha-ROU-me-ni kar-DIA"},
        ],
        "Confidence": [
            {"english": "You are enough, just as you are.", "greek": "Είσαι αρκετός, ακριβώς όπως είσαι.", "pronunciation": "EE-se ar-ke-TOS, a-kri-VOS O-pos EE-se"},
            {"english": "Stand tall, speak up.", "greek": "Στάσου ψηλά, μίλα δυνατά.", "pronunciation": "STA-sou psi-LA, MI-la di-na-TA"},
            {"english": "Believe in your abilities.", "greek": "Πίστεψε στις ικανότητές σου.", "pronunciation": "PEE-stepse stis i-ka-NO-ti-tes sou"},
        ],
        "Perseverance": [
            {"english": "Never give up, keep pushing.", "greek": "Μην τα παρατάς, συνέχισε να προσπαθείς.", "pronunciation": "min ta pa-ra-TAS, si-NE-hi-se na pro-spa-THIS"},
            {"english": "Storms make trees take deeper roots.", "greek": "Οι καταιγίδες κάνουν τα δέντρα να βγάζουν πιο βαθιές ρίζες.", "pronunciation": "ee ka-te-YI-des KA-noun ta DEN-dra na VGA-zoun pio va-THIES REE-zes"},
            {"english": "Patience and persistence win.", "greek": "Η υπομονή και η επιμονή νικούν.", "pronunciation": "ee i-po-mo-NI ke ee e-pi-mo-NI ni-KOUN"},
        ],
        "Inspiration": [
            {"english": "Let your light shine bright.", "greek": "Άσε το φως σου να λάμπει δυνατά.", "pronunciation": "A-se to fos sou na LAM-bi di-na-TA"},
            {"english": "Inspire others by your actions.", "greek": "Εμπνέετε τους άλλους με τις πράξεις σου.", "pronunciation": "em-BNE-e-te tous AL-lous me tis PRA-xeis sou"},
            {"english": "Be the change you want to see.", "greek": "Γίνε η αλλαγή που θέλεις να δεις.", "pronunciation": "YEE-ne ee a-la-YI pou THE-lis na dis"},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "greek": "Διάλεξε τη θετικότητα κάθε μέρα.", "pronunciation": "DIA-le-xe ti the-ti-KO-ti-ta KA-the ME-ra"},
            {"english": "Good vibes only.", "greek": "Μόνο θετική ενέργεια.", "pronunciation": "MO-no the-ti-KI e-NER-yi-a"},
            {"english": "Life is what you make it.", "greek": "Η ζωή είναι ό,τι την κάνεις.", "pronunciation": "ee zo-I EE-ne O-ti tin KA-nis"},
        ],
        "Courage": [
            {"english": "Be brave, take the first step.", "greek": "Να είσαι γενναίος, κάνε το πρώτο βήμα.", "pronunciation": "na EE-se ye-NE-os, KA-ne to PRO-to VI-ma"},
            {"english": "Courage is not the absence of fear.", "greek": "Θάρρος δεν είναι η απουσία φόβου.", "pronunciation": "THA-ros den EE-ne ee a-pou-SI-a FO-vou"},
            {"english": "Face your fears head on.", "greek": "Αντιμέτωπισε τους φόβους σου κατά μέτωπο.", "pronunciation": "an-di-ME-to-pi-se tous FO-vous sou KA-ta ME-to-po"},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "greek": "Να είσαι ευγενικός με όλους όσους συναντάς.", "pronunciation": "na EE-se ev-ye-ni-KOS me O-lous O-sous si-nan-TAS"},
            {"english": "Kindness costs nothing, means everything.", "greek": "Η καλοσύνη δεν κοστίζει τίποτα, σημαίνει τα πάντα.", "pronunciation": "ee ka-lo-SI-ni den ko-STI-zi TI-po-ta, si-ME-ni ta PAN-da"},
            {"english": "Spread kindness wherever you go.", "greek": "Διάδωσε καλοσύνη όπου κι αν πας.", "pronunciation": "DIA-do-se ka-lo-SI-ni O-pou ki an pas"},
        ],
        "Patience": [
            {"english": "Good things take time.", "greek": "Τα καλά πράγματα θέλουν χρόνο.", "pronunciation": "ta ka-LA PRA-gma-ta THE-loun HRO-no"},
            {"english": "Wait patiently, trust the process.", "greek": "Περίμενε υπομονετικά, εμπιστεύσου τη διαδικασία.", "pronunciation": "pe-RI-me-ne i-po-mo-ne-ti-KA, em-bi-STEF-sou ti di-a-di-ka-SI-a"},
            {"english": "Rome wasn't built in a day.", "greek": "Η Ρώμη δεν χτίστηκε σε μία μέρα.", "pronunciation": "ee RO-mi den HTI-sti-ke se MI-a ME-ra"},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "greek": "Συγχώρεσε και ελευθέρωσε τον εαυτό σου.", "pronunciation": "sing-HO-re-se ke e-lef-THE-ro-se ton eaf-TO sou"},
            {"english": "Let go of grudges, find peace.", "greek": "Άσε τις μνησικακίες, βρες γαλήνη.", "pronunciation": "A-se tis mni-si-ka-KI-es, vres ga-LI-ni"},
            {"english": "Forgiveness is a gift to yourself.", "greek": "Η συγχώρεση είναι δώρο στον εαυτό σου.", "pronunciation": "ee sing-HO-re-si EE-ne DO-ro ston eaf-TO sou"},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "greek": "Είσαι πιο δυνατός από ό,τι νομίζεις.", "pronunciation": "EE-se pio di-na-TOS a-po o-ti no-MI-zis"},
            {"english": "Inner strength comes from within.", "greek": "Η εσωτερική δύναμη έρχεται από μέσα σου.", "pronunciation": "ee e-so-te-ri-KI DEE-na-mi ER-he-te a-po ME-sa sou"},
            {"english": "Challenges make you stronger.", "greek": "Οι προκλήσεις σε κάνουν πιο δυνατό.", "pronunciation": "ee pro-KLI-sis se KA-noun pio di-na-TO"},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "greek": "Βρες χαρά σε κάθε στιγμή.", "pronunciation": "vres ha-RA se KA-the stig-MI"},
            {"english": "Joy is contagious, spread it.", "greek": "Η χαρά είναι μεταδοτική, διάδωσέ την.", "pronunciation": "ee ha-RA EE-ne me-ta-do-ti-KI, DI-a-do-se tin"},
            {"english": "Dance like nobody's watching.", "greek": "Χόρεψε σαν να μη σε βλέπει κανείς.", "pronunciation": "HO-rep-se san na mi se VLE-pi ka-NIS"},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "greek": "Βρες ισορροπία στη ζωή σου.", "pronunciation": "vres i-so-ro-PI-a sti zo-I sou"},
            {"english": "Work hard, rest well.", "greek": "Δούλεψε σκληρά, ξεκουράσου καλά.", "pronunciation": "DOU-lep-se skli-RA, kse-kou-RA-sou ka-LA"},
            {"english": "Too much of anything is not good.", "greek": "Το πολύ από κάτι δεν είναι καλό.", "pronunciation": "to po-LY a-po KA-ti den EE-ne ka-LO"},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "greek": "Η ανάπτυξη συμβαίνει έξω από τη ζώνη άνεσής σου.", "pronunciation": "ee a-NA-pty-xi sim-VE-ne E-xo a-po ti ZO-ni A-ne-sis sou"},
            {"english": "Embrace change, grow stronger.", "greek": "Αγκάλιασε την αλλαγή, γίνε πιο δυνατός.", "pronunciation": "an-GA-lia-se tin a-la-YI, YEE-ne pio di-na-TOS"},
            {"english": "Every challenge is a chance to grow.", "greek": "Κάθε πρόκληση είναι μια ευκαιρία να αναπτυχθείς.", "pronunciation": "KA-the PRO-kli-si EE-ne MI-a ef-ke-REE-a na a-na-pty-HIS"},
        ],
        "Purpose": [
            {"english": "Find your purpose, follow it.", "greek": "Βρες τον σκοπό σου, ακολούθησέ τον.", "pronunciation": "vres ton sko-PO sou, a-ko-LOU-thi-se ton"},
            {"english": "Your life has meaning.", "greek": "Η ζωή σου έχει νόημα.", "pronunciation": "ee zo-I sou E-hi NO-i-ma"},
            {"english": "Live with intention, not accident.", "greek": "Ζήσε με πρόθεση, όχι τυχαία.", "pronunciation": "ZEE-se me PRO-the-si, O-hi ti-HE-a"},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "greek": "Να είσαι παρών σε αυτή τη στιγμή.", "pronunciation": "na EE-se pa-RON se af-TI ti stig-MI"},
            {"english": "Breathe deeply, stay grounded.", "greek": "Ανάπνευσε βαθιά, μείνε προσγειωμένος.", "pronunciation": "a-NA-PNEF-se va-THIA, MI-ne pro-syi-o-ME-nos"},
            {"english": "Notice the little things around you.", "greek": "Παρατήρησε τα μικρά πράγματα γύρω σου.", "pronunciation": "pa-ra-TI-ri-se ta mi-KRA PRA-gma-ta YI-ro sou"},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    history = load_phrase_history()
    fresh_phrases = []
    for p in fallbacks:
        if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
            fresh_phrases.append(p)

    if len(fresh_phrases) < num_phrases:
        for cat, cat_fallbacks in all_fallbacks.items():
            if cat != category:
                for p in cat_fallbacks:
                    if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
                        fresh_phrases.append(p)
                    if len(fresh_phrases) >= num_phrases:
                        break
            if len(fresh_phrases) >= num_phrases:
                break

    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str, retries: int = 3):
    import edge_tts
    for attempt in range(retries):
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            if Path(output_path).exists() and Path(output_path).stat().st_size > 300:
                return True
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(0.8 * (attempt + 1))
            else:
                print(f"  TTS error after {retries} attempts: {e}")
    return False


def generate_all_audio(phrases: list, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        lang_file = output_dir / f"lang_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        if (i + 1) % 20 == 0:
            print(f"  Generating audio {i+1}/{len(phrases)}...")

        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if not en_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        lang_success = asyncio.run(generate_single_audio(phrase["greek"], LANG_VOICE, str(lang_file)))
        if not lang_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(lang_file)]
            subprocess.run(cmd, capture_output=True)

        en_duration = get_audio_duration(str(english_file))
        lang_duration = get_audio_duration(str(lang_file))

        pause_between = 0.5
        total_duration = en_duration + pause_between + lang_duration

        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(lang_file),
            "-filter_complex", f"[0:a]apad=pad_dur=0.5[a0];[a0][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{lang_file.as_posix()}'\n")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "lang": str(lang_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "lang_duration": lang_duration
        })

    print(f"\n[audio] Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")
    concat_file = Path(output_file).parent / "narration_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if concat_file.exists():
        concat_file.unlink()
    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True
    return False


# ============== BACKGROUND GENERATION ==============

def create_premium_background(category_english: str):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 255, 252, 245
        else:
            r = int(255 + (245 - 255) * ((ratio - 0.5) * 2))
            g = int(252 + (240 - 252) * ((ratio - 0.5) * 2))
            b = int(245 + (230 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Font paths - check fonts/ directory first
    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    lang_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()

    font_category = load_font(english_font_paths, 42)
    font_english = load_font(english_font_paths, 68)
    font_lang = load_font(lang_font_paths, 82)
    font_pronunciation = load_font(lang_font_paths, 48)
    font_branding = load_font(english_font_paths, 38)

    english = phrase_data.get("english", "")
    greek_text = phrase_data.get("greek", "")
    pronunciation = phrase_data.get("pronunciation", "")

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines

    # Header Bar
    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_category)
    cat_w = cat_bbox[2] - cat_bbox[0]
    badge_h = 75
    badge_pad_x = 40
    container_w = cat_w + (badge_pad_x * 2)
    container_x = 60
    container_y = 60
    draw.rounded_rectangle(
        [(container_x, container_y), (container_x + container_w, container_y + badge_h)],
        radius=15, fill=(45, 35, 65, 255)
    )
    draw.text(
        (container_x + container_w // 2, container_y + badge_h // 2 + 2),
        cat_text,
        fill=(255, 255, 255, 255),
        font=font_category,
        anchor="mm"
    )

    CONTENT_Y_CENTER = VIDEO_HEIGHT // 2
    GAP = 60

    en_lines = wrap_text(english, font_english, VIDEO_WIDTH - 300)
    en_line_h = 80
    en_total_h = len(en_lines) * en_line_h

    lang_lines = wrap_text(greek_text, font_lang, VIDEO_WIDTH - 300)
    lang_line_h = 100
    lang_total_h = len(lang_lines) * lang_line_h

    pron_text = f"[{pronunciation}]"
    pron_lines = wrap_text(pron_text, font_pronunciation, VIDEO_WIDTH - 400)
    pron_line_h = 60
    pron_total_h = len(pron_lines) * pron_line_h

    total_content_h = en_total_h + lang_total_h + pron_total_h + (GAP * 2)
    y_start = CONTENT_Y_CENTER - (total_content_h // 2)

    box_w = VIDEO_WIDTH - 200
    box_x = (VIDEO_WIDTH - box_w) // 2

    # English Box
    en_box_h = en_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_start), (box_x + box_w, y_start + en_box_h)],
        radius=25, fill=(65, 50, 95, 255)
    )
    for i, line in enumerate(en_lines):
        draw.text((VIDEO_WIDTH // 2, y_start + 30 + (i * en_line_h) + en_line_h // 2),
                  line, fill=(255, 255, 255), font=font_english, anchor="mm")

    y_cursor = y_start + en_box_h + GAP

    # Greek Section
    lang_box_h = lang_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_cursor), (box_x + box_w, y_cursor + lang_box_h)],
        radius=25, fill=(95, 80, 125, 255)
    )
    for i, line in enumerate(lang_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 30 + (i * lang_line_h) + lang_line_h // 2),
                  line, fill=(255, 255, 255), font=font_lang, anchor="mm")

    y_cursor += lang_box_h + (GAP // 2)

    # Pronunciation Section
    pron_box_h = pron_total_h + 40
    pron_box_w = box_w - 200
    pron_box_x = (VIDEO_WIDTH - pron_box_w) // 2
    draw.rounded_rectangle(
        [(pron_box_x, y_cursor), (pron_box_x + pron_box_w, y_cursor + pron_box_h)],
        radius=20, fill=(255, 210, 160, 255)
    )
    for i, line in enumerate(pron_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 20 + (i * pron_line_h) + pron_line_h // 2),
                  line, fill=(70, 45, 25), font=font_pronunciation, anchor="mm")

    # Branding
    brand_text = "VELOCITY GREEK"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=font_branding)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text((VIDEO_WIDTH - brand_w - 60, VIDEO_HEIGHT - 80), brand_text,
              fill=(45, 35, 65, 255), font=font_branding)

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


# ============== THUMBNAIL GENERATION ==============

def generate_thumbnail(category_english: str, category_greek: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available for thumbnail. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    lang_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try: return ImageFont.truetype(font_path, size)
            except: continue
        return ImageFont.load_default()

    font_huge = load_font(english_font_paths, 130)
    font_main = load_font(lang_font_paths, 110)
    font_sub = load_font(english_font_paths, 60)
    font_badge = load_font(english_font_paths, 45)

    draw.text((VIDEO_WIDTH // 2, 220), "MASTER GREEK", fill=(45, 35, 65), font=font_huge, anchor="mm")

    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_sub)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - cat_w // 2 - 40, 320), (VIDEO_WIDTH // 2 + cat_w // 2 + 40, 410)],
        radius=20, fill=(65, 50, 95, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 365), cat_text, fill=(255, 255, 255), font=font_sub, anchor="mm")

    draw.text((VIDEO_WIDTH // 2, 530), category_greek, fill=(45, 35, 65), font=font_main, anchor="mm")

    cta_text = "60 ΣΗΜΑΝΤΙΚΕΣ ΦΡΑΣΕΙΣ"
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - 300, 650), (VIDEO_WIDTH // 2 + 300, 730)],
        radius=15, fill=(255, 210, 160, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 690), cta_text, fill=(70, 45, 25), font=font_badge, anchor="mm")

    draw.rectangle([(0, VIDEO_HEIGHT - 100), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=(45, 35, 65, 255))
    draw.text((VIDEO_WIDTH // 2, VIDEO_HEIGHT - 50), "VELOCITY GREEK", fill=(255, 255, 255), font=font_badge, anchor="mm")

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


def extract_video_thumbnail(video_path: str, output_path: str, timestamp_seconds: int = 5):
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp_seconds),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and Path(output_path).exists():
            print(f"  Video thumbnail extracted: {Path(output_path).name}")
            return str(output_path)
        else:
            print(f"  Could not extract video thumbnail")
            return None
    except Exception as e:
        print(f"  Thumbnail extraction error: {e}")
        return None


# ============== TITLE & DESCRIPTION GENERATION ==============

def generate_title_description(category_english: str, category_greek: str, phrases: list, duration_minutes: float, output_dir: str):
    titles = [
        f"Learn Greek in 10 Minutes | {category_english} Phrases Every Beginner NEEDS to Know! ({category_greek})",
        f"60 Greek Phrases for {category_english} | Speak Greek Like a Native! ({category_greek})",
        f"Master Greek {category_english} | 60 Essential Greek Phrases with Pronunciation | Velocity Greek",
        f"Greek Learning Made Easy | {category_english} Vocabulary | 10 Minute Lesson",
        f"Speak Greek Fluently | {category_english} Phrases | English + Greek + Pronunciation",
    ]

    description = f"""\U0001F1EC\U0001F1F7 Learn Greek with Velocity Greek! \U0001F1EC\U0001F1F7

In this video, you'll learn 60 essential Greek phrases about {category_english} ({category_greek}).
Perfect for beginners and intermediate learners!

\U0001F4DA WHAT YOU'LL LEARN:
\u2022 60 practical {category_english} phrases in Greek
\u2022 Correct pronunciation guide
\u2022 Natural pauses for speaking practice
\u2022 Common expressions used by native speakers

\U0001F551 VIDEO TIMESTAMPS:
"""

    avg_phrase_duration = duration_minutes * 60 / len(phrases)
    for i in range(0, len(phrases), 10):
        timestamp = int(i * avg_phrase_duration / 60)
        minute = timestamp
        second = int((i * avg_phrase_duration) % 60)
        end_phrase = min(i + 10, len(phrases))
        description += f"{minute:02d}:{second:02d} Phrases {i+1}-{end_phrase}\n"

    description += """
\U0001F4DD ALL PHRASES IN THIS VIDEO:
"""

    for i, phrase in enumerate(phrases, 1):
        description += f"""
{i}. {phrase['english']}
   Greek: {phrase['greek']}
    Pronunciation: {phrase['pronunciation']}
"""

    description += """
\U0001F3AF PERFECT FOR:
\u2022 Greek beginners wanting to expand vocabulary
\u2022 Intermediate learners practicing pronunciation
\u2022 Anyone interested in Greek language and culture
\u2022 Language enthusiasts and polyglots
\u2022 Students preparing for exams

\U0001F4A1 TIPS FOR LEARNING:
1. Repeat each phrase out loud
2. Practice daily for best results
3. Use the pauses to speak along
4. Write down phrases you find difficult
5. Review this video multiple times

\U0001F514 SUBSCRIBE for more Greek learning content!
\U0001F44D LIKE this video if you found it helpful!
\U0001F4AC COMMENT which phrases you want to learn next!

\U0001F4F1 FOLLOW VELOCITY GREEK:
[Add your social media links here]

\U0001F3B5 MUSIC:
[Add music credits if applicable]

\U0001F4D6 RELATED VIDEOS:
\u2022 Greek Motivation Phrases
\u2022 Greek Love Expressions
\u2022 Basic Greek Greetings

#LearnGreek #GreekPhrases #GreekLanguage #{category_english.replace(' ', '')} #VelocityGreek #GreekForBeginners #SpeakGreek #GreekVocabulary #Pronunciation #LanguageLearning #Greek101 #GreekLesson

---
\u00A9 Velocity Greek - Making Greek learning accessible to everyone!
"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "youtube_upload_info.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("YOUTUBE VIDEO UPLOAD INFORMATION\n")
        f.write("=" * 80 + "\n\n")
        f.write("RECOMMENDED TITLES (Choose one):\n")
        f.write("-" * 80 + "\n")
        for i, title in enumerate(titles, 1):
            f.write(f"\n{i}. {title}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("SELECTED TITLE (Recommended):\n")
        f.write("-" * 80 + "\n")
        f.write(f"\n{titles[0]}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO DESCRIPTION:\n")
        f.write("-" * 80 + "\n\n")
        f.write(description)
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO TAGS (for YouTube):\n")
        f.write("-" * 80 + "\n")
        tags = [
            "Learn Greek",
            "Greek Phrases",
            "Greek Language",
            category_english,
            "Velocity Greek",
            "Greek for Beginners",
            "Speak Greek",
            "Greek Vocabulary",
            "Pronunciation",
            "Language Learning",
            "Greek 101",
            "Greek Lesson"
        ]
        f.write(", ".join(tags) + "\n")

    metadata = {
        "recommended_titles": titles,
        "selected_title": titles[0],
        "description": description,
        "category_english": category_english,
        "category_greek": category_greek,
        "phrases_count": len(phrases),
        "duration_minutes": round(duration_minutes, 2),
        "tags": tags
    }

    with open(output_dir / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[metadata] Generated YouTube upload files")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  video_metadata.json")

    return metadata


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    print(f"\n[video] Creating long-form video from {len(image_files)} images...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", audio_info['combined'],
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-shortest",
            "-vsync", "cfr",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    print("[video] Concatenating clips...")
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_file)]
    subprocess.run(cmd, check=True, capture_output=True)

    if concat_file.exists():
        concat_file.unlink()

    video_duration = get_audio_duration(str(output_file))
    print(f"[video] Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    for clip in temp_clips:
        if clip.exists():
            clip.unlink()


# ============== MAIN WORKFLOW ==============

def generate_longform_video(category_english: str = None, target_phrases: int = None):
    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)

    phrases_count = target_phrases if target_phrases else TARGET_PHRASES

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO - Category: {category_english} ({CATEGORIES_GREEK[category_english]})")
    print(f"Target Phrases: {phrases_count}")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_dir = LONGFORM_DIR / f"{category_english}_longform_{timestamp}"
    video_dir.mkdir(exist_ok=True)

    print(f"[1/6] Generating {phrases_count} unique phrases (checking history)...")
    phrases = generate_phrases_for_longform(category_english, phrases_count)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} -> {phrase['greek']}")

    print(f"\n[info] Total phrases: {len(phrases)}")

    print(f"\n[2/6] Generating {len(phrases)} images with premium backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = video_dir / f"phrase_{i:04d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(phrases)} images...")

    print(f"\n[3/6] Using first phrase image as thumbnail...")
    thumbnail_path = video_dir / "thumbnail.jpg"
    first_phrase = sorted(video_dir.glob("phrase_*.jpg"))
    if first_phrase:
        import shutil
        shutil.copy2(str(first_phrase[0]), str(thumbnail_path))
        print(f"  Thumbnail: {first_phrase[0].name} (content-based)")
    else:
        try:
            from generate_thumbnail import generate_scenic_image
            result = generate_scenic_image(category_english, category_english, str(thumbnail_path))
            if result and Path(result).exists():
                print(f"  gpt-image-2 thumbnail saved")
            else:
                print(f"  gpt-image-2 failed, using built-in")
                generate_thumbnail(category_english, CATEGORIES_GREEK[category_english], str(thumbnail_path))
        except Exception as e:
            print(f"  Thumbnail error: {e}, using built-in")
            generate_thumbnail(category_english, CATEGORIES_GREEK[category_english], str(thumbnail_path))
    video_thumbnail_path = video_dir / "video_thumbnail_frame.jpg"
    print(f"\n[4/6] Generating audio for {len(phrases)} phrases...")
    audio_files = generate_all_audio(phrases, str(video_dir))

    final_audio = video_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    total_duration = sum(a['duration'] for a in audio_files)
    print(f"\n[info] Total audio duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")

    print(f"\n[5/6] Creating long-form video with transitions...")
    output_video = video_dir / "final_video.mp4"

    image_files = sorted([str(p) for p in video_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    print(f"\n[5.5/6] Extracting video frame for thumbnail...")
    extract_video_thumbnail(str(output_video), str(video_thumbnail_path), timestamp_seconds=5)

    print(f"\n[6/6] Generating YouTube title, description, and metadata...")
    title_meta = generate_title_description(
        category_english,
        CATEGORIES_GREEK[category_english],
        phrases,
        total_duration / 60,
        str(video_dir)
    )

    import json as _json
    from pathlib import Path as _Path
    meta_out = {
        "title": title_meta.get("selected_title", f"Learn Greek: {category_english}"),
        "description": title_meta.get("description", ""),
        "tags": ["Learn Greek", "Greek Phrases", "Greek", category_english, "Velocity Greek"],
        "category_english": category_english,
        "category_greek": CATEGORIES_GREEK[category_english],
        "phrases_count": len(phrases),
        "duration_seconds": total_duration,
        "duration_minutes": total_duration / 60,
        "video_path": str(output_video),
        "thumbnail_path": str(thumbnail_path),
        "phrases": phrases,
        "generated_at": datetime.now().isoformat(),
    }
    _Path("output").mkdir(exist_ok=True)
    with open(_Path("output") / "latest_video.json", "w", encoding="utf-8") as f:
        _json.dump(meta_out, f, indent=2, ensure_ascii=False)
    with open(_Path("output") / "latest_upload_info.json", "w", encoding="utf-8") as f:
        _json.dump({"title": meta_out["title"], "description": meta_out["description"],
                     "category": category_english, "phrases_count": len(phrases)}, f, indent=2)

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO COMPLETE!")
    print(f"  {video_dir}")
    print(f"  {output_video.name}")
    print(f"  thumbnail.jpg (generated)")
    print(f"  {video_thumbnail_path.name} (from video)")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  Duration: {total_duration/60:.2f} minutes")
    print(f"  Phrases: {len(phrases)}")
    print(f"  Branding: Velocity Greek")
    print(f"  Format: 16:9 (1920x1080)")
    print(f"{'='*80}\n")

    return meta_out


def generate_multiple_longform(count: int = 1, target_phrases: int = None):
    print(f"\nGenerating {count} long-form video(s)...")
    print("="*80)
    for i in range(count):
        print(f"\n{'='*80}")
        print(f"VIDEO {i+1}/{count}")
        print("="*80)
        generate_longform_video(target_phrases=target_phrases)
    print("\n" + "="*80)
    print(f"ALL {count} LONG-FORM VIDEOS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Velocity Greek YouTube Long-form Video Generator")
    parser.add_argument("--phrases", type=int, default=TARGET_PHRASES, help="Number of phrases to generate")
    parser.add_argument("--category", type=str, default=None, help="Specific category to generate")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("VELOCITY GREEK - YOUTUBE LONG-FORM AUTOMATION")
    print("="*80)
    print("\nFEATURES:")
    print("  16:9 format (1920x1080) for YouTube long-form")
    print(f"  Target {args.phrases} phrases (~{args.phrases * 5.5 / 60:.1f} minute video)")
    print("  Light Theme (Cream background, dark/light purple + peach containers)")
    print("  Natural pauses with commas (non-robotic TTS)")
    print("  Perfect audio-video synchronization")
    print("  NEVER repeats phrases (permanent history tracking)")
    print(f"\nAVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_GREEK[cat]})")
    print(f"\nVIDEO SPECIFICATIONS:")
    print(f"  Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} (16:9)")
    print(f"  Frame Rate: {FPS} FPS")
    print(f"  Target Phrases: {args.phrases}")
    print(f"  Estimated Duration: ~{args.phrases * 5.5 / 60:.1f} minutes")
    print(f"  Phrase History: PERMANENT (never deletes)")
    print("="*80)

    generate_longform_video(category_english=args.category, target_phrases=args.phrases)