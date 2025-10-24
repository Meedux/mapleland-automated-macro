import pyautogui
import time
from typing import Any, Dict


class MovementManager:
    def __init__(self, settings: Dict[str, Any], vision):
        self.settings = settings
        self.vision = vision

    def move_character(self, character_x: int, target_x: int, character_direction_left: bool):
        distance = abs(character_x - target_x)
        if (character_x > target_x and character_direction_left) or (character_x < target_x and not character_direction_left):
            movement_time = distance / 117 * 0.5
        else:
            movement_time = (distance - 16) / 117 * 0.5

        direction = "left" if character_x > target_x else "right"
        pyautogui.keyDown('z')
        pyautogui.keyDown(direction)
        time.sleep(movement_time)
        pyautogui.keyUp(direction)
        pyautogui.keyUp('z')

    def climb_rope(self, rope_x: int, rope_y: int, character_x: int, character_direction_left: bool):
        distance_to_rope = abs(character_x - rope_x)
        if distance_to_rope <= 40:
            if rope_x <= character_x:
                pyautogui.keyDown("left")
                time.sleep(0.1)
                pyautogui.keyUp("left")
            else:
                pyautogui.press("left")
            pyautogui.keyDown("up")
            pyautogui.keyDown("alt")
            time.sleep(3.5)
            pyautogui.keyUp("up")
            pyautogui.keyUp("alt")
        else:
            self.move_character(character_x, rope_x, character_direction_left)

    def patrol(self):
        pyautogui.keyDown("right")
        time.sleep(5)
        pyautogui.keyUp("right")

    def navigate_to(self, x: int, y: int):
        pass
