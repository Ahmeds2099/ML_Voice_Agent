"""
VOICE AGENT - WITH ML COMMAND CLASSIFIER
Whisper MEDIUM + Command Classifier for improved accuracy
"""

import json
import os
import sys
import time
import subprocess
import signal
import re
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

print("="*60)
print("VOICE AGENT - WITH ML CLASSIFIER")
print("Whisper MEDIUM + ML Command Classifier")
print("="*60)

# Global exit flag
running = True

def signal_handler(sig, frame):
    global running
    print("\nStopping agent...")
    running = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Auto‑install missing packages
def ensure_packages():
    required = ['faster-whisper', 'sounddevice', 'numpy', 'keyboard', 'soundfile', 'pyautogui']
    package_map = {
        'faster_whisper': 'faster-whisper',
        'sounddevice': 'sounddevice',
        'numpy': 'numpy',
        'keyboard': 'keyboard',
        'soundfile': 'soundfile',
        'pyautogui': 'pyautogui'
    }
    missing = []
    for import_name, package_name in package_map.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    if missing:
        print(f"\nInstalling missing packages: {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        print("Packages installed. Restart the script.")
        sys.exit(0)

ensure_packages()

# Import everything
import numpy as np
import sounddevice as sd
import soundfile as sf
import keyboard
import pyautogui
from faster_whisper import WhisperModel

# Import the classifier (from command_classifier.py)
from command_classifier import CommandClassifier

# ========================================================================
class VoiceAgent:
    def __init__(self):
        print("\nInitializing Voice Agent...")
        
        # Settings
        self.hotkey = 'f2'
        self.sample_rate = 16000
        self.channels = 1
        
        # Recording state
        self.is_recording = False
        self.audio_frames = []
        self.stream = None
        self.running = True
        
        # Initialize ML Classifier
        print("\nInitializing ML Command Classifier...")
        self.classifier = CommandClassifier()
        
        # Load models and data
        self._init_whisper_medium()
        self._init_memory()
        self._init_apps()
        
        self.speak("Agent starting up with ML classifier.")
        
        print("\n✅ AGENT READY!")
        print(f"Hotkey: {self.hotkey.upper()} (press and hold)")
        print("Model: Whisper MEDIUM + ML Classifier")
        print("\nPress Ctrl+C to exit")
    
    # ====================================================================
    # TTS - PowerShell based
    def speak(self, text):
        """Speak text using PowerShell"""
        print(f"Agent: {text}")
        try:
            escaped_text = text.replace("'", "''")
            command = f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{escaped_text}\')"'
            subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"⚠️ TTS error: {e}")
    
    # ====================================================================
    # Whisper model - MEDIUM version
    def _init_whisper_medium(self):
        print("\nLoading Whisper MEDIUM model...")
        try:
            self.whisper_model = WhisperModel(
                "medium", device="cpu", compute_type="int8",
                num_workers=1, cpu_threads=4
            )
            print("✓ Whisper MEDIUM loaded on CPU")
        except Exception as e:
            print(f"❌ Whisper failed: {e}")
            sys.exit(1)
    
    # ====================================================================
    # Memory
    def _init_memory(self):
        self.memory_file = "agent_memory.json"
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {"tasks": [], "notes": []}
        print(f"✓ Memory loaded: {len(self.data['tasks'])} tasks, {len(self.data['notes'])} notes")
    
    def _init_apps(self):
        self.apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "chrome": "start chrome",
            "browser": "start chrome",
            "firefox": "start firefox",
            "edge": "start msedge",
            "word": "winword",
            "excel": "excel",
            "vscode": "code",
            "visual studio code": "code",
            "pycharm": "pycharm64",
            "spotify": "spotify",
            "vlc": "vlc",
            "cmd": "cmd",
            "command prompt": "cmd",
            "powershell": "powershell",
            "explorer": "explorer",
            "file explorer": "explorer",
            "task manager": "taskmgr",
            "control panel": "control",
            "settings": "start ms-settings:"
        }
        print(f"✓ {len(self.apps)} apps available")
    
    # ====================================================================
    # Audio recording
    def _audio_callback(self, indata, frames, time_info, status):
        if self.is_recording:
            self.audio_frames.append(indata.copy())
    
    def start_recording(self):
        if self.is_recording:
            return
        self.is_recording = True
        self.audio_frames = []
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=self._audio_callback,
                dtype='float32'
            )
            self.stream.start()
            print("\n🎤 Recording... (speak now)")
        except Exception as e:
            print(f"Mic error: {e}")
            self.is_recording = False
    
    def stop_recording(self):
        if not self.is_recording:
            return None
        print("\n⏏️ Processing...")
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        if not self.audio_frames:
            return None
        audio = np.concatenate(self.audio_frames, axis=0)
        if np.max(np.abs(audio)) < 0.005:
            print("No speech detected")
            return None
        temp = f"temp_{int(time.time())}.wav"
        sf.write(temp, audio, self.sample_rate)
        return temp
    
    # ====================================================================
    # Speech to text
    def speech_to_text(self, audio_file):
        try:
            print("  Transcribing...")
            segments, _ = self.whisper_model.transcribe(
                audio_file, language="en",
                beam_size=5, best_of=5, temperature=0.0
            )
            text = " ".join([s.text for s in segments]).strip().lower()
            if text:
                print(f"📝 You said: {text}")
                return text
            else:
                print("No speech recognized")
                return None
        except Exception as e:
            print(f"Whisper error: {e}")
            return None
    
    # ====================================================================
    # APPLICATION CONTROL
    def open_application(self, app_name):
        app_name = app_name.lower().strip()
        if app_name in self.apps:
            subprocess.Popen(self.apps[app_name], shell=True)
            self.speak(f"Opening {app_name}")
            return True
        for key, cmd in self.apps.items():
            if key in app_name or app_name in key:
                subprocess.Popen(cmd, shell=True)
                self.speak(f"Opening {key}")
                return True
        self.speak(f"Couldn't find '{app_name}'")
        return False
    
    # ====================================================================
    # TASK MANAGEMENT
    def add_task(self, task_text):
        self.data["tasks"].append({
            "task": task_text, "done": False,
            "added": datetime.now().isoformat()
        })
        self._save_memory()
        self.speak(f"Added task: {task_text}")
    
    def show_tasks(self):
        tasks = [t for t in self.data["tasks"] if not t.get("done")]
        if tasks:
            self.speak(f"You have {len(tasks)} tasks")
            for i, t in enumerate(tasks[:5], 1):
                self.speak(f"{i}. {t['task']}")
        else:
            self.speak("No pending tasks")
    
    def complete_task(self, task_num):
        try:
            num = int(task_num) - 1
            tasks = [t for t in self.data["tasks"] if not t.get("done")]
            if 0 <= num < len(tasks):
                tasks[num]["done"] = True
                self._save_memory()
                self.speak(f"Completed: {tasks[num]['task']}")
                return True
            else:
                self.speak(f"Task {task_num} not found")
                return False
        except:
            self.speak("Please specify task number")
            return False
    
    def delete_task(self, task_num):
        try:
            num = int(task_num) - 1
            pending = [t for t in self.data["tasks"] if not t.get("done")]
            if 0 <= num < len(pending):
                task = pending[num]
                self.data["tasks"] = [t for t in self.data["tasks"] if t != task]
                self._save_memory()
                self.speak(f"Deleted task: {task['task']}")
                return True
            else:
                self.speak(f"Task {task_num} not found")
                return False
        except:
            self.speak("Please specify task number")
            return False
    
    # ====================================================================
    # NOTES MANAGEMENT
    def add_note(self, note_text):
        if "notes" not in self.data:
            self.data["notes"] = []
        self.data["notes"].append({"note": note_text, "time": datetime.now().isoformat()})
        self._save_memory()
        self.speak(f"Remembered: {note_text[:50]}")
    
    def show_notes(self):
        notes = self.data.get("notes", [])
        if notes:
            count = len(notes)
            self.speak(f"You have {count} notes")
            for i, n in enumerate(notes[-5:], 1):
                self.speak(f"{i}. {n['note'][:50]}")
        else:
            self.speak("No notes saved")
    
    def delete_note(self, note_num):
        try:
            num = int(note_num) - 1
            notes = self.data.get("notes", [])
            if 0 <= num < len(notes):
                deleted = notes.pop(num)
                self._save_memory()
                self.speak(f"Deleted note: {deleted['note'][:50]}")
                return True
            else:
                self.speak(f"Note {note_num} not found")
                return False
        except:
            self.speak("Please specify note number")
            return False
    
    # ====================================================================
    # ML CLASSIFIER INTEGRATION (NEW)
    def classify_and_execute(self, transcribed_text):
        """
        Use ML classifier to validate command, then execute
        """
        # Get classification
        classification = self.classifier.classify_command(transcribed_text)
        
        print(f"\n[ML CLASSIFIER]")
        print(f"  Processed: '{classification['processed_text']}'")
        print(f"  Confidence: {classification['confidence']:.2f}")
        print(f"  Valid: {classification['is_valid']}")
        print(f"  Reason: {classification['reasoning']}")
        
        # If not valid, reject
        if not classification['is_valid']:
            self.speak("I'm not confident about that command. Can you repeat?")
            return False
        
        command = classification['command']
        confidence = classification['confidence']
        processed_text = classification['processed_text']
        
        # Execute based on classified command
        if command == 'open':
            match = re.search(r'open\s+(\w+)', processed_text)
            if match:
                app = match.group(1).strip()
                self.open_application(app)
        
        elif command == 'add_task':
            match = re.search(r'add\s+task\s+(.*)', processed_text)
            if match:
                task = match.group(1).strip()
                if task:
                    self.add_task(task)
                else:
                    self.speak("What task?")
        
        elif command == 'show_tasks':
            self.show_tasks()
        
        elif command == 'complete_task':
            match = re.search(r'complete\s+task\s+(\d+)', processed_text)
            if match:
                self.complete_task(match.group(1))
        
        elif command == 'delete_task':
            match = re.search(r'delete\s+task\s+(\d+)', processed_text)
            if match:
                self.delete_task(match.group(1))
        
        elif command == 'remember':
            match = re.search(r'remember\s+(.*)', processed_text)
            if match:
                note = match.group(1).strip()
                if note:
                    self.add_note(note)
                else:
                    self.speak("What should I remember?")
        
        elif command == 'show_notes':
            self.show_notes()
        
        elif command == 'delete_note':
            match = re.search(r'delete\s+note\s+(\d+)', processed_text)
            if match:
                self.delete_note(match.group(1))
        
        elif command == 'volume_up':
            import ctypes
            for _ in range(3):
                ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0xAF, 0, 2, 0)
            self.speak("Volume increased")
        
        elif command == 'volume_down':
            import ctypes
            for _ in range(3):
                ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0xAE, 0, 2, 0)
            self.speak("Volume decreased")
        
        elif command == 'mute':
            import ctypes
            ctypes.windll.user32.keybd_event(0xAD, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xAD, 0, 2, 0)
            self.speak("Volume toggled")
        
        elif command == 'screenshot':
            filename = f"screenshot_{int(time.time())}.png"
            pyautogui.screenshot(filename)
            self.speak("Screenshot taken")
        
        elif command == 'lock':
            subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
            self.speak("Locking computer")
        
        elif command == 'shutdown':
            self.speak("Shutting down in 30 seconds")
            subprocess.run("shutdown /s /t 30", shell=True)
        
        elif command == 'restart':
            self.speak("Restarting in 30 seconds")
            subprocess.run("shutdown /r /t 30", shell=True)
        
        elif command == 'time':
            self.speak(f"The time is {datetime.now().strftime('%I:%M %p')}")
        
        elif command == 'date':
            self.speak(f"Today is {datetime.now().strftime('%B %d, %Y')}")
        
        elif command == 'help':
            self.show_help()
        
        elif command == 'exit':
            self.speak("Goodbye")
            return "exit"
        
        return True
    
    def show_help(self):
        print("\n" + "="*60)
        print("COMMANDS")
        print("="*60)
        print("\nOPEN APPS: 'open notepad', 'open calculator', 'open chrome'")
        print("SYSTEM: shutdown, restart, lock, screenshot")
        print("VOLUME: volume up, volume down, mute")
        print("TASKS: add task [task], show tasks, complete task [n], delete task [n]")
        print("NOTES: remember [note], show notes, delete note [n]")
        print("TIME: time, date")
        print("GENERAL: help, exit")
        print("="*60)
        self.speak("Check console for commands")
    
    def _save_memory(self):
        with open(self.memory_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    # ====================================================================
    # MAIN LOOP
    def run(self):
        print("\n" + "="*60)
        print("AGENT RUNNING WITH ML CLASSIFIER")
        print(f"Hotkey: {self.hotkey.upper()} (press and hold)")
        print("Press Ctrl+C to exit")
        print("="*60 + "\n")
        
        self.speak("Ready. Press F2 to talk.")
        recording = False
        
        try:
            while self.running:
                if keyboard.is_pressed(self.hotkey):
                    if not recording:
                        recording = True
                        self.start_recording()
                    time.sleep(0.1)
                else:
                    if recording:
                        recording = False
                        audio_file = self.stop_recording()
                        if audio_file:
                            text = self.speech_to_text(audio_file)
                            if text:
                                result = self.classify_and_execute(text)
                                if result == "exit":
                                    break
                            try:
                                os.remove(audio_file)
                            except:
                                pass
                time.sleep(0.05)
        except KeyboardInterrupt:
            pass
        finally:
            self.speak("Agent stopped")
            print("\nGoodbye!")

if __name__ == "__main__":
    agent = VoiceAgent()
    agent.run()
