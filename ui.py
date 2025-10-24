import customtkinter as ctk
import threading
import time
from typing import Dict, Any


class MapleBotUI:
    def __init__(self, settings: Dict[str, Any], start_callback, stop_callback):
        self.settings = settings
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.running = False
        self.lang = self.load_language()

        ctk.set_appearance_mode(settings.get('ui', {}).get('theme', 'dark'))
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title(self.lang['title'])
        self.root.geometry("400x300")

        self.status_label = ctk.CTkLabel(self.root, text=self.lang['status_stopped'])
        self.status_label.pack(pady=20)

        self.start_button = ctk.CTkButton(self.root, text=self.lang['start'], command=self.start_bot)
        self.start_button.pack(pady=10)

        self.stop_button = ctk.CTkButton(self.root, text=self.lang['stop'], command=self.stop_bot, state="disabled")
        self.stop_button.pack(pady=10)

        self.lang_button = ctk.CTkButton(self.root, text=self.lang['switch_lang'], command=self.switch_language)
        self.lang_button.pack(pady=10)

    def load_language(self):
        lang_code = self.settings.get('ui', {}).get('language', 'en')
        if lang_code == 'ko':
            return {
                'title': '메이플랜드 봇',
                'status_stopped': '상태: 중지됨',
                'status_running': '상태: 실행중',
                'start': '시작',
                'stop': '중지',
                'switch_lang': '언어 전환'
            }
        else:
            return {
                'title': 'MapleLand Bot',
                'status_stopped': 'Status: Stopped',
                'status_running': 'Status: Running',
                'start': 'Start',
                'stop': 'Stop',
                'switch_lang': 'Switch Language'
            }

    def switch_language(self):
        current_lang = self.settings['ui']['language']
        new_lang = 'ko' if current_lang == 'en' else 'en'
        self.settings['ui']['language'] = new_lang
        self.lang = self.load_language()
        self.update_ui_texts()

    def update_ui_texts(self):
        self.root.title(self.lang['title'])
        self.status_label.configure(text=self.lang['status_stopped'] if not self.running else self.lang['status_running'])
        self.start_button.configure(text=self.lang['start'])
        self.stop_button.configure(text=self.lang['stop'])
        self.lang_button.configure(text=self.lang['switch_lang'])

    def start_bot(self):
        if not self.running:
            self.running = True
            self.status_label.configure(text=self.lang['status_running'])
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            threading.Thread(target=self.start_callback, daemon=True).start()

    def stop_bot(self):
        if self.running:
            self.running = False
            self.status_label.configure(text=self.lang['status_stopped'])
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.stop_callback()

    def run(self):
        self.root.mainloop()