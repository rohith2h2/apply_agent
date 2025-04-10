"""
Configuration Utilities
======================
This module handles configuration loading and validation.
"""

import os
import json
from pathlib import Path
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config.json"

def load_config(config_path=None):
    """
    Load application configuration from a JSON file and environment variables.
    
    Args:
        config_path (str, optional): Path to the configuration file. Defaults to None.
        
    Returns:
        dict: The application configuration.
    """
    # Default empty config
    config = {}
    
    # Try to load config from file
    try:
        config_path = config_path or os.environ.get('CONFIG_PATH') or DEFAULT_CONFIG_PATH
        
        if Path(config_path).exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
        else:
            logger.warning(f"Configuration file not found at {config_path}, using defaults")
            
            # Create default config
            default_config = {
                "app_name": "Job Application Agent",
                "host": "127.0.0.1",
                "port": 5000,
                "debug": False,
                "data_dir": str(Path(__file__).parent.parent.parent / "data"),
                "openai_api_key": "",
                "selenium_driver_path": "",
                "max_applications_per_day": 10,
                "user_profile_path": str(Path(__file__).parent.parent.parent / "data" / "user_profile.json")
            }
            
            # Write default config
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            
            config = default_config
            logger.info(f"Created default configuration at {config_path}")
    
    except Exception as e:
        logger.error(f"Error loading configuration: {e}", exc_info=True)
    
    # Override with environment variables
    for key in config.keys():
        env_key = f"APPLY_AGENT_{key.upper()}"
        if env_key in os.environ:
            config[key] = os.environ[env_key]
    
    return config 