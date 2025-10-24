import pyautogui
import time
from typing import Any, Dict, Tuple


class CombatManager:
    def __init__(self, settings: Dict[str, Any], vision):
        self.settings = settings
        self.vision = vision

    def find_targets(self, monster_paths: list, character_y: int):
        return self.vision.find_closest_monster(monster_paths, character_y)

    def attack(self, monster_pos: Tuple[int, int], character_x: int, character_direction_left: bool):
        x_diff = monster_pos[0] - character_x
        distance_to_monster = 30
        if x_diff < 0:
            pyautogui.keyDown("z")
            pyautogui.keyDown("left")
            time.sleep(max(0, (abs(x_diff) - distance_to_monster) / 117 * 0.5))
            pyautogui.keyUp("left")
        else:
            pyautogui.keyDown("z")
            pyautogui.keyDown("right")
            time.sleep(max(0, (abs(x_diff) - distance_to_monster) / 117 * 0.5))
            pyautogui.keyUp("right")

        pyautogui.keyDown("ctrl")
        time.sleep(4.5)
        pyautogui.keyUp("ctrl")
        time.sleep(0.5)
        pyautogui.keyUp("z")
