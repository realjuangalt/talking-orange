# server/config_manager.py (no change needed, just verify)
import json
import os
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'config_manager.log'))
    ]
)
logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self):
        self.root_dir = os.path.dirname(__file__)  # server/
        self.config = self.load_config()
        
    def load_config(self):
        config_path = os.path.join(self.root_dir, 'config.json')
        if not os.path.exists(config_path):
            logger.error(f"config.json not found at {config_path}")
            return {}
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                logger.debug(f"Loaded config from {config_path}: {json.dumps(config, indent=2)}")
                return config
        except Exception as e:
            logger.error(f"Failed to load config.json: {e}")
            return {}