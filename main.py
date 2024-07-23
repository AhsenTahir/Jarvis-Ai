import webbrowser
import speech_recognition as sr
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

WEATHER_BASE_URL='https://api.openweathermap.org/data/2.5/weather'
WEATHER_API_KEY='ae3ee0c6bf70e4f7873fa61bc44b07df'

def fetch_weather_data(city, country_code=""):
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
      return f"The weather in {city} is {main_weather} ({description}). Temperature is {temp}°F with {humidity}% humidity."
  except requests.exceptions.RequestException as e:
      return f"Error: An error occurred while fetching weather data. ({e})"
  except Exception as e:
      return f"Error: An unexpected error occurred. ({e})"

# Set up News API key
NEWS_API_KEY = 'enter your api key'
NEWS_API_URL = 'https://newsapi.org/v2/top-headlines'

def text_to_speech(text: str) -> str:
  # Calling the text_to_speech conversion API with detailed parameters
  response = client.text_to_speech.convert(
      voice_id="pNInz6obpgDQGcFmaJgB", # Adam pre-made voice
      optimize_streaming_latency="0",
      output_format="mp3_22050_32",
      text=text,
      model_id="eleven_turbo_v2", # use the turbo model for low latency
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
