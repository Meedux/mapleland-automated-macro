from typing import Any, Dict


class Vision:
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings

    def capture_screen(self):
        return None

    def find_template(self, template_name: str):
        return []

    def read_text(self, region=None):
        return ''
