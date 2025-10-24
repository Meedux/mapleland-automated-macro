import json
import threading
import time
import pyautogui
from pathlib import Path

from combat import CombatManager
from movement import MovementManager
from potion_manager import PotionManager
from vision import Vision
from ui import MapleBotUI


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
        self.running = False
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

                monster = self.combat.find_targets(self.monster_paths, char_y)
                if monster:
                    self.combat.attack(monster, char_x, char_left)
                else:
                    ropes = self.vision.find_ropes(char_y)
                    if ropes:
                        closest_rope = min(ropes, key=lambda r: abs(char_x - r[0]))
                        self.movement.climb_rope(closest_rope[0], closest_rope[1], char_x, char_left)
                    else:
                        self.movement.patrol()

                if time.localtime().tm_min % 10 == 0 and time.localtime().tm_sec < 11:
                    pyautogui.press('pageup')
                if time.localtime().tm_min % 30 == 0 and time.localtime().tm_sec < 11:
                    pyautogui.press('home')
            except Exception as e:
                print(f"Error in main logic: {e}")
                time.sleep(5)

    def start(self):
        self.running = True
        threading.Thread(target=self.check_for_channel_change, daemon=True).start()
        threading.Thread(target=self.potion_thread, daemon=True).start()
        threading.Thread(target=self.main_logic, daemon=True).start()

    def stop(self):
        self.running = False


def main():
    base = Path(__file__).parent
    settings_path = base / 'config' / 'settings.json'
    settings = load_settings(settings_path)

    bot = MapleBot(settings)
    ui = MapleBotUI(settings, bot.start, bot.stop, settings_path)
    ui.run()


if __name__ == '__main__':
    main()
