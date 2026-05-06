import customtkinter as ctk
from tkinter import filedialog
import threading
from tracker import start_tracking

# Configure Modern Appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class PhysicalTherapyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI Physical Therapy Engine")
        self.geometry("500x380")
        
        # Configure layout
        self.grid_columnconfigure(0, weight=1)

        # Thread management for graceful exit
        self.tracking_thread = None
        self.stop_event = threading.Event()

        # Handle window close event to ensure background cleanup
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Main Title
        self.title_label = ctk.CTkLabel(
            self, 
            text="Rehabilitation Tracker", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 20))

        # Exercise Selector
        self.exercise_label = ctk.CTkLabel(self, text="1. Select Exercise:", font=ctk.CTkFont(weight="bold"))
        self.exercise_label.grid(row=1, column=0, padx=40, pady=(10, 0), sticky="w")
        
        self.exercise_var = ctk.StringVar(value="Heel Slides")
        self.exercise_cb = ctk.CTkComboBox(
            self, 
            values=["Heel Slides", "Straight Leg Raise"], 
            variable=self.exercise_var,
            state="readonly",
            width=250
        )
        self.exercise_cb.grid(row=2, column=0, padx=40, pady=(5, 15), sticky="w")

        # Side Selector
        self.side_label = ctk.CTkLabel(self, text="2. Select Target Side:", font=ctk.CTkFont(weight="bold"))
        self.side_label.grid(row=3, column=0, padx=40, pady=(10, 0), sticky="w")
        
        self.side_var = ctk.StringVar(value="Left")
        self.side_cb = ctk.CTkComboBox(
            self, 
            values=["Left", "Right"], 
            variable=self.side_var,
            state="readonly",
            width=250
        )
        self.side_cb.grid(row=4, column=0, padx=40, pady=(5, 25), sticky="w")

        # Buttons Frame
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.grid(row=5, column=0, padx=40, pady=(10, 20), sticky="w")

        self.camera_btn = ctk.CTkButton(
            self.button_frame, 
            text="Open Live Camera", 
            command=self.open_camera,
            width=140
        )
        self.camera_btn.pack(side="left", padx=(0, 15))

        self.video_btn = ctk.CTkButton(
            self.button_frame, 
            text="Upload Video", 
            command=self.upload_video,
            fg_color="#4b5563",
            hover_color="#374151",
            width=140
        )
        self.video_btn.pack(side="left")

    def open_camera(self):
        self.run_tracker(0)

    def upload_video(self):
        file_path = filedialog.askopenfilename(
            title="Select a Video",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov")]
        )
        if file_path:
            self.run_tracker(file_path)

    def run_tracker(self, source):
        """
        Safely stops any active session and initiates a new tracking thread.
        Passes down a threading.Event flag for graceful termination.
        """
        if self.tracking_thread and self.tracking_thread.is_alive():
            self.stop_event.set()
            self.tracking_thread.join(timeout=2.0)
            
        self.stop_event.clear()
        
        exercise = self.exercise_var.get()
        side = self.side_var.get()
        
        self.tracking_thread = threading.Thread(
            target=start_tracking, 
            args=(source, exercise, side, self.stop_event),
            daemon=True
        )
        self.tracking_thread.start()

    def on_closing(self):
        """
        Safely terminate all background threads and release resources 
        when the user clicks the 'X' button on the UI window.
        """
        self.stop_event.set()
        if self.tracking_thread and self.tracking_thread.is_alive():
            self.tracking_thread.join(timeout=2.0)
        self.destroy()

if __name__ == "__main__":
    app = PhysicalTherapyApp()
    app.mainloop()
