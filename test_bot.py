import unittest
from unittest.mock import Mock, patch
from main import MapleBot
from pathlib import Path


class TestMapleBot(unittest.TestCase):
    def setUp(self):
        self.settings = {
            'vision': {'assets_path': 'assets'},
            'monsters': ['test.png'],
            'debug': {'simulation_mode': True}
        }
        self.bot = MapleBot(self.settings)

    def test_verify_preconditions_success(self):
        with patch('platform.system', return_value='Windows'), \
             patch('pyautogui.size', return_value=(1920, 1080)):
            issues = self.bot.verify_preconditions()
            self.assertEqual(len(issues), 0)

    def test_verify_preconditions_failure(self):
        with patch('platform.system', return_value='Linux'), \
             patch('pyautogui.size', return_value=(1920, 1080)):
            issues = self.bot.verify_preconditions()
            self.assertIn("OS must be Windows", issues)

    def test_start_simulation_mode(self):
        self.bot.simulation_mode = True
        result = self.bot.start()
        self.assertTrue(result)  # Should succeed in simulation


if __name__ == '__main__':
    unittest.main()