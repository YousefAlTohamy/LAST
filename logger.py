import json
import datetime
import os

class SessionLogger:
    """
    Handles logging of session data and exporting it to a JSON file.
    Follows Single Responsibility Principle (SRP) for data persistence.
    """
    def __init__(self, exercise_name, side):
        self.exercise_name = exercise_name
        self.side = side
        self.start_time = datetime.datetime.now()
        
        # Track min/max performance metrics
        self.max_knee_angle = 0.0
        self.min_knee_angle = 360.0
        
        # Track final scores
        self.correct_reps = 0
        self.incorrect_reps = 0

    def update(self, knee_angle, correct_reps, incorrect_reps):
        """Called every frame to update metrics."""
        if knee_angle > self.max_knee_angle:
            self.max_knee_angle = knee_angle
        if knee_angle < self.min_knee_angle:
            self.min_knee_angle = knee_angle
            
        self.correct_reps = correct_reps
        self.incorrect_reps = incorrect_reps

    def export(self):
        """Generates a JSON report when the session terminates."""
        end_time = datetime.datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Handle edge case where no data was recorded (e.g. tracking closed immediately)
        if self.min_knee_angle == 360.0:
            self.min_knee_angle = 0.0
            
        report = {
            "session_date": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "exercise": self.exercise_name,
            "side": self.side,
            "duration_seconds": round(duration, 2),
            "performance": {
                "correct_reps": self.correct_reps,
                "incorrect_reps": self.incorrect_reps,
                "max_knee_extension_deg": round(self.max_knee_angle, 2),
                "max_knee_flexion_deg": round(self.min_knee_angle, 2)
            }
        }
        
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        
        log_dir = "sessions"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        filepath = os.path.join(log_dir, f"session_report_{timestamp}.json")
        
        try:
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=4)
            print(f"Session data exported successfully to {filepath}")
        except Exception as e:
            print(f"Failed to export session data: {e}")
