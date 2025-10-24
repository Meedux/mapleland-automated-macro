import pyautogui
import time
from typing import Any, Dict, Tuple
import logging


class CombatManager:
    def __init__(self, settings: Dict[str, Any], vision):
        self.settings = settings
        self.vision = vision

    def find_targets(self, monster_paths: list, character_y: int, char_x: int, char_left: bool):
        return self.vision.find_closest_monster(monster_paths, character_y, char_x, char_left)

    def attack(self, monster_pos: Tuple[int, int], character_x: int, character_direction_left: bool):
        x_diff = monster_pos[0] - character_x
        distance_to_monster = 30
        if x_diff < 0:
            logging.debug("Moving left to attack monster")
            pyautogui.keyDown("z")
            pyautogui.keyDown("left")
            time.sleep(max(0, (abs(x_diff) - distance_to_monster) / 117 * 0.5))
            pyautogui.keyUp("left")
        else:
            logging.debug("Moving right to attack monster")
            pyautogui.keyDown("z")
            pyautogui.keyDown("right")
            time.sleep(max(0, (abs(x_diff) - distance_to_monster) / 117 * 0.5))
            pyautogui.keyUp("right")

        pyautogui.keyDown("ctrl")
        time.sleep(self.settings['hotkeys'].get('key_down_time', 4.5))
        pyautogui.keyUp("ctrl")
        time.sleep(self.settings['hotkeys'].get('attack_delay', 0.5))
        pyautogui.keyUp("z")
        logging.info("Attack sequence completed")
