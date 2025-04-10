#!/usr/bin/env python3
"""
Job Application Agent
====================
Main application entry point.
"""

import os
import logging
import sys
from src.utils.config import load_config
from ui.app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run the application."""
    try:
        # Load configuration
        config = load_config()
        logger.info(f"Starting Job Application Agent with config: {config}")
        
        # Create and run the Flask application
        app = create_app(config)
        app.run(
            host=config.get('host', '127.0.0.1'),
            port=config.get('port', 5000),
            debug=config.get('debug', False)
        )
    except Exception as e:
        logger.error(f"Error starting application: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main() 