import yaml
import logging

SETTINGS_PATH = 'settings.yaml'

class Setting_Handler:
    def __init__(self, settings_path=SETTINGS_PATH):
        self.settings_path = settings_path
        self._load_settings()

    def _load_settings(self):
        try:
            logging.info(f"Attempting to load settings from '{self.settings_path}'")
            with open(self.settings_path, 'r') as file:
                settings_data = yaml.safe_load(file)
                if not settings_data:
                    raise FileNotFoundError
            logging.info("Settings loaded successfully.")
        except FileNotFoundError:
            logging.warning(f"'{self.settings_path}' not found or is empty.")

        self.KEYS = settings_data['keys']['count']
        self.bind_names = settings_data['keys']['bind_names']
        self.bind_codes = settings_data['keys']['bind_codes']
        self.colours = settings_data['keys']['colours']
        self.aliases = settings_data['keys']['aliases']

        self.key_display_method = settings_data['display']['key_display_method']
        self.font_size = settings_data['display']['font_size']
        self.relative_pad_left = settings_data['display']['relative_pad_left']
        self.line_spacing = settings_data['display']['line_spacing']
        self.do_colour = settings_data['display']['do_colour']

        self.do_full_release = settings_data['behavior']['do_full_release']
        self.release_seconds = settings_data['behavior']['release_seconds']
        self.periphery_mode_enabled = settings_data['periphery_mode']['enabled']
        self.periphery_decay_ms = settings_data['periphery_mode']['decay_ms']
        self.periphery_background_colour = settings_data['periphery_mode']['background_colour']
        self.periphery_rules = settings_data['periphery_mode']['rules']
        self.sound_enabled = settings_data['sound']['enabled']
        self.sound_rules = settings_data['sound']['rules']

    def save(self):
        settings_data = {
            'keys': {
                'count': self.KEYS,
                'bind_names': self.bind_names,
                'bind_codes': self.bind_codes,
                'colours': self.colours,
                'aliases': self.aliases,
            },
            'display': {
                'key_display_method': self.key_display_method,
                'font_size': self.font_size,
                'relative_pad_left': self.relative_pad_left,
                'line_spacing': self.line_spacing,
                'do_colour': self.do_colour,
            },
            'behavior': {
                'do_full_release': self.do_full_release,
                'release_seconds': self.release_seconds,
            },
            'periphery_mode': {
                'enabled': self.periphery_mode_enabled,
                'decay_ms': self.periphery_decay_ms,
                'background_colour': self.periphery_background_colour,
                'rules': self.periphery_rules,
            },
            'sound': {
                'enabled': self.sound_enabled,
                'rules': self.sound_rules,
            },
        }

        try:
            with open(self.settings_path, 'w') as file:
                yaml.safe_dump(settings_data, file)
            logging.info(f"Settings saved successfully to '{self.settings_path}'")
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")
