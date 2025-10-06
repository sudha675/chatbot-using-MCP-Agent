# config.py
import os

# Model Configuration
DEFAULT_MODEL = "gemma2:2b"
MAX_HISTORY = 10
STREAM_DELAY = 0.01  # Delay between words for streaming effect

# File Configuration
CONVERSATIONS_DIR = "conversations"
AUTO_SAVE = True  # Auto-save conversations on exit

# Display Configuration
SHOW_RESPONSE_STATS = True  # Show response time and word count
SHOW_WELCOME_MESSAGE = True