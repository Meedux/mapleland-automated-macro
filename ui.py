import customtkinter as ctk
import threading
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any
import tkinter as tk
from tkinter import scrolledtext


class MapleBotUI:
    def __init__(self, settings: Dict[str, Any], start_callback, stop_callback, settings_path: Path, update_settings_callback=None):
        self.settings = settings
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.settings_path = settings_path
        self.update_settings_callback = update_settings_callback
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

        self.logs_button = ctk.CTkButton(self.main_frame, text="Logs", command=self.show_logs)
        self.logs_button.pack(pady=10)

        self.lang_button = ctk.CTkButton(self.main_frame, text=self.lang['switch_lang'], command=self.switch_language)
        self.lang_button.pack(pady=10)

        self.settings_frame = ctk.CTkFrame(self.root)
        self.logs_frame = ctk.CTkFrame(self.root)

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
            success = self.start_callback()
            if success:
                self.running = True
                self.status_label.configure(text=self.lang['status_running'])
                self.start_button.configure(state="disabled")
                self.stop_button.configure(state="normal")
            else:
                # Show error message
                import tkinter.messagebox as messagebox
                messagebox.showerror("Precondition Error", "Precondition verification failed. Check console for details.")

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

            # Preconditions
            ctk.CTkLabel(self.settings_scrollable, text="Preconditions", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10,5))
            for key in ['os', 'resolution', 'scaling', 'game_mode', 'chat_minimized']:
                frame = ctk.CTkFrame(self.settings_scrollable)
                frame.pack(fill="x", pady=2)
                ctk.CTkLabel(frame, text=f"{key.replace('_', ' ').capitalize()}:", width=150).pack(side="left", padx=5)
                if key == 'chat_minimized':
                    combo = ctk.CTkComboBox(frame, values=["True", "False"])
                    combo.set(str(self.settings['preconditions'].get(key, True)))
                    combo.pack(side="left", padx=5)
                    self.entries[f'preconditions_{key}'] = combo
                else:
                    entry = ctk.CTkEntry(frame)
                    entry.insert(0, str(self.settings['preconditions'].get(key, '')))
                    entry.pack(side="left", fill="x", expand=True, padx=5)
                    self.entries[f'preconditions_{key}'] = entry

            # Auth
            ctk.CTkLabel(self.settings_scrollable, text="Auth", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20,5))
            for key in ['id', 'password']:
                frame = ctk.CTkFrame(self.settings_scrollable)
                frame.pack(fill="x", pady=2)
                ctk.CTkLabel(frame, text=f"{key.capitalize()}:", width=100).pack(side="left", padx=5)
                entry = ctk.CTkEntry(frame, show="*" if key == 'password' else "")
                entry.insert(0, self.settings['auth'].get(key, ''))
                entry.pack(side="left", fill="x", expand=True, padx=5)
                self.entries[f'auth_{key}'] = entry

            # Hotkeys
            ctk.CTkLabel(self.settings_scrollable, text="Hotkeys", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20,5))
            for key in ['start', 'stop', 'hp_potion', 'mp_potion', 'attack', 'jump', 'loot', 'key_down_time', 'attack_delay']:
                frame = ctk.CTkFrame(self.settings_scrollable)
                frame.pack(fill="x", pady=2)
                ctk.CTkLabel(frame, text=f"{key.replace('_', ' ').capitalize()}:", width=150).pack(side="left", padx=5)
                entry = ctk.CTkEntry(frame)
                entry.insert(0, str(self.settings['hotkeys'].get(key, '')))
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
            for key in ['nickname_threshold']:
                frame = ctk.CTkFrame(self.settings_scrollable)
                frame.pack(fill="x", pady=2)
                ctk.CTkLabel(frame, text=f"{key.replace('_', ' ').capitalize()}:", width=150).pack(side="left", padx=5)
                entry = ctk.CTkEntry(frame)
                entry.insert(0, str(self.settings['vision'].get(key, '')))
                entry.pack(side="left", fill="x", expand=True, padx=5)
                self.entries[f'vision_{key}'] = entry

            # Movement
            ctk.CTkLabel(self.settings_scrollable, text="Movement", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20,5))
            frame = ctk.CTkFrame(self.settings_scrollable)
            frame.pack(fill="x", pady=2)
            ctk.CTkLabel(frame, text="Speed Factor:", width=150).pack(side="left", padx=5)
            entry = ctk.CTkEntry(frame)
            entry.insert(0, str(self.settings['movement'].get('speed_factor', 117)))
            entry.pack(side="left", fill="x", expand=True, padx=5)
            self.entries['movement_speed_factor'] = entry

            # Monster Settings
            ctk.CTkLabel(self.settings_scrollable, text="Monster Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20,5))
            for key in ['nickname_recognition_rate', 'monster_recognition_rate', 'x_range', 'y_range']:
                frame = ctk.CTkFrame(self.settings_scrollable)
                frame.pack(fill="x", pady=2)
                ctk.CTkLabel(frame, text=f"{key.replace('_', ' ').capitalize()}:", width=200).pack(side="left", padx=5)
                entry = ctk.CTkEntry(frame)
                entry.insert(0, str(self.settings['monster_settings'].get(key, '')))
                entry.pack(side="left", fill="x", expand=True, padx=5)
                self.entries[f'monster_settings_{key}'] = entry
            frame = ctk.CTkFrame(self.settings_scrollable)
            frame.pack(fill="x", pady=2)
            ctk.CTkLabel(frame, text="Handle Opposite:", width=150).pack(side="left", padx=5)
            handle_opposite_combo = ctk.CTkComboBox(frame, values=["True", "False"])
            handle_opposite_combo.set(str(self.settings['monster_settings'].get('handle_opposite', True)))
            handle_opposite_combo.pack(side="left", padx=5)
            self.entries['monster_settings_handle_opposite'] = handle_opposite_combo

            # Misc
            ctk.CTkLabel(self.settings_scrollable, text="Misc", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20,5))
            for key in ['hp_potion_percent', 'mp_potion_percent', 'user_detect_time', 'stationary_time']:
                frame = ctk.CTkFrame(self.settings_scrollable)
                frame.pack(fill="x", pady=2)
                ctk.CTkLabel(frame, text=f"{key.replace('_', ' ').capitalize()}:", width=150).pack(side="left", padx=5)
                entry = ctk.CTkEntry(frame)
                entry.insert(0, str(self.settings['misc'].get(key, '')))
                entry.pack(side="left", fill="x", expand=True, padx=5)
                self.entries[f'misc_{key}'] = entry
            for key in ['handle_opposite', 'clear_remain', 'lie_detector', 'user_detect', 'stationary']:
                frame = ctk.CTkFrame(self.settings_scrollable)
                frame.pack(fill="x", pady=2)
                ctk.CTkLabel(frame, text=f"{key.replace('_', ' ').capitalize()}:", width=150).pack(side="left", padx=5)
                combo = ctk.CTkComboBox(frame, values=["True", "False"])
                combo.set(str(self.settings['misc'].get(key, False)))
                combo.pack(side="left", padx=5)
                self.entries[f'misc_{key}'] = combo
            frame = ctk.CTkFrame(self.settings_scrollable)
            frame.pack(fill="x", pady=2)
            ctk.CTkLabel(frame, text="Stationary Direction:", width=150).pack(side="left", padx=5)
            stationary_direction_combo = ctk.CTkComboBox(frame, values=["left", "right"])
            stationary_direction_combo.set(self.settings['misc'].get('stationary_direction', 'right'))
            stationary_direction_combo.pack(side="left", padx=5)
            self.entries['misc_stationary_direction'] = stationary_direction_combo

            # UI
            ctk.CTkLabel(self.settings_scrollable, text="UI", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20,5))
            frame = ctk.CTkFrame(self.settings_scrollable)
            frame.pack(fill="x", pady=2)
            ctk.CTkLabel(frame, text="Language:", width=100).pack(side="left", padx=5)
            lang_combo = ctk.CTkComboBox(frame, values=["en", "ko"])
            lang_combo.set(self.settings['ui'].get('language', 'en'))
            lang_combo.pack(side="left", padx=5)
            self.entries['ui_language'] = lang_combo
            frame = ctk.CTkFrame(self.settings_scrollable)
            frame.pack(fill="x", pady=2)
            ctk.CTkLabel(frame, text="Theme:", width=100).pack(side="left", padx=5)
            theme_combo = ctk.CTkComboBox(frame, values=["light", "dark", "system"])
            theme_combo.set(self.settings['ui'].get('theme', 'dark'))
            theme_combo.pack(side="left", padx=5)
            self.entries['ui_theme'] = theme_combo

            # Debug
            ctk.CTkLabel(self.settings_scrollable, text="Debug", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20,5))
            for key in ['enable_debug', 'simulation_mode']:
                frame = ctk.CTkFrame(self.settings_scrollable)
                frame.pack(fill="x", pady=2)
                ctk.CTkLabel(frame, text=f"{key.replace('_', ' ').capitalize()}:", width=150).pack(side="left", padx=5)
                combo = ctk.CTkComboBox(frame, values=["True", "False"])
                combo.set(str(self.settings['debug'].get(key, False)))
                combo.pack(side="left", padx=5)
                self.entries[f'debug_{key}'] = combo

            # Routes
            ctk.CTkLabel(self.settings_scrollable, text="Routes (JSON)", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20,5))
            self.routes_text = ctk.CTkTextbox(self.settings_scrollable, height=100)
            self.routes_text.insert("0.0", json.dumps(self.settings.get('routes', []), indent=2))
            self.routes_text.pack(fill="x", pady=5)

            # Buffs
            ctk.CTkLabel(self.settings_scrollable, text="Buffs (JSON)", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20,5))
            self.buffs_text = ctk.CTkTextbox(self.settings_scrollable, height=100)
            self.buffs_text.insert("0.0", json.dumps(self.settings.get('buffs', []), indent=2))
            self.buffs_text.pack(fill="x", pady=5)

            # Save button
            save_button = ctk.CTkButton(self.settings_scrollable, text=self.lang['save'], command=self.save_settings)
            save_button.pack(pady=20)

    def save_settings(self):
        # Update settings from entries
        for key, entry in self.entries.items():
            parts = key.split('_', 1)
            section = parts[0]
            subkey = parts[1] if len(parts) > 1 else ''
            if isinstance(entry, ctk.CTkEntry):
                value = entry.get()
            elif isinstance(entry, ctk.CTkComboBox):
                value = entry.get()
                if value in ["True", "False"]:
                    value = value == "True"
            else:
                continue

            if section == 'preconditions':
                if subkey == 'scaling':
                    self.settings['preconditions'][subkey] = int(value)
                elif subkey == 'chat_minimized':
                    self.settings['preconditions'][subkey] = value == "True"
                else:
                    self.settings['preconditions'][subkey] = value
            elif section == 'auth':
                self.settings['auth'][subkey] = value
            elif section == 'hotkeys':
                if subkey in ['key_down_time', 'attack_delay']:
                    self.settings['hotkeys'][subkey] = float(value)
                else:
                    self.settings['hotkeys'][subkey] = value
            elif section == 'combat':
                self.settings['combat'][subkey] = int(value) if subkey == 'skill_delay_ms' else value
            elif section == 'potion':
                if subkey in ['hp_threshold', 'mp_threshold']:
                    self.settings['potion'][subkey] = int(value)
                else:
                    self.settings['potion'][subkey] = value
            elif section == 'vision':
                if subkey == 'nickname_threshold':
                    self.settings['vision'][subkey] = float(value)
            elif section == 'movement':
                self.settings['movement'][subkey] = int(value)
            elif section == 'monster_settings':
                if subkey in ['nickname_recognition_rate', 'monster_recognition_rate', 'x_range', 'y_range']:
                    self.settings['monster_settings'][subkey] = float(value) if 'rate' in subkey else int(value)
                else:
                    self.settings['monster_settings'][subkey] = value
            elif section == 'misc':
                if subkey in ['hp_potion_percent', 'mp_potion_percent', 'user_detect_time', 'stationary_time']:
                    self.settings['misc'][subkey] = int(value)
                else:
                    self.settings['misc'][subkey] = value
            elif section == 'ui':
                self.settings['ui'][subkey] = value
            elif section == 'debug':
                self.settings['debug'][subkey] = value

        # Handle text areas
        try:
            self.settings['routes'] = json.loads(self.routes_text.get("0.0", "end-1c"))
        except json.JSONDecodeError:
            print("Invalid routes JSON")
        try:
            self.settings['buffs'] = json.loads(self.buffs_text.get("0.0", "end-1c"))
        except json.JSONDecodeError:
            print("Invalid buffs JSON")

        # Save to file
        with self.settings_path.open('w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4)

        # Update theme if changed
        ctk.set_appearance_mode(self.settings['ui']['theme'])

        # Update language if changed
        old_lang = self.lang
        self.lang = self.load_language()
        if self.lang != old_lang:
            self.update_ui_texts()

        # Notify bot of settings update
        if self.update_settings_callback:
            self.update_settings_callback(self.settings)

        self.show_main()

    def show_main(self):
        self.settings_frame.pack_forget()
        self.logs_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    def show_logs(self):
        self.main_frame.pack_forget()
        self.settings_frame.pack_forget()
        self.logs_frame.pack(fill="both", expand=True, padx=20, pady=20)

        if not hasattr(self, 'logs_text'):
            ctk.CTkLabel(self.logs_frame, text="Application Logs").pack(pady=10)
            self.logs_text = scrolledtext.ScrolledText(self.logs_frame, wrap=tk.WORD, height=20)
            self.logs_text.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Set up logging to this widget
            self.setup_logging()

        back_button = ctk.CTkButton(self.logs_frame, text=self.lang['back'], command=self.show_main)
        back_button.pack(pady=10)

    def load_logs(self):
        # For now, just simulate loading logs
        self.logs_text.configure(state="normal")
        self.logs_text.delete("0.0", "end")
        self.logs_text.insert("0.0", "Log file content goes here...\n")
        self.logs_text.insert("end", "Another log entry...\n")
        self.logs_text.configure(state="disabled")

    def setup_logging(self):
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget

            def emit(self, record):
                msg = self.format(record)
                self.text_widget.after(0, lambda: self._append_text(msg))  # Thread-safe

            def _append_text(self, msg):
                self.text_widget.insert(tk.END, msg + '\n')
                self.text_widget.see(tk.END)

        # Add our custom handler
        handler = TextHandler(self.logs_text)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logging.root.addHandler(handler)

    def run(self):
        self.root.mainloop()