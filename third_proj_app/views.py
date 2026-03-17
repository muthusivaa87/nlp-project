from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from textblob import TextBlob
from deep_translator import GoogleTranslator
from langdetect import detect


# LOGIN
def login_view(request):
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid login')
    return render(request, 'login.html')


# REGISTER
def register_view(request):
    if request.method == 'POST':
        if request.POST['password1'] == request.POST['password2']:
            User.objects.create_user(
                username=request.POST['username'],
                password=request.POST['password1']
            )
            return redirect('login')
    return render(request, 'register.html')


# LOGOUT
def logout_view(request):
    logout(request)
    return redirect('login')


# HOME
def home(request):
    return render(request, 'home.html')


# ABOUT
def about(request):
    return render(request, 'about.html')


# CONTACT
def contact(request):
    return render(request, 'contact.html')


# NLP UPLOAD + RESULT
def upload_text(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        selected_lang = request.POST.get('lang')

        # 🔹 Detect Language
        try:
            detected_lang = detect(text)
        except:
            detected_lang = "unknown"

        # 🔹 Translate INPUT → Selected Language (for display)
        try:
            translated_text = GoogleTranslator(
                source='auto',
                target=selected_lang
            ).translate(text)
        except:
            translated_text = text

        # 🔹 Convert to English (for NLP)
        try:
            english_text = GoogleTranslator(
                source='auto',
                target='en'
            ).translate(text)
        except:
            english_text = text

        # 🔹 Sentiment Analysis
        blob = TextBlob(english_text)
        polarity = blob.sentiment.polarity

        if polarity > 0:
            result = "Positive 😊"
        elif polarity < 0:
            result = "Negative 😞"
        else:
            result = "Neutral 😐"

        return render(request, 'result.html', {
            'original': text,
            'detected': detected_lang,
            'translated': translated_text,
            'result': result,
            'lang': selected_lang
        })

    return render(request, 'upload.html')