
import logging
import re

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from textblob import TextBlob
from deep_translator import GoogleTranslator, MyMemoryTranslator
from langdetect import detect, DetectorFactory, LangDetectException

logger = logging.getLogger(__name__)
DetectorFactory.seed = 0

# Map standard language codes to MyMemory language codes.
MYMEMORY_CODES = {
    "en": "en-GB",
    "ta": "ta-IN",
    "hi": "hi-IN",
    "fr": "fr-FR",
    "ur": "ur-PK",
}

SUPPORTED_LANGUAGES = set(MYMEMORY_CODES)


# LOGIN
def login_view(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username", ""),
            password=request.POST.get("password", "")
        )
        if user:
            login(request, user)
            return redirect("home")
        messages.error(request, "Invalid login")
    return render(request, "login.html")


# REGISTER
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        if not username or not password1:
            messages.error(request, "Username and password are required.")
        elif password1 != password2:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            User.objects.create_user(
                username=username,
                password=password1
            )
            return redirect("login")

    return render(request, "register.html")


# LOGOUT
def logout_view(request):
    logout(request)
    return redirect("login")


# HOME
def home(request):
    return render(request, "home.html")


# ABOUT
def about(request):
    return render(request, "about.html")


# CONTACT
def contact(request):
    return render(request, "contact.html")


def detect_language(text):
    """Detect language, with a small short-text English heuristic."""
    if not text or not text.strip():
        return "unknown"

    # langdetect often mistakes short English greetings for other languages.
    short_english = {
        "hello", "hi", "hey", "good morning",
        "good evening", "thank you", "thanks",
        "how are you", "good night"
    }

    normalized = re.sub(r"[.!?]+$", "", text.strip().lower())

    if normalized in short_english:
        return "en"

    try:
        return detect(text)
    except LangDetectException:
        return "unknown"


def translate_text(text, source, target):
    """Translate with Google, then try MyMemory if supported."""
    if source == target:
        return text

    errors = []

    try:
        result = GoogleTranslator(
            source=source if source != "unknown" else "auto",
            target=target
        ).translate(text)

        if result and result.strip():
            return result

        errors.append("Google returned an empty translation.")

    except Exception as exc:
        logger.warning("Google translation failed: %s", exc)
        errors.append("Google translation unavailable.")

    # MyMemory requires regional language codes.
    if target in MYMEMORY_CODES and source in MYMEMORY_CODES:
        try:
            result = MyMemoryTranslator(
                source=MYMEMORY_CODES[source],
                target=MYMEMORY_CODES[target]
            ).translate(text)

            if result and result.strip():
                # Reject known API error messages.
                if "QUERY LENGTH LIMIT EXCE" not in result.upper():
                    return result

            errors.append("MyMemory returned an invalid translation.")

        except Exception as exc:
            logger.warning("MyMemory translation failed: %s", exc)
            errors.append("MyMemory translation unavailable.")

    raise RuntimeError(
        "Translation failed. Please try again later."
    )


# NLP UPLOAD + RESULT
def upload_text(request):
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        selected_lang = request.POST.get("lang", "").strip().lower()

        if not text:
            messages.error(request, "Please enter text to translate.")
            return render(request, "upload.html")

        if selected_lang not in SUPPORTED_LANGUAGES:
            messages.error(request, "Please select a supported language.")
            return render(request, "upload.html")

        detected_lang = detect_language(text)

        # Preserve existing auto-detection workflow.
        source_lang = detected_lang

        translation_error = None
        translated_text = ""

        try:
            translated_text = translate_text(
                text,
                source_lang,
                selected_lang
            )
        except Exception as exc:
            translation_error = str(exc)
            logger.error("Translation failed: %s", exc)

        # Sentiment analysis is performed on English text.
        english_text = None

        if detected_lang == "en":
            english_text = text
        else:
            try:
                english_text = translate_text(
                    text,
                    detected_lang,
                    "en"
                )
            except Exception as exc:
                logger.warning("Sentiment translation failed: %s", exc)

        if english_text:
            polarity = TextBlob(english_text).sentiment.polarity

            if polarity > 0:
                result = "Positive 😊"
            elif polarity < 0:
                result = "Negative 😞"
            else:
                result = "Neutral 😐"
        else:
            result = "Unavailable (English translation failed)"

        return render(request, "result.html", {
            "original": text,
            "detected": detected_lang,
            "translated": translated_text,
            "result": result,
            "lang": selected_lang,
            "translation_error": translation_error,
        })

    return render(request, "upload.html")
