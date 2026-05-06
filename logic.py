import random

class ExerciseStateMachine:
    """
    Independent State Machine for tracking exercise phases and counting reps.
    """
    def __init__(self, exercise_name):
        self.exercise_name = exercise_name
        
        # We explicitly use stages to ensure clean resets between reps
        self.state = "RESTING" 
        
        self.correct_reps = 0
        self.incorrect_reps = 0
        
        # Track the minimum angle achieved during a single repetition
        self.min_joint_angle_during_rep = 180.0
        self.initial_end_effector_y = None
        
        self.current_warning = None
        
        # High-Priority Event flags that trigger EXACTLY once per rep completion
        self.rep_completed_correctly = False
        self.rep_completed_with_error = False
        
        # --- Configurable Biomechanical Angle Thresholds ---
        # Heel Slides (Legs)
        self.HEEL_SLIDE_EXTENDED_KNEE = 160 
        self.HEEL_SLIDE_TARGET_FLEXION = 110 
        self.HEEL_SLIDE_FOOT_LIFT_TOLERANCE = 45 # Pixels
        
        # Straight Leg Raise (Legs)
        self.SLR_FLAT_ELEVATION = 15
        self.SLR_TARGET_ELEVATION = 45 
        self.SLR_STRAIGHT_KNEE_MIN = 160 

        # Biceps Curls (Arms)
        self.BICEP_EXTENDED_ELBOW = 150
        self.BICEP_FLEXED_ELBOW = 45
        
        # Random positive affirmation pool
        self.positive_phrases = ["Good job", "Perfect", "Well done", "Great form", "Keep it up"]

    def _reset_rep_tracking(self, new_state, end_effector_y=None, joint_angle=180.0):
        """Forces a clean reset of all internal phase flags to catch the next full ROM."""
        self.state = new_state
        self.min_joint_angle_during_rep = joint_angle
        if end_effector_y is not None:
            self.initial_end_effector_y = end_effector_y

    def update(self, joint_angle, elevation_angle, end_effector_y):
        """
        Main entry point for the state machine loop.
        """
        # Reset transient triggers every frame
        self.current_warning = None
        self.rep_completed_correctly = False
        self.rep_completed_with_error = False
        
        if self.exercise_name == "Heel Slides":
            return self._update_heel_slides(joint_angle, end_effector_y)
        elif self.exercise_name == "Straight Leg Raise":
            return self._update_straight_leg_raise(joint_angle, elevation_angle)
        elif self.exercise_name == "Biceps Curls":
            return self._update_biceps_curls(joint_angle)
        
        return self.correct_reps, self.incorrect_reps

    def _update_heel_slides(self, knee_angle, ankle_y):
        if self.initial_end_effector_y is None and self.state in ["RESTING", "EXTENDED"]:
            self.initial_end_effector_y = ankle_y

        # Error check: Foot lift
        if self.state != "RESTING" and self.initial_end_effector_y is not None:
            if (self.initial_end_effector_y - ankle_y) > self.HEEL_SLIDE_FOOT_LIFT_TOLERANCE: 
                self.incorrect_reps += 1
                self.rep_completed_with_error = True
                self.current_warning = "WARNING: Do not lift your heel"
                
                # CLEAN RESET for the next repetition
                self._reset_rep_tracking("RESTING", end_effector_y=ankle_y)
                return self.correct_reps, self.incorrect_reps

        # Standard Phase Progression
        if self.state == "RESTING":
            if knee_angle > self.HEEL_SLIDE_EXTENDED_KNEE:
                self._reset_rep_tracking("EXTENDED", end_effector_y=ankle_y)
                
        elif self.state == "EXTENDED":
            if knee_angle < (self.HEEL_SLIDE_EXTENDED_KNEE - 10): 
                self.state = "FLEXING"
                self.min_joint_angle_during_rep = knee_angle
                
        elif self.state == "FLEXING":
            if knee_angle < self.min_joint_angle_during_rep:
                self.min_joint_angle_during_rep = knee_angle
            if knee_angle < self.HEEL_SLIDE_TARGET_FLEXION: 
                self.state = "FLEXED"
                
        elif self.state == "FLEXED":
            if knee_angle > (self.HEEL_SLIDE_TARGET_FLEXION + 10): 
                self.state = "EXTENDING"
                
        elif self.state == "EXTENDING":
            if knee_angle > self.HEEL_SLIDE_EXTENDED_KNEE: 
                self.correct_reps += 1
                self.rep_completed_correctly = True
                
                # CLEAN RESET for the next repetition
                self._reset_rep_tracking("EXTENDED", end_effector_y=ankle_y)

        return self.correct_reps, self.incorrect_reps

    def _update_straight_leg_raise(self, knee_angle, elevation_angle):
        # Error check: Knee bent during ROM
        if self.state in ["LIFTING", "RAISED", "LOWERING"]:
            if knee_angle < self.SLR_STRAIGHT_KNEE_MIN:
                self.incorrect_reps += 1
                self.rep_completed_with_error = True
                self.current_warning = "WARNING: Keep your knee straight"
                
                # CLEAN RESET for the next repetition
                self._reset_rep_tracking("RESTING", joint_angle=knee_angle)
                return self.correct_reps, self.incorrect_reps

        # Standard Phase Progression
        if self.state == "RESTING":
            if elevation_angle < self.SLR_FLAT_ELEVATION:
                self._reset_rep_tracking("FLAT", joint_angle=knee_angle)
                
        elif self.state == "FLAT":
            if elevation_angle > (self.SLR_FLAT_ELEVATION + 5): 
                self.state = "LIFTING"
                self.min_joint_angle_during_rep = knee_angle
                
        elif self.state == "LIFTING":
            if knee_angle < self.min_joint_angle_during_rep:
                self.min_joint_angle_during_rep = knee_angle
            if elevation_angle > self.SLR_TARGET_ELEVATION: 
                self.state = "RAISED"
                
        elif self.state == "RAISED":
            if knee_angle < self.min_joint_angle_during_rep:
                self.min_joint_angle_during_rep = knee_angle
            if elevation_angle < (self.SLR_TARGET_ELEVATION - 10): 
                self.state = "LOWERING"
                
        elif self.state == "LOWERING":
            if knee_angle < self.min_joint_angle_during_rep:
                self.min_joint_angle_during_rep = knee_angle
            if elevation_angle < self.SLR_FLAT_ELEVATION: 
                # Valid Completion check
                if self.min_joint_angle_during_rep < self.SLR_STRAIGHT_KNEE_MIN:
                    self.incorrect_reps += 1
                    self.rep_completed_with_error = True
                    self.current_warning = "WARNING: Keep your knee straight"
                else:
                    self.correct_reps += 1
                    self.rep_completed_correctly = True
                
                # CLEAN RESET for the next repetition
                self._reset_rep_tracking("FLAT", joint_angle=knee_angle)

        return self.correct_reps, self.incorrect_reps

    def _update_biceps_curls(self, elbow_angle):
        if self.state == "RESTING":
            if elbow_angle > self.BICEP_EXTENDED_ELBOW:
                self._reset_rep_tracking("EXTENDED", joint_angle=elbow_angle)
                
        elif self.state == "EXTENDED":
            if elbow_angle < (self.BICEP_EXTENDED_ELBOW - 10): 
                self.state = "FLEXING"
                self.min_joint_angle_during_rep = elbow_angle
                
        elif self.state == "FLEXING":
            if elbow_angle < self.min_joint_angle_during_rep:
                self.min_joint_angle_during_rep = elbow_angle
                
            if elbow_angle < self.BICEP_FLEXED_ELBOW: 
                self.state = "FLEXED"
                
            # Error check: If extending before reaching target flexion
            if elbow_angle > (self.min_joint_angle_during_rep + 15) and self.min_joint_angle_during_rep > self.BICEP_FLEXED_ELBOW:
                self.incorrect_reps += 1
                self.rep_completed_with_error = True
                self.current_warning = "WARNING: Complete the full curl"
                self._reset_rep_tracking("RESTING", joint_angle=elbow_angle)
                return self.correct_reps, self.incorrect_reps
                
        elif self.state == "FLEXED":
            if elbow_angle > (self.BICEP_FLEXED_ELBOW + 10): 
                self.state = "EXTENDING"
                
        elif self.state == "EXTENDING":
            if elbow_angle > self.BICEP_EXTENDED_ELBOW: 
                self.correct_reps += 1
                self.rep_completed_correctly = True
                self._reset_rep_tracking("EXTENDED", joint_angle=elbow_angle)

        return self.correct_reps, self.incorrect_reps


    def get_audio_cue(self):
        """
        Discrete event trigger: only fires exactly once when a rep completes.
        Returns the specific voice cue to be spoken.
        """
        cue = None
        if self.rep_completed_correctly:
            cue = random.choice(self.positive_phrases)
            
        elif self.rep_completed_with_error:
            if self.exercise_name == "Heel Slides":
                cue = "Error. Please keep your heel flat on the bed."
            elif self.exercise_name == "Straight Leg Raise":
                cue = "Error. Keep your knee completely straight while lifting."
            elif self.exercise_name == "Biceps Curls":
                cue = "Error. Please complete the full range of motion."
                
        if cue:
            print(f"--> [LOGIC STATE] Triggering audio: {cue}")
            
        return cue
