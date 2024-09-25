#============================================#
#               Imports
#============================================#
import webbrowser
import speech_recognition as sr
import google.generativeai as genai
from threading import Timer
import threading
import sys
import os
import re  
import requests
import uuid
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import pywhatkit as kit
from playsound import playsound
import random
from googlesearch import search
from config import ELEVENLABS_API_KEY, GEMINI_API_KEY, WEATHER_API_KEY, NEWS_API_KEY 

#============================================#
#               API Keys
#============================================#

GEMINI_API_KEY = GEMINI_API_KEY
WEATHER_API_KEY = 'WEATHER_API_KEY'
NEWS_API_KEY = 'NEWS_API_KEY    '

#============================================#
#               Constants
#============================================#
WEATHER_BASE_URL = 'https://api.openweathermap.org/data/2.5/'
NEWS_API_URL = 'https://newsapi.org/v2/top-headlines'

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)  # Use the imported API key
os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY

music_list = []
popular_songs = [
    "Shape of You", "Blinding Lights", "Dance Monkey",
    "Rockstar", "Someone You Loved"
]

#============================================#
#               Weather Functions
#============================================#
def fetch_weather_data(city, country_code):
    params = {
        'q': f"{city},{country_code}",
        'appid': WEATHER_API_KEY,
        'units': 'imperial'
    }
    try:
        response = requests.get(WEATHER_BASE_URL, params=params)
        response.raise_for_status()
        weather_data = response.json()
        main_weather = weather_data['weather'][0]['main']
        description = weather_data['weather'][0]['description']
        temp = weather_data['main']['temp']
        humidity = weather_data['main']['humidity']
        processed_weather_data = {
            'main_weather': main_weather,
            'description': description,
            'temperature': temp,
            'humidity': humidity
        }
        return processed_weather_data
    except requests.exceptions.RequestException as e:
        return f"Error: An error occurred while fetching weather data. ({e})"
    except Exception as e:
        return f"Error: An unexpected error occurred. ({e})"

#============================================#
#               Speech Functions
#============================================#
def text_to_speech(text: str) -> str:
    response = client.text_to_speech.convert(
        voice_id="pNInz6obpgDQGcFmaJgB",
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_turbo_v2",
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )
    save_file_path = f"{uuid.uuid4()}.mp3"
    with open(save_file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)
    playsound(save_file_path)
    os.remove(save_file_path)

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

#============================================#
#               Gemini AI Functions
#============================================#
def clean_response(text):
    clean_text = re.sub(r'[\*#,_~`]', '', text)
    return clean_text

def get_gemini_response(prompt):
    api_key = os.environ.get('GEMINI_API_KEY')
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text

#============================================#
#               News Functions
#============================================#
def fetch_news(category=None):
    params = {
        'apiKey': NEWS_API_KEY,
        'country': 'us',
        'category': category,
        'pageSize': 5
    }
    response = requests.get(NEWS_API_URL, params=params)
    news_data = response.json()
    articles = news_data.get('articles', [])
    return articles

#============================================#
#             Google Search Functions
#============================================#
def google_search_and_read(query):
    try:
        # Perform Google search
        search_results = search(query, num_results=1)
        if search_results:
            # Read the first search result
            text_to_speech(search_results[0])
        else:
            text_to_speech(f"Sorry, couldn't find the information about '{query}'.")
    except Exception as e:
        text_to_speech(f"An error occurred while looking for that information: {str(e)}")

#============================================#
#               Command Handling
#============================================#
def handle_command(text):
    text = text.lower()

    weather_actions = {
        r"what's the weather like today|today's weather": "",
        r"can you tell me the weather in (.+)": lambda match: match.group(1),
        r"is it raining( in (.+))?": lambda match: match.group(2) if match.group(2) else "",
        r"what's the temperature( in (.+))?": lambda match: match.group(2) if match.group(2) else "",
        r"weather in my area|weather near me": ""
    }

    for pattern, action in weather_actions.items():
        match = re.match(pattern, text)
        if match:
            location = action(match) if callable(action) else action
            if not location:
                location = "New York,US"
            else:
                location += ",US"
            
            weather_data = fetch_weather_data(*location.split(','))
            if isinstance(weather_data, dict):
                response = f"Here's the weather for {location.split(',')[0]}:\n"
                response += f"Condition: {weather_data['main_weather']}, {weather_data['description']}\n"
                response += f"Temperature: {weather_data['temperature']}°F\n"
                response += f"Humidity: {weather_data['humidity']}%"
            else:
                response = weather_data
            
            print("Jarvis:", response)
            text_to_speech(response)
            return

    if "open" in text and "website" in text:
        try:
            site = text.split("open ")[1].split(" website")[0].strip()
            formatted_site = site.replace(" ", "").lower()
            url = f"http://{formatted_site}.com"
            response = f"Opening {site} website"
            webbrowser.open(url)
        except IndexError:
            response = "Sorry, I couldn't understand the website name."
    elif "news" in text:
        category = None
        if "technology" in text:
            category = "technology"
        elif "sports" in text:
            category = "sports"
        elif "politics" in text:
            category = "politics"
        
        # Search Google and read the information
        google_search_and_read(text)
        
        articles = fetch_news(category)
        if articles:
            response = "Here are the latest news headlines:\n"
            for article in articles:
                title = article.get('title')
                url = article.get('url')
                response += f"- {title}\n"
                print(f"-(URL: {url})" if url else "") 
        else:
            response = "Sorry, I couldn't fetch the news at this moment."
    elif "play music" in text:
        play_youtube_music(text)
        return
    else:
        response = get_gemini_response(text)
        response = clean_response(response)

    print("Jarvis:", response)
    text_to_speech(response)

#============================================#
#               Music Functions
#============================================#
def add_favsong():
    max_retries = 3
    for _ in range(max_retries):
        text_to_speech("Do you have any favourite song you want to add to my memory?")
        new_song = speech_to_text()
        if new_song:
            music_list.append(new_song)
            print(f"I have added {new_song} to your favourites.")
            return
        else:
            text_to_speech("I didn't catch that, let's try again")
    text_to_speech("I'm sorry, I couldn't add a new song after several attempts.")

def play_youtube_music(command):
    query = command.replace("play music", "").strip()
    if not query:
        if not music_list:
            text_to_speech("Your favourite songs list is empty, would you like to add any songs?")
            response = speech_to_text()
            if response and "yes" in response.lower():
                add_favsong()
        if music_list:
            text_to_speech("I will play one of your favourite songs")
            random_song = random.choice(music_list)
            text_to_speech(f"Playing {random_song} for you.")
            try:
                kit.playonyt(random_song)
            except Exception as e:
                text_to_speech(f"I am sorry, I couldn't play that. The error was: {str(e)}")
        else:
            text_to_speech("I'll play a random popular song for you.")
            random_popular_song = random.choice(popular_songs)
            text_to_speech(f"Playing {random_popular_song} for you.")
            try:
                kit.playonyt(random_popular_song)
            except Exception as e:
                text_to_speech(f"I am sorry, I could not play that. The error was: {str(e)}")
    else:
        try:
            kit.playonyt(query)
        except Exception as e:
            text_to_speech(f"An error occurred while trying to play the music. The error was: {str(e)}")

#============================================#
#               Main Function
#============================================#
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

#============================================#
#               Entry Point
#============================================#
if __name__ == "__main__":
    main()
