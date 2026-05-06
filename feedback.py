import cv2
import threading
import queue
import time
import subprocess

class AudioManager:
    """
    Manages asynchronous Text-to-Speech audio feedback.
    Uses native Windows PowerShell to provide instant, deadlock-free speech.
    """
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.last_played = {}
        self.cooldown = 3.0 
        
        self.thread = threading.Thread(target=self._audio_worker, daemon=True)
        self.thread.start()

    def _audio_worker(self):
        """
        Background worker that continuously pulls messages from the queue.
        Executes a hidden PowerShell command for instant TTS.
        """
        while True:
            message = self.audio_queue.get()
            
            if message is None:
                self.audio_queue.task_done()
                break 
                
            print(f"--> [AUDIO THREAD] Speaking instantly: {message}")
            try:
                # Fast native Windows TTS command
                ps_command = f'powershell -Command "Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Speak(\'{message}\');"'
                
                # Run it synchronously inside this background thread (blocks only this thread, not the camera)
                subprocess.run(ps_command, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                
                print(f"--> [AUDIO THREAD] Finished: {message}")
            except Exception as e:
                print(f"--> [AUDIO THREAD] PowerShell TTS Error: {e}")
            finally:
                self.audio_queue.task_done()

    def play(self, message, force=False):
        """Enqueue a message for speech."""
        if not message:
            return

        current_time = time.time()
        
        # High Priority / Discrete Events bypass deduplication completely
        if force:
            self.audio_queue.put(message)
            return
            
        # General spam-prevention for non-forced continuous warnings
        if message in self.last_played and (current_time - self.last_played[message]) < self.cooldown:
            return 
                
        self.last_played[message] = current_time
        self.audio_queue.put(message)

    def stop(self):
        """Safely stops the background audio thread."""
        self.audio_queue.put(None)
        if self.thread.is_alive():
            self.thread.join(timeout=2.0)

class VisualFeedbackController:
    """
    Handles drawing clean overlays and diagnostic graphics on the video frame.
    """
    @staticmethod
    def draw_overlay(frame, exercise_name, correct, incorrect, warning_text=None):
        h, w, _ = frame.shape
        
        # Transparent overlay box
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (320, 140), (0, 0, 0), cv2.FILLED)
        
        alpha = 0.6
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # Title and Counters
        cv2.putText(frame, exercise_name, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Correct Reps: {correct}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Errors: {incorrect}", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Warning Text at bottom center
        if warning_text:
            text_size = cv2.getTextSize(warning_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 3)[0]
            text_x = (w - text_size[0]) // 2
            text_y = h - 50
            cv2.putText(frame, warning_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

    @staticmethod
    def draw_angles(frame, knee_pos, ankle_pos, knee_angle, elevation_angle):
        if knee_pos:
            cv2.putText(frame, f"{int(knee_angle)} deg", (knee_pos[0] + 20, knee_pos[1]), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        if ankle_pos:
            cv2.putText(frame, f"Elev: {int(elevation_angle)} deg", (ankle_pos[0] + 20, ankle_pos[1]), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
