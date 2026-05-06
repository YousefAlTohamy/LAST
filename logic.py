import random

class ExerciseStateMachine:
    """
    Independent State Machine for tracking exercise phases and counting reps.
    Applies strict physical therapy rules to evaluate correct and incorrect repetitions.
    """
    def __init__(self, exercise_name):
        self.exercise_name = exercise_name
        
        # We explicitly use stages to ensure clean resets between reps
        self.state = "RESTING" 
        
        self.correct_reps = 0
        self.incorrect_reps = 0
        
        self.min_knee_angle_during_rep = 180.0
        self.initial_ankle_y = None
        
        self.current_warning = None
        
        # High-Priority Event flags that trigger EXACTLY once per rep completion
        self.rep_completed_correctly = False
        self.rep_completed_with_error = False
        
        # Random positive affirmation pool
        self.positive_phrases = ["Good job", "Perfect", "Well done", "Great form", "Keep it up"]

    def _reset_rep_tracking(self, new_state, ankle_y=None, knee_angle=180.0):
        """Forces a clean reset of all internal phase flags to catch the next full ROM."""
        self.state = new_state
        self.min_knee_angle_during_rep = knee_angle
        if ankle_y is not None:
            self.initial_ankle_y = ankle_y

    def update(self, knee_angle, elevation_angle, ankle_y):
        """
        Main entry point for the state machine loop.
        """
        # Reset transient triggers every frame
        self.current_warning = None
        self.rep_completed_correctly = False
        self.rep_completed_with_error = False
        
        if self.exercise_name == "Heel Slides":
            return self._update_heel_slides(knee_angle, ankle_y)
        elif self.exercise_name == "Straight Leg Raise":
            return self._update_straight_leg_raise(knee_angle, elevation_angle)
        
        return self.correct_reps, self.incorrect_reps

    def _update_heel_slides(self, knee_angle, ankle_y):
        if self.initial_ankle_y is None and self.state in ["RESTING", "EXTENDED"]:
            self.initial_ankle_y = ankle_y

        # Error check: Foot lift
        if self.state != "RESTING" and self.initial_ankle_y is not None:
            if (self.initial_ankle_y - ankle_y) > 45: 
                self.incorrect_reps += 1
                self.rep_completed_with_error = True
                self.current_warning = "WARNING: Do not lift your heel"
                
                # CLEAN RESET for the next repetition
                self._reset_rep_tracking("RESTING", ankle_y=ankle_y)
                return self.correct_reps, self.incorrect_reps

        # Standard Phase Progression
        if self.state == "RESTING":
            if knee_angle > 160:
                self._reset_rep_tracking("EXTENDED", ankle_y=ankle_y)
                
        elif self.state == "EXTENDED":
            if knee_angle < 150: 
                self.state = "FLEXING"
                self.min_knee_angle_during_rep = knee_angle
                
        elif self.state == "FLEXING":
            if knee_angle < self.min_knee_angle_during_rep:
                self.min_knee_angle_during_rep = knee_angle
            if knee_angle < 110: 
                self.state = "FLEXED"
                
        elif self.state == "FLEXED":
            if knee_angle > 120: 
                self.state = "EXTENDING"
                
        elif self.state == "EXTENDING":
            if knee_angle > 160: 
                self.correct_reps += 1
                self.rep_completed_correctly = True
                
                # CLEAN RESET for the next repetition
                self._reset_rep_tracking("EXTENDED", ankle_y=ankle_y)

        return self.correct_reps, self.incorrect_reps

    def _update_straight_leg_raise(self, knee_angle, elevation_angle):
        # Error check: Knee bent during ROM
        if self.state in ["LIFTING", "RAISED", "LOWERING"]:
            if knee_angle < 160:
                self.incorrect_reps += 1
                self.rep_completed_with_error = True
                self.current_warning = "WARNING: Keep your knee straight"
                
                # CLEAN RESET for the next repetition
                self._reset_rep_tracking("RESTING", knee_angle=knee_angle)
                return self.correct_reps, self.incorrect_reps

        # Standard Phase Progression
        if self.state == "RESTING":
            if elevation_angle < 15:
                self._reset_rep_tracking("FLAT", knee_angle=knee_angle)
                
        elif self.state == "FLAT":
            if elevation_angle > 20: 
                self.state = "LIFTING"
                self.min_knee_angle_during_rep = knee_angle
                
        elif self.state == "LIFTING":
            if knee_angle < self.min_knee_angle_during_rep:
                self.min_knee_angle_during_rep = knee_angle
            if elevation_angle > 45: 
                self.state = "RAISED"
                
        elif self.state == "RAISED":
            if knee_angle < self.min_knee_angle_during_rep:
                self.min_knee_angle_during_rep = knee_angle
            if elevation_angle < 35: 
                self.state = "LOWERING"
                
        elif self.state == "LOWERING":
            if knee_angle < self.min_knee_angle_during_rep:
                self.min_knee_angle_during_rep = knee_angle
            if elevation_angle < 15: 
                # Valid Completion check
                if self.min_knee_angle_during_rep < 160:
                    self.incorrect_reps += 1
                    self.rep_completed_with_error = True
                    self.current_warning = "WARNING: Keep your knee straight"
                else:
                    self.correct_reps += 1
                    self.rep_completed_correctly = True
                
                # CLEAN RESET for the next repetition
                self._reset_rep_tracking("FLAT", knee_angle=knee_angle)

        return self.correct_reps, self.incorrect_reps

    def get_audio_cue(self):
        """
        Discrete event trigger: only fires exactly once when a rep completes.
        Returns the specific voice cue to be spoken.
        """
        if self.rep_completed_correctly:
            return random.choice(self.positive_phrases)
            
        if self.rep_completed_with_error:
            if self.exercise_name == "Heel Slides":
                return "Error. Please keep your heel flat on the bed."
            elif self.exercise_name == "Straight Leg Raise":
                return "Error. Keep your knee completely straight while lifting."
                
        return None
