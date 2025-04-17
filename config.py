import json
import os

# Default configuration
DEFAULT_CONFIG = {
    # Ozon API credentials
    "client_id": "",
    "api_key": "",

    # Telegram settings
    "telegram_bot_token": "",
    "telegram_channel": "",

    # Price monitoring settings
    "check_min_price": True,
    "check_marketing_price": True,
    "check_price": True,

    # Product visibility filter
    "visibility": "ALL",  # Options: "ALL" or "IN_SALE"

    # Timer settings (in minutes)
    "timer_interval": 60,

    # Application settings
    "auto_start": False,
    "log_level": "INFO"
}

CONFIG_FILE = "ozon_monitor_config.json"

def load_config():
    """Load configuration from file or create default if not exists"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)

                # Ensure all required keys are present (for backward compatibility)
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value

                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG
    else:
        # Create default config file
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
