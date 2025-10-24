import pyautogui
import time
import logging
from typing import Any, Dict


class PotionManager:
    def __init__(self, settings: Dict[str, Any], vision):
        self.settings = settings
        self.vision = vision

    def check_and_use(self):
        hp_current, hp_max, mp_current, mp_max = self.vision.read_hp_mp()
        if hp_current and hp_max:
            hp_percentage = (hp_current / hp_max) * 100
            if hp_percentage < self.settings['misc'].get('hp_potion_percent', 50):
                if not (hp_percentage < 20 and str(hp_max)[0] == '4'):
                    logging.info(f"Using HP potion (HP: {hp_percentage:.1f}%)")
                    pyautogui.press(self.settings['hotkeys'].get('hp_potion', 'del'))
        if mp_current and mp_max:
            mp_percentage = (mp_current / mp_max) * 100
            if mp_percentage < self.settings['misc'].get('mp_potion_percent', 30):
                if not (mp_percentage < 20 and str(mp_max)[0] == '4'):
                    logging.info(f"Using MP potion (MP: {mp_percentage:.1f}%)")
                    pyautogui.press(self.settings['hotkeys'].get('mp_potion', 'end'))
