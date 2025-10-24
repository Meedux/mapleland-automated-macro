import customtkinter as ctk
import threading
import time
import json
from pathlib import Path
from typing import Dict, Any


class MapleBotUI:
    def __init__(self, settings: Dict[str, Any], start_callback, stop_callback, settings_path: Path):
        self.settings = settings
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.settings_path = settings_path
        self.running = False
        self.lang = self.load_language()

        ctk.set_appearance_mode(settings.get('ui', {}).get('theme', 'dark'))
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title(self.lang['title'])
        self.root.geometry("600x500")
        self.root.resizable(True, True)

        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.status_label = ctk.CTkLabel(self.main_frame, text=self.lang['status_stopped'])
        self.status_label.pack(pady=20)

        self.start_button = ctk.CTkButton(self.main_frame, text=self.lang['start'], command=self.start_bot)
        self.start_button.pack(pady=10)

        self.stop_button = ctk.CTkButton(self.main_frame, text=self.lang['stop'], command=self.stop_bot, state="disabled")
        self.stop_button.pack(pady=10)

        self.settings_button = ctk.CTkButton(self.main_frame, text=self.lang['settings'], command=self.show_settings)
        self.settings_button.pack(pady=10)

        self.lang_button = ctk.CTkButton(self.main_frame, text=self.lang['switch_lang'], command=self.switch_language)
        self.lang_button.pack(pady=10)

        self.settings_frame = ctk.CTkFrame(self.root)
        # Settings frame will be populated in show_settings

    def load_language(self):
        lang_code = self.settings.get('ui', {}).get('language', 'en')
        if lang_code == 'ko':
            return {
                'title': '메이플랜드 봇',
                'status_stopped': '상태: 중지됨',
                'status_running': '상태: 실행중',
                'start': '시작',
                'stop': '중지',
                'settings': '설정',
                'switch_lang': '언어 전환',
                'save': '저장',
                'back': '뒤로'
            }
        else:
            return {
                'title': 'MapleLand Bot',
                'status_stopped': 'Status: Stopped',
                'status_running': 'Status: Running',
                'start': 'Start',
                'stop': 'Stop',
                'settings': 'Settings',
                'switch_lang': 'Switch Language',
                'save': 'Save',
                'back': 'Back'
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
        self.settings_button.configure(text=self.lang['settings'])
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
            self.stop_button.configure(text=self.lang['stop'], state="disabled")
            self.stop_callback()

    def show_settings(self):
        self.main_frame.pack_forget()
        self.settings_frame.pack(fill="both", expand=True, padx=20, pady=20)

        if not hasattr(self, 'settings_scrollable'):
            self.settings_scrollable = ctk.CTkScrollableFrame(self.settings_frame)
            self.settings_scrollable.pack(fill="both", expand=True, padx=10, pady=10)

            self.entries = {}

            # Back button
            back_button = ctk.CTkButton(self.settings_frame, text=self.lang['back'], command=self.show_main)
            back_button.pack(pady=10)

            # Hotkeys
            ctk.CTkLabel(self.settings_scrollable, text="Hotkeys", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10,5))
            for key in ['start', 'stop', 'loot']:
                frame = ctk.CTkFrame(self.settings_scrollable)
                frame.pack(fill="x", pady=2)
                ctk.CTkLabel(frame, text=f"{key.capitalize()}:", width=100).pack(side="left", padx=5)
                entry = ctk.CTkEntry(frame)
                entry.insert(0, self.settings['hotkeys'].get(key, ''))
                entry.pack(side="left", fill="x", expand=True, padx=5)
                self.entries[f'hotkeys_{key}'] = entry

            # Combat
            ctk.CTkLabel(self.settings_scrollable, text="Combat", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20,5))
            frame = ctk.CTkFrame(self.settings_scrollable)
            frame.pack(fill="x", pady=2)
            ctk.CTkLabel(frame, text="Skill Delay (ms):", width=150).pack(side="left", padx=5)
            entry = ctk.CTkEntry(frame)
            entry.insert(0, str(self.settings['combat'].get('skill_delay_ms', 200)))
            entry.pack(side="left", fill="x", expand=True, padx=5)
            self.entries['combat_skill_delay_ms'] = entry

            # Potion
            ctk.CTkLabel(self.settings_scrollable, text="Potion", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20,5))
            for key in ['hp_threshold', 'mp_threshold', 'hp_potion_key', 'mp_potion_key']:
                frame = ctk.CTkFrame(self.settings_scrollable)
                frame.pack(fill="x", pady=2)
                ctk.CTkLabel(frame, text=f"{key.replace('_', ' ').capitalize()}:", width=150).pack(side="left", padx=5)
                entry = ctk.CTkEntry(frame)
                entry.insert(0, str(self.settings['potion'].get(key, '')))
                entry.pack(side="left", fill="x", expand=True, padx=5)
                self.entries[f'potion_{key}'] = entry

            # Vision
            ctk.CTkLabel(self.settings_scrollable, text="Vision", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20,5))
            frame = ctk.CTkFrame(self.settings_scrollable)
            frame.pack(fill="x", pady=2)
            ctk.CTkLabel(frame, text="Tesseract Path:", width=150).pack(side="left", padx=5)
            entry = ctk.CTkEntry(frame)
            entry.insert(0, self.settings['vision'].get('tesseract_path', ''))
            entry.pack(side="left", fill="x", expand=True, padx=5)
            self.entries['vision_tesseract_path'] = entry

            # UI
            ctk.CTkLabel(self.settings_scrollable, text="UI", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20,5))
            frame = ctk.CTkFrame(self.settings_scrollable)
            frame.pack(fill="x", pady=2)
            ctk.CTkLabel(frame, text="Theme:", width=100).pack(side="left", padx=5)
            theme_combo = ctk.CTkComboBox(frame, values=["light", "dark", "system"])
            theme_combo.set(self.settings['ui'].get('theme', 'dark'))
            theme_combo.pack(side="left", padx=5)
            self.entries['ui_theme'] = theme_combo

            # Save button
            save_button = ctk.CTkButton(self.settings_scrollable, text=self.lang['save'], command=self.save_settings)
            save_button.pack(pady=20)

    def save_settings(self):
        # Update settings from entries
        for key, entry in self.entries.items():
            section, subkey = key.split('_', 1)
            if isinstance(entry, ctk.CTkEntry):
                value = entry.get()
            elif isinstance(entry, ctk.CTkComboBox):
                value = entry.get()
            if section == 'hotkeys':
                self.settings['hotkeys'][subkey] = value
            elif section == 'combat':
                self.settings['combat'][subkey] = int(value) if subkey == 'skill_delay_ms' else value
            elif section == 'potion':
                self.settings['potion'][subkey] = int(value) if subkey in ['hp_threshold', 'mp_threshold'] else value
            elif section == 'vision':
                self.settings['vision'][subkey] = value
            elif section == 'ui':
                self.settings['ui'][subkey] = value

        # Save to file
        with self.settings_path.open('w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4)

        # Update theme if changed
        ctk.set_appearance_mode(self.settings['ui']['theme'])

        self.show_main()

    def show_main(self):
        self.settings_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    def run(self):
        self.root.mainloop()