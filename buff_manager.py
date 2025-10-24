import time
import random
import pyautogui
from typing import Any, Dict, List


class BuffManager:
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.last_buff_times = {}

    def check_and_cast_buffs(self):
        current_time = time.time()
        buffs = self.settings.get('buffs', [])
        for buff in buffs:
            if not buff.get('active', False):
                continue
            buff_name = buff['name']
            interval = buff['interval']
            random_range = buff.get('random_range', 0)
            last_time = self.last_buff_times.get(buff_name, 0)
            if current_time - last_time >= interval + random.randint(0, random_range):
                self.cast_buff(buff)
                self.last_buff_times[buff_name] = current_time

    def cast_buff(self, buff: Dict[str, Any]):
        key = buff['key']
        down_time = buff['down_time']
        pyautogui.keyDown(key)
        time.sleep(down_time)
        pyautogui.keyUp(key)