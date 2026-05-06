import cv2
import mediapipe as mp
import numpy as np
from kinematics import KinematicsCalculator
from logic import ExerciseStateMachine
from feedback import AudioManager, VisualFeedbackController
from logger import SessionLogger

def start_tracking(source, exercise, side, stop_event):
    """
    Main Tracking Engine Loop.
    Integrates all modules: Pose Tracking, Math, Logic, Feedback, and Logging.
    """
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        min_detection_confidence=0.5, 
        min_tracking_confidence=0.5
    )

    # --- Model Warm-up (Eliminate Cold-Start Latency) ---
    print("Warming up MediaPipe Pose model...")
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    pose.process(dummy_frame)
    print("Model warm-up complete.")

    cap = cv2.VideoCapture(source)

    # --- FPS Regulation ---
    # Determine if source is live camera or video file
    if isinstance(source, str):
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0 or fps is None:
            fps = 30
        frame_delay = int(1000 / fps)
    else:
        # Live camera (e.g. source is 0)
        frame_delay = 1

    if exercise == "Biceps Curls":
        if side == "Left":
            target_indices = [11, 13, 15] # Shoulder, Elbow, Wrist
        else:
            target_indices = [12, 14, 16]
    else:
        if side == "Left":
            target_indices = [23, 25, 27] # Hip, Knee, Ankle
        else:
            target_indices = [24, 26, 28]
        
    print(f"--- Starting tracking for {exercise} - {side} Side ---")
    
    # Initialize Core Modules
    state_machine = ExerciseStateMachine(exercise)
    audio_manager = AudioManager()
    session_logger = SessionLogger(exercise, side)

    current_visual_warning = None
    warning_frames_remaining = 0

    # The loop will naturally break if stop_event is set by the UI
    while cap.isOpened() and not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print("Video stream ended or cannot be read.")
            break

        # --- Resize high-resolution frames (bounding box) to fit the screen ---
        max_width = 1000
        max_height = 800
        h, w, _ = frame.shape
        scale_w = max_width / w
        scale_h = max_height / h
        scale = min(scale_w, scale_h)
        
        if scale < 1.0:
            new_width = int(w * scale)
            new_height = int(h * scale)
            frame = cv2.resize(frame, (new_width, new_height))

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            h, w, _ = frame.shape
            
            pts = []
            visible = True
            for idx in target_indices:
                lm = landmarks[idx]
                if lm.visibility > 0.4:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    pts.append((cx, cy))
                    cv2.circle(frame, (cx, cy), 8, (0, 255, 0), cv2.FILLED)
                else:
                    pts.append(None)
                    visible = False
            
            if visible and len(pts) == 3:
                p1, p2, p3 = pts[0], pts[1], pts[2]
                
                # Draw skeleton lines
                cv2.line(frame, p1, p2, (255, 0, 0), 4)
                cv2.line(frame, p2, p3, (255, 0, 0), 4)

                # Phase 3: Kinematics
                joint_angle = KinematicsCalculator.calculate_angle(p1, p2, p3)
                elevation_angle = KinematicsCalculator.calculate_elevation_angle(p1, p3)
                
                # Phase 4: State Machine
                correct, incorrect = state_machine.update(joint_angle, elevation_angle, p3[1])
                
                # Phase 6: Session Logging
                session_logger.update(joint_angle, correct, incorrect)
                
                # Phase 5: Feedback Management
                VisualFeedbackController.draw_angles(frame, p2, p3, joint_angle, elevation_angle)
                
                audio_cue = state_machine.get_audio_cue()
                if audio_cue:
                    # Force playback so critical rep completion feedback is never blocked by cooldown
                    audio_manager.play(audio_cue, force=True)
                
                if state_machine.current_warning:
                    current_visual_warning = state_machine.current_warning
                    warning_frames_remaining = 30 
                
                display_warning = current_visual_warning if warning_frames_remaining > 0 else None
                VisualFeedbackController.draw_overlay(frame, exercise, correct, incorrect, display_warning)
                
                if warning_frames_remaining > 0:
                    warning_frames_remaining -= 1

        cv2.imshow('AI Physical Therapy Tracker - Press ESC to Exit', frame)

        # Allow user to close specifically the OpenCV window using ESC
        if cv2.waitKey(frame_delay) & 0xFF == 27: 
            break

    # --- Phase 6: Graceful Teardown & Export ---
    print("\n--- Session Terminated. Saving Data... ---")
    session_logger.export()
    
    # Safely terminate audio background thread
    audio_manager.stop()
    
    # Release camera and window resources
    cap.release()
    cv2.destroyAllWindows()
    pose.close()
