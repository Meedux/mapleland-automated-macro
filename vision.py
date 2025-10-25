import cv2
import numpy as np
import pyautogui
import easyocr
import re
import logging
import os
import sys
from typing import Any, Dict, Tuple, Optional, List
from pathlib import Path


class Vision:
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        # Initialize EasyOCR reader for English (can add more languages if needed)
        # Prefer a bundled `easyocr_models` directory when frozen with PyInstaller.
        model_dir_setting = self.settings.get('vision', {}).get('easyocr_model_dir', 'easyocr_models')
        # If running from a PyInstaller bundle, files are unpacked to sys._MEIPASS
        base = getattr(sys, '_MEIPASS', None) or os.path.abspath(os.path.dirname(__file__))
        bundled_model_dir = os.path.join(base, model_dir_setting)
        if os.path.isdir(bundled_model_dir):
            try:
                self.reader = easyocr.Reader(['en'], gpu=False, model_storage_directory=bundled_model_dir)
            except Exception:
                logging.warning(f"Failed to initialize EasyOCR with bundled models at {bundled_model_dir}, falling back to default initialization")
                self.reader = easyocr.Reader(['en'], gpu=False)
        else:
            # Default initialization (will download models if they are missing)
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
            logging.error("Character template images not found")
            raise FileNotFoundError("Character template images not found")

        screenshot = self.capture_screen()
        left_result = cv2.matchTemplate(screenshot, left_template, cv2.TM_CCOEFF_NORMED)
        right_result = cv2.matchTemplate(screenshot, right_template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.8

        left_max = cv2.minMaxLoc(left_result)[1]
        right_max = cv2.minMaxLoc(right_result)[1]

        if left_max >= threshold and left_max > right_max:
            loc = cv2.minMaxLoc(left_result)[3]
            logging.debug(f"Character found facing left at ({loc[0]}, {loc[1]})")
            return loc[0], loc[1], True
        elif right_max >= threshold and right_max > left_max:
            loc = cv2.minMaxLoc(right_result)[3]
            logging.debug(f"Character found facing right at ({loc[0]}, {loc[1]})")
            return loc[0], loc[1], False
        else:
            logging.debug("Character not found in current frame")
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
                logging.warning(f"Monster template not found: {path}")
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
        if closest:
            logging.debug(f"Closest monster found at {closest}")
        else:
            logging.debug("No monsters found within range")
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
        logging.debug(f"HP: {hp_current}/{hp_max}, MP: {mp_current}/{mp_max}")
        return hp_current, hp_max, mp_current, mp_max

    def detect_user(self):
        user_path = self.assets_path / 'ui_elements' / 'reduser.png'
        screenshot = self.capture_screen((12, 67, 270, 307))  # 282-12=270, 374-67=307
        loc = self.find_template(str(user_path), screenshot, 0.7)
        return len(loc) > 0

    def detect_lie_detector(self):
        """Detect the polygraph / lie-detector overlay that appears when a lie detector is used.
        Uses a template image path from settings: settings['vision'].get('lie_template').
        Returns True if detected.
        """
        if not self.settings.get('misc', {}).get('lie_detector', False):
            return False

        lie_template_setting = self.settings.get('vision', {}).get('lie_template', '')
        if not lie_template_setting:
            # default fallback
            lie_path = self.assets_path / 'ui_elements' / 'polygraph.png'
        else:
            lie_path = Path(lie_template_setting)

        try:
            # Search full screen for the polygraph overlay — threshold configurable
            threshold = float(self.settings.get('vision', {}).get('lie_threshold', 0.7))
        except Exception:
            threshold = 0.7

        screenshot = self.capture_screen()
        locs = self.find_template(str(lie_path), screenshot, threshold)
        found = len(locs) > 0
        if found:
            logging.warning(f"Lie detector overlay detected at {locs[:3]}")
        return found

    def detect_enemy_detector(self):
        """Detect the anti-auto-play enemy overlay/image that should trigger an emergency stop.
        Uses a template image path from settings: settings['vision'].get('enemy_template').
        Returns True if detected.
        """
        if not self.settings.get('misc', {}).get('enemy_detector', False):
            return False

        enemy_template_setting = self.settings.get('vision', {}).get('enemy_template', '')
        if not enemy_template_setting:
            enemy_path = self.assets_path / 'ui_elements' / 'enemy_alert.png'
        else:
            enemy_path = Path(enemy_template_setting)

        try:
            threshold = float(self.settings.get('vision', {}).get('enemy_threshold', 0.7))
        except Exception:
            threshold = 0.7

        screenshot = self.capture_screen()
        locs = self.find_template(str(enemy_path), screenshot, threshold)
        found = len(locs) > 0
        if found:
            logging.error(f"Enemy anti-auto-play indicator detected at {locs[:3]}")
        return found

    def _parse_color(self, color_val):
        """Parse color from hex string like '#rrggbb' or 'r,g,b' into (B,G,R) tuple for OpenCV images."""
        if isinstance(color_val, (list, tuple)) and len(color_val) == 3:
            r, g, b = color_val
            return (int(b), int(g), int(r))
        if isinstance(color_val, str):
            s = color_val.strip()
            if s.startswith('#') and len(s) == 7:
                r = int(s[1:3], 16)
                g = int(s[3:5], 16)
                b = int(s[5:7], 16)
                return (b, g, r)
            parts = [p.strip() for p in s.split(',')]
            if len(parts) == 3:
                r, g, b = map(int, parts)
                return (b, g, r)
        raise ValueError(f"Unsupported color format: {color_val}")

    def detect_chat_event(self):
        """Detect chat messages in the chat area by color.
        Returns (found: bool, label: Optional[str]) where label is the matching chat type (e.g., 'whisper').
        Uses settings:
          - vision.chat_region: [x,y,w,h]
          - vision.chat_colors: {label: color}
          - vision.chat_color_tolerance: int (per-channel tolerance)
          - vision.chat_pixel_ratio: float (fraction of pixels that must match)
        """
        if not self.settings.get('misc', {}).get('chat_detector', False):
            return False, None

        cfg = self.settings.get('vision', {})
        region = cfg.get('chat_region', [10, 800, 400, 200])
        try:
            x, y, w, h = map(int, region)
        except Exception:
            x, y, w, h = 10, 800, 400, 200

        img = self.capture_screen((x, y, w, h))
        # Convert to BGR (already BGR) and sample
        chat_colors = cfg.get('chat_colors', {})
        tolerance = int(cfg.get('chat_color_tolerance', 30))
        pixel_ratio = float(cfg.get('chat_pixel_ratio', 0.002))
        h_img, w_img = img.shape[:2]
        total_pixels = h_img * w_img

        for label, color_val in chat_colors.items():
            try:
                target_bgr = self._parse_color(color_val)
            except Exception:
                logging.debug(f"Skipping invalid chat color for {label}: {color_val}")
                continue
            # Create mask where pixels are within tolerance
            lower = np.array([max(0, c - tolerance) for c in target_bgr], dtype=np.uint8)
            upper = np.array([min(255, c + tolerance) for c in target_bgr], dtype=np.uint8)
            mask = cv2.inRange(img, lower, upper)
            match_count = int(cv2.countNonZero(mask))
            if match_count > max(3, int(total_pixels * pixel_ratio)):
                logging.warning(f"Chat event detected: {label} (matches={match_count}) in region {region}")
                return True, label

        return False, None

    def detect_other_user(self):
        """Detect other players appearing on the screen using a template (e.g., nameplate/player sprite).
        Uses settings['vision']['other_user_template'] and 'other_user_threshold'. Returns True if found.
        """
        if not self.settings.get('misc', {}).get('other_user_detector', False):
            return False

        other_template_setting = self.settings.get('vision', {}).get('other_user_template', '')
        if not other_template_setting:
            other_path = self.assets_path / 'ui_elements' / 'other_user.png'
        else:
            other_path = Path(other_template_setting)

        try:
            threshold = float(self.settings.get('vision', {}).get('other_user_threshold', 0.75))
        except Exception:
            threshold = 0.75

        screenshot = self.capture_screen()
        locs = self.find_template(str(other_path), screenshot, threshold)
        found = len(locs) > 0
        if found:
            logging.error(f"Other user detected at {locs[:3]}")
        return found

    def detect_top_floor(self):
        """Detect if the character is currently located on a designated top-floor area.
        Uses optional settings['vision']['top_floor_template'] for template matching and
        returns True if matched.
        """
        if not self.settings.get('misc', {}).get('top_floor_stoppage', False):
            return False

        tpl = self.settings.get('vision', {}).get('top_floor_template', '')
        if not tpl:
            tpl_path = self.assets_path / 'ui_elements' / 'top_floor.png'
        else:
            tpl_path = Path(tpl)

        try:
            threshold = float(self.settings.get('vision', {}).get('top_floor_threshold', 0.7))
        except Exception:
            threshold = 0.7

        screenshot = self.capture_screen()
        locs = self.find_template(str(tpl_path), screenshot, threshold)
        found = len(locs) > 0
        if found:
            logging.info(f"Top-floor template detected at {locs[:3]}")
        return found

    def detect_map_ends_blocked(self):
        """Heuristic to detect if both ends of the map show a dark 'blocked' area.
        Samples small strips at left and right edges and checks mean brightness.
        Returns True if both ends are sufficiently dark.
        """
        try:
            screen = pyautogui.screenshot()
            img = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2GRAY)
            h, w = img.shape
            edge_w = int(max(10, w * 0.03))
            left_strip = img[ int(h*0.4):int(h*0.8), 0:edge_w ]
            right_strip = img[ int(h*0.4):int(h*0.8), w-edge_w:w ]
            left_mean = np.mean(left_strip)
            right_mean = np.mean(right_strip)
            # threshold for 'dark' area
            if left_mean < 40 and right_mean < 40:
                logging.info(f"Map ends appear blocked/dark (left_mean={left_mean:.1f}, right_mean={right_mean:.1f})")
                return True
        except Exception:
            pass
        return False

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
        logging.info(f"Nickname captured: '{nickname}'")
        return nickname if nickname else None
