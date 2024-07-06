import webbrowser
import speech_recognition as sr
import pyttsx3
import time
import google.generativeai as genai
from threading import Timer
import threading
import sys
import os

os.environ['GEMINI_API_KEY'] = 'enter you api key here'

def text_to_speech(text):
    engine = pyttsx3.init()
    engine.setProperty('voice', engine.getProperty('voices')[0].id)
    engine.setProperty('rate', 180)
    engine.setProperty('volume', 1.0)
    engine.say(text)
    engine.runAndWait()

def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Speak Now...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I could not understand the audio")
        return None
    except sr.RequestError:
        print("Sorry, my speech service is down")
    return None

def get_gemini_response(prompt):
    api_key = os.environ.get('GEMINI_API_KEY')
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text
    

def handle_command(text):
    if "open" in text and "website" in text:
        try:
            site = text.split("open ")[1].split(" website")[0].strip()
            # urls are not uppercase and do not have spaces
            formatted_site = site.replace(" ", "").lower()
            url = f"http://{formatted_site}.com"
            response = f"Opening {site} website"
            webbrowser.open(url)
        except IndexError:
            error_response = "Sorry, I couldn't understand the website name."
    else:
        response = get_gemini_response(text)
    print("Jarvis:", response)
    text_to_speech(response)
            
print("Configuration Done")

def main():
    shutdown_event = threading.Event()
    shutdown_timer = None

    def reset_timer():
        nonlocal shutdown_timer
        if shutdown_timer:
            shutdown_timer.cancel()
        shutdown_timer = Timer(60, lambda: shutdown_event.set())
        shutdown_timer.start()

    def shutdown():
        print("Shutting down Jarvis.")
        text_to_speech("Shutting down Jarvis.")
        if shutdown_timer:
            shutdown_timer.cancel()
        sys.exit(0)

    print("Jarvis is ready. Say 'Jarvis' followed by your command.")
    text_to_speech("Jarvis is ready. Say 'Jarvis' followed by your command.")

    reset_timer()
    
    while not shutdown_event.is_set():
        text = speech_to_text()
        if text:
            if "jarvis" in text.lower():
                reset_timer()
                command_text = text.lower().replace("jarvis", "").strip()
                if "close" in command_text or "exit" in command_text:
                    shutdown()
                handle_command(command_text)
            else:
                print("Command ignored, no 'Jarvis' keyword detected.")
        else:
            print("No speech detected. Please try again.")
            
    shutdown()

if __name__ == "__main__":
    main()