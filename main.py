import json
import threading
import time
import pyautogui
import platform
import logging
import locales
from pathlib import Path

from combat import CombatManager
from movement import MovementManager
from potion_manager import PotionManager
from vision import Vision
from ui import MapleBotUI
from buff_manager import BuffManager
from debug_overlay import DebugOverlay


def load_settings(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


class MapleBot:
    def __init__(self, settings):
        self.settings = settings
        self.vision = Vision(settings)
        self.combat = CombatManager(settings, self.vision)
        self.movement = MovementManager(settings, self.vision)
        self.potion = PotionManager(settings, self.vision)
        self.buff = BuffManager(settings)
        self.debug_overlay = DebugOverlay(settings)
        self.running = False
        self.simulation_mode = settings.get('debug', {}).get('simulation_mode', False)
        self.monster_paths = [Path(settings['vision']['assets_path']) / 'mob_templates' / img for img in settings['monsters']]

    def change_channel(self):
        logging.info("Starting channel change procedure")
        time.sleep(3.0)
        pyautogui.click(1681, 98)
        time.sleep(1.5)
        pyautogui.click(1681, 175)
        time.sleep(1.5)
        ch_path = Path(self.settings['vision']['assets_path']) / 'ui_elements' / 'ch.png'
        loc = pyautogui.locateOnScreen(str(ch_path), confidence=0.7)
        if loc:
            pyautogui.click(pyautogui.center(loc))
        time.sleep(1.5)
        pyautogui.click(1081, 714)
        time.sleep(1.5)
        pyautogui.click(1072, 635)
        time.sleep(180)
        mainch_path = Path(self.settings['vision']['assets_path']) / 'ui_elements' / 'mainch.png'
        while True:
            loc = pyautogui.locateOnScreen(str(mainch_path), confidence=0.7)
            if loc:
                pyautogui.click(979, 709)
                time.sleep(5)
                pyautogui.click(579, 805)
                logging.info("Channel change completed successfully")
                break
            else:
                logging.debug("Waiting for main channel screen...")
                time.sleep(30)

    def check_for_channel_change(self):
        logging.info("Channel change monitoring thread started")
        while self.running:
            if self.vision.detect_user():
                logging.warning("User detected, changing channel")
                self.change_channel()
            time.sleep(10)

    def potion_thread(self):
        logging.info("Potion monitoring thread started")
        while self.running:
            self.potion.check_and_use()
            time.sleep(1)

    def simulate_or_execute(self, action_desc, func, *args, **kwargs):
        if self.simulation_mode:
            logging.info(f"SIMULATION: {action_desc}")
        else:
            func(*args, **kwargs)

    def main_logic(self):
        logging.info("Main logic thread started")
        while self.running:
            try:
                # Check for anti-auto-play enemy indicator (highest priority)
                if self.settings.get('misc', {}).get('enemy_detector', False):
                    if self.vision.detect_enemy_detector():
                        logging.error("Anti-auto-play enemy detected — emergency stop")
                        # Stop the bot immediately; other threads check self.running
                        self.stop()
                        # Trigger an emergency alarm/popup
                        self.trigger_enemy_alarm()
                        # break out of loop since running is now False
                        break

                # Check for lie detector overlay next
                if self.settings.get('misc', {}).get('lie_detector', False):
                    if self.vision.detect_lie_detector():
                        logging.warning("Lie detector detected — triggering alarm")
                        self.trigger_lie_alarm()
                        # give a short pause to avoid spamming
                        time.sleep(1)
                        continue
                # Check for chat events (whispers/colored chat)
                if self.settings.get('misc', {}).get('chat_detector', False):
                    chat_found, chat_label = self.vision.detect_chat_event()
                    if chat_found:
                        logging.warning(f"Chat event ({chat_label}) detected — emergency stop")
                        self.stop()
                        self.trigger_chat_alarm(chat_label)
                        break

                # Check for other users on map
                if self.settings.get('misc', {}).get('other_user_detector', False):
                    if self.vision.detect_other_user():
                        logging.error("Other user detected on map — emergency stop")
                        self.stop()
                        self.trigger_other_user_alarm()
                        break
                char_x, char_y, char_left = self.vision.find_character_coordinates()
                if char_x is None:
                    logging.warning("Character not found, attempting to locate")
                    pyautogui.keyDown("left")
                    pyautogui.keyDown("alt")
                    time.sleep(3)
                    pyautogui.keyUp("left")
                    pyautogui.keyUp("alt")
                    pyautogui.keyDown("right")
                    pyautogui.keyDown("alt")
                    time.sleep(3)
                    pyautogui.keyUp("right")
                    pyautogui.keyUp("alt")
                    continue

                logging.debug(f"Character at ({char_x}, {char_y}), direction: {'left' if char_left else 'right'}")
                monster = self.combat.find_targets(self.monster_paths, char_y, char_x, char_left)
                if monster:
                    logging.info(f"Monster found at {monster}, attacking")
                    self.combat.attack(monster, char_x, char_left)
                else:
                    logging.debug("No monster found, checking for ropes")
                    ropes = self.vision.find_ropes(char_y)
                    if ropes:
                        closest_rope = min(ropes, key=lambda r: abs(char_x - r[0]))
                        logging.info(f"Rope found at {closest_rope}, climbing")
                        self.movement.climb_rope(closest_rope[0], closest_rope[1], char_x, char_left)
                    else:
                        logging.debug("No ropes found, patrolling")
                        self.movement.patrol()

                hp_current, hp_max, mp_current, mp_max = self.vision.read_hp_mp()
                self.debug_overlay.update(hp_current, hp_max, mp_current, mp_max, char_x, char_y, "Searching for monsters")

                if time.localtime().tm_min % 10 == 0 and time.localtime().tm_sec < 11:
                    logging.info("Performing 10-minute maintenance (page up)")
                    pyautogui.press('pageup')
                if time.localtime().tm_min % 30 == 0 and time.localtime().tm_sec < 11:
                    logging.info("Performing 30-minute maintenance (home)")
                    pyautogui.press('home')
            except Exception as e:
                logging.error(f"Error in main logic: {e}")
                time.sleep(5)

    def start(self):
        logging.info("Attempting to start MapleBot")
        issues = self.verify_preconditions()
        if issues:
            logging.error("Bot start failed due to precondition failures")
            self.settings['preconditions']['verified'] = False
            return False
        logging.info("Preconditions passed, starting bot threads")
        self.settings['preconditions']['verified'] = True
        self.running = True
        threading.Thread(target=self.check_for_channel_change, daemon=True).start()
        threading.Thread(target=self.potion_thread, daemon=True).start()
        threading.Thread(target=self.main_logic, daemon=True).start()
        logging.info("MapleBot started successfully")
        return True

    def stop(self):
        logging.info("Stopping MapleBot")
        self.running = False

    def update_settings(self, new_settings):
        self.settings = new_settings
        # Update components that use settings
        self.vision.settings = new_settings
        self.combat.settings = new_settings
        self.movement.settings = new_settings
        self.potion.settings = new_settings
        self.buff.settings = new_settings
        self.debug_overlay.settings = new_settings
        logging.info("Settings updated in real-time")

    def trigger_lie_alarm(self):
        """Trigger alarm: play sound and show popup via UI if available. Non-blocking."""
        if getattr(self, 'alarm_active', False):
            logging.debug("Alarm already active")
            return
        self.alarm_active = True
        logging.warning("Triggering lie detector alarm")

        # Start beep thread
        def beep_loop():
            try:
                import winsound
                while self.alarm_active:
                    winsound.Beep(1000, 400)
                    time.sleep(0.2)
            except Exception:
                # Fallback simple print if winsound unavailable
                while self.alarm_active:
                    logging.warning("ALARM (no sound available on platform)")
                    time.sleep(1)

        threading.Thread(target=beep_loop, daemon=True).start()

        # Show popup via UI if present
        if hasattr(self, 'ui') and self.ui is not None:
            try:
                # localized message (prefer UI's current language)
                try:
                    msg = self.ui.lang.get('lie_alarm_msg')
                except Exception:
                    msg = locales.get_lang(self.settings.get('ui', {}).get('language', 'en')).get('lie_alarm_msg')
                # Use tkinter-safe scheduling
                self.ui.root.after(0, lambda m=msg: self.ui.show_alarm_popup(m))
            except Exception as e:
                logging.error(f"Failed to show alarm popup: {e}")

    def trigger_enemy_alarm(self):
        """Trigger the emergency alarm for anti-auto-play enemy detection."""
        if getattr(self, 'enemy_alarm_active', False):
            logging.debug("Enemy alarm already active")
            return
        self.enemy_alarm_active = True
        logging.critical("Triggering ENEMY emergency alarm — stop all automation")

        # Start beep thread (higher urgency tone)
        def beep_loop_enemy():
            try:
                import winsound
                while self.enemy_alarm_active:
                    winsound.Beep(1500, 500)
                    time.sleep(0.1)
            except Exception:
                while self.enemy_alarm_active:
                    logging.critical("ENEMY ALARM (no sound available on platform)")
                    time.sleep(1)

        threading.Thread(target=beep_loop_enemy, daemon=True).start()

        if hasattr(self, 'ui') and self.ui is not None:
            try:
                try:
                    msg = self.ui.lang.get('enemy_alarm_msg')
                except Exception:
                    msg = locales.get_lang(self.settings.get('ui', {}).get('language', 'en')).get('enemy_alarm_msg')
                self.ui.root.after(0, lambda m=msg: self.ui.show_alarm_popup(m))
            except Exception as e:
                logging.error(f"Failed to show enemy alarm popup: {e}")

    def trigger_chat_alarm(self, chat_label: str = None):
        """Trigger alarm for chat events (including whispers)."""
        if getattr(self, 'chat_alarm_active', False):
            logging.debug("Chat alarm already active")
            return
        self.chat_alarm_active = True
    logging.critical(f"Triggering CHAT alarm ({chat_label})")

    def beep_loop_chat():
        try:
            import winsound
            while self.chat_alarm_active:
                winsound.Beep(1200, 400)
                time.sleep(0.2)
        except Exception:
            while self.chat_alarm_active:
                logging.critical("CHAT ALARM (no sound available on platform)")
                time.sleep(1)

        threading.Thread(target=beep_loop_chat, daemon=True).start()

        if hasattr(self, 'ui') and self.ui is not None:
            try:
                try:
                    if chat_label:
                        tmpl = self.ui.lang.get('chat_alarm_msg_with_label')
                        msg = tmpl.format(label=chat_label)
                    else:
                        msg = self.ui.lang.get('chat_alarm_msg')
                except Exception:
                    if chat_label:
                        tmpl = locales.get_lang(self.settings.get('ui', {}).get('language', 'en')).get('chat_alarm_msg_with_label')
                        msg = tmpl.format(label=chat_label)
                    else:
                        msg = locales.get_lang(self.settings.get('ui', {}).get('language', 'en')).get('chat_alarm_msg')
                self.ui.root.after(0, lambda m=msg: self.ui.show_alarm_popup(m))
            except Exception as e:
                logging.error(f"Failed to show chat alarm popup: {e}")

    def trigger_other_user_alarm(self):
        """Trigger alarm for when other users appear on the map."""
        if getattr(self, 'other_user_alarm_active', False):
            logging.debug("Other-user alarm already active")
            return
        self.other_user_alarm_active = True
    logging.critical("Triggering OTHER-USER alarm — other player on map")

    def beep_loop_other():
        try:
            import winsound
            while self.other_user_alarm_active:
                winsound.Beep(1800, 500)
                time.sleep(0.15)
        except Exception:
            while self.other_user_alarm_active:
                logging.critical("OTHER-USER ALARM (no sound available on platform)")
                time.sleep(1)

        threading.Thread(target=beep_loop_other, daemon=True).start()

        if hasattr(self, 'ui') and self.ui is not None:
            try:
                try:
                    msg = self.ui.lang.get('other_user_alarm_msg')
                except Exception:
                    msg = locales.get_lang(self.settings.get('ui', {}).get('language', 'en')).get('other_user_alarm_msg')
                self.ui.root.after(0, lambda m=msg: self.ui.show_alarm_popup(m))
            except Exception as e:
                logging.error(f"Failed to show other-user alarm popup: {e}")

    def dismiss_alarm(self):
        logging.info("Dismissing alarms (lie, enemy, chat, other-user)")
        # Clear any active alarms
        self.alarm_active = False
        self.enemy_alarm_active = False
        self.chat_alarm_active = False
        self.other_user_alarm_active = False
        # Ensure UI popup is dismissed
        if hasattr(self, 'ui') and self.ui is not None:
            try:
                self.ui.root.after(0, lambda: self.ui._destroy_alarm_popup())
            except Exception as e:
                logging.error(f"Failed to dismiss alarm popup in UI: {e}")

    def verify_preconditions(self):
        issues = []
        expected_os = self.settings['preconditions'].get('os', 'windows').lower()
        if platform.system().lower() != expected_os:
            issues.append(f"OS must be {expected_os}, current: {platform.system()}")
            logging.warning(f"Precondition failed: OS mismatch - expected {expected_os}, got {platform.system()}")
        
        expected_resolution = self.settings['preconditions'].get('resolution', '1920x1080')
        try:
            width, height = map(int, expected_resolution.split('x'))
            screen_size = pyautogui.size()
            if screen_size != (width, height):
                issues.append(f"Resolution must be {expected_resolution}, current: {screen_size[0]}x{screen_size[1]}")
                logging.warning(f"Precondition failed: Resolution mismatch - expected {expected_resolution}, got {screen_size[0]}x{screen_size[1]}")
            else:
                logging.info(f"Precondition passed: Resolution {expected_resolution}")
        except ValueError:
            issues.append(f"Invalid resolution format: {expected_resolution}")
            logging.error(f"Precondition error: Invalid resolution format {expected_resolution}")
        
        # Scaling and other checks are harder to verify automatically
        # For now, assume they are set correctly if specified
        
        if not issues:
            logging.info("All preconditions verified successfully")
        return issues


def main():
    base = Path(__file__).parent
    settings_path = base / 'config' / 'settings.json'
    settings = load_settings(settings_path)

    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    bot = MapleBot(settings)
    ui = MapleBotUI(settings, bot.start, bot.stop, settings_path, bot.update_settings)
    # give bot a reference to UI so it can pop up alarms
    bot.ui = ui
    # allow UI to notify bot to dismiss alarms
    ui.alarm_dismiss_callback = bot.dismiss_alarm
    ui.run()


if __name__ == '__main__':
    main()
