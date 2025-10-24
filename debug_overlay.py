import tkinter as tk
from typing import Any, Dict


class DebugOverlay:
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.enabled = settings.get('debug', {}).get('enable_debug', False)
        if self.enabled:
            self.root = tk.Tk()
            self.root.attributes("-topmost", True)
            self.root.attributes("-alpha", 0.7)
            self.root.overrideredirect(True)
            self.root.geometry("300x200+10+10")
            
            self.hp_label = tk.Label(self.root, text="HP: --/--", font=("Arial", 12), bg="black", fg="white")
            self.hp_label.pack()
            self.mp_label = tk.Label(self.root, text="MP: --/--", font=("Arial", 12), bg="black", fg="white")
            self.mp_label.pack()
            self.pos_label = tk.Label(self.root, text="Pos: --,--", font=("Arial", 12), bg="black", fg="white")
            self.pos_label.pack()
            self.action_label = tk.Label(self.root, text="Action: Idle", font=("Arial", 12), bg="black", fg="white")
            self.action_label.pack()
        else:
            self.root = None

    def update(self, hp_current, hp_max, mp_current, mp_max, char_x, char_y, action):
        if self.enabled and self.root:
            self.hp_label.config(text=f"HP: {hp_current}/{hp_max}")
            self.mp_label.config(text=f"MP: {mp_current}/{mp_max}")
            self.pos_label.config(text=f"Pos: {char_x},{char_y}")
            self.action_label.config(text=f"Action: {action}")
            self.root.update()

    def run(self):
        if self.enabled and self.root:
            self.root.mainloop()