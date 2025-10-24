import json
import threading
import time
import pyautogui
import platform
import logging
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
                time.sleep(2)
                pyautogui.click(1396, 532)
                time.sleep(20)
                pyautogui.click(1400, 766)
                break
            else:
                time.sleep(30)

    def check_for_channel_change(self):
        while self.running:
            if self.vision.detect_user():
                self.change_channel()
            time.sleep(10)

    def potion_thread(self):
        while self.running:
            self.potion.check_and_use()
            time.sleep(1)

    def simulate_or_execute(self, action_desc, func, *args, **kwargs):
        if self.simulation_mode:
            logging.info(f"SIMULATION: {action_desc}")
        else:
            func(*args, **kwargs)

    def main_logic(self):
        while self.running:
            try:
                char_x, char_y, char_left = self.vision.find_character_coordinates()
                if char_x is None:
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

                monster = self.combat.find_targets(self.monster_paths, char_y, char_x, char_left)
                if monster:
                    self.debug_overlay.update(hp_current, hp_max, mp_current, mp_max, char_x, char_y, "Attacking monster")
                    self.combat.attack(monster, char_x, char_left)
                else:
                    ropes = self.vision.find_ropes(char_y)
                    if ropes:
                        closest_rope = min(ropes, key=lambda r: abs(char_x - r[0]))
                        self.movement.climb_rope(closest_rope[0], closest_rope[1], char_x, char_left)
                    else:
                        self.movement.patrol()

                self.buff.check_and_cast_buffs()

                hp_current, hp_max, mp_current, mp_max = self.vision.read_hp_mp()
                self.debug_overlay.update(hp_current, hp_max, mp_current, mp_max, char_x, char_y, "Searching for monsters")

                logging.info(f"Character at ({char_x}, {char_y}), direction: {'left' if char_left else 'right'}")

                if time.localtime().tm_min % 10 == 0 and time.localtime().tm_sec < 11:
                    pyautogui.press('pageup')
                if time.localtime().tm_min % 30 == 0 and time.localtime().tm_sec < 11:
                    pyautogui.press('home')
            except Exception as e:
                print(f"Error in main logic: {e}")
                time.sleep(5)

    def start(self):
        issues = self.verify_preconditions()
        if issues:
            print("Precondition verification failed:")
            for issue in issues:
                print(f"- {issue}")
            self.settings['preconditions']['verified'] = False
            return False
        self.settings['preconditions']['verified'] = True
        self.running = True
        threading.Thread(target=self.check_for_channel_change, daemon=True).start()
        threading.Thread(target=self.potion_thread, daemon=True).start()
        threading.Thread(target=self.main_logic, daemon=True).start()
        return True

    def stop(self):
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

    def verify_preconditions(self):
        issues = []
        expected_os = self.settings['preconditions'].get('os', 'windows').lower()
        if platform.system().lower() != expected_os:
            issues.append(f"OS must be {expected_os}, current: {platform.system()}")
        
        expected_resolution = self.settings['preconditions'].get('resolution', '1920x1080')
        try:
            width, height = map(int, expected_resolution.split('x'))
            screen_size = pyautogui.size()
            if screen_size != (width, height):
                issues.append(f"Resolution must be {expected_resolution}, current: {screen_size[0]}x{screen_size[1]}")
        except ValueError:
            issues.append(f"Invalid resolution format: {expected_resolution}")
        
        # Scaling and other checks are harder to verify automatically
        # For now, assume they are set correctly if specified
        
        return issues


def main():
    base = Path(__file__).parent
    settings_path = base / 'config' / 'settings.json'
    settings = load_settings(settings_path)

    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    bot = MapleBot(settings)
    ui = MapleBotUI(settings, bot.start, bot.stop, settings_path, bot.update_settings)
    ui.run()


if __name__ == '__main__':
    main()
