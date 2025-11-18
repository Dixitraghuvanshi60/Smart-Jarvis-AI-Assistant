import os
import sys
import json
import queue
import sounddevice as sd
import vosk
import pyttsx3
import datetime
import webbrowser
import socket
import subprocess
from dotenv import load_dotenv
from openai import OpenAI


# ================= CONFIGURATION ================= #

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("❌ ERROR: No OpenAI API key found in .env")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

vosk_model = "vosk-model-small-en-us-0.15"
if not os.path.exists(vosk_model):
    print("❌ Vosk model not found!")
    sys.exit(1)


# ================= AUDIO SETUP ================= #

engine = pyttsx3.init()
engine.setProperty("rate", 170)
engine.setProperty("volume", 1.0)

model = vosk.Model(vosk_model)
q = queue.Queue()


def speak(text):
    print(f"\n🗣 Jarvis: {text}")
    engine.say(text)
    engine.runAndWait()


def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))


# ================= INTERNET CHECK ================= #

def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False


# ================= SPEECH RECOGNITION ================= #

def recognize_speech(timeout=5):
    rec = vosk.KaldiRecognizer(model, 16000)
    result_text = ""

    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype='int16',
        channels=1,
        callback=callback
    ):
        print("🎙 Listening... (or type your command below)")
        sd.sleep(int(timeout * 1000))

        while not q.empty():
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "")
                if text:
                    result_text = text.lower()
                    break

    return result_text


# ================= LOCAL COMMANDS ================= #

def handle_local_command(command):
    command = command.strip()

    if "time" in command:
        speak("The time is " + datetime.datetime.now().strftime("%I:%M %p"))

    elif "date" in command:
        speak("Today's date is " + datetime.datetime.now().strftime("%B %d, %Y"))

    elif "open youtube" in command:
        speak("Opening YouTube")
        webbrowser.open("https://www.youtube.com")

    elif "open google" in command:
        speak("Opening Google")
        webbrowser.open("https://www.google.com")

    elif "open folder" in command:
        folder_name = command.replace("open folder", "").strip()
        folder_paths = {
            "downloads": r"C:\Users\Dell\Downloads",
            "documents": r"C:\Users\Dell\Documents",
            "desktop": r"C:\Users\Dell\Desktop",
            "pictures": r"C:\Users\Dell\Pictures",
            "music": r"C:\Users\Dell\Music",
            "videos": r"C:\Users\Dell\Videos",
        }
        if folder_name in folder_paths:
            speak(f"Opening {folder_name} folder")
            os.startfile(folder_paths[folder_name])
        else:
            speak("Sorry, I don't know that folder.")

    elif "open" in command:
        app_name = command.replace("open", "").strip()
        app_paths = {
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "visual studio code": r"C:\Users\Dell\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            "notepad": r"C:\Windows\System32\notepad.exe",
            "calculator": r"C:\Windows\System32\calc.exe"
        }
        if app_name in app_paths and os.path.exists(app_paths[app_name]):
            speak(f"Opening {app_name}")
            os.startfile(app_paths[app_name])
        else:
            speak("App not found.")

    elif "close" in command:
        app_name = command.replace("close", "").strip()
        process_names = {
            "chrome": "chrome.exe",
            "notepad": "notepad.exe",
            "calculator": "Calculator.exe",
            "visual studio code": "Code.exe"
        }
        if app_name in process_names:
            try:
                subprocess.call(
                    ["taskkill", "/f", "/im", process_names[app_name]],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                speak(f"Closed {app_name}")
            except:
                speak("Unable to close the app.")
        else:
            speak("Unknown application.")

    elif "exit" in command or "quit" in command or "bye" in command:
        speak("Goodbye")
        sys.exit(0)

    else:
        return False

    return True


# ================= ONLINE CHAT MODE ================= #

def online_chat(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        reply = response.choices[0].message.content
        speak(reply)
    except Exception as e:
        print("❌ Online mode failed:", e)
        speak("Sorry, I couldn't connect online.")


# ================= MAIN LOOP ================= #

def main():
    speak("Jarvis is now active. How can I assist you?")

    while True:
        print("\n🎧 Say 'hey jarvis' or type below.")
        text = recognize_speech()

        if not text.strip():
            text = input("💬 Type your command: ").strip().lower()

        if not text:
            continue

        if "hey jarvis" in text:
            speak("Yes, I am listening.")
            command = recognize_speech()

            if not command.strip():
                command = input("💬 Type your command: ").strip().lower()

            if not command:
                continue

            if not handle_local_command(command):
                if is_connected():
                    online_chat(command)
                else:
                    speak("No internet. I will work offline.")
        else:
            if not handle_local_command(text):
                if is_connected():
                    online_chat(text)
                else:
                    speak("No internet available.")


# ================= RUN ================= #

if __name__ == "__main__":
    main()
