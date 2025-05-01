import json
import os
import logging
from platformdirs import user_config_dir

logger = logging.getLogger(__name__)

APP_NAME = "MotivationalWidget"
APP_AUTHOR = "YourAppNameOrAuthor" # Or replace with a more specific author/org name
CONFIG_FILE_NAME = "settings.json"

class ConfigManager:
    def __init__(self, config_file_path=None):
        if config_file_path:
            self.config_path = config_file_path
        else:
            # Determine the platform-specific config directory
            config_dir = user_config_dir(APP_NAME, APP_AUTHOR)
            if not os.path.exists(config_dir):
                try:
                    os.makedirs(config_dir)
                    logger.info(f"Created config directory: {config_dir}")
                except OSError as e:
                    logger.error(f"Failed to create config directory {config_dir}: {e}")
                    # Fallback to current directory if creation fails
                    config_dir = "."
            self.config_path = os.path.join(config_dir, CONFIG_FILE_NAME)

        logger.info(f"Using config file path: {self.config_path}")
        self.settings = self._get_default_settings()
        self.load_config()

    def _get_default_settings(self):
        """Returns the default application settings."""
        return {
            "csv_path": "quotes.csv",
            "interval_ms": 10000, # 10 seconds
            "background_type": "color", # 'color', 'image', 'video'
            "background_value": "#1E1E1E", # Default dark grey color
            "image_paths": [], # List to store multiple background image paths when using image type
            "text_color": "#DCDCDC", # Default light grey text
            "font_family": "Arial", # Default font family
            "font_size": 14, # Default font size
            "always_on_top": True,
            "window_geometry": None # To store position and size [x, y, width, height]
        }

    def load_config(self):
        """Loads settings from the JSON config file. Merges with defaults if file exists, otherwise uses defaults."""
        defaults = self._get_default_settings()
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # Merge loaded settings with defaults, ensuring all keys exist
                    self.settings = defaults
                    self.settings.update(loaded_settings)
                    logger.info(f"Loaded settings from {self.config_path}")
            else:
                logger.info("Config file not found. Using default settings.")
                self.settings = defaults
                # Optionally save defaults immediately on first run
                # self.save_config()
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {self.config_path}. Using default settings.", exc_info=True)
            self.settings = defaults
        except Exception as e:
            logger.error(f"Failed to load config file {self.config_path}: {e}", exc_info=True)
            self.settings = defaults # Fallback to defaults on any other error

        # Ensure essential keys have valid defaults even after loading potentially incomplete file
        for key, value in defaults.items():
            if key not in self.settings:
                self.settings[key] = value


    def save_config(self):
        """Saves the current settings to the JSON config file."""
        try:
            # Ensure the directory exists before writing
            config_dir = os.path.dirname(self.config_path)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            logger.info(f"Saved settings to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config file {self.config_path}: {e}", exc_info=True)

    def get_setting(self, key, default=None):
        """Gets a specific setting value by key."""
        # Return a copy for mutable types like lists/dicts if necessary
        # For this config structure, direct access is likely fine.
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        """Sets a specific setting value by key."""
        self.settings[key] = value
        # Consider saving immediately or having an explicit save call elsewhere
        # self.save_config() # Uncomment to save on every change

    def get_all_settings(self):
        """Returns the entire settings dictionary."""
        return self.settings.copy() # Return a copy to prevent external modification

# Example Usage (for testing)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("--- Testing ConfigManager --- ")

    # Test with default location
    print("\nTesting with default config location...")
    config_manager = ConfigManager()
    print(f"Config Path: {config_manager.config_path}")
    print(f"Initial Settings: {config_manager.get_all_settings()}")

    # Modify a setting
    config_manager.set_setting("interval_ms", 5000)
    config_manager.set_setting("new_setting", "test_value") # Add a new setting
    print(f"Modified Settings: {config_manager.get_all_settings()}")

    # Save settings
    config_manager.save_config()

    # Create a new manager instance to test loading
    print("\nCreating new instance to test loading...")
    config_manager_load = ConfigManager()
    print(f"Loaded Settings: {config_manager_load.get_all_settings()}")

    # Test setting retrieval
    print(f"Interval: {config_manager_load.get_setting('interval_ms')}")
    print(f"New Setting: {config_manager_load.get_setting('new_setting')}")
    print(f"Non-existent setting (with default): {config_manager_load.get_setting('no_such_key', 'default_val')}")

    # Clean up the created config file for testing
    try:
        os.remove(config_manager.config_path)
        logger.info(f"Removed test config file: {config_manager.config_path}")
        # Attempt to remove directory if empty
        config_dir = os.path.dirname(config_manager.config_path)
        if not os.listdir(config_dir): # Check if directory is empty
            os.rmdir(config_dir)
            logger.info(f"Removed test config directory: {config_dir}")
    except OSError as e:
        logger.warning(f"Could not remove test config file/dir: {e}")

    print("\n--- ConfigManager Test Complete --- ") 