import cv2
import numpy as np
import pyautogui
import easyocr
import re
from typing import Any, Dict, Tuple, Optional, List
from pathlib import Path


class Vision:
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        # Initialize EasyOCR reader for English (can add more languages if needed)
        self.reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if GPU available
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

    def find_closest_monster(self, monster_paths: List[str], character_y: int, char_x: int = 960, char_left: bool = False):
        screenshot = self.capture_screen()
        closest = None
        min_dist = float('inf')
        x_range = self.settings.get('monster_settings', {}).get('x_range', 200)
        y_range = self.settings.get('monster_settings', {}).get('y_range', 60)
        handle_opposite = self.settings.get('monster_settings', {}).get('handle_opposite', True)
        threshold = self.settings.get('monster_settings', {}).get('monster_recognition_rate', 0.8)
        
        for path in monster_paths:
            template = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if template is None:
                continue
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            loc = np.where(result >= threshold)
            for pt in zip(*loc[::-1]):
                if abs(character_y - pt[1]) < y_range and abs(char_x - pt[0]) < x_range:
                    # Check direction
                    if handle_opposite and ((char_left and pt[0] > char_x) or (not char_left and pt[0] < char_x)):
                        continue  # Skip opposite direction monsters if not handling
                    dist = abs(pt[0] - char_x)
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
        
        # Convert to RGB for easyocr
        hp_img_rgb = cv2.cvtColor(hp_img, cv2.COLOR_BGR2RGB)
        mp_img_rgb = cv2.cvtColor(mp_img, cv2.COLOR_BGR2RGB)
        
        hp_results = self.reader.readtext(hp_img_rgb)
        mp_results = self.reader.readtext(mp_img_rgb)
        
        hp_text = ' '.join([result[1] for result in hp_results])
        mp_text = ' '.join([result[1] for result in mp_results])

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

    def capture_nickname(self):
        # Assuming nickname is in a fixed region, e.g., above character
        nickname_region = (800, 800, 320, 50)  # Example region, adjust as needed
        img = self.capture_screen(nickname_region)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # For easyocr, convert to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.reader.readtext(img_rgb)
        text = ' '.join([result[1] for result in results])
        # Clean up text
        nickname = re.sub(r'[^\w\s]', '', text).strip()
        return nickname if nickname else None
