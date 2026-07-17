import os
from flask import Flask, request
import requests
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# =============================================
# CONFIGURATION (env vars for Railway deploy)
# =============================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "educatia123")
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "learnateducatiadso@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_APP_PASSWORD", "")
MAAM_PHONE_NUMBER = "971504605940"
MAAM_EMAIL = "info@learnateducatia.com"

if not ACCESS_TOKEN:
    logger.warning("⚠️  WHATSAPP_ACCESS_TOKEN not set! Bot won't be able to send messages.")
if not PHONE_NUMBER_ID:
    logger.warning("⚠️  WHATSAPP_PHONE_NUMBER_ID not set! Bot won't be able to send messages.")
if not SMTP_PASSWORD:
    logger.warning("⚠️  SMTP_APP_PASSWORD not set! Bot won't be able to send notification emails.")

API_URL = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

# =============================================
# SESSION & NOTIFICATION TRACKING
# =============================================

user_sessions = {}
notified_users = set()


def get_session(phone):
    return user_sessions.get(phone, {"step": "new"})


def set_session(phone, data):
    user_sessions[phone] = data


# =============================================
# NOTIFICATION FUNCTIONS
# =============================================

def notify_maam_new_contact(user_phone):
    """Sends a WhatsApp notification to Ma'am about a new contact."""
    msg = f"🔔 *New Contact Alert!*\n\nA new user has just contacted the Educatia Bot.\nUser's Phone Number: *+{user_phone}*"
    
    # Send WhatsApp Notification
    try:
        send_text(MAAM_PHONE_NUMBER, msg)
        logger.info(f"WhatsApp notification sent to {MAAM_PHONE_NUMBER} for new user {user_phone}")
    except BaseException as e:
        logger.error(f"Failed to send WhatsApp notification: {e}")

    # Note: Email notification via smtplib is disabled because Railway blocks outbound SMTP
    # (ports 25, 465, 587) which causes the process to crash with SystemExit.

# =============================================
# WHATSAPP API — SEND FUNCTIONS
# =============================================

def send_text(to, text):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=data, timeout=10)
        logger.info(f"Text to {to}: {resp.status_code}")
        return resp.json()
    except Exception as e:
        logger.error(f"send_text error: {e}")
        return {}


def send_list(to, body, button_text, sections, header=None, footer=None):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    interactive = {
        "type": "list",
        "body": {"text": body},
        "action": {"button": button_text, "sections": sections},
    }
    if header:
        interactive["header"] = {"type": "text", "text": header}
    if footer:
        interactive["footer"] = {"text": footer}

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": interactive,
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=data, timeout=10)
        logger.info(f"List to {to}: {resp.status_code}")
        return resp.json()
    except Exception as e:
        logger.error(f"send_list error: {e}")
        return {}


def send_buttons(to, body, buttons, header=None, footer=None):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    btn_objects = [
        {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
        for b in buttons
    ]
    interactive = {
        "type": "button",
        "body": {"text": body},
        "action": {"buttons": btn_objects},
    }
    if header:
        interactive["header"] = {"type": "text", "text": header}
    if footer:
        interactive["footer"] = {"text": footer}

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": interactive,
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=data, timeout=10)
        logger.info(f"Buttons to {to}: {resp.status_code}")
        return resp.json()
    except Exception as e:
        logger.error(f"send_buttons error: {e}")
        return {}


# =============================================
# FLOW: MAIN MENU
# =============================================

GREETINGS = [
    "hi", "hello", "hey", "start", "menu", "hii", "helo",
    "salam", "assalam", "assalamualaikum", "main menu",
    "home", "restart",
]


def show_main_menu(to):
    set_session(to, {"step": "main_menu"})
    sections = [
        {
            "title": "How can we help?",
            "rows": [
                {"id": "cat_acadsupport", "title": "Academic Support", "description": "All curriculums & subjects"},
                {"id": "cat_childskill", "title": "Child Skill Development", "description": "Abacus, Coding, Robotics"},
                {"id": "cat_language", "title": "Language Training", "description": "English, Arabic, Hindi, French"},
                {"id": "cat_adult", "title": "Courses for Adults", "description": "Professional courses"},
                {"id": "cat_daycare", "title": "Day Care", "description": "DSO branch — Mon to Fri"},
                {"id": "cat_branches", "title": "Branch Info & Timings", "description": "Our 3 Dubai locations"},
                {"id": "cat_admission", "title": "Admission Process", "description": "How to register"},
                {"id": "cat_team", "title": "Talk to Our Team", "description": "Speak to staff directly"},
            ],
        }
    ]
    send_list(
        to,
        body=(
            "👋 *Welcome to Learn At Educatia!* 🎓\n\n"
            "We offer world-class courses for children & adults "
            "across our three Dubai branches + online.\n\n"
            "Tap below or reply with a number:\n\n"
            "1️⃣ Academic Support\n"
            "2️⃣ Child Skill Development\n"
            "3️⃣ Language Training\n"
            "4️⃣ Courses for Adults\n"
            "5️⃣ Day Care\n"
            "6️⃣ Branch Info & Timings\n"
            "7️⃣ Admission Process\n"
            "8️⃣ Talk to Our Team"
        ),
        button_text="View Options",
        sections=sections,
        footer="Reply 'menu' anytime to return here",
    )


# =============================================
# FLOW: BRANCH SELECTION
# =============================================

def show_branch_list(to, category):
    """4-option branch picker (Academic / Adult — includes Online)."""
    set_session(to, {"step": "select_branch", "category": category})

    if category == "academic_support":
        label = "📚 *Academic Support*"
    elif category == "child_skill":
        label = "🔬 *Child Skill Development*"
    elif category == "language":
        label = "🗣 *Language Training*"
    elif category in ("academic",):
        label = "📚 *Academic Classes for Children*"
    else:
        label = "👨‍💼 *Courses for Adults*"

    body = (
        f"{label}\n\n"
        "We offer courses at multiple locations.\n"
        "Tap below or reply with a number:\n\n"
        "1️⃣ International City\n"
        "2️⃣ Dubai Silicon Oasis\n"
        "3️⃣ Al Jadaf\n"
        "4️⃣ Online Classes"
    )

    sections = [
        {
            "title": "Select Location",
            "rows": [
                {"id": "branch_ic", "title": "International City", "description": "V17, Russia Cluster"},
                {"id": "branch_dso", "title": "Dubai Silicon Oasis", "description": "Park Avenue 607"},
                {"id": "branch_jadaf", "title": "Al Jadaf", "description": "Nastaran Building, Office 503"},
                {"id": "branch_online", "title": "Online Classes", "description": "Learn from anywhere"},
            ],
        }
    ]
    send_list(to, body, "Choose Location", sections)


# =============================================
# FLOW: ACADEMIC CLASSES (Children) per branch
# =============================================

# ── Academic Support (all curriculums & subjects) ──
ACADEMIC_SUPPORT_COURSES = {
    "ic": [
        {"id": "as_lang", "title": "Languages", "description": "Arabic/French/Hindi/English"},
        {"id": "as_math", "title": "Insight in Mathematics", "description": "Beginner/Inter/Adv"},
        {"id": "as_science", "title": "Insight in Science", "description": "Phy/Chem/Bio"},
        {"id": "as_commerce", "title": "Commerce and Accounting", "description": "Accounts/BST/Eco"},
    ],
    "dso": [
        {"id": "as_lang", "title": "Languages", "description": "Arabic/French/Hindi/English"},
        {"id": "as_math", "title": "Mathematics", "description": "Beginner / Inter / Advanced"},
        {"id": "as_science", "title": "Science", "description": "Physics / Chemistry / Biology"},
        {"id": "as_commerce", "title": "Commerce & Accounting", "description": "Accounts/BST/Economics"},
    ],
    "jadaf": [
        {"id": "as_lang", "title": "Languages", "description": "Arabic/French/Hindi/English"},
        {"id": "as_math", "title": "Mathematics", "description": "Beginner / Inter / Advanced"},
        {"id": "as_science", "title": "Science", "description": "Physics / Chemistry / Biology"},
        {"id": "as_commerce", "title": "Commerce & Accounting", "description": "Accounts/BST/Economics"},
    ],
    "online": [
        {"id": "as_lang", "title": "Languages", "description": "Arabic/French/Hindi/English"},
        {"id": "as_math", "title": "Mathematics", "description": "Beginner / Inter / Advanced"},
        {"id": "as_science", "title": "Science", "description": "Physics / Chemistry / Biology"},
        {"id": "as_commerce", "title": "Commerce & Accounting", "description": "Accounts/BST/Economics"},
    ],
}

# ── Child Skill Development ──
CHILD_SKILL_COURSES = {
    "ic": [
        {"id": "cs_abacus", "title": "Abacus", "description": "Ages 6-10, mental arithmetic"},
        {"id": "cs_vedic", "title": "Vedic Maths", "description": "Ages 8-16, fast calculations"},
        {"id": "cs_coding", "title": "Coding for Kids", "description": "Scratch/Python/App development"},
        {"id": "cs_robotics", "title": "Robotics", "description": "Beginner/Inter/Adv"},
        {"id": "cs_handwriting", "title": "Handwriting is beautiful", "description": "Writing skills"},
        {"id": "cs_creative", "title": "Creative skills", "description": "Art & Craft sessions"},
        {"id": "cs_science_exp", "title": "Live science experiments", "description": "Ages 10+"},
        {"id": "cs_msoffice", "title": "MS Office", "description": "Beginner/Inter"},
    ],
    "dso": [
        {"id": "cs_abacus", "title": "Abacus", "description": "Ages 6-10, mental arithmetic"},
        {"id": "cs_vedic", "title": "Vedic Maths", "description": "Ages 8-16, fast calculations"},
        {"id": "cs_coding", "title": "Coding for Kids", "description": "Scratch/Python/App development"},
        {"id": "cs_robotics", "title": "Robotics", "description": "Beginner/Inter/Adv"},
        {"id": "cs_handwriting", "title": "Handwriting is beautiful", "description": "Writing skills"},
        {"id": "cs_creative", "title": "Creative skills", "description": "Art & Craft sessions"},
        {"id": "cs_science_exp", "title": "Live science experiments", "description": "Ages 10+"},
        {"id": "cs_msoffice", "title": "MS Office", "description": "Beginner/Inter"},
    ],
    "jadaf": [
        {"id": "cs_abacus", "title": "Abacus", "description": "Ages 6-10, mental arithmetic"},
        {"id": "cs_vedic", "title": "Vedic Maths", "description": "Ages 8-16, fast calculations"},
        {"id": "cs_coding", "title": "Coding for Kids", "description": "Scratch/Python/App development"},
        {"id": "cs_robotics", "title": "Robotics", "description": "Beginner/Inter/Adv"},
        {"id": "cs_handwriting", "title": "Handwriting is beautiful", "description": "Writing skills"},
        {"id": "cs_creative", "title": "Creative skills", "description": "Art & Craft sessions"},
        {"id": "cs_science_exp", "title": "Live science experiments", "description": "Ages 10+"},
        {"id": "cs_msoffice", "title": "MS Office", "description": "Beginner/Inter"},
    ],
    "online": [
        {"id": "cs_abacus", "title": "Abacus", "description": "Ages 6-10, mental arithmetic"},
        {"id": "cs_vedic", "title": "Vedic Maths", "description": "Ages 8-16, fast calculations"},
        {"id": "cs_coding", "title": "Coding for Kids", "description": "Scratch/Python/App development"},
        {"id": "cs_robotics", "title": "Robotics", "description": "Beginner/Inter/Adv"},
        {"id": "cs_handwriting", "title": "Handwriting is beautiful", "description": "Writing skills"},
        {"id": "cs_creative", "title": "Creative skills", "description": "Art & Craft sessions"},
        {"id": "cs_science_exp", "title": "Live science experiments", "description": "Ages 10+"},
        {"id": "cs_msoffice", "title": "MS Office", "description": "Beginner/Inter"},
    ],
}

# ── Language Training ──
LANGUAGE_COURSES = {
    "ic": [
        {"id": "lt_eng_beg", "title": "English communication", "description": "Beginner/Inter level"},
        {"id": "lt_phonics", "title": "Phonics classes", "description": "Ages 5+, 36 hrs/level"},
        {"id": "lt_pubspeak", "title": "Public speaking", "description": "& Creative writing"},
        {"id": "lt_arabic_rw", "title": "Arabic reading & writing", "description": "Ages 6+"},
        {"id": "lt_hindi_rw", "title": "Hindi reading & writing", "description": "Ages 6+"},
        {"id": "lt_french_rw", "title": "French reading & writing", "description": "Ages 6+"},
    ],
    "dso": [
        {"id": "lt_eng_beg", "title": "English communication", "description": "Beginner/Inter level"},
        {"id": "lt_phonics", "title": "Phonics classes", "description": "Ages 5+, 36 hrs/level"},
        {"id": "lt_pubspeak", "title": "Public speaking", "description": "& Creative writing"},
        {"id": "lt_arabic_rw", "title": "Arabic reading & writing", "description": "Ages 6+"},
        {"id": "lt_hindi_rw", "title": "Hindi reading & writing", "description": "Ages 6+"},
        {"id": "lt_french_rw", "title": "French reading & writing", "description": "Ages 6+"},
    ],
    "jadaf": [
        {"id": "lt_eng_beg", "title": "English communication", "description": "Beginner/Inter level"},
        {"id": "lt_phonics", "title": "Phonics classes", "description": "Ages 5+, 36 hrs/level"},
        {"id": "lt_pubspeak", "title": "Public speaking", "description": "& Creative writing"},
        {"id": "lt_arabic_rw", "title": "Arabic reading & writing", "description": "Ages 6+"},
        {"id": "lt_hindi_rw", "title": "Hindi reading & writing", "description": "Ages 6+"},
        {"id": "lt_french_rw", "title": "French reading & writing", "description": "Ages 6+"},
    ],
    "online": [
        {"id": "lt_eng_beg", "title": "English communication", "description": "Beginner/Inter level"},
        {"id": "lt_phonics", "title": "Phonics classes", "description": "Ages 5+, 36 hrs/level"},
        {"id": "lt_pubspeak", "title": "Public speaking", "description": "& Creative writing"},
        {"id": "lt_arabic_rw", "title": "Arabic reading & writing", "description": "Ages 6+"},
        {"id": "lt_hindi_rw", "title": "Hindi reading & writing", "description": "Ages 6+"},
        {"id": "lt_french_rw", "title": "French reading & writing", "description": "Ages 6+"},
    ],
}

BRANCH_NAMES = {
    "ic": "International City",
    "dso": "Dubai Silicon Oasis",
    "jadaf": "Al Jadaf",
    "online": "Online",
}


def show_category_courses(to, branch, category):
    """Show courses list for a given category and branch."""
    COURSE_MAP = {
        "academic_support": (ACADEMIC_SUPPORT_COURSES, "📖 *Academic Support"),
        "child_skill": (CHILD_SKILL_COURSES, "🔬 *Child Skill Development"),
        "language": (LANGUAGE_COURSES, "🗣 *Language Training"),
    }
    course_dict, label_prefix = COURSE_MAP.get(category, (ACADEMIC_SUPPORT_COURSES, "📚 *Courses"))
    set_session(to, {"step": "select_course", "category": category, "branch": branch})
    courses = course_dict.get(branch, [])
    if not courses:
        send_text(to, "Sorry, no courses found for this branch. Reply *menu* to go back 🔙")
        return
    bname = BRANCH_NAMES.get(branch, branch)
    numbered = "\n".join(f"{i+1}. {c['title']}" for i, c in enumerate(courses))
    sections = [{"title": "Available Courses", "rows": courses}]
    send_list(
        to,
        body=(
            f"{label_prefix} — {bname}*\n\n"
            "Tap below or reply with the course number:\n\n"
            f"{numbered}"
        ),
        button_text="View Courses",
        sections=sections,
        footer="Reply 'menu' for main menu",
    )


def show_academic_courses(to, branch):
    show_category_courses(to, branch, "academic_support")


# =============================================
# FLOW: ADULT CLASSES per branch
# =============================================

ADULT_COURSES = {
    "ic": [
        {"id": "a_eng_basic", "title": "English Comm Beg/Elem", "description": "Beginner/Elementary"},
        {"id": "a_eng_adv", "title": "English Comm Inter+", "description": "PreInter/Inter/Upper/Advanced"},
        {"id": "a_arabic", "title": "Spoken Arabic", "description": "Beginner/Inter/Advanced"},
        {"id": "a_ielts", "title": "IELTS Academic/General", "description": "Exam preparation"},
        {"id": "a_excel", "title": "Excel Skills for Adults", "description": "For Adults"},
        {"id": "a_python", "title": "Python Coding Language", "description": "Programming for adults"},
        {"id": "a_grw", "title": "Get Ready To Work", "description": "MS Office + AI training"},
    ],
    "dso": [
        {"id": "a_eng_basic", "title": "English Comm Beg/Elem", "description": "Beginner/Elementary"},
        {"id": "a_eng_adv", "title": "English Comm Inter+", "description": "PreInter/Inter/Upper/Advanced"},
        {"id": "a_arabic", "title": "Spoken Arabic", "description": "Beginner/Inter/Advanced"},
        {"id": "a_ielts", "title": "IELTS Academic/General", "description": "Exam preparation"},
        {"id": "a_excel", "title": "Excel Skills for Adults", "description": "For Adults"},
        {"id": "a_python", "title": "Python Coding Language", "description": "Programming for adults"},
        {"id": "a_grw", "title": "Get Ready To Work", "description": "MS Office + AI training"},
    ],
    "jadaf": [
        {"id": "a_eng_basic", "title": "English Comm Beg/Elem", "description": "Beginner/Elementary"},
        {"id": "a_eng_adv", "title": "English Comm Inter+", "description": "PreInter/Inter/Upper/Advanced"},
        {"id": "a_arabic", "title": "Spoken Arabic", "description": "Beginner/Inter/Advanced"},
        {"id": "a_ielts", "title": "IELTS Academic/General", "description": "Exam preparation"},
        {"id": "a_excel", "title": "Excel Skills for Adults", "description": "For Adults"},
        {"id": "a_python", "title": "Python Coding Language", "description": "Programming for adults"},
        {"id": "a_grw", "title": "Get Ready To Work", "description": "MS Office + AI training"},
    ],
    "online": [
        {"id": "a_eng_basic", "title": "English Comm Beg/Elem", "description": "Beginner/Elementary"},
        {"id": "a_eng_adv", "title": "English Comm Inter+", "description": "PreInter/Inter/Upper/Advanced"},
        {"id": "a_arabic", "title": "Spoken Arabic", "description": "Beginner/Inter/Advanced"},
        {"id": "a_ielts", "title": "IELTS Academic/General", "description": "Exam preparation"},
        {"id": "a_excel", "title": "Excel Skills for Adults", "description": "For Adults"},
        {"id": "a_python", "title": "Python Coding Language", "description": "Programming for adults"},
        {"id": "a_grw", "title": "Get Ready To Work", "description": "MS Office + AI training"},
    ],
}


def show_adult_courses(to, branch):
    set_session(to, {"step": "select_course", "category": "adult", "branch": branch})
    courses = ADULT_COURSES.get(branch, [])
    if not courses:
        send_text(to, "Sorry, no adult courses found for this branch. Reply *menu* to go back 🔙")
        return

    bname = BRANCH_NAMES.get(branch, branch)
    # Build numbered text for body
    numbered = "\n".join(
        f"{i+1}. {c['title']}" for i, c in enumerate(courses)
    )
    sections = [{"title": "Available Courses", "rows": courses}]
    send_list(
        to,
        body=(
            f"👨‍💼 *Adult Courses — {bname}*\n\n"
            "Tap below or reply with the course number:\n\n"
            f"{numbered}\n\n"
            "📝 *Detailed pricing available for English & Arabic courses.*"
        ),
        button_text="View Courses",
        sections=sections,
        footer="Reply 'menu' for main menu",
    )


# =============================================
# FLOW: COURSE DETAIL (English & Arabic with
#       full pricing, others → contact team)
# =============================================

def show_course_detail(to, course_id, branch, category):
    set_session(to, {"step": "viewing", "category": category, "branch": branch, "course": course_id})
    bname = BRANCH_NAMES.get(branch, branch)

    # --- ENGLISH / COMMUNICATION SKILLS ---
    if course_id in ("c_comms", "a_comms"):
        if branch == "ic":
            text = (
                "🌟 *ENGLISH COURSES — International City* 🌟\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📗 *BEGINNER ENGLISH*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📚 Grammar | Vocabulary | Spoken English | Writing Skills\n"
                "📅 Total Sessions: 36\n"
                "⏱️ Duration: 1 Hour per Session\n"
                "💰 Fees: AED 1,220 + VAT (Incl. Registration & Book)\n"
                "📍 International City\n\n"
                "✨ Learn. Speak. Grow with Confidence.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📘 *INTERMEDIATE ENGLISH*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📚 Grammar | Vocabulary | Spoken English | Writing | Listening\n"
                "📅 Total Sessions: 24\n"
                "⏱️ Duration: 1 Hour per Session\n"
                "💰 Fees: AED 1,220 + VAT (Incl. Registration & Book)\n"
                "📍 International City\n\n"
                "🚀 Boost your English fluency with confidence!\n\n"
                "📞 Contact: +971 50 460 5940\n"
                "Reply *menu* to go back 🔙"
            )
        elif branch == "dso":
            text = (
                "🌟 *ENGLISH COURSES — Dubai Silicon Oasis* 🌟\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📗 *BEGINNER ENGLISH*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📚 Grammar | Vocabulary | Spoken English | Writing Skills\n"
                "📅 Total Sessions: 36\n"
                "⏱️ Duration: 1 Hour per Session\n"
                "💰 Fees: AED 1,470 + VAT (Incl. Registration & Book)\n"
                "📍 Dubai Silicon Oasis\n\n"
                "✨ Learn. Speak. Grow with Confidence.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📘 *INTERMEDIATE ENGLISH*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📚 Grammar | Vocabulary | Spoken English | Writing | Listening\n"
                "📅 Total Sessions: 24\n"
                "⏱️ Duration: 1 Hour per Session\n"
                "💰 Fees: AED 1,470 + VAT (Incl. Registration & Book)\n"
                "📍 Dubai Silicon Oasis\n\n"
                "🚀 Boost your English fluency with confidence!\n\n"
                "📞 Contact: +971 50 460 5940\n"
                "Reply *menu* to go back 🔙"
            )
        else:
            text = (
                f"🌟 *Communication Skills / English — {bname}* 🌟\n\n"
                "We offer Communication Skills courses at this location.\n\n"
                "📞 Contact us for detailed pricing & schedule:\n"
                "*+971 50 460 5940*\n\n"
                "Reply *menu* to go back 🔙"
            )
        send_text(to, text)
        return

    # --- ARABIC ---
    if course_id in ("c_arabic", "a_arabic"):
        if branch == "ic":
            text = (
                "🌟 *ARABIC COURSES — International City* 🌟\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📗 *BEGINNER ARABIC*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📚 Arabic Basics | Grammar | Speaking Skills\n"
                "📅 Total Sessions: 20\n"
                "⏱️ Duration: 1 Hour per Session\n"
                "💰 Fees: AED 1,220 + VAT (Incl. Registration & Book)\n"
                "📍 International City\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📘 *INTERMEDIATE ARABIC*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📚 Arabic Grammar | Speaking | Listening | Reading Skills\n"
                "📅 Total Sessions: 20\n"
                "⏱️ Duration: 1 Hour per Session\n"
                "💰 Fees: AED 1,420 + VAT (Incl. Registration & Book)\n"
                "📍 International City\n\n"
                "🚀 Learn Arabic and start speaking with confidence!\n\n"
                "📞 Contact: +971 50 460 5940\n"
                "Reply *menu* to go back 🔙"
            )
        elif branch == "dso":
            text = (
                "🌟 *ARABIC COURSE — Dubai Silicon Oasis* 🌟\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📗 *BEGINNER ARABIC*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📚 Arabic Basics | Grammar | Speaking Skills\n"
                "📅 Total Sessions: 20\n"
                "⏱️ Duration: 1 Hour per Session\n"
                "💰 Fees: AED 1,270 + VAT (Incl. Registration & Book)\n"
                "📍 Dubai Silicon Oasis\n\n"
                "🚀 Learn Arabic and start speaking with confidence!\n\n"
                "📞 Contact: +971 50 460 5940\n"
                "Reply *menu* to go back 🔙"
            )
        elif branch == "online":
            text = (
                "🌟 *ARABIC COURSE — Online* 🌟\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📗 *BEGINNER ARABIC*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📚 Arabic Basics | Grammar | Speaking Skills\n"
                "📅 Total Sessions: 20\n"
                "⏱️ Duration: 1 Hour per Session\n"
                "💰 Fees: AED 1,220 + VAT (Incl. Registration & Book)\n\n"
                "🚀 Learn Arabic from basics and start speaking with confidence!\n\n"
                "📞 Contact: +971 50 460 5940\n"
                "Reply *menu* to go back 🔙"
            )
        else:
            text = (
                f"🌟 *Arabic — {bname}* 🌟\n\n"
                "We offer Arabic courses at this location.\n\n"
                "📞 Contact us for detailed pricing & schedule:\n"
                "*+971 50 460 5940*\n\n"
                "Reply *menu* to go back 🔙"
            )
        send_text(to, text)
        return

    if course_id == "as_lang" and branch == "ic":
        text = (
            "📚 *Academic Support — Languages*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "We offer academic support in Arabic, French, Hindi & English "
            "for all curriculums: CBSE / ICSE / GCSE / IGCSE / AS & A Levels / IB / American\n\n"
            "💰 *Fees:*\n"
            "• Up to Grade/Year 7: AED 350–400 + VAT/month (twice a week)\n"
            "• Grade/Year 8 & above: Yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "as_lang" and branch == "dso":
        text = (
            "📚 *Academic Support — Languages*\n"
            "📍 Dubai Silicon Oasis\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "We offer academic support in Arabic, French, Hindi & English "
            "for all curriculums: CBSE / ICSE / GCSE / IGCSE / AS & A Levels / IB / American\n\n"
            "💰 *Fees:*\n"
            "• Up to Grade/Year 7: AED 400 + VAT/month (twice a week)\n"
            "• Grade/Year 8 & above: Yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "as_lang" and branch == "jadaf":
        text = (
            "📚 *Academic Support — Languages*\n"
            "📍 Al Jadaf\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "We offer academic support in Arabic, French, Hindi & English "
            "for all curriculums: CBSE / ICSE / GCSE / IGCSE / AS & A Levels / IB / American\n\n"
            "💰 *Fees:*\n"
            "• Up to Grade/Year 7: AED 350–400 + VAT/month (twice a week)\n"
            "• Grade/Year 8 & above: Yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "as_lang" and branch == "online":
        text = (
            "📚 *Academic Support — Languages*\n"
            "🌐 Online Classes\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "We offer academic support in Arabic, French, Hindi & English "
            "for all curriculums: CBSE / ICSE / GCSE / IGCSE / AS & A Levels / IB / American\n\n"
            "💰 *Fees:*\n"
            "• Up to Grade/Year 7: AED 400 + VAT/month (twice a week)\n"
            "• Grade/Year 8 & above: Yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "as_math" and branch == "ic":
        text = (
            "📐 *Academic Support — Insight in Mathematics*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Insight in Mathematics (Beginner/Inter/Adv)\n\n"
            "Our Insight in Mathematics classes help students stay on track with their school curriculum, "
            "strengthen key concepts and improve academic performance.\n\n"
            "💰 *Fees:*\n"
            "• Up to Grade/Year 7: AED 350–400 + VAT/month (twice a week)\n"
            "• Grade/Year 8 & above: Yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "as_math" and branch == "dso":
        text = (
            "📐 *Academic Support — Insight in Mathematics*\n"
            "📍 Dubai Silicon Oasis\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Insight in Mathematics (Beginner/Inter/Adv)\n\n"
            "Our Insight in Mathematics classes help students stay on track with their school curriculum, "
            "strengthen key concepts and improve academic performance.\n\n"
            "💰 *Fees:*\n"
            "• Up to Grade/Year 7: AED 400 + VAT/month (twice a week)\n"
            "• Grade/Year 8 & above: Yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "as_math" and branch == "jadaf":
        text = (
            "📐 *Academic Support — Insight in Mathematics*\n"
            "📍 Al Jadaf\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Insight in Mathematics (Beginner/Inter/Adv)\n\n"
            "Our Insight in Mathematics classes help students stay on track with their school curriculum, "
            "strengthen key concepts and improve academic performance.\n\n"
            "💰 *Fees:*\n"
            "• Up to Grade/Year 7: AED 350–400 + VAT/month (twice a week)\n"
            "• Grade/Year 8 & above: Yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "as_math" and branch == "online":
        text = (
            "📐 *Academic Support — Insight in Mathematics*\n"
            "🌐 Online Classes\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Insight in Mathematics (Beginner/Inter/Adv)\n\n"
            "Our Insight in Mathematics classes help students stay on track with their school curriculum, "
            "strengthen key concepts and improve academic performance.\n\n"
            "💰 *Fees:*\n"
            "• Up to Grade/Year 7: AED 400 + VAT/month (twice a week)\n"
            "• Grade/Year 8 & above: Yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "as_science" and branch == "ic":
        text = (
            "🔬 *Academic Support — Insight in Science*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Insight in Science (Phy/Chem/Bio)\n\n"
            "Our Insight in Science classes help students stay on track with their school curriculum, "
            "strengthen key concepts and improve academic performance.\n\n"
            "💰 *Fees:*\n"
            "• Up to Grade/Year 7: AED 350–400 + VAT/month (twice a week)\n"
            "• Grade/Year 8 & above: Yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "as_science" and branch == "dso":
        text = (
            "🔬 *Academic Support — Insight in Science*\n"
            "📍 Dubai Silicon Oasis\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Insight in Science (Phy/Chem/Bio)\n\n"
            "Our Insight in Science classes help students stay on track with their school curriculum, "
            "strengthen key concepts and improve academic performance.\n\n"
            "💰 *Fees:*\n"
            "• Up to Grade/Year 7: AED 400 + VAT/month (twice a week)\n"
            "• Grade/Year 8 & above: Yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "as_science" and branch == "jadaf":
        text = (
            "🔬 *Academic Support — Insight in Science*\n"
            "📍 Al Jadaf\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Insight in Science (Phy/Chem/Bio)\n\n"
            "Our Insight in Science classes help students stay on track with their school curriculum, "
            "strengthen key concepts and improve academic performance.\n\n"
            "💰 *Fees:*\n"
            "• Up to Grade/Year 7: AED 350–400 + VAT/month (twice a week)\n"
            "• Grade/Year 8 & above: Yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "as_science" and branch == "online":
        text = (
            "🔬 *Academic Support — Insight in Science*\n"
            "🌐 Online Classes\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Insight in Science (Phy/Chem/Bio)\n\n"
            "Our Insight in Science classes help students stay on track with their school curriculum, "
            "strengthen key concepts and improve academic performance.\n\n"
            "💰 *Fees:*\n"
            "• Up to Grade/Year 7: AED 400 + VAT/month (twice a week)\n"
            "• Grade/Year 8 & above: Yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "as_commerce" and branch == "ic":
        text = (
            "💼 *Academic Support — Commerce and Accounting*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Commerce and Accounting (Accounts/BST/Eco)\n\n"
            "Our Commerce and Accounting classes help students stay on track with their school curriculum "
            "and improve academic performance.\n\n"
            "💰 *Fees:*\n"
            "• Classes conducted twice or thrice a week (based on requirements)\n"
            "• Offered under a yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "as_commerce" and branch == "dso":
        text = (
            "💼 *Academic Support — Commerce and Accounting*\n"
            "📍 Dubai Silicon Oasis\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Commerce and Accounting (Accounts/BST/Eco)\n\n"
            "Our Commerce and Accounting classes help students stay on track with their school curriculum "
            "and improve academic performance.\n\n"
            "💰 *Fees:*\n"
            "• Classes conducted twice or thrice a week (based on requirements)\n"
            "• Offered under a yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "as_commerce" and branch == "jadaf":
        text = (
            "💼 *Academic Support — Commerce and Accounting*\n"
            "📍 Al Jadaf\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Commerce and Accounting (Accounts/BST/Eco)\n\n"
            "Our Commerce and Accounting classes help students stay on track with their school curriculum "
            "and improve academic performance.\n\n"
            "💰 *Fees:*\n"
            "• Classes conducted twice or thrice a week (based on requirements)\n"
            "• Offered under a yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "as_commerce" and branch == "online":
        text = (
            "💼 *Academic Support — Commerce and Accounting*\n"
            "🌐 Online Classes\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Commerce and Accounting (Accounts/BST/Eco)\n\n"
            "Our Commerce and Accounting classes help students stay on track with their school curriculum "
            "and improve academic performance.\n\n"
            "💰 *Fees:*\n"
            "• Classes conducted twice or thrice a week (based on requirements)\n"
            "• Offered under a yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_abacus" and branch == "ic":
        text = (
            "🔢 *Abacus — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 6 to 10 years 👦👧\n"
            "⏳ Duration: 3 months (24 classes, 1 hour each)\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our Abacus Course is designed to develop strong mental arithmetic skills while enhancing concentration, memory, and logical thinking through the proven technique of bead-based calculations.\n"
            "Students learn to perform rapid ➕ addition, ➖ subtraction, ✖ multiplication, and ➗ division using the abacus 🧮, gradually progressing to fast and accurate mental calculations without the need for the physical tool.\n\n"
            "💰 Registration Fee: AED 100 + VAT (one-time)\n"
            "💰 Course Fee: AED 1,000 + VAT\n\n"
            "🎁 Course Includes\n"
            "• 📚 Course Books\n"
            "• 📝 Practice Worksheets\n"
            "• 📊 Mock Tests\n"
            "• 💻 E-Books\n"
            "• 🏅 Certificate issued by the Indian Institute of Vedic Maths and Abacus (IIVA)\n"
            "📈 Levels: Multiple levels are available based on the child's age and prior knowledge, ensuring a personalized learning journey.\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_abacus" and branch == "dso":
        text = (
            "🔢 *Abacus — Dubai Silicon Oasis*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 6 to 10 years 👦👧\n"
            "⏳ Duration: 3 months (24 classes, 1 hour each)\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our Abacus Course is designed to develop strong mental arithmetic skills while enhancing concentration, memory, and logical thinking through the proven technique of bead-based calculations.\n"
            "Students learn to perform rapid ➕ addition, ➖ subtraction, ✖ multiplication, and ➗ division using the abacus 🧮, gradually progressing to fast and accurate mental calculations without the need for the physical tool.\n\n"
            "🎁 Course Includes\n"
            "• 📚 Course Books\n"
            "• 📝 Practice Worksheets\n"
            "• 📊 Mock Tests\n"
            "• 💻 E-Books\n"
            "• 🏅 Certificate issued by the Indian Institute of Vedic Maths and Abacus (IIVA)\n"
            "📈 Levels: Multiple levels are available based on the child's age and prior knowledge, ensuring a personalized learning journey.\n"
            "💰 Registration Fee: AED 150 + VAT (one-time)\n"
            "💰 Course Fee: AED 1,000 + VAT\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_abacus" and branch == "jadaf":
        text = (
            "🔢 *Abacus — Al Jadaf*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 6 to 10 years 👦👧\n"
            "⏳ Duration: 3 months (24 classes, 1 hour each)\n"
            "📍 Location: Al Jadaf\n"
            "📖 Course Description\n"
            "Our Abacus Course is designed to develop strong mental arithmetic skills while enhancing concentration, memory, and logical thinking through the proven technique of bead-based calculations.\n"
            "Students learn to perform rapid ➕ addition, ➖ subtraction, ✖ multiplication, and ➗ division using the abacus 🧮, gradually progressing to fast and accurate mental calculations without the need for the physical tool.\n\n"
            "🎁 Course Includes\n"
            "• 📚 Course Books\n"
            "• 📝 Practice Worksheets\n"
            "• 📊 Mock Tests\n"
            "• 💻 E-Books\n"
            "• 🏅 Certificate issued by the Indian Institute of Vedic Maths and Abacus (IIVA)\n"
            "📈 Levels: Multiple levels are available based on the child's age and prior knowledge, ensuring a personalized learning journey.\n"
            "💰 Registration Fee: AED 150 + VAT (one-time)\n"
            "💰 Course Fee: AED 1,500 + VAT\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_abacus" and branch == "online":
        text = (
            "🔢 *Abacus — Online*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📖 Course Description\n"
            "Develop strong mental calculation skills, concentration, memory, and number sense through structured Abacus training. The course helps children improve speed, accuracy, and confidence in mathematics through fun and interactive activities. Our Abacus courses are certified from Indian Institute of Abacus and Vedic maths (IIVA).\n\n"
            "📞 For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_vedic" and branch == "ic":
        text = (
            "🧮 *Vedic Maths — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 8 to 16 years 👦👧\n"
            "⏳ Duration: 3 months (24 classes, 1 hour each)\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our Vedic Maths Course introduces students to powerful calculation techniques that make solving mathematical problems faster, simpler, and more accurate. Through easy-to-learn strategies, students improve their speed, accuracy, logical thinking, and confidence in Mathematics, making everyday calculations and competitive exam preparation more efficient.\n\n"
            "💰 Registration Fee: AED 100 + VAT (one-time)\n"
            "💰 Course Fee: AED 1,000 + VAT\n\n"
            "🎁 Course Includes\n"
            "• 📚 Course Books\n"
            "• 📝 Practice Worksheets\n"
            "• 📊 Mock Tests\n"
            "• 💻 E-Books\n"
            "• 🏅 Certificate issued by the Indian Institute of Vedic Maths and Abacus (IIVA)\n"
            "📈 Levels: Multiple levels are available based on the child's age and prior knowledge, ensuring a personalized learning journey.\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_vedic" and branch == "dso":
        text = (
            "🧮 *Vedic Maths — Dubai Silicon Oasis*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 8 to 16 years 👦👧\n"
            "⏳ Duration: 3 months (24 classes, 1 hour each)\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our Vedic Maths Course introduces students to powerful calculation techniques that make solving mathematical problems faster, simpler, and more accurate. Through easy-to-learn strategies, students improve their speed, accuracy, logical thinking, and confidence in Mathematics, making everyday calculations and competitive exam preparation more efficient.\n\n"
            "🎁 Course Includes\n"
            "• 📚 Course Books\n"
            "• 📝 Practice Worksheets\n"
            "• 📊 Mock Tests\n"
            "• 💻 E-Books\n"
            "• 🏅 Certificate issued by the Indian Institute of Vedic Maths and Abacus (IIVA)\n"
            "📈 Levels: Multiple levels are available based on the child's age and prior knowledge, ensuring a personalized learning journey.\n"
            "💰 Registration Fee: AED 150 + VAT (one-time)\n"
            "💰 Course Fee: AED 1,000 + VAT\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_vedic" and branch == "jadaf":
        text = (
            "🧮 *Vedic Maths — Al Jadaf*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 8 to 16 years 👦👧\n"
            "⏳ Duration: 3 months (24 classes, 1 hour each)\n"
            "📍 Location: Al Jadaf\n"
            "📖 Course Description\n"
            "Our Vedic Maths Course introduces students to powerful calculation techniques that make solving mathematical problems faster, simpler, and more accurate. Through easy-to-learn strategies, students improve their speed, accuracy, logical thinking, and confidence in Mathematics, making everyday calculations and competitive exam preparation more efficient.\n\n"
            "🎁 Course Includes\n"
            "• 📚 Course Books\n"
            "• 📝 Practice Worksheets\n"
            "• 📊 Mock Tests\n"
            "• 💻 E-Books\n"
            "• 🏅 Certificate issued by the Indian Institute of Vedic Maths and Abacus (IIVA)\n"
            "📈 Levels: Multiple levels are available based on the child's age and prior knowledge, ensuring a personalized learning journey.\n"
            "💰 Registration Fee: AED 150 + VAT (one-time)\n"
            "💰 Course Fee: AED 1,500 + VAT\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_vedic" and branch == "online":
        text = (
            "🧮 *Vedic Maths — Online*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📖 Course Description\n"
            "Enhance mathematical skills with powerful calculation techniques and shortcuts inspired by Vedic mathematics. Children learn faster problem-solving methods, improve calculation speed, and build greater confidence in handling numbers. Our Vedic Maths courses are certified from Indian Institute of Abacus and Vedic maths (IIVA).\n\n"
            "📞 For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_coding" and branch == "ic":
        text = (
            "💻 *Coding for Kids — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 7 years and above\n"
            "⏳ Duration: Minimum of 18 hours per level (class frequency and duration vary depending on the season and batch)\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our Coding Courses introduce children to the fundamentals of computational thinking and programming through Scratch, Python, and App Development. Students learn how computers and digital systems work by understanding inputs, outputs, logic, algorithms, and problem-solving techniques. The courses encourage creativity, logical reasoning, and innovation while building essential coding skills for the future.\n"
            "📈 Levels: Multiple levels are available across all courses based on the child's age and prior knowledge, ensuring a progressive learning experience.\n"
            "💰 Course Fee: Approximately AED 1,000 + VAT per level.\n"
            "Registration Fee: AED 100 + VAT (one-time)\n"
            "🎁 Course Includes\n"
            "💻 Hands-on coding projects and activities\n"
            "📚 Learning materials and practice exercises\n"
            "🏅 Educatia Course Completion Certificate\n"
            "📜 KHDA Certificate (available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_coding" and branch == "dso":
        text = (
            "💻 *Coding for Kids — Dubai Silicon Oasis*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 7 years and above\n"
            "⏳ Duration: Minimum of 18 hours per level (class frequency and duration vary depending on the season and batch)\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our Coding Courses introduce children to the fundamentals of computational thinking and programming through Scratch, Python, and App Development. Students learn how computers and digital systems work by understanding inputs, outputs, logic, algorithms, and problem-solving techniques. The courses encourage creativity, logical reasoning, and innovation while building essential coding skills for the future.\n"
            "📈 Levels: Multiple levels are available across all courses based on the child's age and prior knowledge, ensuring a progressive learning experience.\n"
            "🎁 Course Includes\n"
            "💻 Hands-on coding projects and activities\n"
            "📚 Learning materials and practice exercises\n"
            "🏅 Educatia Course Completion Certificate\n"
            "📜 KHDA Certificate (available upon request)\n"
            "💰 Course Fee: Approximately AED 1,000 + VAT per level.\n"
            "Registration Fee: AED 150 + VAT (one-time)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_coding" and branch == "jadaf":
        text = (
            "💻 *Coding for Kids — Al Jadaf*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 7 years and above\n"
            "⏳ Duration: Minimum of 18 hours per level (class frequency and duration vary depending on the season and batch)\n"
            "📍 Location: Al Jadaf\n"
            "📖 Course Description\n"
            "Our Coding Courses introduce children to the fundamentals of computational thinking and programming through Scratch, Python, and App Development. Students learn how computers and digital systems work by understanding inputs, outputs, logic, algorithms, and problem-solving techniques. The courses encourage creativity, logical reasoning, and innovation while building essential coding skills for the future.\n"
            "📈 Levels: Multiple levels are available across all courses based on the child's age and prior knowledge, ensuring a progressive learning experience.\n"
            "🎁 Course Includes\n"
            "💻 Hands-on coding projects and activities\n"
            "📚 Learning materials and practice exercises\n"
            "🏅 Educatia Course Completion Certificate\n"
            "📜 KHDA Certificate (available upon request)\n"
            "💰 Course Fee: Approximately AED 1,500 + VAT per level.\n"
            "Registration Fee: AED 150 + VAT (one-time)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_coding" and branch == "online":
        text = (
            "💻 *Coding for Kids — Online*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📖 Course Description\n"
            "Introduce children to the world of coding through creative, hands-on learning. Students develop logical thinking, problem-solving skills, and computational thinking while creating animations, games, applications, and real-world projects using age-appropriate programming languages.\n\n"
            "📞 For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_robotics" and branch == "ic":
        text = (
            "🤖 *Robotics (Beginner/Inter/Adv) — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 7 years and above\n"
            "⏳ Duration: Minimum of 18 hours per level (class frequency and duration vary depending on the season and batch)\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our Robotics Course helps students understand the interaction between hardware and software through hands-on learning. Students work with microcontrollers like micro and Arduino, learn sensors, inputs, outputs, programming, and debugging techniques to build functional robotic projects while developing problem-solving and engineering skills.\n"
            "📈 Levels: Multiple levels are available across all courses based on the child's age and prior knowledge, ensuring a progressive learning experience.\n"
            "💰 Course Fee: Approximately AED 1,000 + VAT per level.\n"
            "Registration Fee: AED 100 + VAT (one-time)\n"
            "🎁 Course Includes\n"
            "• 💻 Hands-on projects and activities\n"
            "• 📚 Learning materials and practice exercises\n"
            "• 🏅 Educatia Course Completion Certificate\n"
            "• 📜 KHDA Certificate (available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_robotics" and branch == "dso":
        text = (
            "🤖 *Robotics (Beginner/Inter/Adv) — Dubai Silicon Oasis*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 7 years and above\n"
            "⏳ Duration: Minimum of 18 hours per level (class frequency and duration vary depending on the season and batch)\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our Robotics Course helps students understand the interaction between hardware and software through hands-on learning. Students work with microcontrollers like micro and Arduino, learn sensors, inputs, outputs, programming, and debugging techniques to build functional robotic projects while developing problem-solving and engineering skills.\n"
            "📈 Levels: Multiple levels are available across all courses based on the child's age and prior knowledge, ensuring a progressive learning experience.\n"
            "🎁 Course Includes\n"
            "• 💻 Hands-on projects and activities\n"
            "• 📚 Learning materials and practice exercises\n"
            "• 🏅 Educatia Course Completion Certificate\n"
            "• 📜 KHDA Certificate (available upon request)\n"
            "💰 Course Fee: Approximately AED 1,000 + VAT per level.\n"
            "Registration Fee: AED 150 + VAT (one-time)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_robotics" and branch == "jadaf":
        text = (
            "🤖 *Robotics (Beginner/Inter/Adv) — Al Jadaf*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 7 years and above\n"
            "⏳ Duration: Minimum of 18 hours per level (class frequency and duration vary depending on the season and batch)\n"
            "📍 Location: Al Jadaf\n"
            "📖 Course Description\n"
            "Our Robotics Course helps students understand the interaction between hardware and software through hands-on learning. Students work with microcontrollers like micro and Arduino, learn sensors, inputs, outputs, programming, and debugging techniques to build functional robotic projects while developing problem-solving and engineering skills.\n"
            "📈 Levels: Multiple levels are available across all courses based on the child's age and prior knowledge, ensuring a progressive learning experience.\n"
            "🎁 Course Includes\n"
            "• 💻 Hands-on projects and activities\n"
            "• 📚 Learning materials and practice exercises\n"
            "• 🏅 Educatia Course Completion Certificate\n"
            "• 📜 KHDA Certificate (available upon request)\n"
            "💰 Course Fee: Approximately AED 1,500 + VAT per level.\n"
            "Registration Fee: AED 150 + VAT (one-time)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_robotics" and branch == "online":
        text = (
            "🤖 *Robotics (Beginner/Inter/Adv) — Online*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📖 Course Description\n"
            "Explore the exciting world of robotics through hands-on projects involving programming, electronics, sensors, and automation. Children develop creativity, engineering skills, teamwork, and problem-solving abilities while building and programming their own robotic projects.\n\n"
            "📞 For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_handwriting" and branch == "ic":
        text = (
            "✍️ *Handwriting is beautiful — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 6 years and above\n"
            "⏳ Duration: Minimum of 24 hours per level\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our Handwriting Course is designed to help students develop neat, legible, and confident handwriting through guided practice and structured techniques. The program focuses on improving letter formation, spacing, alignment, writing speed, and overall presentation skills.\n"
            "📈 Levels: Multiple levels are available across all courses based on the child's age and prior knowledge, ensuring a progressive learning experience.\n"
            "💰 Course Fee: AED 1000 + VAT per level.\n"
            "Registration Fee: AED 100 + VAT (one-time)\n\n"
            "🎁 Course Takeaways\n"
            "📚 Handwriting Practice Book & Learning Materials\n"
            "✍️ Improved Letter Formation, Neatness, and Writing Style\n"
            "📝 Regular Practice Worksheets and Guided Feedback\n"
            "🚀 Enhanced Writing Speed, Spacing, and Presentation Skills\n"
            "🏅 Educatia Course Completion Certificate (KHDA Certificate available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_handwriting" and branch == "dso":
        text = (
            "✍️ *Handwriting is beautiful — Dubai Silicon Oasis*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 6 years and above\n"
            "⏳ Duration: Minimum of 24 hours per level\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our Handwriting Course is designed to help students develop neat, legible, and confident handwriting through guided practice and structured techniques. The program focuses on improving letter formation, spacing, alignment, writing speed, and overall presentation skills.\n"
            "📈 Levels: Multiple levels are available across all courses based on the child's age and prior knowledge, ensuring a progressive learning experience.\n"
            "🎁 Course Takeaways\n"
            "📚 Handwriting Practice Book & Learning Materials\n"
            "✍️ Improved Letter Formation, Neatness, and Writing Style\n"
            "📝 Regular Practice Worksheets and Guided Feedback\n"
            "🚀 Enhanced Writing Speed, Spacing, and Presentation Skills\n"
            "🏅 Educatia Course Completion Certificate (KHDA Certificate available upon request)\n"
            "💰 Course Fee: AED 1000 + VAT per level.\n"
            "Registration Fee: AED 150 + VAT (one-time)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_handwriting" and branch == "jadaf":
        text = (
            "✍️ *Handwriting is beautiful — Al Jadaf*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 6 years and above\n"
            "⏳ Duration: Minimum of 24 hours per level\n"
            "📍 Location: Al Jadaf\n"
            "📖 Course Description\n"
            "Our Handwriting Course is designed to help students develop neat, legible, and confident handwriting through guided practice and structured techniques. The program focuses on improving letter formation, spacing, alignment, writing speed, and overall presentation skills.\n"
            "📈 Levels: Multiple levels are available across all courses based on the child's age and prior knowledge, ensuring a progressive learning experience.\n"
            "🎁 Course Takeaways\n"
            "📚 Handwriting Practice Book & Learning Materials\n"
            "✍️ Improved Letter Formation, Neatness, and Writing Style\n"
            "📝 Regular Practice Worksheets and Guided Feedback\n"
            "🚀 Enhanced Writing Speed, Spacing, and Presentation Skills\n"
            "🏅 Educatia Course Completion Certificate (KHDA Certificate available upon request)\n"
            "💰 Course Fee: AED 1000 + VAT per level.\n"
            "Registration Fee: AED 150 + VAT (one-time)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_handwriting" and branch == "online":
        text = (
            "✍️ *Handwriting is beautiful — Online*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👦👧 Age Group: 6 years and above\n"
            "⏱ Duration: Min 24 hours per level\n\n"
            "Develop neat, legible & confident handwriting through guided practice. "
            "Focuses on letter formation, spacing, alignment, writing speed & presentation.\n\n"
            "💰 *Fees:*\n"
            "• Registration Fee: AED 150 + VAT (one-time)\n"
            "• Course Fee: AED 1,000 + VAT per level\n\n"
            "📦 Includes: Practice Book • Worksheets • Feedback • Educatia Certificate\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_creative" and branch == "ic":
        text = (
            "🎨 *Creative skills — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Our Art & Craft sessions are designed to encourage creativity, imagination, and self-expression through fun, hands-on activities. These sessions are offered as part of our Summer and Winter Camps and include exciting activities such as finger painting, paper craft, origami, canvas painting, and much more.\n"
            "Children explore different art techniques while developing fine motor skills, creativity, and confidence in their artistic abilities.\n\n"
            "📞 Contact us for the next camp schedule:\n"
            "*+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_creative" and branch == "dso":
        text = (
            "🎨 *Creative skills — Dubai Silicon Oasis*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Our Art & Craft sessions are designed to encourage creativity, imagination, and self-expression through fun, hands-on activities. These sessions are offered as part of our Summer and Winter Camps and include exciting activities such as finger painting, paper craft, origami, canvas painting, and much more.\n"
            "Children explore different art techniques while developing fine motor skills, creativity, and confidence in their artistic abilities.\n\n"
            "📞 Contact us for the next camp schedule:\n"
            "*+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_creative" and branch == "jadaf":
        text = (
            "🎨 *Creative skills — Al Jadaf*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Our Art & Craft sessions are designed to encourage creativity, imagination, and self-expression through fun, hands-on activities. These sessions are offered as part of our Summer and Winter Camps and include exciting activities such as finger painting, paper craft, origami, canvas painting, and much more.\n"
            "Children explore different art techniques while developing fine motor skills, creativity, and confidence in their artistic abilities.\n\n"
            "📞 Contact us for the next camp schedule:\n"
            "*+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_creative" and branch == "online":
        text = (
            "🎨 *Creative skills — Online*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Art & Craft sessions designed to encourage creativity, imagination & self-expression.\n\n"
            "Activities include: Finger painting • Paper craft • Origami • Canvas painting & more!\n\n"
            "ℹ️ Creative skills sessions are offered as part of our Summer & Winter Camps.\n\n"
            "📞 Contact us for the next camp schedule:\n"
            "*+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_science_exp" and branch == "ic":
        text = (
            "⚗️ *Live science experiments — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 10 years and above\n"
            "⏳ Duration: Minimum of 12 hours per level\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our Live Science Experiments program introduces children to the fascinating world of science through exciting hands-on experiments and demonstrations. Students explore scientific concepts by observing, experimenting, and understanding the \"why\" behind everyday phenomena, making learning fun, interactive, and memorable.\n"
            "These sessions are also offered as complimentary enrichment sessions for students enrolled in our Academic Support Science Classes, helping them strengthen their understanding of scientific concepts through practical learning.\n\n"
            "💰 Course Fee: AED 500 + VAT per level.\n"
            "Registration Fee: AED 100 + VAT (one-time)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_science_exp" and branch == "dso":
        text = (
            "⚗️ *Live science experiments — Dubai Silicon Oasis*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 10 years and above\n"
            "⏳ Duration: Minimum of 12 hours per level\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our Live Science Experiments program introduces children to the fascinating world of science through exciting hands-on experiments and demonstrations. Students explore scientific concepts by observing, experimenting, and understanding the \"why\" behind everyday phenomena, making learning fun, interactive, and memorable.\n"
            "These sessions are also offered as complimentary enrichment sessions for students enrolled in our Academic Support Science Classes, helping them strengthen their understanding of scientific concepts through practical learning.\n\n"
            "💰 Course Fee: AED 600 + VAT per level.\n"
            "Registration Fee: AED 150 + VAT (one-time)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_science_exp" and branch == "jadaf":
        text = (
            "⚗️ *Live science experiments — Al Jadaf*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👦👧 Age Group: 10 years and above\n"
            "⏱ Duration: Min 12 hours per level\n\n"
            "Exciting hands-on experiments introducing children to the fascinating world of science. "
            "Students explore scientific concepts by observing, experimenting & understanding "
            "the 'why' behind everyday phenomena.\n\n"
            "ℹ️ Also offered as complimentary enrichment for Academic Support Science students.\n\n"
            "💰 *Fees:*\n"
            "• Registration Fee: AED 100 + VAT (one-time)\n"
            "• Course Fee: AED 500 + VAT per level\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_science_exp" and branch == "online":
        text = (
            "⚗️ *Live science experiments — Online*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👦👧 Age Group: 10 years and above\n"
            "⏱ Duration: Min 12 hours per level\n\n"
            "Exciting hands-on experiments introducing children to the fascinating world of science. "
            "Students explore scientific concepts by observing, experimenting & understanding "
            "the 'why' behind everyday phenomena.\n\n"
            "ℹ️ Also offered as complimentary enrichment for Academic Support Science students.\n\n"
            "💰 *Fees:*\n"
            "• Registration Fee: AED 150 + VAT (one-time)\n"
            "• Course Fee: AED 600 + VAT per level\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_msoffice" and branch == "ic":
        text = (
            "💾 *MS Office (Beginner/Inter) — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 9 years and above\n"
            "⏳ Duration: Minimum of 20 hours per level\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our MS Office Course is designed to introduce children to essential digital productivity skills through practical learning. Students learn to create and format documents, prepare presentations, organize data, and use various tools in Microsoft Word, PowerPoint, and Excel. The course also introduces children to the use of AI tools for learning, creativity, and improving productivity, helping them understand how technology can support their academic and future needs.\n\n"
            "🎁 Course Takeaways\n"
            "• 🖥️ Practical knowledge of Microsoft Word, PowerPoint, and Excel\n"
            "• 📝 Skills to create documents, presentations, and spreadsheets\n"
            "• 📊 Basic data handling and formatting skills\n"
            "• 🎨 Ability to design creative presentations and projects\n"
            "• 🏅 Educatia Course Completion Certificate (KHDA certificate upon request)\n"
            "💰 Course Fee: AED 1000 + VAT per level.\n"
            "Registration Fee: AED 100 + VAT (one-time)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_msoffice" and branch == "dso":
        text = (
            "💾 *MS Office (Beginner/Inter) — Dubai Silicon Oasis*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 9 years and above\n"
            "⏳ Duration: Minimum of 20 hours per level\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our MS Office Course is designed to introduce children to essential digital productivity skills through practical learning. Students learn to create and format documents, prepare presentations, organize data, and use various tools in Microsoft Word, PowerPoint, and Excel. The course also introduces children to the use of AI tools for learning, creativity, and improving productivity, helping them understand how technology can support their academic and future needs.\n\n"
            "🎁 Course Takeaways\n"
            "• 🖥️ Practical knowledge of Microsoft Word, PowerPoint, and Excel\n"
            "• 📝 Skills to create documents, presentations, and spreadsheets\n"
            "• 📊 Basic data handling and formatting skills\n"
            "• 🎨 Ability to design creative presentations and projects\n"
            "• 🏅 Educatia Course Completion Certificate (KHDA certificate upon request)\n"
            "💰 Course Fee: AED 1000 + VAT per level.\n"
            "Registration Fee: AED 150 + VAT (one-time)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_msoffice" and branch == "jadaf":
        text = (
            "💾 *MS Office (Beginner/Inter) — Al Jadaf*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 9 years and above\n"
            "⏳ Duration: Minimum of 20 hours per level\n"
            "📍 Location: Al Jadaf\n"
            "📖 Course Description\n"
            "Our MS Office Course is designed to introduce children to essential digital productivity skills through practical learning. Students learn to create and format documents, prepare presentations, organize data, and use various tools in Microsoft Word, PowerPoint, and Excel. The course also introduces children to the use of AI tools for learning, creativity, and improving productivity, helping them understand how technology can support their academic and future needs.\n\n"
            "🎁 Course Takeaways\n"
            "• 🖥️ Practical knowledge of Microsoft Word, PowerPoint, and Excel\n"
            "• 📝 Skills to create documents, presentations, and spreadsheets\n"
            "• 📊 Basic data handling and formatting skills\n"
            "• 🎨 Ability to design creative presentations and projects\n"
            "• 🏅 Educatia Course Completion Certificate (KHDA certificate upon request)\n"
            "💰 Course Fee: AED 1500 + VAT per level.\n"
            "Registration Fee: AED 150 + VAT (one-time)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_msoffice" and branch == "online":
        text = (
            "💾 *MS Office (Beginner/Inter) — Online*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📖 Course Description\n"
            "Build essential digital skills by learning Microsoft Word, Excel, and PowerPoint through practical activities and projects. Children develop confidence in creating documents, organising information, preparing presentations, and using technology effectively for academic and future professional needs.\n\n"
            "📞 For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_eng_beg" and branch == "ic":
        text = (
            "🗣 *English communication Beginner*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 5 years and above\n"
            "⏳ Duration: Minimum of 36 hours per level\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our Communication Skills for Kids Programme is designed for early\n"
            "learners to develop strong foundational communication skills in English.\n"
            "The programme helps children build confidence in speaking, improve\n"
            "vocabulary, and develop clear sentence formation through structured, age"
            "appropriate learning activities.\n"
            "At the early stage, children are introduced to English in a simple,\n"
            "engaging, and supportive environment that encourages them to express themselves naturally and confidently\n"
            "💰 Course Fee: AED 1220 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_eng_beg" and branch == "dso":
        text = (
            "🗣 *English communication Beginner*\n"
            "📍 Dubai Silicon Oasis\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 5 years and above\n"
            "⏳ Duration: Minimum of 36 hours per level\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our Communication Skills for Kids Programme is designed for early\n"
            "learners to develop strong foundational communication skills in English.\n"
            "The programme helps children build confidence in speaking, improve\n"
            "vocabulary, and develop clear sentence formation through structured, age"
            "appropriate learning activities.\n"
            "At the early stage, children are introduced to English in a simple,\n"
            "engaging, and supportive environment that encourages them to express themselves naturally and confidently\n"
            "💰 Course Fee: AED 1220 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_eng_beg" and branch == "jadaf":
        text = (
            "🗣 *English communication Beginner*\n"
            "📍 Al Jadaf\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 5 years and above\n"
            "⏳ Duration: Minimum of 36 hours per level\n"
            "📍 Location: Al Jadaf\n"
            "📖 Course Description\n"
            "Our Communication Skills for Kids Programme is designed for early\n"
            "learners to develop strong foundational communication skills in English.\n"
            "The programme helps children build confidence in speaking, improve\n"
            "vocabulary, and develop clear sentence formation through structured, age"
            "appropriate learning activities.\n"
            "At the early stage, children are introduced to English in a simple,\n"
            "engaging, and supportive environment that encourages them to express themselves naturally and confidently\n"
            "💰 Course Fee: AED 1470 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_eng_beg" and branch == "online":
        text = (
            "🗣 *English Communication (Beginner / Intermediate)*\n"
            "🌐 Online Classes\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Develop children's confidence in speaking English through interactive activities focused on vocabulary, grammar, pronunciation, reading, writing, and everyday communication. The course helps learners express themselves clearly and improve their overall language skills.\n\n"
            "📞 For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_eng_int" and branch == "ic":
        text = (
            "🗣 *English Communication Intermediate*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 8 years and above\n"
            "⏳ Duration: Minimum of 24 hours per level\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our Communication Skills for Kids Programme is designed for early\n"
            "learners to develop strong foundational communication skills in English.\n"
            "The programme helps children build confidence in speaking, improve\n"
            "vocabulary, and develop clear sentence formation through structured, age"
            "appropriate learning activities.\n"
            "At the early stage, children are introduced to English in a simple,\n"
            "engaging, and supportive environment that encourages them to express themselves naturally and confidently\n"
            "💰 Course Fee: AED 1220 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_eng_int" and branch == "dso":
        text = (
            "🗣 *English Communication Intermediate*\n"
            "📍 Dubai Silicon Oasis\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 8 years and above\n"
            "⏳ Duration: Minimum of 24 hours per level\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our Communication Skills for Kids Programme is designed for early\n"
            "learners to develop strong foundational communication skills in English.\n"
            "The programme helps children build confidence in speaking, improve\n"
            "vocabulary, and develop clear sentence formation through structured, age"
            "appropriate learning activities.\n"
            "At the early stage, children are introduced to English in a simple,\n"
            "engaging, and supportive environment that encourages them to express themselves naturally and confidently\n"
            "💰 Course Fee: AED 1220 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_eng_int" and branch == "jadaf":
        text = (
            "🗣 *English Communication Intermediate*\n"
            "📍 Al Jadaf\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 8 years and above\n"
            "⏳ Duration: Minimum of 24 hours per level\n"
            "📍 Location: Al Jadaf\n"
            "📖 Course Description\n"
            "Our Communication Skills for Kids Programme is designed for early\n"
            "learners to develop strong foundational communication skills in English.\n"
            "The programme helps children build confidence in speaking, improve\n"
            "vocabulary, and develop clear sentence formation through structured, age"
            "appropriate learning activities.\n"
            "At the early stage, children are introduced to English in a simple,\n"
            "engaging, and supportive environment that encourages them to express themselves naturally and confidently\n"
            "💰 Course Fee: AED 1470 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_eng_int" and branch == "online":
        text = (
            "🗣 *English Communication (Beginner / Intermediate)*\n"
            "🌐 Online Classes\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Develop children's confidence in speaking English through interactive activities focused on vocabulary, grammar, pronunciation, reading, writing, and everyday communication. The course helps learners express themselves clearly and improve their overall language skills.\n\n"
            "📞 For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_phonics" and branch == "ic":
        text = (
            "🔤 *Phonics classes — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 5 years and above\n"
            "⏳ Duration: Minimum of 36 hours per level\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our Phonics Classes are designed to help young learners develop strong reading, spelling, and pronunciation skills through systematic sound-based learning. Children learn letter sounds, blending techniques, word formation, and reading strategies in a fun and interactive way, building confidence and a strong foundation in English language skills.\n"
            "💰 Course Fee: AED 1220 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_phonics" and branch == "dso":
        text = (
            "🔤 *Phonics classes — Dubai Silicon Oasis*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 5 years and above\n"
            "⏳ Duration: Minimum of 36 hours per level\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our Phonics Classes are designed to help young learners develop strong reading, spelling, and pronunciation skills through systematic sound-based learning. Children learn letter sounds, blending techniques, word formation, and reading strategies in a fun and interactive way, building confidence and a strong foundation in English language skills.\n"
            "💰 Course Fee: AED 1220 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_phonics" and branch == "jadaf":
        text = (
            "🔤 *Phonics classes — Al Jadaf*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 5 years and above\n"
            "⏳ Duration: Minimum of 36 hours per level\n"
            "📍 Location: Al Jadaf\n"
            "📖 Course Description\n"
            "Our Phonics Classes are designed to help young learners develop strong reading, spelling, and pronunciation skills through systematic sound-based learning. Children learn letter sounds, blending techniques, word formation, and reading strategies in a fun and interactive way, building confidence and a strong foundation in English language skills.\n"
            "💰 Course Fee: AED 1470 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_phonics" and branch == "online":
        text = (
            "🔤 *Phonics classes — Online*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Build a strong foundation in reading and language skills through systematic phonics learning. Children develop letter-sound recognition, pronunciation, vocabulary, blending, spelling, and reading fluency through engaging activities, stories, and interactive practice. The course helps young learners become confident and independent readers.\n\n"
            "📞 For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_pubspeak" and branch == "ic":
        text = (
            "🎤 *Public speaking and Creative writing*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 8 years and above\n"
            "⏳ Duration: Minimum of 16 hours per level\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our Public Speaking and Creative Writing Classes are designed to help children express their thoughts confidently and creatively. Through engaging activities, storytelling, writing exercises, and speaking practices, students develop communication skills, imagination, vocabulary, and the confidence to present their ideas effectively.\n"
            "💰 Course Fee: AED 900 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_pubspeak" and branch == "dso":
        text = (
            "🎤 *Public speaking and Creative writing*\n"
            "📍 Dubai Silicon Oasis\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 8 years and above\n"
            "⏳ Duration: Minimum of 16 hours per level\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our Public Speaking and Creative Writing Classes are designed to help children express their thoughts confidently and creatively. Through engaging activities, storytelling, writing exercises, and speaking practices, students develop communication skills, imagination, vocabulary, and the confidence to present their ideas effectively.\n"
            "💰 Course Fee: AED 950 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_pubspeak" and branch == "jadaf":
        text = (
            "🎤 *Public speaking and Creative writing*\n"
            "📍 Al Jadaf\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 8 years and above\n"
            "⏳ Duration: Minimum of 16 hours per level\n"
            "📍 Location: Al Jadaf\n"
            "📖 Course Description\n"
            "Our Public Speaking and Creative Writing Classes are designed to help children express their thoughts confidently and creatively. Through engaging activities, storytelling, writing exercises, and speaking practices, students develop communication skills, imagination, vocabulary, and the confidence to present their ideas effectively.\n"
            "💰 Course Fee: AED 1270 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_pubspeak" and branch == "online":
        text = (
            "🎤 *Public speaking and Creative writing*\n"
            "🌐 Online Classes\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Enhance children's communication, confidence, and creativity through engaging activities in speech delivery, storytelling, presentations, vocabulary building, and creative writing. The course encourages children to express ideas effectively and develop strong communication skills.\n\n"
            "📞 For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_arabic_rw" and branch == "ic":
        text = (
            "🌙 *Arabic Reading and Writing skills — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 6 years and above\n"
            "⏳ Duration: Minimum of 24 hours per level\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our Arabic Reading and Writing Skills Course is designed for school-going children and adults who wish to develop a strong foundation in the Arabic language. The course focuses on learning Arabic alphabets, correct pronunciation, reading techniques, and writing skills through structured and practical lessons, helping learners gain confidence in reading and writing Arabic.\n"
            "💰 Course Fee: AED 1220 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_arabic_rw" and branch == "dso":
        text = (
            "🌙 *Arabic Reading and Writing skills — Dubai Silicon Oasis*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 6 years and above\n"
            "⏳ Duration: Minimum of 24 hours per level\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our Arabic Reading and Writing Skills Course is designed for school-going children and adults who wish to develop a strong foundation in the Arabic language. The course focuses on learning Arabic alphabets, correct pronunciation, reading techniques, and writing skills through structured and practical lessons, helping learners gain confidence in reading and writing Arabic.\n"
            "💰 Course Fee: AED 1270 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_arabic_rw" and branch == "jadaf":
        text = (
            "🌙 *Arabic Reading and Writing skills — Al Jadaf*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: 6 years and above\n"
            "⏳ Duration: Minimum of 24 hours per level\n"
            "📍 Location: Al Jadaf\n"
            "📖 Course Description\n"
            "Our Arabic Reading and Writing Skills Course is designed for school-going children and adults who wish to develop a strong foundation in the Arabic language. The course focuses on learning Arabic alphabets, correct pronunciation, reading techniques, and writing skills through structured and practical lessons, helping learners gain confidence in reading and writing Arabic.\n"
            "💰 Course Fee: AED 1270 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_arabic_rw" and branch == "online":
        text = (
            "🌙 *Arabic Reading and Writing skills — Online*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Build a strong foundation in Arabic reading and writing through structured lessons covering alphabets, vocabulary, sentence formation, pronunciation, and writing practice. The course helps children develop confidence in understanding and using Arabic effectively.\n\n"
            "📞 For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_hindi_rw" and branch == "ic":
        text = (
            "\U0001f4d6 *Hindi reading and writing skills \u2014 International City*\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            "\U0001f4cc Age Group: 6 years and above\n"
            "\u23f3 Duration: Minimum of 24 hours per level\n"
            "\U0001f4cd Location: International City\n"
            "\U0001f4d6 Course Description\n"
            "Our Hindi Reading and Writing Skills Course is designed for school-going children and adults who wish to develop a strong foundation in the Hindi language. The course focuses on learning Hindi alphabets, correct pronunciation, reading techniques, and writing skills through structured and practical lessons, helping learners gain confidence in reading and writing Hindi.\n"
            "\U0001f4b0 Course Fee: AED 1220 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "\U0001f4de Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back \U0001f519"
        )
        send_text(to, text)
        return

    if course_id == "lt_hindi_rw" and branch == "dso":
        text = (
            "\U0001f4d6 *Hindi reading and writing skills \u2014 Dubai Silicon Oasis*\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            "\U0001f4cc Age Group: 6 years and above\n"
            "\u23f3 Duration: Minimum of 24 hours per level\n"
            "\U0001f4cd Location: Dubai Silicon Oasis\n"
            "\U0001f4d6 Course Description\n"
            "Our Hindi Reading and Writing Skills Course is designed for school-going children and adults who wish to develop a strong foundation in the Hindi language. The course focuses on learning Hindi alphabets, correct pronunciation, reading techniques, and writing skills through structured and practical lessons, helping learners gain confidence in reading and writing Hindi.\n"
            "\U0001f4b0 Course Fee: AED 1270 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "\U0001f4de Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back \U0001f519"
        )
        send_text(to, text)
        return

    if course_id == "lt_hindi_rw" and branch == "jadaf":
        text = (
            "\U0001f4d6 *Hindi reading and writing skills \u2014 Al Jadaf*\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            "\U0001f4cc Age Group: 6 years and above\n"
            "\u23f3 Duration: Minimum of 24 hours per level\n"
            "\U0001f4cd Location: Al Jadaf\n"
            "\U0001f4d6 Course Description\n"
            "Our Hindi Reading and Writing Skills Course is designed for school-going children and adults who wish to develop a strong foundation in the Hindi language. The course focuses on learning Hindi alphabets, correct pronunciation, reading techniques, and writing skills through structured and practical lessons, helping learners gain confidence in reading and writing Hindi.\n"
            "\U0001f4b0 Course Fee: AED 1270 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "\U0001f4de Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back \U0001f519"
        )
        send_text(to, text)
        return

    if course_id == "lt_hindi_rw" and branch == "online":
        text = (
            "\U0001f4d6 *Hindi reading and writing skills \u2014 Online*\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            "Help children develop Hindi language skills through engaging lessons focused on alphabets, reading, writing, vocabulary, grammar, and sentence formation. The course builds confidence in communicating and understanding Hindi.\n\n"
            "\U0001f4de For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back \U0001f519"
        )
        send_text(to, text)
        return

    if course_id == "lt_french_rw" and branch == "ic":
        text = (
            "\U0001f1eb\U0001f1f7 *French reading and writing skills \u2014 International City*\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            "\U0001f4cc Age Group: 6 years and above\n"
            "\u23f3 Duration: Minimum of 24 hours per level\n"
            "\U0001f4cd Location: International City\n"
            "\U0001f4d6 Course Description\n"
            "Our French Reading and Writing Skills Course is designed for school-going children and adults who wish to develop a strong foundation in the French language. The course focuses on learning French alphabets, correct pronunciation, reading techniques, and writing skills through structured and practical lessons, helping learners gain confidence in reading and writing Frenchi.\n"
            "\U0001f4b0 Course Fee: AED 1420 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "\U0001f4de Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back \U0001f519"
        )
        send_text(to, text)
        return

    if course_id == "lt_french_rw" and branch == "dso":
        text = (
            "\U0001f1eb\U0001f1f7 *French reading and writing skills \u2014 Dubai Silicon Oasis*\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            "\U0001f4cc Age Group: 6 years and above\n"
            "\u23f3 Duration: Minimum of 24 hours per level\n"
            "\U0001f4cd Location: Dubai Silicon Oasis\n"
            "\U0001f4d6 Course Description\n"
            "Our French Reading and Writing Skills Course is designed for school-going children and adults who wish to develop a strong foundation in the French language. The course focuses on learning French alphabets, correct pronunciation, reading techniques, and writing skills through structured and practical lessons, helping learners gain confidence in reading and writing Frenchi.\n"
            "\U0001f4b0 Course Fee: AED 1470 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "\U0001f4de Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back \U0001f519"
        )
        send_text(to, text)
        return

    if course_id == "lt_french_rw" and branch == "jadaf":
        text = (
            "\U0001f1eb\U0001f1f7 *French reading and writing skills \u2014 Al Jadaf*\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            "\U0001f4cc Age Group: 6 years and above\n"
            "\u23f3 Duration: Minimum of 24 hours per level\n"
            "\U0001f4cd Location: Al Jadaf\n"
            "\U0001f4d6 Course Description\n"
            "Our French Reading and Writing Skills Course is designed for school-going children and adults who wish to develop a strong foundation in the French language. The course focuses on learning French alphabets, correct pronunciation, reading techniques, and writing skills through structured and practical lessons, helping learners gain confidence in reading and writing Frenchi.\n"
            "\U0001f4b0 Course Fee: AED 1470 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "\U0001f4de Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back \U0001f519"
        )
        send_text(to, text)
        return

    if course_id == "lt_french_rw" and branch == "online":
        text = (
            "\U0001f1eb\U0001f1f7 *French reading and writing skills \u2014 Online*\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            "Introduce children to the French language through interactive lessons covering alphabets, pronunciation, vocabulary, reading, writing, and basic communication skills. The course creates a strong foundation for learning French with confidence.\n\n"
            "\U0001f4de For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back \U0001f519"
        )
        send_text(to, text)
        return

    if course_id == "a_eng_basic" and branch == "ic":
        text = (
            "🗣 *English communication Beginner/Elementary*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: All ages\n"
            "⏳ Duration: Minimum of 36 hours per level (3 months course)\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our Communication Skills in English Programme is designed to help\n"
            "learners develop confidence, clarity, and fluency in spoken and written\n"
            "English. Through interactive activities, practical exercises, and guided\n"
            "practice, students improve their vocabulary, pronunciation, sentence\n"
            "structure, and overall communication ability.\n"
            "The programme is structured across three progressive levels to support\n"
            "learners at different stages, gradually building the skills needed for\n"
            "effective academic, social, and professional communication\n\n"
            "💰 Course Fee: AED 1220 + VAT per level (includes class fees, registration fees and material fees)\n"
            "Certifications : Educatia Course Completion Certificate (KHDA Certificate available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_eng_basic" and branch == "dso":
        text = (
            "🗣 *English communication Beginner/Elementary*\n"
            "📍 Dubai Silicon Oasis\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: All ages\n"
            "⏳ Duration: Minimum of 36 hours per level (3 months course)\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our Communication Skills in English Programme is designed to help\n"
            "learners develop confidence, clarity, and fluency in spoken and written\n"
            "English. Through interactive activities, practical exercises, and guided\n"
            "practice, students improve their vocabulary, pronunciation, sentence\n"
            "structure, and overall communication ability.\n"
            "The programme is structured across three progressive levels to support\n"
            "learners at different stages, gradually building the skills needed for\n"
            "effective academic, social, and professional communication\n\n"
            "💰 Course Fee: AED 1470 + VAT per level (includes class fees, registration fees and material fees)\n"
            "Certifications : Educatia Course Completion Certificate (KHDA Certificate available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_eng_basic" and branch == "jadaf":
        text = (
            "🗣 *English communication Beginner/Elementary*\n"
            "📍 Al Jadaf\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Develop confidence and fluency in spoken and written English through interactive sessions focused on grammar, vocabulary, pronunciation, listening, reading, writing, and real-life communication. Suitable for learners looking to improve everyday, academic, or professional English skills.\n\n"
            "💰 Course Fee: AED 150 + VAT per hour\n"
            "One-Time Registration Fee: AED 150 + VAT\n"
            "🎉 Special Discounts Available on bookings of 20+ sessions.\n"
            "Certifications : Educatia Course Completion Certificate (KHDA Certificate available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_eng_basic" and branch == "online":
        text = (
            "🗣 *English communication Beginner/Elementary*\n"
            "🌐 Online Classes\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Improve your English fluency and confidence through structured lessons focused on speaking, pronunciation, vocabulary, grammar, reading, writing, and real-life communication. The course is designed to help learners communicate effectively in personal, academic, and professional environments.\n\n"
            "📞 For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_eng_adv" and branch == "ic":
        text = (
            "🗣 *English communication PreInter/Inter/Upper Inter/Advanced*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: All ages\n"
            "⏳ Duration: Minimum of 24 hours per level (3 months course)\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our Communication Skills in English Programme is designed to help\n"
            "learners develop confidence, clarity, and fluency in spoken and written\n"
            "English. Through interactive activities, practical exercises, and guided\n"
            "practice, students improve their vocabulary, pronunciation, sentence\n"
            "structure, and overall communication ability.\n"
            "The programme is structured across three progressive levels to support\n"
            "learners at different stages, gradually building the skills needed for\n"
            "effective academic, social, and professional communication\n\n"
            "💰 Course Fee: AED 1220 + VAT per level (includes class fees, registration fees and material fees)\n"
            "Certifications : Educatia Course Completion Certificate (KHDA Certificate available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_eng_adv" and branch == "dso":
        text = (
            "🗣 *English communication PreInter/Inter/Upper Inter/Advanced*\n"
            "📍 Dubai Silicon Oasis\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: All ages\n"
            "⏳ Duration: Minimum of 24 hours per level (3 months course)\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our Communication Skills in English Programme is designed to help\n"
            "learners develop confidence, clarity, and fluency in spoken and written\n"
            "English. Through interactive activities, practical exercises, and guided\n"
            "practice, students improve their vocabulary, pronunciation, sentence\n"
            "structure, and overall communication ability.\n"
            "The programme is structured across three progressive levels to support\n"
            "learners at different stages, gradually building the skills needed for\n"
            "effective academic, social, and professional communication\n\n"
            "💰 Course Fee: AED 1470 + VAT per level (includes class fees, registration fees and material fees)\n"
            "Certifications : Educatia Course Completion Certificate (KHDA Certificate available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_eng_adv" and branch == "jadaf":
        text = (
            "🗣 *English communication PreInter/Inter/Upper Inter/Advanced*\n"
            "📍 Al Jadaf\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Develop confidence and fluency in spoken and written English through interactive sessions focused on grammar, vocabulary, pronunciation, listening, reading, writing, and real-life communication. Suitable for learners looking to improve everyday, academic, or professional English skills.\n\n"
            "💰 Course Fee: AED 150 + VAT per hour\n"
            "One-Time Registration Fee: AED 150 + VAT\n"
            "🎉 Special Discounts Available on bookings of 20+ sessions.\n"
            "Certifications : Educatia Course Completion Certificate (KHDA Certificate available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_eng_adv" and branch == "online":
        text = (
            "🗣 *English communication Beginner/Intermediate/Advanced*\n"
            "🌐 Online Classes\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Improve your English fluency and confidence through structured lessons focused on speaking, pronunciation, vocabulary, grammar, reading, writing, and real-life communication. The course is designed to help learners communicate effectively in personal, academic, and professional environments.\n\n"
            "📞 For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_arabic" and branch == "ic":
        text = (
            "🌙 *Spoken Arabic Beginner/ Inter/Advanced*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: All ages\n"
            "⏳ Duration: Minimum of 20 hours per level\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our Arabic Language Programme is designed to help learners develop\n"
            "strong skills in reading, writing, speaking, and understanding Arabic.\n"
            "Through structured lessons, interactive activities, and guided practice,\n"
            "students gradually build confidence and fluency in the language.\n"
            "The programme focuses on vocabulary development, correct\n"
            "pronunciation, sentence formation, and practical communication skills.\n"
            "Learners are exposed to real-life situations to help them use Arabic\n"
            "effectively in everyday conversations.\n"
            "Suitable for beginners and progressing learners, the course ensures a\n"
            "step-by-step approach to mastering the language in a supportive and\n"
            "engaging environment.\n\n"
            "💰 Course Fee: AED 1220 + VAT per level (includes class fees, registration fees and material fees)\n"
            "Certifications : Educatia Course Completion Certificate (KHDA Certificate available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_arabic" and branch == "dso":
        text = (
            "🌙 *Spoken Arabic Beginner/ Inter/Advanced*\n"
            "📍 Dubai Silicon Oasis\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: All ages\n"
            "⏳ Duration: Minimum of 20 hours per level\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our Arabic Language Programme is designed to help learners develop\n"
            "strong skills in reading, writing, speaking, and understanding Arabic.\n"
            "Through structured lessons, interactive activities, and guided practice,\n"
            "students gradually build confidence and fluency in the language.\n"
            "The programme focuses on vocabulary development, correct\n"
            "pronunciation, sentence formation, and practical communication skills.\n"
            "Learners are exposed to real-life situations to help them use Arabic\n"
            "effectively in everyday conversations.\n"
            "Suitable for beginners and progressing learners, the course ensures a\n"
            "step-by-step approach to mastering the language in a supportive and\n"
            "engaging environment.\n\n"
            "💰 Course Fee: AED 1470 + VAT per level (includes class fees, registration fees and material fees)\n"
            "Certifications : Educatia Course Completion Certificate (KHDA Certificate available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_arabic" and branch == "jadaf":
        text = (
            "🌙 *Spoken Arabic Beginner/ Inter/Advanced*\n"
            "📍 Al Jadaf\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Learn to communicate confidently in Arabic through practical lessons covering speaking, listening, reading, writing, grammar, and vocabulary. The course is ideal for residents, professionals, and students who wish to use Arabic effectively in daily life, work, or social interactions.\n\n"
            "💰 Course Fee: AED 150 + VAT per hour\n"
            "One-Time Registration Fee: AED 150 + VAT\n"
            "🎉 Special Discounts Available on bookings of 20+ sessions.\n"
            "Certifications : Educatia Course Completion Certificate (KHDA Certificate available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_arabic" and branch == "online":
        text = (
            "🌙 *Spoken Arabic Beginner/ Inter/Advanced*\n"
            "🌐 Online Classes\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Learn Arabic confidently through practical sessions designed to develop speaking, listening, vocabulary, pronunciation, and everyday conversation skills. The course is suitable for beginners as well as learners who wish to improve their Arabic communication abilities for personal or professional use.\n\n"
            "📞 For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_ielts" and branch == "ic":
        text = (
            "🎓 *IELTS Academic/General*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: All ages\n"
            "⏳ Duration: 20 hours of instructor-led classes + 10 hours of guided self-practice, which can be completed either at the institute or at the student's convenient location.\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our IELTS Preparation Course is designed to help students and professionals achieve their desired band score in the IELTS General Training and Academic modules. The course provides focused training in Listening, Reading, Writing, and Speaking skills, along with exam strategies, practice tests, and personalized guidance to improve accuracy, confidence, and overall performance.\n\n"
            "💰 Course Fee: AED 1420 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_ielts" and branch == "dso":
        text = (
            "🎓 *IELTS Academic/General*\n"
            "📍 Dubai Silicon Oasis\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: All ages\n"
            "⏳ Duration: 20 hours of instructor-led classes + 10 hours of guided self-practice, which can be completed either at the institute or at the student's convenient location.\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our IELTS Preparation Course is designed to help students and professionals achieve their desired band score in the IELTS General Training and Academic modules. The course provides focused training in Listening, Reading, Writing, and Speaking skills, along with exam strategies, practice tests, and personalized guidance to improve accuracy, confidence, and overall performance.\n\n"
            "💰 Course Fee: AED 1470 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_ielts" and branch == "jadaf":
        text = (
            "🎓 *IELTS Academic/General*\n"
            "📍 Al Jadaf\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Prepare for success in the IELTS examination with comprehensive training in Listening, Reading, Writing, and Speaking. The course includes expert guidance, exam strategies, practice tests, personalised feedback, and time-management techniques to help learners achieve their target band score.\n"
            "💰 Course Fee: AED 150 + VAT per hour\n"
            "One-Time Registration Fee: AED 150 + VAT\n"
            "🎉 Special Discounts Available on bookings of 20+ sessions.\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_ielts" and branch == "online":
        text = (
            "🎓 *IELTS Academic/General*\n"
            "🌐 Online Classes\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Prepare effectively for the IELTS examination with comprehensive training in Listening, Reading, Writing, and Speaking modules. The course includes exam strategies, practice sessions, personalised feedback, and guidance to help learners achieve their desired band score.\n\n"
            "📞 For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_excel" and branch == "ic":
        text = (
            "📊 *Professional Excel Skills for Adults*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: All ages\n"
            "⏳ Duration: Minimum of 20 hours per level\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our Professional Excel Skills Course is designed for adults who want to enhance their efficiency and confidence in using Microsoft Excel for workplace and professional needs. The course covers essential to advanced Excel tools, formulas, data management, and reporting techniques through practical, hands-on exercises.\n\n"
            "💰 Course Fee: AED 1100 + VAT per level (includes class fees, registration fees and material fees)\n"
            "Certifications : Educatia Course Completion Certificate (KHDA Certificate available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_excel" and branch == "dso":
        text = (
            "📊 *Professional Excel Skills for Adults*\n"
            "📍 Dubai Silicon Oasis\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: All ages\n"
            "⏳ Duration: Minimum of 20 hours per level\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our Professional Excel Skills Course is designed for adults who want to enhance their efficiency and confidence in using Microsoft Excel for workplace and professional needs. The course covers essential to advanced Excel tools, formulas, data management, and reporting techniques through practical, hands-on exercises.\n\n"
            "💰 Course Fee: AED 1350 + VAT per level (includes class fees, registration fees and material fees)\n"
            "Certifications : Educatia Course Completion Certificate (KHDA Certificate available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_excel" and branch == "jadaf":
        text = (
            "📊 *Professional Excel Skills for Adults*\n"
            "📍 Al Jadaf\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Master Microsoft Excel from the fundamentals to advanced features used in the workplace. Learn formulas, functions, data analysis, charts, PivotTables, conditional formatting, data validation, and productivity tools to confidently manage and analyse data for business and professional use.\n\n"
            "💰 Course Fee: AED 150 + VAT per hour\n"
            "One-Time Registration Fee: AED 150 + VAT\n"
            "🎉 Special Discounts Available on bookings of 20+ sessions.\n"
            "Certifications : Educatia Course Completion Certificate (KHDA Certificate available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_excel" and branch == "online":
        text = (
            "📊 *Professional Excel Skills for Adults*\n"
            "🌐 Online Classes\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Master Microsoft Excel skills required for modern workplaces, from basic functions to advanced data management techniques. Learn formulas, functions, charts, PivotTables, data analysis, and productivity tools to improve efficiency and confidence in handling professional tasks.\n\n"
            "📞 For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_python" and branch == "ic":
        text = (
            "💻 *Python coding Language*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: All ages\n"
            "⏳ Duration: 20 hours per level\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our Python Coding Course for Adults is designed to introduce learners to programming concepts and practical coding skills. Students learn Python fundamentals, problem-solving techniques, data handling, and application development through hands-on exercises and real-world examples. The course helps learners build confidence in coding and explore opportunities in automation, data analysis, and technology-driven fields.\n\n"
            "💰 Course Fee: AED 1100 + VAT per level (includes class fees, registration fees and material fees)\n"
            "Certifications : Educatia Course Completion Certificate (KHDA Certificate available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_python" and branch == "dso":
        text = (
            "💻 *Python coding Language*\n"
            "📍 Dubai Silicon Oasis\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Age Group: All ages\n"
            "⏳ Duration: 20 hours per level\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our Python Coding Course for Adults is designed to introduce learners to programming concepts and practical coding skills. Students learn Python fundamentals, problem-solving techniques, data handling, and application development through hands-on exercises and real-world examples. The course helps learners build confidence in coding and explore opportunities in automation, data analysis, and technology-driven fields.\n\n"
            "💰 Course Fee: AED 1350 + VAT per level (includes class fees, registration fees and material fees)\n"
            "Certifications : Educatia Course Completion Certificate (KHDA Certificate available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_python" and branch == "jadaf":
        text = (
            "💻 *Python coding Language*\n"
            "📍 Al Jadaf\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Build a strong foundation in Python programming through hands-on projects and practical coding exercises. Learn programming concepts such as variables, loops, functions, data structures, file handling, and problem-solving techniques while developing applications and automation skills.\n\n"
            "💰 Course Fee: AED 150 + VAT per hour\n"
            "One-Time Registration Fee: AED 150 + VAT\n"
            "🎉 Special Discounts Available on bookings of 20+ sessions.\n"
            "Certifications : Educatia Course Completion Certificate (KHDA Certificate available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_python" and branch == "online":
        text = (
            "💻 *Python coding Language*\n"
            "🌐 Online Classes\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Learn Python programming through practical, hands-on training designed for beginners and professionals. Develop skills in programming logic, problem-solving, automation, data handling, and application development through real-world coding exercises and projects.\n\n"
            "📞 For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_grw" and branch == "ic":
        text = (
            "💼 *Get Ready To Work (MS Office + AI training)*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⏳ Duration: 20 hours per level\n"
            "📍 Location: International City\n"
            "📖 Course Description\n"
            "Our Get Ready to Work Programme is designed to equip learners with\n"
            "essential computer and digital skills required in today's professional\n"
            "environment. The course focuses on practical, hands-on training that\n"
            "helps students become confident in using workplace tools, improving\n"
            "productivity, and adapting to modern, technology-driven jobs.\n"
            "Through structured sessions, learners gain experience in Microsoft Office\n"
            "tools, AI applications, email communication, and essential digital skills\n"
            "needed in offices and professional settings.\n"
            "💰 Course Fee: AED 1100 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_grw" and branch == "dso":
        text = (
            "💼 *Get Ready To Work (MS Office + AI training)*\n"
            "📍 Dubai Silicon Oasis\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⏳ Duration: 20 hours per level\n"
            "📍 Location: Dubai Silicon Oasis\n"
            "📖 Course Description\n"
            "Our Get Ready to Work Programme is designed to equip learners with\n"
            "essential computer and digital skills required in today's professional\n"
            "environment. The course focuses on practical, hands-on training that\n"
            "helps students become confident in using workplace tools, improving\n"
            "productivity, and adapting to modern, technology-driven jobs.\n"
            "Through structured sessions, learners gain experience in Microsoft Office\n"
            "tools, AI applications, email communication, and essential digital skills\n"
            "needed in offices and professional settings.\n"
            "💰 Course Fee: AED 1350 + VAT per level (includes class fees, registration fees and material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_grw" and branch == "jadaf":
        text = (
            "💼 *Get Ready To Work (MS Office + AI training)*\n"
            "📍 Al Jadaf\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Equip yourself with essential workplace skills through comprehensive training in Microsoft Word, Excel, PowerPoint, Outlook, and modern AI tools. Learn document creation, spreadsheets, presentations, email management, AI-powered productivity, prompt writing, and digital workplace best practices to become job-ready for today's professional environment.\n"
            "💰 Course Fee: AED 150 + VAT per hour\n"
            "One-Time Registration Fee: AED 150 + VAT\n"
            "🎉 Special Discounts Available on bookings of 20+ sessions.\n"
            "Certifications : Educatia Course Completion Certificate (KHDA Certificate available upon request)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "a_grw" and branch == "online":
        text = (
            "💼 *Get Ready To Work (MS Office + AI training)*\n"
            "🌐 Online Classes\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Develop essential workplace skills through practical training in Microsoft Office applications and modern AI tools. Learn document creation, spreadsheets, presentations, professional communication, AI-powered productivity tools, and digital skills required to succeed in today's workplace.\n\n"
            "📞 For course charges and enrolment details, kindly contact our Admissions Team:\n"
            "*+971 50 460 5940 / +971 52 870 5940*\n\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return


        course_names = {
        "as_lang": "Languages — Academic Support",
        "as_math": "Mathematics — Academic Support",
        "as_science": "Science — Academic Support",
        "as_commerce": "Commerce & Accounting",
        "cs_abacus": "Abacus",
        "cs_vedic": "Vedic Maths",
        "cs_coding": "Coding for Kids",
        "cs_robotics": "Robotics",
        "cs_handwriting": "Handwriting",
        "cs_creative": "Creative Skills",
        "cs_science_exp": "Live Science Experiments",
        "cs_msoffice": "MS Office for Kids",
        "lt_eng_beg": "English Communication — Beginner",
        "lt_eng_int": "English Communication — Intermediate",
        "lt_phonics": "Phonics Classes",
        "lt_pubspeak": "Public Speaking & Creative Writing",
        "lt_arabic_rw": "Arabic Reading & Writing",
        "lt_hindi_rw": "Hindi Reading & Writing",
        "lt_french_rw": "French Reading & Writing",
        "a_eng_basic": "English — Beginner",
        "a_eng_adv": "English — Intermediate+",
        "a_ielts": "IELTS",
        "a_excel": "Professional Excel",
        "a_python": "Python Coding",
        "a_grw": "Get Ready To Work",
        "a_msoffice": "MS Office",
        "a_word": "MS Word",
        "a_french": "French",
        "a_abacus": "Abacus",
        "c_ielts": "IELTS",
    }
    cname = course_names.get(course_id, course_id)
    text = (
        f"📚 *{cname} — {bname}*\n\n"
        f"We offer {cname} at our {bname} branch.\n\n"
        f"📍 Location: {bname}\n\n"
        "For detailed pricing, batch timings, and enrollment:\n\n"
        "📞 *Contact: +971 50 460 5940*\n"
        "Our team will share the schedule and help you register!\n\n"
        "Reply *menu* to go back 🔙"
    )
    send_text(to, text)


# =============================================
# FLOW: BRANCH INFO
# =============================================

def show_branch_info(to):
    set_session(to, {"step": "viewing", "category": "branches"})
    text = (
        "📍 *Our Branches*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🏫 *Branch 1 — International City*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "V17 Shop No 4, Russia Cluster\n"
        "International City, Dubai\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🏫 *Branch 2 — Dubai Silicon Oasis*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Park Avenue 607\n"
        "Dubai Silicon Oasis\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🏫 *Branch 3 — Al Jadaf*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Nastaran Building, Next to Riah Tower\n"
        "Al Jadaf – Jaddaf Waterfront, Dubai\n"
        "Office Number 503\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🕘 *Timings:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Monday – Thursday: 10:00 AM – 1:00 PM\n"
        "• Friday: 10:00 AM – 12:00 PM\n\n"
        "📞 *Contact:* +971 50 460 5940\n\n"
        "Reply *menu* to go back 🔙"
    )
    send_text(to, text)


# =============================================
# FLOW: ADMISSION PROCESS
# =============================================

def show_admission(to):
    set_session(to, {"step": "viewing", "category": "admission"})
    text = (
        "📝 *Admission Process*\n\n"
        "Getting started at Educatia is simple!\n\n"
        "1️⃣ Choose your course & preferred branch\n"
        "2️⃣ Registration link will be sent to you\n"
        "3️⃣ Receive your invoice\n"
        "4️⃣ Complete payment\n"
        "5️⃣ Start your classes! 🎉\n\n"
        "📞 *Contact us to get started:*\n"
        "*+971 50 460 5940*\n\n"
        "Our team will guide you through the entire process.\n\n"
        "Reply *menu* to go back 🔙"
    )
    send_text(to, text)


# =============================================
# FLOW: DAY CARE
# =============================================

def show_daycare(to):
    set_session(to, {"step": "viewing", "category": "daycare"})
    text = (
        "👶 *Day Care at Educatia*\n\n"
        "We provide a safe and nurturing environment for your little ones.\n\n"
        "For details on availability, timings, and fees, please contact our team:\n\n"
        "📞 *+971 50 460 5940*\n\n"
        "A staff member will assist you with all the information you need!\n\n"
        "Reply *menu* to go back 🔙"
    )
    send_text(to, text)


# =============================================
# FLOW: TALK TO TEAM
# =============================================

def show_contact_team(to):
    set_session(to, {"step": "viewing", "category": "team"})
    text = (
        "👩‍💼 *Connect with Our Team*\n\n"
        "We're here to help! You can reach us at:\n\n"
        "📞 Call / WhatsApp: *+971 50 460 5940*\n\n"
        "A staff member will get back to you shortly! 😊\n\n"
        "Reply *menu* to go back 🔙"
    )
    send_text(to, text)


# =============================================
# FLOW: OTHER ENQUIRY
# =============================================

def show_other(to):
    set_session(to, {"step": "awaiting_other"})
    text = (
        "💬 *Other Enquiry*\n\n"
        "Please type your question and our team will get back to you.\n\n"
        "Or contact us directly at:\n"
        "📞 *+971 50 460 5940*\n\n"
        "Reply *menu* to go back 🔙"
    )
    send_text(to, text)


# =============================================
# FAQ HANDLER
# =============================================

def handle_faq(to, msg):
    """Handle frequently asked questions. Returns True if handled."""

    # Safety
    if any(w in msg for w in ["safe", "safety", "secure", "security"]):
        send_text(
            to,
            "🛡️ *Safety at Educatia*\n\n"
            "Absolutely! The safety of every child is our top priority.\n\n"
            "✅ Trained & verified staff\n"
            "✅ Secure premises with CCTV\n"
            "✅ Safe and joyful learning environment\n"
            "✅ Small batch sizes for attention\n\n"
            "Your child is in great hands! 😊\n\n"
            "📞 Contact: +971 50 460 5940\n"
            "Reply *menu* to go back 🔙",
        )
        return True

    # Transportation
    if any(w in msg for w in ["transport", "bus", "pick up", "pickup", "drop"]):
        send_text(
            to,
            "🚌 *Transportation*\n\n"
            "Yes, transportation facilities are available!\n"
            "Additional charges apply based on your location.\n\n"
            "📞 Contact us for transport details & pricing:\n"
            "*+971 50 460 5940*\n\n"
            "Reply *menu* to go back 🔙",
        )
        return True

    # Fees / Cost (generic)
    if any(w in msg for w in ["fee", "fees", "cost", "price", "pricing", "how much", "charges"]):
        send_text(
            to,
            "💰 *Fee Enquiry*\n\n"
            "Fees vary by course and branch. Let me help you find the right info!\n\n"
            "Reply *menu* to browse our programs, or tell me which course you're interested in.\n\n"
            "📞 Or call: *+971 50 460 5940*",
        )
        return True

    # Timings / Schedule
    if any(w in msg for w in ["timing", "timings", "time", "schedule", "when", "hours"]):
        send_text(
            to,
            "🕘 *Our Timings*\n\n"
            "• Monday – Thursday: 10:00 AM – 1:00 PM\n"
            "• Friday: 10:00 AM – 12:00 PM\n\n"
            "Class schedules vary by course. Contact us for specific batch timings:\n"
            "📞 *+971 50 460 5940*\n\n"
            "Reply *menu* to explore our courses 🔙",
        )
        return True

    # Location
    if any(w in msg for w in ["location", "address", "where", "directions", "map"]):
        show_branch_info(to)
        return True

    return False


# =============================================
# SESSION-AWARE NUMBER INPUT HANDLER
# =============================================

BRANCH_MAP_3 = {"1": "ic", "2": "dso", "3": "jadaf"}
BRANCH_MAP_4 = {"1": "ic", "2": "dso", "3": "jadaf", "4": "online"}
MAIN_MENU_MAP = {
    "1": "cat_acadsupport",
    "2": "cat_childskill",
    "3": "cat_language",
    "4": "cat_adult",
    "5": "cat_daycare",
    "6": "cat_branches",
    "7": "cat_admission",
    "8": "cat_team",
}


def handle_number_input(from_number, num, session):
    """Route a number based on current session step. Returns True if handled."""
    step = session.get("step", "new")
    category = session.get("category", "")
    branch = session.get("branch", "")

    # ── Branch selection (4 branches: Academic/Adult/new categories) ──
    if step == "select_branch" and category in ("academic", "adult", "academic_support", "child_skill", "language"):
        b = BRANCH_MAP_4.get(num)
        if b:
            if category in ("academic_support", "child_skill", "language"):
                show_category_courses(from_number, b, category)
            elif category == "academic":
                set_session(from_number, {
                    "step": "select_course",
                    "category": "academic",
                    "branch": b,
                })
                show_academic_courses(from_number, b)
            else:
                set_session(from_number, {
                    "step": "select_course",
                    "category": "adult",
                    "branch": b,
                })
                show_adult_courses(from_number, b)
            return True

    # ── Course selection (numbered list) ──
    if step == "select_course":
        COURSE_DICT_MAP = {
            "academic_support": ACADEMIC_SUPPORT_COURSES,
            "child_skill": CHILD_SKILL_COURSES,
            "language": LANGUAGE_COURSES,
            "adult": ADULT_COURSES,
        }
        course_dict = COURSE_DICT_MAP.get(category, ADULT_COURSES)
        courses = course_dict.get(branch, [])
        try:
            idx = int(num) - 1
            if 0 <= idx < len(courses):
                course_id = courses[idx]["id"]
                show_course_detail(from_number, course_id, branch, category)
                return True
        except (ValueError, TypeError):
            pass

    # ── Default: main menu numbers ──
    menu_id = MAIN_MENU_MAP.get(num)
    if menu_id:
        handle_interactive(from_number, menu_id, {"step": "main_menu"})
        return True

    return False


# =============================================
# MAIN MESSAGE HANDLER
# =============================================

def handle_message(from_number, msg_text=None, interactive_id=None):
    session = get_session(from_number)

    # ── Interactive responses (button / list clicks) ──
    if interactive_id:
        handle_interactive(from_number, interactive_id, session)
        return

    # ── Text messages ──
    if not msg_text:
        return
    msg = msg_text.strip().lower()

    # Greetings → main menu
    if msg in GREETINGS:
        show_main_menu(from_number)
        return

    # Back → main menu
    if msg in ["back", "0"]:
        show_main_menu(from_number)
        return

    # Thank you
    if any(w in msg for w in ["thank", "thanks", "thankyou", "shukran"]):
        send_text(
            from_number,
            "You're welcome! 😊\n\nReply *menu* anytime if you need anything else.\n"
            "📞 Contact: +971 50 460 5940",
        )
        return

    # ── Session-aware number shortcuts ──
    if msg in ["1", "2", "3", "4", "5", "6", "7", "8"]:
        if handle_number_input(from_number, msg, session):
            return

    # ── Keyword shortcuts ──
    if "academ" in msg or "children" in msg or "kids" in msg or "child" in msg:
        show_branch_list(from_number, "academic")
        return
    if "adult" in msg:
        show_branch_list(from_number, "adult")
        return
    if "day care" in msg or "daycare" in msg:
        show_daycare(from_number)
        return
    if "branch" in msg:
        show_branch_info(from_number)
        return
    if "admission" in msg or "register" in msg or "enroll" in msg or "enrol" in msg:
        show_admission(from_number)
        return
    if "team" in msg or "human" in msg or "agent" in msg or "speak" in msg or "talk" in msg:
        show_contact_team(from_number)
        return

    # Course-specific keywords
    if "english" in msg:
        send_text(from_number, "📚 We offer English courses at IC & DSO!\n\nReply *3* for children's courses or *4* for adult courses to see details and pricing.")
        return
    if "arabic" in msg:
        send_text(from_number, "📚 We offer Arabic courses at IC, DSO & Online!\n\nReply *3* for children's courses or *4* for adult courses to see details and pricing.")
        return
    if "ielts" in msg:
        send_text(from_number, "📚 We offer IELTS preparation at all branches + online!\n\nReply *3* for children or *4* for adults to find your branch.")
        return
    if "math" in msg or "science" in msg:
        send_text(from_number, "📚 We offer Mathematics & Science courses for children!\n\nReply *3* to see children's courses by branch.")
        return
    if "robot" in msg or "python" in msg or "coding" in msg:
        show_branch_list(from_number, "child_skill")
        return
    if "excel" in msg or "office" in msg or "word" in msg:
        send_text(from_number, "📚 We offer MS Office / Excel / Word courses!\n\nReply *3* for kids or *4* for adults to see courses by branch.")
        return

    # ── FAQ handler ──
    if handle_faq(from_number, msg):
        return

    # ── Fallback ──
    show_main_menu(from_number)


# =============================================
# INTERACTIVE RESPONSE HANDLER
# =============================================

def handle_interactive(from_number, item_id, session):
    """Route button / list clicks based on ID."""

    # ── Main menu category selections ──
    if item_id == "cat_acadsupport":
        show_branch_list(from_number, "academic_support")
        return
    if item_id == "cat_childskill":
        show_branch_list(from_number, "child_skill")
        return
    if item_id == "cat_language":
        show_branch_list(from_number, "language")
        return
    if item_id == "cat_adult":
        show_branch_list(from_number, "adult")
        return
    if item_id == "cat_daycare":
        show_daycare(from_number)
        return
    if item_id == "cat_branches":
        show_branch_info(from_number)
        return
    if item_id == "cat_admission":
        show_admission(from_number)
        return
    if item_id == "cat_team":
        show_contact_team(from_number)
        return
    if item_id == "cat_other":
        show_other(from_number)
        return

    # ── Branch selections ──
    if item_id.startswith("branch_"):
        branch = item_id.replace("branch_", "")
        category = session.get("category", "")

        if category in ("academic_support", "child_skill", "language"):
            show_category_courses(from_number, branch, category)
        elif category == "adult":
            set_session(from_number, {
                "step": "select_course",
                "category": "adult",
                "branch": branch,
            })
            show_adult_courses(from_number, branch)
        else:
            show_main_menu(from_number)
        return

    # ── Course selections ──
    if any(item_id.startswith(p) for p in ("c_", "a_", "as_", "cs_", "lt_")):
        branch = session.get("branch", "ic")
        category = session.get("category", "academic_support")
        show_course_detail(from_number, item_id, branch, category)
        return

    # Fallback
    show_main_menu(from_number)


# =============================================
# WEBHOOK ENDPOINTS
# =============================================

@app.route("/", methods=["GET"])
def health():
    return "Educatia Bot is running! 🎓", 200


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Webhook verified!")
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:
            message = value["messages"][0]
            from_number = message["from"]

            # Notify Ma'am if this is a first-time user
            if from_number not in notified_users and from_number != MAAM_PHONE_NUMBER:
                notified_users.add(from_number)
                notify_maam_new_contact(from_number)

            if message["type"] == "text":
                msg_text = message["text"]["body"]
                handle_message(from_number, msg_text=msg_text)

            elif message["type"] == "interactive":
                interactive = message["interactive"]
                if interactive["type"] == "list_reply":
                    item_id = interactive["list_reply"]["id"]
                    handle_message(from_number, interactive_id=item_id)
                elif interactive["type"] == "button_reply":
                    btn_id = interactive["button_reply"]["id"]
                    handle_message(from_number, interactive_id=btn_id)

    except Exception as e:
        logger.error(f"Webhook error: {e}")

    return "OK", 200


# =============================================
# RUN
# =============================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
