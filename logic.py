class ExerciseStateMachine:
    """
    Independent State Machine for tracking exercise phases and counting reps.
    Applies strict physical therapy rules to evaluate correct and incorrect repetitions.
    """
    def __init__(self, exercise_name):
        self.exercise_name = exercise_name
        self.state = "RESTING"
        
        self.correct_reps = 0
        self.incorrect_reps = 0
        
        # State tracking variables
        self.min_knee_angle_during_rep = 180.0
        self.initial_ankle_y = None
        
        # Feedback variables
        self.current_warning = None
        self.just_completed_correct_rep = False

    def update(self, knee_angle, elevation_angle, ankle_y):
        """
        Main entry point for the state machine loop.
        Dispatches to the specific exercise logic based on the selected exercise.
        """
        # Reset transient flags for the current frame
        self.current_warning = None
        self.just_completed_correct_rep = False
        
        if self.exercise_name == "Heel Slides":
            return self._update_heel_slides(knee_angle, ankle_y)
        elif self.exercise_name == "Straight Leg Raise":
            return self._update_straight_leg_raise(knee_angle, elevation_angle)
        
        return self.correct_reps, self.incorrect_reps

    def _update_heel_slides(self, knee_angle, ankle_y):
        if self.initial_ankle_y is None and self.state in ["RESTING", "EXTENDED"]:
            self.initial_ankle_y = ankle_y

        # Error Detection: Did the patient lift their foot?
        if self.state != "RESTING" and self.initial_ankle_y is not None:
            if (self.initial_ankle_y - ankle_y) > 45: 
                self.incorrect_reps += 1
                self.state = "RESTING" 
                self.initial_ankle_y = ankle_y 
                self.current_warning = "WARNING: Do not lift your heel"
                return self.correct_reps, self.incorrect_reps

        # Standard State Progression
        if self.state == "RESTING":
            if knee_angle > 160:
                self.state = "EXTENDED"
                self.initial_ankle_y = ankle_y 
                
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
                self.just_completed_correct_rep = True
                self.state = "EXTENDED"
                self.initial_ankle_y = ankle_y 

        return self.correct_reps, self.incorrect_reps

    def _update_straight_leg_raise(self, knee_angle, elevation_angle):
        # Immediate Error Detection during the movement
        if self.state in ["LIFTING", "RAISED", "LOWERING"]:
            if knee_angle < 160:
                self.incorrect_reps += 1
                self.state = "RESTING" 
                self.current_warning = "WARNING: Keep your knee straight"
                return self.correct_reps, self.incorrect_reps

        # Standard State Progression
        if self.state == "RESTING":
            if elevation_angle < 15:
                self.state = "FLAT"
                self.min_knee_angle_during_rep = knee_angle
                
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
                # Validation of the completed movement
                if self.min_knee_angle_during_rep < 160:
                    self.incorrect_reps += 1
                    self.current_warning = "WARNING: Keep your knee straight"
                else:
                    self.correct_reps += 1
                    self.just_completed_correct_rep = True
                self.state = "FLAT"

        return self.correct_reps, self.incorrect_reps

    def get_audio_cue(self):
        """
        Returns the specific voice cue to be spoken based on the current state.
        Removes the 'WARNING: ' prefix for natural speech.
        """
        if self.current_warning:
            return self.current_warning.replace("WARNING: ", "")
        if self.just_completed_correct_rep:
            return "Good job"
        return None
