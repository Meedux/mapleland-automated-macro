import cv2
import numpy as np
import pyautogui
import pytesseract
import re
from typing import Any, Dict, Tuple, Optional, List
from pathlib import Path


class Vision:
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        pytesseract.pytesseract.tesseract_cmd = settings.get('tesseract_path', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
        self.assets_path = Path(settings.get('assets_path', 'assets'))

    def capture_screen(self, region=None):
        screenshot = pyautogui.screenshot(region=region)
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    def find_template(self, template_path: str, screenshot=None, threshold=0.8):
        if screenshot is None:
            screenshot = self.capture_screen()
        template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
        if template is None:
            return []
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(result >= threshold)
        return list(zip(*loc[::-1]))

    def find_character_coordinates(self):
        left_char_path = self.assets_path / 'ui_elements' / 'left_char.png'
        right_char_path = self.assets_path / 'ui_elements' / 'right_char.png'
        left_template = cv2.imread(str(left_char_path), cv2.IMREAD_COLOR)
        right_template = cv2.imread(str(right_char_path), cv2.IMREAD_COLOR)
        if left_template is None or right_template is None:
            raise FileNotFoundError("Character template images not found")

        screenshot = self.capture_screen()
        left_result = cv2.matchTemplate(screenshot, left_template, cv2.TM_CCOEFF_NORMED)
        right_result = cv2.matchTemplate(screenshot, right_template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.8

        left_max = cv2.minMaxLoc(left_result)[1]
        right_max = cv2.minMaxLoc(right_result)[1]

        if left_max >= threshold and left_max > right_max:
            loc = cv2.minMaxLoc(left_result)[3]
            return loc[0], loc[1], True
        elif right_max >= threshold and right_max > left_max:
            loc = cv2.minMaxLoc(right_result)[3]
            return loc[0], loc[1], False
        else:
            return None, None, None

    def find_closest_monster(self, monster_paths: List[str], character_y: int):
        screenshot = self.capture_screen()
        closest = None
        min_dist = float('inf')
        for path in monster_paths:
            template = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if template is None:
                continue
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            loc = np.where(result >= 0.8)
            for pt in zip(*loc[::-1]):
                if abs(character_y - pt[1]) < 60:
                    dist = abs(pt[0] - 960)  # assuming center x
                    if dist < min_dist:
                        min_dist = dist
                        closest = pt
        return closest

    def find_ropes(self, character_y: int):
        rope_path = self.assets_path / 'ui_elements' / 'rope.png'
        screenshot = self.capture_screen()
        loc = self.find_template(str(rope_path), screenshot)
        valid_ropes = [pt for pt in loc if abs(character_y - pt[1]) < 200]
        return valid_ropes

    def read_hp_mp(self):
        hp_region = (401, 978, 150, 21)
        mp_region = (611, 979, 150, 20)
        hp_img = self.capture_screen(hp_region)
        mp_img = self.capture_screen(mp_region)
        hp_text = pytesseract.image_to_string(hp_img, config='--psm 6')
        mp_text = pytesseract.image_to_string(mp_img, config='--psm 6')

        def parse_ratio(text):
            match = re.search(r'[|\[\({\s]?\s*(\d+)\s*[/\s]?\s*(\d+)[|\]\)}\s]?', text)
            if match:
                current, max_val = map(int, match.groups())
                return current, max_val
            return None, None

        hp_current, hp_max = parse_ratio(hp_text)
        mp_current, mp_max = parse_ratio(mp_text)
        return hp_current, hp_max, mp_current, mp_max

    def detect_user(self):
        user_path = self.assets_path / 'ui_elements' / 'reduser.png'
        screenshot = self.capture_screen((12, 67, 270, 307))  # 282-12=270, 374-67=307
        loc = self.find_template(str(user_path), screenshot, 0.7)
        return len(loc) > 0
