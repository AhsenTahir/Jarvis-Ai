import webbrowser
import speech_recognition as sr
import pyttsx3
import time
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
import os
from playsound import playsound

ELEVENLABS_API_KEY = os.getenv("enter your api key")
client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY,
)
os.environ['GEMINI_API_KEY'] = 'enter your api key here'

#set up weather

WEATHER_BASE_URL='https://api.openweathermap.org/data/2.5/'
WEATHER_API_KEY='ae3ee0c6bf70e4f7873fa61bc44b07df'

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



def handle_command(text):
   weather_actions = {
    "what's the weather like today|today's weather": lambda text: fetch_weather_data(""),  # Empty location for current location
    "can you tell me the weather in (.*)": lambda text: fetch_weather_data(text.split("in ")[-1]),  # Capture location after "in"
    "is it raining (.*)": lambda text: fetch_weather_data(text.split("raining ")[-1]),  # Capture location after "raining" (optional)
    "what's the temperature (.*)": lambda text: fetch_weather_data(text.split("temperature ")[-1]),  # Capture location after "temperature" (optional)
    "weather in my area|weather near me": lambda text: fetch_weather_data(""),  # Use current location
    # ... add more phrases and actions

       text = text.lower()  # Case-insensitive matching

  for phrase, action in weather_actions.items():
    match = re.match(phrase, text)
    if match:
      location = match.group(1) if match.groups() else ""  # Extract captured location (if any)
      fetch_weather_data(location)
      return  # Exit after successful match and action

  print("Sorry, I couldn't understand your weather request.")
}
# Set up News API key
NEWS_API_KEY = 'enter your api key'
NEWS_API_URL = 'https://newsapi.org/v2/top-headlines'



def text_to_speech(text: str) -> str:
    # Calling the text_to_speech conversion API with detailed parameters
    response = client.text_to_speech.convert(
        voice_id="pNInz6obpgDQGcFmaJgB",  # Adam pre-made voice
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_turbo_v2",  # use the turbo model for low latency
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    # Generating a unique file name for the output MP3 file
    save_file_path = f"{uuid.uuid4()}.mp3"

    # Writing the audio to a file
    with open(save_file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    # Play the audio file
    playsound(save_file_path)

    # Delete the audio file after playing
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
def clean_response(text):
    # Remove unwanted characters using regex
    clean_text = re.sub(r'[\*#,_~`]', '', text)
    return clean_text

def get_gemini_response(prompt):
    api_key = os.environ.get('GEMINI_API_KEY')
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text
    
def fetch_news(category=None):
  params = {
    'apiKey': NEWS_API_KEY,
    'country': 'us',
    'category': category,
    'pageSize': 5  # Number of articles to fetch
  }
  response = requests.get(NEWS_API_URL, params=params)
  news_data = response.json()
  articles = news_data.get('articles', [])
  return articles

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
    elif "news" in text:
        category = None
        if "technology" in text:
            category = "technology"
        elif "sports" in text:
            category = "sports"
        elif "politics" in text:
            category = "politics"
        
        articles = fetch_news(category)
        if articles:
            response = "Here are the latest news headlines:\n"
            for article in articles:
                title = article.get('title')
                url = article.get('url')
                response += f"- {title}\n"
                print(f"-(URL: {url})" if url else "") 
            print("Jarvis:", response)
            text_to_speech(response)
        else:
            response = "Sorry, I couldn't fetch the news at this moment."
            print("Jarvis:", response)
            text_to_speech(response)
    else:
     response = get_gemini_response(text)
     response = clean_response(response)
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
