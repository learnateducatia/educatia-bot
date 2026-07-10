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

def show_branch_buttons(to, category):
    """3-button branch picker (Summer Camp / STEM Camp — no online)."""
    set_session(to, {"step": "select_branch", "category": category})

    if category == "summer_camp":
        label = "☀️ *Summer Camp 2026*"
    else:
        label = "🔬 *STEM Camp 2026*"

    body = (
        f"{label}\n\n"
        "Available at all three branches!\n"
        "Which branch? Tap below or reply:\n\n"
        "1️⃣ International City\n"
        "2️⃣ Dubai Silicon Oasis\n"
        "3️⃣ Al Jadaf"
    )

    send_buttons(
        to,
        body,
        [
            {"id": "branch_ic", "title": "International City"},
            {"id": "branch_dso", "title": "Dubai Silicon Oasis"},
            {"id": "branch_jadaf", "title": "Al Jadaf"},
        ],
    )


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
# FLOW: SUMMER CAMP (per branch)
# =============================================

def show_summer_camp(to, branch):
    set_session(to, {"step": "viewing", "category": "summer_camp", "branch": branch})

    common_activities = (
        "🎨 *Activities include:*\n"
        "Zumba, yoga, day outing, science experiments, cooking fun, "
        "carnival, creative crafts, games, movie time and much more!\n\n"
        "🌞 A safe and joyful environment where kids learn, explore, and grow!\n\n"
        "⭐ *Early Bird Discount: AED 100 off!*\n\n"
        "🌟 *Limited seats available – Enroll now!*\n"
        "📞 Contact: +971 50 460 5940\n\n"
        "Reply *menu* to go back 🔙"
    )

    if branch == "ic":
        text = (
            "🌟 *Educatia's Summer Camp 2026 — International City* 🌟\n\n"
            "📅 Duratio: July 6th – August 28th, 2026\n"
            "👧🧒 Age Group: 5 – 16 Years\n"
            "🗓 Days: Monday to Friday\n"
            "🏫 Mode: Physical Camp\n\n"
            "🕘 *Timings:*\n"
            "• Monday to Friday: 10:00 AM – 1:00 PM\n\n"
            "💰 *Fees:*\n"
            "• Per Week: AED 350 + VAT\n"
            "• 4 Weeks: AED 1,200 + VAT (Incl. Materials & Day Trip)\n"
            "• 6 Weeks: AED 1,700 + VAT (Incl. Materials & Day Trip)\n"
            "• 8 Weeks: AED 2,200 + VAT (Incl. Materials & Day Trip)\n"
            "• 🚌 Transportation: Additional charges apply\n\n"
            "📍 *Location:* V17 Shop No 4, Russia Cluster, International City, Dubai\n\n"
            + common_activities
        )
    elif branch == "dso":
        text = (
            "🌟 *Educatia's Summer Camp 2026 — Dubai Silicon Oasis* 🌟\n\n"
            "📅 Duration: July 6th – August 28th, 2026\n"
            "👧🧒 Age Group: 5 – 16 Years\n"
            "🗓 Days: Monday to Friday\n"
            "🏫 Mode: Physical Camp\n\n"
            "🕘 *Timings:*\n"
            "• Monday to Friday: 10:00 AM – 1:00 PM\n\n"
            "💰 *Fees:*\n"
            "• Per Week: AED 400 + VAT\n"
            "• 4 Weeks: AED 1,400 + VAT (Incl. Materials & Day Trip)\n"
            "• 6 Weeks: AED 2,000 + VAT (Incl. Materials & Day Trip)\n"
            "• 8 Weeks: AED 2,600 + VAT (Incl. Materials & Day Trip)\n"
            "• 🚌 Transportation: Additional charges apply\n\n"
            "📍 *Location:* Park Avenue 607, Dubai Silicon Oasis\n\n"
            + common_activities
        )
    elif branch == "jadaf":
        text = (
            "🌟 *Educatia's Summer Camp 2026 — Al Jadaf* 🌟\n\n"
            "📅 Duration: July 6th – August 28th, 2026\n"
            "👧🧒 Age Group: 5 – 16 Years\n"
            "🗓 Days: Monday to Friday\n"
            "🏫 Mode: Physical Camp\n\n"
            "🕘 *Timings:*\n"
            "• Monday to Friday: 10:00 AM – 1:00 PM\n\n"
            "💰 *Fees:*\n"
            "• Per Week: AED 500 + VAT\n"
            "• 4 Weeks: AED 1,500 + VAT (Incl. Materials & Day Trip)\n"
            "• 6 Weeks: AED 2,200 + VAT (Incl. Materials & Day Trip)\n"
            "• 8 Weeks: AED 2,800 + VAT (Incl. Materials & Day Trip)\n\n"
            "📍 *Location:* Nastaran Building, Next to Riah Tower, Al Jadaf – Jaddaf Waterfront, Dubai – Office 503\n\n"
            + common_activities
        )
    else:
        text = "Summer Camp is only available at our physical branches. Reply *menu* to go back 🔙"

    send_text(to, text)


# =============================================
# FLOW: STEM CAMP — AGE SELECTION
# =============================================

def show_stem_age_selection(to, branch):
    set_session(to, {"step": "select_age", "category": "stem_camp", "branch": branch})
    send_buttons(
        to,
        (
            "🔬 *STEM Camp 2026*\n\n"
            "We have two age-group programs.\n"
            "Tap below or reply:\n\n"
            "1️⃣ Ages 8–11 (STEM Explorers)\n"
            "2️⃣ Ages 12–17 (Teens)"
        ),
        [
            {"id": "age_8_11", "title": "Ages 8–11"},
            {"id": "age_12_17", "title": "Ages 12–17"},
        ],
    )


# =============================================
# FLOW: STEM CAMP JUNIOR (8–11) per branch
# =============================================

def show_stem_junior(to, branch):
    set_session(to, {"step": "viewing", "category": "stem_junior", "branch": branch})

    common_desc = (
        "👩‍🔬 Hands-on experiments\n"
        "🤖 Beginner-friendly robotics\n"
        "🧩 Cool projects & team challenges\n"
        "🌟 No experience needed – just curiosity!\n\n"
        "📖 *Curriculum:*\n"
        "• Micro:bit and Scratch coding (10 classes)\n"
        "• Arduino programming (hardware & software)\n"
        "• Introduction to Data Science, AI & Machine Learning\n\n"
    )

    common_footer = (
        "🔗 *Register now & spark a love for innovation!*\n"
        "📞 Contact: +971 50 460 5940\n\n"
        "Reply *menu* to go back 🔙"
    )

    if branch == "ic":
        text = (
            "🔬 *STEM Camp — STEM Explorers (Ages 8–11)*\n"
            "📍 *International City*\n\n"
            + common_desc
            + "🗓 Start Date: 6th July 2026\n"
            "🕰 Timings:\n"
            "• Mon–Thu: 10:00 AM – 1:00 PM\n"
            "• Friday: 10:00 AM – 12:00 PM\n\n"
            "💰 *Fees:*\n"
            "• 1 Week: AED 350 + VAT\n"
            "• 4 Weeks: AED 1,200 + VAT\n"
            "📦 Kit Charges: AED 250 + VAT\n\n"
            "📍 V17 Shop No 4, Russia Cluster, International City, Dubai\n\n"
            + common_footer
        )
    elif branch == "dso":
        text = (
            "🔬 *STEM Camp — STEM Explorers (Ages 8–11)*\n"
            "📍 *Dubai Silicon Oasis*\n\n"
            + common_desc
            + "🗓 Start Date: 6th July 2026\n"
            "🕰 Timings: 2:00 PM – 5:00 PM\n\n"
            "💰 *Fees:*\n"
            "• 1 Week: AED 400 + VAT\n"
            "• 4 Weeks: AED 1,400 + VAT\n"
            "📦 Kit Charges: AED 250 + VAT\n\n"
            "📍 Park Avenue 607, Dubai Silicon Oasis\n\n"
            + common_footer
        )
    elif branch == "jadaf":
        text = (
            "🔬 *STEM Camp — STEM Explorers (Ages 8–11)*\n"
            "📍 *Al Jadaf*\n\n"
            + common_desc
            + "🗓 Start Date: 6th July 2026\n\n"
            "💰 *Fees:*\n"
            "• 1 Week: AED 500 + VAT\n"
            "• 4 Weeks: AED 1,600 + VAT\n"
            "📦 Kit Charges: AED 300 + VAT\n\n"
            "📍 Nastaran Building, Next to Riah Tower, Al Jadaf, Dubai – Office 503\n\n"
            + common_footer
        )
    else:
        text = "STEM Camp is only available at our physical branches. Reply *menu* to go back 🔙"

    send_text(to, text)


# =============================================
# FLOW: STEM CAMP TEENS (12–17) per branch
# =============================================

def show_stem_teen(to, branch):
    set_session(to, {"step": "viewing", "category": "stem_teen", "branch": branch})

    common_desc = (
        "Get ready to dive into a world of innovation, creativity, and discovery! "
        "Our STEM camp is the ultimate playground for curious minds who love to explore "
        "how things work and dream of building what's next.\n\n"
        "📖 *Curriculum:*\n"
        "• Arduino programming (without & with sensors)\n"
        "• Obstacle avoidance & Logic Gates\n"
        "• IoT projects (for advanced learners)\n"
        "• AI & Machine Learning introduction\n\n"
    )

    common_footer = (
        "📦 *Optional Kit Charges:*\n"
        "• Arduino Starter Kit: AED 200\n"
        "• Sensor Kit: AED 100\n"
        "• Chassis Kit: AED 100\n\n"
        "🎁 *Refer a friend and get more discount!*\n\n"
        "📞 Contact: +971 50 460 5940\n\n"
        "Reply *menu* to go back 🔙"
    )

    if branch == "ic":
        text = (
            "💫 *STEM Camp for Teens (Ages 12–17)*\n"
            "📍 *International City*\n\n"
            + common_desc
            + "🗓 Start Date: 6th July 2026\n"
            "🕰 Timings:\n"
            "• Mon–Thu: 10:00 AM – 1:00 PM\n"
            "• Friday: 10:00 AM – 12:00 PM\n\n"
            "💰 *Fees:*\n"
            "• 1 Week: AED 500 + VAT\n"
            "• 4 Weeks: AED 1,800 + VAT\n\n"
            "📍 V17 Shop No 4, Russia Cluster, International City, Dubai\n\n"
            + common_footer
        )
    elif branch == "dso":
        text = (
            "💫 *STEM Camp for Teens (Ages 12–17)*\n"
            "📍 *Dubai Silicon Oasis*\n\n"
            + common_desc
            + "🗓 Start Date: 6th July 2026\n"
            "🕰 Timings: 2:00 PM – 5:00 PM\n\n"
            "💰 *Fees:*\n"
            "• 1 Week: AED 500 + VAT\n"
            "• 4 Weeks: AED 1,800 + VAT\n\n"
            "📍 Park Avenue 607, Dubai Silicon Oasis\n\n"
            + common_footer
        )
    elif branch == "jadaf":
        text = (
            "💫 *STEM Camp for Teens (Ages 12–17)*\n"
            "📍 *Al Jadaf*\n\n"
            + common_desc
            + "🗓 Start Date: 6th July 2026\n\n"
            "💰 *Fees:*\n"
            "• 1 Week: AED 600 + VAT\n"
            "• 4 Weeks: AED 2,200 + VAT\n\n"
            "📍 Nastaran Building, Next to Riah Tower, Al Jadaf, Dubai – Office 503\n\n"
            + common_footer
        )
    else:
        text = "STEM Camp is only available at our physical branches. Reply *menu* to go back 🔙"

    send_text(to, text)


# =============================================
# FLOW: ACADEMIC CLASSES (Children) per branch
# =============================================

# ── Academic Support (all curriculums & subjects) ──
ACADEMIC_SUPPORT_COURSES = {
    "ic": [
        {"id": "as_lang", "title": "Languages", "description": "Arabic/French/Hindi/English"},
        {"id": "as_math", "title": "Mathematics", "description": "Beginner / Inter / Advanced"},
        {"id": "as_science", "title": "Science", "description": "Physics / Chemistry / Biology"},
        {"id": "as_commerce", "title": "Commerce & Accounting", "description": "Accounts/BST/Economics"},
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
        {"id": "cs_coding", "title": "Coding for Kids", "description": "Scratch/Python/App Dev"},
        {"id": "cs_robotics", "title": "Robotics", "description": "Beginner / Inter / Advanced"},
        {"id": "cs_handwriting", "title": "Handwriting", "description": "Beautiful writing skills"},
        {"id": "cs_creative", "title": "Creative Skills", "description": "Art & Craft sessions"},
        {"id": "cs_science_exp", "title": "Live Science Experiments", "description": "Ages 10+"},
        {"id": "cs_msoffice", "title": "MS Office for Kids", "description": "Word, Excel, PowerPoint"},
    ],
    "dso": [
        {"id": "cs_abacus", "title": "Abacus", "description": "Mental arithmetic"},
        {"id": "cs_vedic", "title": "Vedic Maths", "description": "Fast calculations"},
        {"id": "cs_coding", "title": "Coding for Kids", "description": "Scratch/Python/App Dev"},
        {"id": "cs_robotics", "title": "Robotics", "description": "Beginner / Inter / Advanced"},
        {"id": "cs_handwriting", "title": "Handwriting", "description": "Beautiful writing"},
        {"id": "cs_creative", "title": "Creative Skills", "description": "Art & Craft"},
        {"id": "cs_science_exp", "title": "Live Science Experiments", "description": "Hands-on science"},
        {"id": "cs_msoffice", "title": "MS Office for Kids", "description": "Word, Excel, PowerPoint"},
    ],
    "jadaf": [
        {"id": "cs_abacus", "title": "Abacus", "description": "Mental arithmetic"},
        {"id": "cs_vedic", "title": "Vedic Maths", "description": "Fast calculations"},
        {"id": "cs_coding", "title": "Coding for Kids", "description": "Scratch/Python/App Dev"},
        {"id": "cs_robotics", "title": "Robotics", "description": "Beginner / Inter / Advanced"},
        {"id": "cs_msoffice", "title": "MS Office for Kids", "description": "Word, Excel, PowerPoint"},
    ],
    "online": [
        {"id": "cs_abacus", "title": "Abacus", "description": "Mental arithmetic"},
        {"id": "cs_vedic", "title": "Vedic Maths", "description": "Fast calculations"},
        {"id": "cs_coding", "title": "Coding for Kids", "description": "Scratch/Python/App Dev"},
        {"id": "cs_robotics", "title": "Robotics", "description": "Beginner / Inter / Advanced"},
        {"id": "cs_handwriting", "title": "Handwriting", "description": "Beautiful writing"},
        {"id": "cs_creative", "title": "Creative Skills", "description": "Art & Craft"},
        {"id": "cs_msoffice", "title": "MS Office for Kids", "description": "Word, Excel, PowerPoint"},
    ],
}

# ── Language Training ──
LANGUAGE_COURSES = {
    "ic": [
        {"id": "lt_eng_beg", "title": "English Comm - Beginner", "description": "Ages 5+, 36 hrs/level"},
        {"id": "lt_eng_int", "title": "English Comm - Inter", "description": "Ages 8+, 24 hrs/level"},
        {"id": "lt_phonics", "title": "Phonics Classes", "description": "Ages 5+, 36 hrs/level"},
        {"id": "lt_pubspeak", "title": "Public Speaking", "description": "Ages 8+, 16 hrs/level"},
        {"id": "lt_arabic_rw", "title": "Arabic Reading & Writing", "description": "Ages 6+"},
        {"id": "lt_hindi_rw", "title": "Hindi Reading & Writing", "description": "Ages 6+"},
        {"id": "lt_french_rw", "title": "French Reading & Writing", "description": "Ages 6+"},
    ],
    "dso": [
        {"id": "lt_eng_beg", "title": "English Comm - Beginner", "description": "Foundation English"},
        {"id": "lt_eng_int", "title": "English Comm - Inter", "description": "Intermediate English"},
        {"id": "lt_pubspeak", "title": "Public Speaking", "description": "Confident communication"},
        {"id": "lt_arabic_rw", "title": "Arabic Reading & Writing", "description": "Arabic skills"},
        {"id": "lt_hindi_rw", "title": "Hindi Reading & Writing", "description": "Hindi skills"},
        {"id": "lt_french_rw", "title": "French Reading & Writing", "description": "French skills"},
    ],
    "jadaf": [
        {"id": "lt_eng_beg", "title": "English Comm - Beginner", "description": "Foundation English"},
        {"id": "lt_eng_int", "title": "English Comm - Inter", "description": "Intermediate English"},
        {"id": "lt_pubspeak", "title": "Public Speaking", "description": "Confident communication"},
        {"id": "lt_arabic_rw", "title": "Arabic Reading & Writing", "description": "Arabic skills"},
        {"id": "lt_hindi_rw", "title": "Hindi Reading & Writing", "description": "Hindi skills"},
        {"id": "lt_french_rw", "title": "French Reading & Writing", "description": "French skills"},
    ],
    "online": [
        {"id": "lt_eng_beg", "title": "English Comm - Beginner", "description": "Foundation English"},
        {"id": "lt_eng_int", "title": "English Comm - Inter", "description": "Intermediate English"},
        {"id": "lt_pubspeak", "title": "Public Speaking", "description": "Confident communication"},
        {"id": "lt_arabic_rw", "title": "Arabic Reading & Writing", "description": "Arabic skills"},
        {"id": "lt_hindi_rw", "title": "Hindi Reading & Writing", "description": "Hindi skills"},
        {"id": "lt_french_rw", "title": "French Reading & Writing", "description": "French skills"},
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
        {"id": "a_eng_basic", "title": "English - Beginner", "description": "Beginner / Elementary"},
        {"id": "a_eng_adv", "title": "English - Intermediate+", "description": "Pre-Inter to Advanced"},
        {"id": "a_arabic", "title": "Spoken Arabic", "description": "Beginner to Advanced"},
        {"id": "a_ielts", "title": "IELTS", "description": "Academic & General"},
        {"id": "a_excel", "title": "Professional Excel", "description": "Excel skills for adults"},
        {"id": "a_python", "title": "Python Coding", "description": "Programming for adults"},
        {"id": "a_grw", "title": "Get Ready To Work", "description": "MS Office + AI training"},
    ],
    "dso": [
        {"id": "a_comms", "title": "Communication Skills", "description": "Adults – English fluency"},
        {"id": "a_arabic", "title": "Spoken Arabic", "description": "Language course for adults"},
        {"id": "a_ielts", "title": "IELTS", "description": "Exam preparation"},
        {"id": "a_msoffice", "title": "MS Office", "description": "Word, Excel, PowerPoint"},
        {"id": "a_excel", "title": "MS Excel", "description": "Spreadsheet mastery"},
        {"id": "a_word", "title": "MS Word", "description": "Document skills"},
    ],
    "jadaf": [
        {"id": "a_ielts", "title": "IELTS", "description": "Exam preparation"},
        {"id": "a_excel", "title": "MS Excel", "description": "For adults"},
        {"id": "a_comms", "title": "Communication Skills", "description": "For adults"},
        {"id": "a_abacus", "title": "Abacus", "description": "Mental math"},
    ],
    "online": [
        {"id": "a_ielts", "title": "IELTS", "description": "Exam preparation"},
        {"id": "a_excel", "title": "MS Excel", "description": "Spreadsheet mastery"},
        {"id": "a_comms", "title": "Communication Skills", "description": "Beginner to Advanced"},
        {"id": "a_msoffice", "title": "MS Office", "description": "Word, Excel, PowerPoint"},
        {"id": "a_word", "title": "MS Word", "description": "Document skills"},
        {"id": "a_arabic", "title": "Spoken Arabic", "description": "Beginner to Advanced"},
        {"id": "a_french", "title": "French", "description": "Beginner to Advanced"},
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

    # ── ACADEMIC SUPPORT COURSES (IC) ──
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

    if course_id == "as_math" and branch == "ic":
        text = (
            "📐 *Academic Support — Mathematics*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Insight in Mathematics (Beginner / Inter / Advanced)\n\n"
            "Our Maths classes help students stay on track with their school curriculum, "
            "strengthen key concepts and improve academic performance.\n\n"
            "💰 *Fees:*\n"
            "• Up to Grade/Year 7: AED 350–400 + VAT/month (twice a week)\n"
            "• Grade/Year 8 & above: Yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "as_science" and branch == "ic":
        text = (
            "🔬 *Academic Support — Science*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Insight in Science (Physics / Chemistry / Biology)\n\n"
            "Our Science classes help students stay on track with their school curriculum, "
            "strengthen key concepts and improve academic performance.\n\n"
            "💰 *Fees:*\n"
            "• Up to Grade/Year 7: AED 350–400 + VAT/month (twice a week)\n"
            "• Grade/Year 8 & above: Yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "as_commerce" and branch == "ic":
        text = (
            "💼 *Academic Support — Commerce & Accounting*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Accounts / Business Studies / Economics\n\n"
            "Our Commerce & Accounting classes help students stay on track with their school curriculum "
            "and improve academic performance.\n\n"
            "💰 *Fees:*\n"
            "• Classes conducted twice or thrice a week (based on requirements)\n"
            "• Offered under a yearly enrolment plan with installment options\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    # ── CHILD SKILL DEVELOPMENT COURSES (IC) ──
    if course_id == "cs_abacus" and branch == "ic":
        text = (
            "🔢 *Abacus — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👦👧 Age Group: 6 to 10 years\n"
            "⏱ Duration: 3 months | 24 classes | 1 hr each\n\n"
            "Develop strong mental arithmetic skills through bead-based calculations. "
            "Students learn addition, subtraction, multiplication & division, "
            "progressing to fast mental calculations.\n\n"
            "💰 *Fees:*\n"
            "• Registration Fee: AED 100 + VAT (one-time)\n"
            "• Course Fee: AED 1,000 + VAT\n\n"
            "📦 Includes: Course Books • Worksheets • Mock Tests • E-Books • IIVA Certificate\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_vedic" and branch == "ic":
        text = (
            "🧮 *Vedic Maths — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👦👧 Age Group: 8 to 16 years\n"
            "⏱ Duration: 3 months | 24 classes | 1 hr each\n\n"
            "Powerful calculation techniques making maths faster, simpler & more accurate. "
            "Improve speed, accuracy, logical thinking and confidence in Mathematics.\n\n"
            "💰 *Fees:*\n"
            "• Registration Fee: AED 100 + VAT (one-time)\n"
            "• Course Fee: AED 1,000 + VAT\n\n"
            "📦 Includes: Course Books • Worksheets • Mock Tests • E-Books • IIVA Certificate\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_coding" and branch == "ic":
        text = (
            "💻 *Coding for Kids — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👦👧 Age Group: 7 years and above\n"
            "⏱ Duration: Min 18 hours per level\n\n"
            "Scratch / Python / App Development\n\n"
            "Introduces children to computational thinking and programming. "
            "Students learn inputs, outputs, logic, algorithms & problem-solving "
            "while building essential coding skills for the future.\n\n"
            "💰 *Fees:*\n"
            "• Registration Fee: AED 100 + VAT (one-time)\n"
            "• Course Fee: ~AED 1,000 + VAT per level\n\n"
            "📦 Includes: Hands-on projects • Learning materials • Educatia Certificate • KHDA Certificate\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_robotics" and branch == "ic":
        text = (
            "🤖 *Robotics — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👦👧 Age Group: 7 years and above\n"
            "⏱ Duration: Min 18 hours per level\n\n"
            "Beginner / Intermediate / Advanced\n\n"
            "Students work with micro:bit & Arduino, learning sensors, inputs, outputs, "
            "programming & debugging to build functional robotic projects.\n\n"
            "💰 *Fees:*\n"
            "• Registration Fee: AED 100 + VAT (one-time)\n"
            "• Course Fee: ~AED 1,000 + VAT per level\n\n"
            "📦 Includes: Hands-on projects • Learning materials • Educatia Certificate • KHDA Certificate\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_handwriting" and branch == "ic":
        text = (
            "✍️ *Handwriting — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👦👧 Age Group: 6 years and above\n"
            "⏱ Duration: Min 24 hours per level\n\n"
            "Develop neat, legible & confident handwriting through guided practice. "
            "Focuses on letter formation, spacing, alignment, writing speed & presentation.\n\n"
            "💰 *Fees:*\n"
            "• Registration Fee: AED 100 + VAT (one-time)\n"
            "• Course Fee: AED 1,000 + VAT per level\n\n"
            "📦 Includes: Practice Book • Worksheets • Feedback • Educatia Certificate\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_creative" and branch == "ic":
        text = (
            "🎨 *Creative Skills — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Art & Craft sessions designed to encourage creativity, imagination & self-expression.\n\n"
            "Activities include: Finger painting • Paper craft • Origami • Canvas painting & more!\n\n"
            "ℹ️ Creative Skills sessions are offered as part of our Summer & Winter Camps.\n\n"
            "📞 Contact us for the next camp schedule:\n"
            "*+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "cs_science_exp" and branch == "ic":
        text = (
            "⚗️ *Live Science Experiments — International City*\n"
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

    if course_id == "cs_msoffice" and branch == "ic":
        text = (
            "💾 *MS Office for Kids — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👦👧 Age Group: 9 years and above\n"
            "⏱ Duration: Min 20 hours per level\n\n"
            "Microsoft Word • PowerPoint • Excel\n\n"
            "Students learn to create documents, presentations & spreadsheets. "
            "Also includes introduction to AI tools for learning & creativity.\n\n"
            "💰 *Fees:*\n"
            "• Registration Fee: AED 100 + VAT (one-time)\n"
            "• Course Fee: AED 1,000 + VAT per level\n\n"
            "📦 Includes: Practical Word/Excel/PowerPoint skills • Educatia Certificate • KHDA Certificate\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    # ── LANGUAGE TRAINING COURSES (IC) ──
    if course_id == "lt_eng_beg" and branch == "ic":
        text = (
            "🗣 *English Communication — Beginner*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👦👧 Age Group: 5 years and above\n"
            "⏱ Duration: Min 36 hours per level\n\n"
            "Helps early learners build confidence in speaking, improve vocabulary "
            "& develop clear sentence formation through age-appropriate activities.\n\n"
            "💰 *Course Fee: AED 1,220 + VAT per level*\n"
            "(Includes class fees, registration & material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_eng_int" and branch == "ic":
        text = (
            "🗣 *English Communication — Intermediate*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👦👧 Age Group: 8 years and above\n"
            "⏱ Duration: Min 24 hours per level\n\n"
            "Builds on foundational English skills — speaking, vocabulary, sentence formation, "
            "grammar & listening in a supportive and engaging environment.\n\n"
            "💰 *Course Fee: AED 1,220 + VAT per level*\n"
            "(Includes class fees, registration & material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_phonics" and branch == "ic":
        text = (
            "🔤 *Phonics Classes — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👦👧 Age Group: 5 years and above\n"
            "⏱ Duration: Min 36 hours per level\n\n"
            "Systematic sound-based learning — letter sounds, blending techniques, "
            "word formation & reading strategies. Builds a strong foundation in English.\n\n"
            "💰 *Course Fee: AED 1,220 + VAT per level*\n"
            "(Includes class fees, registration & material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_pubspeak" and branch == "ic":
        text = (
            "🎤 *Public Speaking & Creative Writing*\n"
            "📍 International City\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👦👧 Age Group: 8 years and above\n"
            "⏱ Duration: Min 16 hours per level\n\n"
            "Helps children express thoughts confidently & creatively through storytelling, "
            "writing exercises & speaking practices. Develop communication, vocabulary & confidence.\n\n"
            "💰 *Course Fee: AED 900 + VAT per level*\n"
            "(Includes class fees, registration & material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    if course_id == "lt_arabic_rw" and branch == "ic":
        text = (
            "🌙 *Arabic Reading & Writing — International City*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👦👧 Age Group: 6 years and above\n"
            "⏱ Duration: Min 24 hours per level\n\n"
            "Learn Arabic alphabets, correct pronunciation, reading techniques & writing skills. "
            "Structured and practical lessons for school-going children.\n\n"
            "💰 *Course Fee: AED 1,220 + VAT per level*\n"
            "(Includes class fees, registration & material fees)\n\n"
            "📞 Contact: *+971 50 460 5940*\n"
            "Reply *menu* to go back 🔙"
        )
        send_text(to, text)
        return

    # ── ALL OTHER COURSES (DSO/Jadaf/Online or unspecified) → generic info + contact ---
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

    # ── Branch selection (3 branches: Summer/STEM) ──
    if step == "select_branch" and category in ("summer_camp", "stem_camp"):
        b = BRANCH_MAP_3.get(num)
        if b:
            if category == "summer_camp":
                show_summer_camp(from_number, b)
            else:
                set_session(from_number, {
                    "step": "select_age",
                    "category": "stem_camp",
                    "branch": b,
                })
                show_stem_age_selection(from_number, b)
            return True

    # ── Branch selection (4 branches: Academic/Adult) ──
    if step == "select_branch" and category in ("academic", "adult"):
        b = BRANCH_MAP_4.get(num)
        if b:
            if category == "academic":
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

    # ── STEM age group selection ──
    if step == "select_age" and category == "stem_camp":
        if num == "1":
            show_stem_junior(from_number, branch)
            return True
        if num == "2":
            show_stem_teen(from_number, branch)
            return True

    # ── Course selection (numbered list) ──
    if step == "select_course" and category in ("academic", "adult"):
        if category == "academic":
            courses = CHILDREN_COURSES.get(branch, [])
        else:
            courses = ADULT_COURSES.get(branch, [])
        idx = int(num) - 1
        if 0 <= idx < len(courses):
            course_id = courses[idx]["id"]
            show_course_detail(from_number, course_id, branch, category)
            return True

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
    if "summer" in msg and "camp" in msg:
        show_branch_buttons(from_number, "summer_camp")
        return
    if "stem" in msg:
        show_branch_buttons(from_number, "stem_camp")
        return
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
    if "robot" in msg:
        show_branch_buttons(from_number, "stem_camp")
        return
    if "python" in msg or "coding" in msg:
        show_branch_buttons(from_number, "stem_camp")
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
    # Legacy summer/stem camp support
    if item_id == "cat_summer":
        show_branch_buttons(from_number, "summer_camp")
        return
    if item_id == "cat_stem":
        show_branch_buttons(from_number, "stem_camp")
        return

    # ── Branch selections ──
    if item_id.startswith("branch_"):
        branch = item_id.replace("branch_", "")
        category = session.get("category", "")

        if category == "summer_camp":
            show_summer_camp(from_number, branch)
        elif category == "stem_camp":
            set_session(from_number, {
                "step": "select_age",
                "category": "stem_camp",
                "branch": branch,
            })
            show_stem_age_selection(from_number, branch)
        elif category in ("academic_support", "child_skill", "language"):
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

    # ── STEM age group selections ──
    if item_id == "age_8_11":
        branch = session.get("branch", "ic")
        show_stem_junior(from_number, branch)
        return
    if item_id == "age_12_17":
        branch = session.get("branch", "ic")
        show_stem_teen(from_number, branch)
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
