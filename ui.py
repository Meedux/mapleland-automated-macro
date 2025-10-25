import customtkinter as ctk
import threading
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any
import tkinter as tk
from tkinter import scrolledtext
import pyautogui
import locales
import window_utils
import tkinter.messagebox as messagebox
import json


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

        # Modern header with icon, title and status indicator
        self.header = ctk.CTkFrame(self.main_frame, corner_radius=12)
        self.header.pack(fill='x', pady=(0,12))

        # Left: Title
        left = ctk.CTkFrame(self.header, fg_color='transparent')
        left.pack(side='left', padx=10)
        self.title_label = ctk.CTkLabel(left, text=self.lang['title'], font=ctk.CTkFont(size=18, weight='bold'))
        self.title_label.pack(side='left', padx=6)

        # Right: Controls and status
        right = ctk.CTkFrame(self.header, fg_color='transparent')
        right.pack(side='right', padx=6)

        # Animated status indicator
        self.status_canvas = tk.Canvas(right, width=18, height=18, bg=self.root['bg'], highlightthickness=0)
        self.status_canvas.pack(side='right', padx=(6,12))
        self._status_indicator = self.status_canvas.create_oval(2,2,16,16, fill='#aa0000')
        self._status_pulse_state = 0
        # textual status next to indicator
        self.status_text = ctk.CTkLabel(right, text=self.lang['status_stopped'])
        self.status_text.pack(side='right', padx=(6,0))

        # Compact controls
        self.start_button = ctk.CTkButton(right, text=self.lang['start'], command=self.start_bot, width=80)
        self.start_button.pack(side='right', padx=6)
        self.stop_button = ctk.CTkButton(right, text=self.lang['stop'], command=self.stop_bot, width=80, state='disabled')
        self.stop_button.pack(side='right')
        self.settings_button = ctk.CTkButton(right, text=self.lang['settings'], command=self.show_settings)
        self.settings_button.pack(side='right', padx=6)

        # Main content area (controls + terminal)
        self.content = ctk.CTkFrame(self.main_frame)
        self.content.pack(fill='both', expand=True)

        # Left column: controls
        self.controls_col = ctk.CTkFrame(self.content, width=220)
        self.controls_col.pack(side='left', fill='y', padx=(0,12), pady=6)
        self.controls_col.pack_propagate(False)

        # Right column: terminal / logs
        self.logs_col = ctk.CTkFrame(self.content)
        self.logs_col.pack(side='right', fill='both', expand=True, pady=6)

        # Control placeholders
        self.lang_button = ctk.CTkButton(self.controls_col, text=self.lang['switch_lang'], command=self.switch_language)
        self.lang_button.pack(pady=(6,4), padx=8, fill='x')

        

        # Logs header with toolbar
        logs_header = ctk.CTkFrame(self.logs_col, fg_color='transparent')
        logs_header.pack(fill='x', pady=(0,6))
        self.logs_header_label = ctk.CTkLabel(logs_header, text=self.lang.get('activity_terminal', 'Activity Terminal'), font=ctk.CTkFont(size=14, weight='bold'))
        self.logs_header_label.pack(side='left', padx=8)
        self.log_filter = ctk.CTkComboBox(logs_header, values=[self.lang.get('log_filter_all','ALL'), self.lang.get('log_filter_info','INFO'), self.lang.get('log_filter_warning','WARNING'), self.lang.get('log_filter_error','ERROR')], width=120)
        self.log_filter.set(self.lang.get('log_filter_all','ALL'))
        self.log_filter.pack(side='right', padx=6)
        self.clear_btn = ctk.CTkButton(logs_header, text=self.lang.get('clear','Clear'), width=70, command=lambda: self._clear_logs())
        self.clear_btn.pack(side='right', padx=6)
        self.copy_btn = ctk.CTkButton(logs_header, text=self.lang.get('copy','Copy'), width=70, command=lambda: self._copy_logs())
        self.copy_btn.pack(side='right', padx=6)

        # Terminal area (modern, monospace)
        self.logs_text_main = ctk.CTkTextbox(self.logs_col, width=400, height=220, wrap='word')
        # Try to access underlying text widget for tag support
        try:
            self._inner_text = self.logs_text_main.text
            self._inner_text.configure(font=('Consolas', 10), bg='#1e1e1e', fg='#e6e6e6', insertbackground='#e6e6e6')
            # configure tags
            self._inner_text.tag_configure('INFO', foreground='#9bd39b')
            self._inner_text.tag_configure('WARNING', foreground='#ffd066')
            self._inner_text.tag_configure('ERROR', foreground='#ff6b6b')
        except Exception:
            # Fallback if CTkTextbox internals differ
            self._inner_text = None
        self.logs_text_main.pack(fill='both', expand=True, padx=8)

        # Initially hide logs until start
        self.logs_col.pack_forget()

        self.settings_frame = ctk.CTkFrame(self.root)

    def load_language(self):
        lang_code = self.settings.get('ui', {}).get('language', 'en')
        try:
            return locales.get_lang(lang_code)
        except Exception:
            logging.exception("Failed to load language; falling back to English")
            return locales.get_lang('en')

    def switch_language(self):
        current_lang = self.settings['ui']['language']
        new_lang = 'ko' if current_lang == 'en' else 'en'
        self.settings['ui']['language'] = new_lang
        self.lang = self.load_language()
        self.update_ui_texts()

    def _pulse_status(self):
        """Animate the status indicator: green when running, red when stopped."""
        try:
            running = getattr(self, 'running', False)
            # pulse between two color intensities
            if running:
                # green pulse
                self._status_pulse_state = (self._status_pulse_state + 1) % 20
                intensity = 120 + int(80 * (0.5 + 0.5 * (self._status_pulse_state / 19)))
                color = f'#00{intensity:02x}00'
            else:
                self._status_pulse_state = (self._status_pulse_state + 1) % 20
                intensity = 170 - int(80 * (self._status_pulse_state / 19))
                color = f'#{intensity:02x}0000'
            self.status_canvas.itemconfig(self._status_indicator, fill=color)
        except Exception:
            pass
        finally:
            self.root.after(120, self._pulse_status)

    def update_ui_texts(self):
        self.root.title(self.lang['title'])
        # Update header texts and status
        try:
            self.title_label.configure(text=self.lang['title'])
        except Exception:
            pass
        try:
            self.status_text.configure(text=self.lang['status_stopped'] if not self.running else self.lang['status_running'])
        except Exception:
            pass
        try:
            if hasattr(self, 'back_button'):
                self.back_button.configure(text=self.lang.get('back', self.lang.get('back', 'Back')))
        except Exception:
            pass
        try:
            if hasattr(self, 'save_button'):
                self.save_button.configure(text=self.lang.get('save', self.lang.get('save', 'Save')))
        except Exception:
            pass
        self.start_button.configure(text=self.lang['start'])
        self.stop_button.configure(text=self.lang['stop'])
        self.settings_button.configure(text=self.lang['settings'])
        self.lang_button.configure(text=self.lang['switch_lang'])
        # Update logs header and toolbar
        try:
            if hasattr(self, 'logs_header_label'):
                self.logs_header_label.configure(text=self.lang.get('activity_terminal', 'Activity Terminal'))
        except Exception:
            pass
        try:
            if hasattr(self, 'clear_btn'):
                self.clear_btn.configure(text=self.lang.get('clear','Clear'))
        except Exception:
            pass
        try:
            if hasattr(self, 'copy_btn'):
                self.copy_btn.configure(text=self.lang.get('copy','Copy'))
        except Exception:
            pass
        try:
            # update log filter values (reset choices)
            if hasattr(self, 'log_filter'):
                vals = [self.lang.get('log_filter_all','ALL'), self.lang.get('log_filter_info','INFO'), self.lang.get('log_filter_warning','WARNING'), self.lang.get('log_filter_error','ERROR')]
                try:
                    self.log_filter.configure(values=vals)
                    self.log_filter.set(vals[0])
                except Exception:
                    pass
        except Exception:
            pass
        # Update section labels and detect buttons texts
        try:
            for k, lbl in getattr(self, 'section_labels', {}).items():
                key = f"{k}_title"
                if key in self.lang:
                    try:
                        lbl.configure(text=self.lang.get(key, lbl.cget('text')))
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            for btn in getattr(self, 'detect_buttons', []):
                try:
                    btn.configure(text=self.lang.get('detect','Detect'))
                except Exception:
                    pass
        except Exception:
            pass
        try:
            if hasattr(self, 'lang_label_widget'):
                self.lang_label_widget.configure(text=self.lang.get('language_label','Language:'))
        except Exception:
            pass
        try:
            if hasattr(self, 'theme_label_widget'):
                self.theme_label_widget.configure(text=self.lang.get('theme_label','Theme:'))
        except Exception:
            pass

    def start_bot(self):
        if not self.running:
            # Show the select-window modal immediately when Start is pressed.
            try:
                selected_hwnd = self._prompt_select_window()
                if not selected_hwnd:
                    # user cancelled or selection failed
                    return
            except Exception:
                logging.exception('Error during select-window flow')
                return

            # At this point the selected window has been focused and validated by the modal.
            success = self.start_callback()
            if success:
                self.running = True
                # update buttons
                self.start_button.configure(state="disabled")
                self.stop_button.configure(state="normal")
                # Show logs area with a smooth reveal
                try:
                    self.logs_col.pack(side='right', fill='both', expand=True, pady=6)
                except Exception:
                    pass
                self.setup_main_logging()
                # start pulsing animation
                self._pulse_status()
                try:
                    self.status_text.configure(text=self.lang['status_running'])
                except Exception:
                    pass
            else:
                # Show error message
                import tkinter.messagebox as messagebox
                messagebox.showerror(self.lang.get('precondition_error_title','Precondition Error'), self.lang.get('precondition_error_text','Precondition verification failed. Check console for details.'))

    def stop_bot(self):
        if self.running:
            self.running = False
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.stop_callback()
            # Hide logs
            try:
                self.logs_col.pack_forget()
            except Exception:
                pass
            try:
                self.status_text.configure(text=self.lang['status_stopped'])
            except Exception:
                pass

    def show_settings(self):
        self.main_frame.pack_forget()
        self.settings_frame.pack(fill="both", expand=True, padx=20, pady=20)

        if not hasattr(self, 'settings_scrollable'):
            self.settings_scrollable = ctk.CTkScrollableFrame(self.settings_frame)
            self.settings_scrollable.pack(fill="both", expand=True, padx=10, pady=10)

            self.entries = {}

            # Back button
            self.back_button = ctk.CTkButton(self.settings_frame, text=self.lang.get('back','Back'), command=self.show_main)
            self.back_button.pack(pady=10)

            # store section labels for localization updates
            self.section_labels = {}
            self.detect_buttons = []

            # Preconditions
            lbl = ctk.CTkLabel(self.settings_scrollable, text=self.lang.get('preconditions_title','Preconditions'), font=ctk.CTkFont(size=16, weight="bold"))
            lbl.pack(pady=(10,5))
            self.section_labels['preconditions'] = lbl
            for key in ['os', 'resolution', 'scaling', 'game_mode', 'chat_minimized']:
                frame = ctk.CTkFrame(self.settings_scrollable)
                frame.pack(fill="x", pady=2)
                ctk.CTkLabel(frame, text=f"{key.replace('_', ' ').capitalize()}:", width=150).pack(side="left", padx=5)
                if key == 'resolution':
                    entry = ctk.CTkEntry(frame)
                    entry.insert(0, str(self.settings['preconditions'].get(key, '')))
                    entry.pack(side="left", fill="x", expand=True, padx=5)
                    self.entries[f'preconditions_{key}'] = entry
                    # capture entry in lambda default arg to avoid late-binding issues
                    detect_btn = ctk.CTkButton(frame, text=self.lang.get('detect','Detect'), width=80, command=lambda e=entry: self.detect_resolution(e))
                    detect_btn.pack(side="right", padx=5)
                    self.detect_buttons.append(detect_btn)
                elif key == 'chat_minimized':
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
            lbl = ctk.CTkLabel(self.settings_scrollable, text=self.lang.get('auth_title','Auth'), font=ctk.CTkFont(size=16, weight="bold"))
            lbl.pack(pady=(20,5))
            self.section_labels['auth'] = lbl
            for key in ['id', 'password']:
                frame = ctk.CTkFrame(self.settings_scrollable)
                frame.pack(fill="x", pady=2)
                ctk.CTkLabel(frame, text=f"{key.capitalize()}:", width=100).pack(side="left", padx=5)
                entry = ctk.CTkEntry(frame, show="*" if key == 'password' else "")
                entry.insert(0, self.settings['auth'].get(key, ''))
                entry.pack(side="left", fill="x", expand=True, padx=5)
                self.entries[f'auth_{key}'] = entry

            # Hotkeys
            lbl = ctk.CTkLabel(self.settings_scrollable, text=self.lang.get('hotkeys_title','Hotkeys'), font=ctk.CTkFont(size=16, weight="bold"))
            lbl.pack(pady=(20,5))
            self.section_labels['hotkeys'] = lbl
            for key in ['start', 'stop', 'hp_potion', 'mp_potion', 'attack', 'jump', 'loot', 'key_down_time', 'attack_delay']:
                frame = ctk.CTkFrame(self.settings_scrollable)
                frame.pack(fill="x", pady=2)
                ctk.CTkLabel(frame, text=f"{key.replace('_', ' ').capitalize()}:", width=150).pack(side="left", padx=5)
                entry = ctk.CTkEntry(frame)
                entry.insert(0, str(self.settings['hotkeys'].get(key, '')))
                entry.pack(side="left", fill="x", expand=True, padx=5)
                self.entries[f'hotkeys_{key}'] = entry

            # Combat
            lbl = ctk.CTkLabel(self.settings_scrollable, text=self.lang.get('combat_title','Combat'), font=ctk.CTkFont(size=16, weight="bold"))
            lbl.pack(pady=(20,5))
            self.section_labels['combat'] = lbl
            frame = ctk.CTkFrame(self.settings_scrollable)
            frame.pack(fill="x", pady=2)
            ctk.CTkLabel(frame, text="Skill Delay (ms):", width=150).pack(side="left", padx=5)
            entry = ctk.CTkEntry(frame)
            entry.insert(0, str(self.settings['combat'].get('skill_delay_ms', 200)))
            entry.pack(side="left", fill="x", expand=True, padx=5)
            self.entries['combat_skill_delay_ms'] = entry

            # Potion
            lbl = ctk.CTkLabel(self.settings_scrollable, text=self.lang.get('potion_title','Potion'), font=ctk.CTkFont(size=16, weight="bold"))
            lbl.pack(pady=(20,5))
            self.section_labels['potion'] = lbl
            for key in ['hp_threshold', 'mp_threshold', 'hp_potion_key', 'mp_potion_key']:
                frame = ctk.CTkFrame(self.settings_scrollable)
                frame.pack(fill="x", pady=2)
                ctk.CTkLabel(frame, text=f"{key.replace('_', ' ').capitalize()}:", width=150).pack(side="left", padx=5)
                entry = ctk.CTkEntry(frame)
                entry.insert(0, str(self.settings['potion'].get(key, '')))
                entry.pack(side="left", fill="x", expand=True, padx=5)
                self.entries[f'potion_{key}'] = entry

            # Vision
            lbl = ctk.CTkLabel(self.settings_scrollable, text=self.lang.get('vision_title','Vision'), font=ctk.CTkFont(size=16, weight="bold"))
            lbl.pack(pady=(20,5))
            self.section_labels['vision'] = lbl
            for key in ['nickname_threshold']:
                frame = ctk.CTkFrame(self.settings_scrollable)
                frame.pack(fill="x", pady=2)
                ctk.CTkLabel(frame, text=f"{key.replace('_', ' ').capitalize()}:", width=150).pack(side="left", padx=5)
                entry = ctk.CTkEntry(frame)
                entry.insert(0, str(self.settings['vision'].get(key, '')))
                entry.pack(side="left", fill="x", expand=True, padx=5)
                self.entries[f'vision_{key}'] = entry

            # Movement
            lbl = ctk.CTkLabel(self.settings_scrollable, text=self.lang.get('movement_title','Movement'), font=ctk.CTkFont(size=16, weight="bold"))
            lbl.pack(pady=(20,5))
            self.section_labels['movement'] = lbl
            frame = ctk.CTkFrame(self.settings_scrollable)
            frame.pack(fill="x", pady=2)
            ctk.CTkLabel(frame, text="Speed Factor:", width=150).pack(side="left", padx=5)
            entry = ctk.CTkEntry(frame)
            entry.insert(0, str(self.settings['movement'].get('speed_factor', 117)))
            entry.pack(side="left", fill="x", expand=True, padx=5)
            self.entries['movement_speed_factor'] = entry

            # Monster Settings
            lbl = ctk.CTkLabel(self.settings_scrollable, text=self.lang.get('monster_settings_title','Monster Settings'), font=ctk.CTkFont(size=16, weight="bold"))
            lbl.pack(pady=(20,5))
            self.section_labels['monster_settings'] = lbl
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
            lbl = ctk.CTkLabel(self.settings_scrollable, text=self.lang.get('misc_title','Misc'), font=ctk.CTkFont(size=16, weight="bold"))
            lbl.pack(pady=(20,5))
            self.section_labels['misc'] = lbl
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
            lbl = ctk.CTkLabel(self.settings_scrollable, text=self.lang.get('ui_title','UI'), font=ctk.CTkFont(size=16, weight="bold"))
            lbl.pack(pady=(20,5))
            self.section_labels['ui'] = lbl
            frame = ctk.CTkFrame(self.settings_scrollable)
            frame.pack(fill="x", pady=2)
            self.lang_label_widget = ctk.CTkLabel(frame, text=self.lang.get('language_label','Language:'), width=100)
            self.lang_label_widget.pack(side="left", padx=5)
            lang_combo = ctk.CTkComboBox(frame, values=["en", "ko"])
            lang_combo.set(self.settings['ui'].get('language', 'en'))
            lang_combo.pack(side="left", padx=5)
            self.entries['ui_language'] = lang_combo
            frame = ctk.CTkFrame(self.settings_scrollable)
            frame.pack(fill="x", pady=2)
            self.theme_label_widget = ctk.CTkLabel(frame, text=self.lang.get('theme_label','Theme:'), width=100)
            self.theme_label_widget.pack(side="left", padx=5)
            theme_combo = ctk.CTkComboBox(frame, values=["light", "dark", "system"])
            theme_combo.set(self.settings['ui'].get('theme', 'dark'))
            theme_combo.pack(side="left", padx=5)
            self.entries['ui_theme'] = theme_combo

            # Debug
            lbl = ctk.CTkLabel(self.settings_scrollable, text=self.lang.get('debug_title','Debug'), font=ctk.CTkFont(size=16, weight="bold"))
            lbl.pack(pady=(20,5))
            self.section_labels['debug'] = lbl
            for key in ['enable_debug', 'simulation_mode']:
                frame = ctk.CTkFrame(self.settings_scrollable)
                frame.pack(fill="x", pady=2)
                ctk.CTkLabel(frame, text=f"{key.replace('_', ' ').capitalize()}:", width=150).pack(side="left", padx=5)
                combo = ctk.CTkComboBox(frame, values=["True", "False"])
                combo.set(str(self.settings['debug'].get(key, False)))
                combo.pack(side="left", padx=5)
                self.entries[f'debug_{key}'] = combo

            # Routes
            lbl = ctk.CTkLabel(self.settings_scrollable, text=self.lang.get('routes_json_title','Routes (JSON)'), font=ctk.CTkFont(size=16, weight="bold"))
            lbl.pack(pady=(20,5))
            self.section_labels['routes_json'] = lbl
            self.routes_text = ctk.CTkTextbox(self.settings_scrollable, height=100)
            self.routes_text.insert("0.0", json.dumps(self.settings.get('routes', []), indent=2))
            self.routes_text.pack(fill="x", pady=5)

            # Buffs
            lbl = ctk.CTkLabel(self.settings_scrollable, text=self.lang.get('buffs_json_title','Buffs (JSON)'), font=ctk.CTkFont(size=16, weight="bold"))
            lbl.pack(pady=(20,5))
            self.section_labels['buffs_json'] = lbl
            self.buffs_text = ctk.CTkTextbox(self.settings_scrollable, height=100)
            self.buffs_text.insert("0.0", json.dumps(self.settings.get('buffs', []), indent=2))
            self.buffs_text.pack(fill="x", pady=5)

            # Save button
            self.save_button = ctk.CTkButton(self.settings_scrollable, text=self.lang.get('save','Save'), command=self.save_settings)
            self.save_button.pack(pady=20)

    def detect_resolution(self, entry):
        width, height = pyautogui.size()
        resolution_str = f"{width}x{height}"
        entry.delete(0, "end")
        entry.insert(0, resolution_str)

    def _prompt_select_window(self) -> bool:
        """Show a modern modal (CTk) allowing the user to pick the game window.

        Returns True if user cancelled, False if a window was selected and saved.
        """
        try:
            try:
                wins = window_utils.list_windows()
            except OSError:
                messagebox.showinfo(self.lang.get('select_window','Select Game Window'), self.lang.get('window_utils_not_supported','Window selection is only supported on Windows.'))
                return True

            if not wins:
                messagebox.showinfo(self.lang.get('select_window','Select Game Window'), self.lang.get('no_windows_found','No visible windows found.'))
                return True

            # Build modern CTk modal
            dlg = ctk.CTkToplevel(self.root)
            dlg.title(self.lang.get('select_window','Select Game Window'))
            dlg.geometry('760x420')
            dlg.transient(self.root)
            dlg.grab_set()

            left = ctk.CTkFrame(dlg, width=360)
            left.pack(side='left', fill='y', padx=(12,6), pady=12)
            left.pack_propagate(False)

            right = ctk.CTkFrame(dlg)
            right.pack(side='right', fill='both', expand=True, padx=(6,12), pady=12)

            # Search box
            search_var = tk.StringVar()
            search_entry = ctk.CTkEntry(left, placeholder_text=self.lang.get('search','Search...'), textvariable=search_var)
            search_entry.pack(fill='x', padx=8, pady=(6,6))

            list_frame = ctk.CTkScrollableFrame(left)
            list_frame.pack(fill='both', expand=True, padx=8, pady=6)

            # Create buttons per window
            items = []
            selected = {'hwnd': None, 'title': None}

            def make_item(hwnd, title):
                btn = ctk.CTkButton(list_frame, text=title if len(title) < 80 else title[:77] + '...', anchor='w', width=320, fg_color='transparent', hover=False)
                def on_click():
                    selected['hwnd'] = hwnd
                    selected['title'] = title
                    _show_preview(hwnd, title)
                    # highlight selection by changing fg_color
                    for b, _ in items:
                        try:
                            b.configure(fg_color='transparent')
                        except Exception:
                            pass
                    try:
                        btn.configure(fg_color='#2b2b2b')
                    except Exception:
                        pass
                btn.configure(command=on_click)
                btn.pack(fill='x', pady=4, padx=4)
                return btn

            for hwnd, title in wins:
                b = make_item(hwnd, title)
                items.append((b, (hwnd, title)))

            # Preview area
            preview_label = ctk.CTkLabel(right, text=self.lang.get('preview','Preview'))
            preview_label.pack(anchor='nw', padx=6, pady=(6,2))
            preview_canvas = ctk.CTkFrame(right, height=260, fg_color='#1f1f1f')
            preview_canvas.pack(fill='both', padx=6, pady=(0,6), expand=False)
            preview_canvas.pack_propagate(False)

            # Image placeholder
            preview_img_label = ctk.CTkLabel(preview_canvas, text='')
            preview_img_label.pack(expand=True)

            details_label = ctk.CTkLabel(right, text='')
            details_label.pack(anchor='nw', padx=6)

            # Helper to show preview by focusing briefly and taking a screenshot
            try:
                from PIL import Image, ImageTk
                PIL_AVAILABLE = True
            except Exception:
                PIL_AVAILABLE = False

            def _show_preview(hwnd, title):
                # Do NOT focus windows during preview. Only update textual preview info.
                details_label.configure(text=title)
                if not PIL_AVAILABLE:
                    preview_img_label.configure(text=self.lang.get('preview_unavailable','Preview unavailable (Pillow missing)'))
                    return
                try:
                    # Optionally, show a generic placeholder or small screenshot of current screen
                    img = pyautogui.screenshot()
                    w, h = img.size
                    target_w = min(640, int(w * 0.12))
                    target_h = int(target_w * (h / w))
                    thumb = img.resize((target_w, target_h))
                    photo = ImageTk.PhotoImage(thumb)
                    preview_img_label.configure(image=photo, text='')
                    preview_img_label.image = photo
                except Exception:
                    preview_img_label.configure(text=self.lang.get('preview_failed','Preview failed'))

            # Footer buttons (fixed height to avoid overlap; Confirm will be centered)
            footer = ctk.CTkFrame(dlg)
            footer.configure(height=80)
            footer.pack(fill='x', padx=12, pady=(0,12))
            footer.pack_propagate(False)

            selected = {'hwnd': None, 'title': None}

            def _confirm():
                if not selected['hwnd']:
                    messagebox.showwarning(self.lang.get('select_window','Select Game Window'), self.lang.get('no_window_selected','Please select a window first.'))
                    return
                # persist selection
                try:
                    self.settings.setdefault('ui', {})['game_window_title'] = selected['title']
                    with self.settings_path.open('w', encoding='utf-8') as f:
                        json.dump(self.settings, f, indent=4)
                except Exception:
                    logging.exception('Failed to save selected window to settings')
                # try to focus one last time
                try:
                    ok = window_utils.focus_window(selected['hwnd'])
                except Exception:
                    ok = False
                if not ok:
                    messagebox.showwarning(self.lang.get('select_window','Select Game Window'), self.lang.get('window_focus_failed','Could not bring window to foreground; please focus it manually.'))
                    return
                # Give OS a moment to update, then verify game UI via Vision
                time.sleep(0.25)
                try:
                    if hasattr(self, 'bot') and getattr(self.bot, 'vision', None) is not None:
                        x, y, left_dir = self.bot.vision.find_character_coordinates()
                    else:
                        x = None
                except Exception:
                    x = None
                if x is None:
                    messagebox.showerror(self.lang.get('select_window','Select Game Window'), self.lang.get('window_detect_failed','Could not detect game UI in the focused window. Make sure the game is visible and try again.'))
                    return
                # success
                messagebox.showinfo(self.lang.get('select_window','Select Game Window'), self.lang.get('window_focused','Window focused successfully'))
                dlg.grab_release()
                dlg.destroy()

            def _cancel():
                dlg.grab_release()
                dlg.destroy()

            # Arrange footer vertically: top row has Cancel (left) and Refresh (right) side-by-side,
            # bottom row has the Confirm button centered. This is more robust across DPI/scaling.
            footer.grid_columnconfigure(0, weight=1)
            footer.grid_columnconfigure(1, weight=1)

            # Refresh button will re-enumerate windows (useful if new windows opened while modal is shown)
            def _refresh_windows():
                try:
                    wins_new = window_utils.list_windows()
                except Exception:
                    wins_new = []
                # clear existing items
                for b, _ in list(items):
                    try:
                        b.destroy()
                    except Exception:
                        pass
                items.clear()
                selected['hwnd'] = None
                selected['title'] = None
                for hwnd, title in wins_new:
                    b = make_item(hwnd, title)
                    items.append((b, (hwnd, title)))

            # Build a top row frame for the two smaller side-by-side buttons
            top_row = ctk.CTkFrame(footer)
            top_row.pack(fill='x', padx=12, pady=(8,6))

            left_top_btn = ctk.CTkButton(top_row, text=self.lang.get('cancel','Cancel'), command=_cancel, width=120)
            left_top_btn.pack(side='left', anchor='w', padx=(0,8))

            refresh_btn = ctk.CTkButton(top_row, text=self.lang.get('refresh','Refresh'), command=_refresh_windows, width=120)
            refresh_btn.pack(side='right', anchor='e', padx=(8,0))

            # Bottom row for Confirm (centered)
            bottom_row = ctk.CTkFrame(footer)
            bottom_row.pack(fill='x', padx=12, pady=(0,8))

            confirm_btn = ctk.CTkButton(bottom_row, text=self.lang.get('confirm','Confirm'), command=_confirm, width=260)
            confirm_btn.pack(pady=4)

            # Simple search/filter implementation
            def _on_search(*_):
                q = search_var.get().lower()
                for b, (hwnd, title) in items:
                    visible = (q in title.lower()) if q else True
                    try:
                        if visible:
                            b.pack_configure()
                        else:
                            b.pack_forget()
                    except Exception:
                        pass

            search_var.trace_add('write', _on_search)

            self.root.wait_window(dlg)
            return selected.get('hwnd')
        except Exception as e:
            logging.exception(f"Error opening window selector: {e}")
            return True

    

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
                    try:
                        self.settings['preconditions'][subkey] = int(value)
                    except Exception:
                        logging.warning(f"Could not parse int for preconditions.scaling from '{value}', keeping original")
                elif subkey == 'chat_minimized':
                    self.settings['preconditions'][subkey] = value == "True"
                else:
                    self.settings['preconditions'][subkey] = value
            elif section == 'auth':
                self.settings['auth'][subkey] = value
            elif section == 'hotkeys':
                if subkey in ['key_down_time', 'attack_delay']:
                    try:
                        self.settings['hotkeys'][subkey] = float(value)
                    except Exception:
                        logging.warning(f"Could not parse float for hotkeys.{subkey} from '{value}'")
                else:
                    self.settings['hotkeys'][subkey] = value
            elif section == 'combat':
                if subkey == 'skill_delay_ms':
                    try:
                        self.settings['combat'][subkey] = int(value)
                    except Exception:
                        logging.warning(f"Could not parse int for combat.{subkey} from '{value}'")
                else:
                    self.settings['combat'][subkey] = value
            elif section == 'potion':
                if subkey in ['hp_threshold', 'mp_threshold']:
                    try:
                        self.settings['potion'][subkey] = int(value)
                    except Exception:
                        logging.warning(f"Could not parse int for potion.{subkey} from '{value}'")
                else:
                    self.settings['potion'][subkey] = value
            elif section == 'vision':
                if subkey == 'nickname_threshold':
                    try:
                        self.settings['vision'][subkey] = float(value)
                    except Exception:
                        logging.warning(f"Could not parse float for vision.{subkey} from '{value}'")
            elif section == 'movement':
                try:
                    self.settings['movement'][subkey] = int(value)
                except Exception:
                    logging.warning(f"Could not parse int for movement.{subkey} from '{value}'")
            elif section == 'monster_settings':
                if subkey in ['nickname_recognition_rate', 'monster_recognition_rate', 'x_range', 'y_range']:
                    try:
                        self.settings['monster_settings'][subkey] = float(value) if 'rate' in subkey else int(value)
                    except Exception:
                        logging.warning(f"Could not parse number for monster_settings.{subkey} from '{value}'")
                else:
                    self.settings['monster_settings'][subkey] = value
            elif section == 'misc':
                if subkey in ['hp_potion_percent', 'mp_potion_percent', 'user_detect_time', 'stationary_time']:
                    try:
                        self.settings['misc'][subkey] = int(value)
                    except Exception:
                        logging.warning(f"Could not parse int for misc.{subkey} from '{value}'")
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
            logging.warning(self.lang.get('invalid_routes_json', 'Invalid routes JSON'))
        try:
            self.settings['buffs'] = json.loads(self.buffs_text.get("0.0", "end-1c"))
        except json.JSONDecodeError:
            logging.warning(self.lang.get('invalid_buffs_json', 'Invalid buffs JSON'))

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
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    def setup_main_logging(self):
        class MainTextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget

            def emit(self, record):
                try:
                    msg = self.format(record)
                    level = record.levelname
                except Exception:
                    msg = str(record)
                    level = 'INFO'
                # ensure thread-safe GUI update
                try:
                    self.text_widget.after(0, lambda: self._append_text(msg, level))
                except Exception:
                    pass

            def _append_text(self, msg, level='INFO'):
                try:
                    if hasattr(self.text_widget, 'insert'):
                        # If underlying tkinter text is available, use tags
                        try:
                            inner = getattr(self.text_widget, 'text', None) or self.text_widget
                            inner.insert(tk.END, msg + '\n', level if level in ['WARNING','ERROR'] else 'INFO')
                            inner.see(tk.END)
                        except Exception:
                            self.text_widget.insert(tk.END, msg + '\n')
                            self.text_widget.see(tk.END)
                except Exception:
                    pass
        # Add handler for main logs
        handler = MainTextHandler(self.logs_text_main)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logging.root.addHandler(handler)

        # Expose alarm popup methods as instance methods
        self.show_alarm_popup = self._show_alarm_popup
        self._on_alarm_dismiss = self._on_alarm_dismiss_impl
        self._destroy_alarm_popup = self._destroy_alarm_popup_impl

    def run(self):
        # Start status pulsing loop
        try:
            self._pulse_status()
        except Exception:
            pass
        self.root.mainloop()

    # Alarm popup implementations as instance methods
    def _show_alarm_popup(self, message: str):
        """Create a modal popup to notify the user of an occurrence; remains until Dismiss."""
        try:
            # If already displayed, bring to top
            if hasattr(self, '_alarm_window') and self._alarm_window is not None:
                try:
                    self._alarm_window.lift()
                except Exception:
                    pass
                return

            self._alarm_window = tk.Toplevel(self.root)
            self._alarm_window.title(self.lang.get('alarm_title','Occurrence Issue Alarm'))
            self._alarm_window.attributes('-topmost', True)
            self._alarm_window.configure(bg='#2b2b2b')
            self._alarm_window.geometry('420x160+200+200')

            label = tk.Label(self._alarm_window, text=message, font=("Arial", 14, 'bold'), bg='#2b2b2b', fg='#ff6666', wraplength=380)
            label.pack(pady=(20,10))

            dismiss_btn = tk.Button(self._alarm_window, text=self.lang.get('dismiss','Dismiss'), command=self._on_alarm_dismiss_impl, bg='#444444', fg='#ffffff')
            dismiss_btn.pack(pady=(0,20))

            self._alarm_window.protocol("WM_DELETE_WINDOW", self._on_alarm_dismiss_impl)
        except Exception as e:
            logging.error(f"Failed to create alarm popup: {e}")

    def _on_alarm_dismiss_impl(self):
        # Tell bot to stop alarm via callback if provided
        try:
            if hasattr(self, 'alarm_dismiss_callback') and callable(self.alarm_dismiss_callback):
                self.alarm_dismiss_callback()
        except Exception as e:
            logging.error(f"Error calling alarm dismiss callback: {e}")
        finally:
            self._destroy_alarm_popup_impl()

    def _destroy_alarm_popup_impl(self):
        try:
            if hasattr(self, '_alarm_window') and self._alarm_window is not None:
                try:
                    self._alarm_window.destroy()
                except Exception:
                    pass
                self._alarm_window = None
        except Exception as e:
            logging.error(f"Failed to destroy alarm popup: {e}")

    # Utility actions for logs
    def _clear_logs(self):
        try:
            if self._inner_text:
                self._inner_text.delete('1.0', tk.END)
            else:
                self.logs_text_main.delete('0.0', tk.END)
        except Exception:
            pass

    def _copy_logs(self):
        try:
            if self._inner_text:
                text = self._inner_text.get('1.0', tk.END)
            else:
                text = self.logs_text_main.get('0.0', tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
        except Exception:
            pass