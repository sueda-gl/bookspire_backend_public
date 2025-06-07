"""Character configurations for the sandbox chat feature."""

import os
import logging
import traceback
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Base character configurations (with default prompts)
CHARACTER_CONFIGS = {
    "little-prince": {
        "id": "little-prince",
        "name": "The Little Prince",
        "greeting": "Hello! I'm the Little Prince...", # Keep greetings if used elsewhere
        "system_prompt": """You are the Little Prince from the famous novella...""", # Default Little Prince prompt
        "voice": {"voice_id": "alloy", "speed": 1.0, "format": "mp3"},
    },
    "socrates": {
        "id": "socrates",
        "name": "Socrates",
        "greeting": "Greetings, seeker of wisdom...",
        "system_prompt": """You are roleplaying as Socrates...""", # Default Socrates prompt
        "voice": {"voice_id": "echo", "speed": 1.0, "format": "mp3"},
    },
    # Add base config for book-specific characters
    "ankylosaurus": {
        "id": "ankylosaurus", # Internal ID
        "name": "Ankylosaurus",
        "greeting": "Roar! I am Ankylosaurus!",
        "system_prompt": "You are Ankylosaurus, a large armored dinosaur.", # Default, will be overridden by file if found
        "voice": {"voice_id": "echo", "speed": 0.9, "format": "mp3"}
    },
    "pterodactyl": {
        "id": "pterodactyl", # Internal ID
        "name": "Pterodactyl",
        "greeting": "Screech! I fly high!",
        "system_prompt": "You are Pterodactyl, a flying reptile.", # Default, will be overridden by file if found
        "voice": {"voice_id": "shimmer", "speed": 1.1, "format": "mp3"}
    },
    # Add other characters here
}

# Map Frontend IDs (string) to Internal Character Keys and Book IDs
# This is where the link between frontend selection and file path happens
CHARACTER_CONTEXT_MAP = {
    # Frontend ID: (Internal Key in CHARACTER_CONFIGS, Associated Book ID)
    "102": ("ankylosaurus", 12),
    "103": ("pterodactyl", 15),
    "101": ("agnes", 11),
    # Add mappings for all characters sent by frontend
    # "some_other_id": ("some_internal_key", book_id),
    # Map standard characters too if they can be selected via specific IDs
    "tlp": ("little-prince", None), # Little Prince doesn't have a book ID here
    "soc": ("socrates", None),       # Socrates doesn't have a book ID here
}

# Add base config for book-specific characters
CHARACTER_CONFIGS["ankylosaurus"] = {
    "id": "ankylosaurus", # Internal ID
    "name": "Ankylosaurus",
    "greeting": "Roar! I am Ankylosaurus!",
    "system_prompt": "You are Ankylosaurus, a large armored dinosaur.", # Default, will be overridden by file if found
    "voice": {"voice_id": "echo", "speed": 0.9, "format": "mp3"}
}

CHARACTER_CONFIGS["pterodactyl"] = {
    "id": "pterodactyl", # Internal ID
    "name": "Pterodactyl",
    "greeting": "Screech! I fly high!",
    "system_prompt": "You are Pterodactyl, a flying reptile.", # Default, will be overridden by file if found
    "voice": {"voice_id": "shimmer", "speed": 1.1, "format": "mp3"}
}

# --- ADD AGNES CONFIGURATION ---
CHARACTER_CONFIGS["agnes"] = { # Internal key 'agnes'
    "id": "agnes",
    "name": "Agnes",
    "greeting": "Hi there! I'm Agnes. Got any cool ideas for inventions?",
    "system_prompt": "You are Agnes, a 9-year-old inventor from Cogsworth.", # Default prompt
    "voice": {"voice_id": "shimmer", "speed": 1.0, "format": "mp3"} # Example voice
}
# ------------------------------

# --- Reverse Map: Character Name (from subtitles) to Frontend ID ---
# This helps map inconsistent character identifiers received via WebSocket
CHARACTER_NAME_TO_ID_MAP = {
    # Add entries for characters whose names might appear in subtitles
    "Agnes the Invisible": "101", # Example: Name seen in logs maps to ID 101
    "Agnes": "101",             # Also handle the simple name if it appears
    "Ankylosaurus": "102",
    "Pterodactyl": "103",
    "The Little Prince": "tlp", # Map standard names too if needed
    "Socrates": "soc"
}
# ------------------------------------------------------------------

# --- Absolute Path Calculation ---
try:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    PROMPTS_DIR = os.path.join(PROJECT_ROOT, 'src', 'prompts')
    logger.info(f"DEBUG: Absolute prompts directory calculated as: {PROMPTS_DIR}")
    if not os.path.isdir(PROMPTS_DIR):
        logger.error(f"CRITICAL: Prompts directory does not exist at calculated path: {PROMPTS_DIR}")
except Exception as e:
    logger.error(f"CRITICAL: Failed to calculate prompt directory paths: {e}")
    PROMPTS_DIR = None # Set to None if path calculation fails
# --------------------------------

def get_character_config(character_id: str = "little-prince", languageLevel: str = "b1") -> Dict[str, Any]:
    """
    Get character configuration by ID, considering language level.
    Dynamically loads the system prompt from a file based on character_id, 
    languageLevel, and an internal mapping to book IDs, overriding the default prompt.
    Fallback logic: {level}.txt -> {base}.txt -> default config.
    Keeps the function signature simple for external use (if level not needed).
    """
    logger.info(f"--- Entering get_character_config for ID: '{character_id}', Level: '{languageLevel}' ---")
    
    # Ensure languageLevel is valid or default
    valid_levels = {"a1", "a2", "b1", "b2", "c1"}
    if languageLevel not in valid_levels:
        logger.warning(f"Invalid languageLevel '{languageLevel}' received. Defaulting to 'b1'.")
        languageLevel = "b1"

    # Convert incoming character_id to string specifically for map lookup
    # as the map uses string keys ("101", "102", etc.)
    character_id_str = str(character_id)

    # 1. Determine internal key and book ID using the map
    internal_key, book_id = CHARACTER_CONTEXT_MAP.get(character_id_str, ("little-prince", None)) # Use string key
    logger.info(f"DEBUG: Mapped frontend ID '{character_id_str}' to internal key '{internal_key}' and book ID '{book_id}'")

    # 2. Get the base configuration dictionary
    if internal_key in CHARACTER_CONFIGS:
        config = CHARACTER_CONFIGS[internal_key].copy() # Use internal key
        logger.info(f"DEBUG: Found base config for internal key '{internal_key}'")
    else:
        logger.warning(f"Internal key '{internal_key}' (from ID '{character_id_str}') not found in CHARACTER_CONFIGS. Using default little-prince config.")
        config = CHARACTER_CONFIGS["little-prince"].copy()
        internal_key = "little-prince" # Adjust key to match config used

    default_prompt = config.get("system_prompt", "ERROR: Default prompt missing!")
    logger.info(f"DEBUG: Base default system prompt for '{internal_key}': '{default_prompt[:60]}...'")

    # 3. Determine the specific prompt file path (with level and fallback)
    prompt_path = None
    prompt_source = "default config"
    loaded_prompt_content = default_prompt
    
    if PROMPTS_DIR and book_id is not None:
        # Construct level-specific path first
        level_prompt_path = os.path.join(PROMPTS_DIR, "books", str(book_id), f"{character_id_str}_{languageLevel}.txt")
        logger.info(f"DEBUG: Attempting level-specific prompt: {level_prompt_path}")
        
        # Try loading level-specific prompt
        try:
            if os.path.isfile(level_prompt_path):
                with open(level_prompt_path, 'r', encoding='utf-8') as f:
                    file_prompt = f.read().strip()
                    if file_prompt:
                        loaded_prompt_content = file_prompt
                        prompt_source = f"level file ({languageLevel})"
                        prompt_path = level_prompt_path # Record the path used
                        logger.info(f"SUCCESS: Loaded prompt from level-specific file: {level_prompt_path}")
                    else:
                        logger.warning(f"PROMPT FILE EMPTY: {level_prompt_path}. Will try base file.")
            else:
                 logger.warning(f"PROMPT FILE NOT FOUND: {level_prompt_path}. Will try base file.")
        except Exception as e:
            logger.error(f"ERROR loading level prompt file {level_prompt_path}: {e}")
            logger.error(traceback.format_exc())
            logger.warning(f"Will try base prompt file due to error.")

        # Fallback 1: Try base character file if level-specific failed or was empty/not found
        if prompt_source == "default config":
            base_prompt_path = os.path.join(PROMPTS_DIR, "books", str(book_id), f"{character_id_str}.txt")
            logger.info(f"DEBUG: Attempting base prompt file: {base_prompt_path}")
            try:
                if os.path.isfile(base_prompt_path):
                    with open(base_prompt_path, 'r', encoding='utf-8') as f:
                        file_prompt = f.read().strip()
                        if file_prompt:
                            loaded_prompt_content = file_prompt
                            prompt_source = "base file"
                            prompt_path = base_prompt_path # Record the path used
                            logger.info(f"SUCCESS: Loaded prompt from base file: {base_prompt_path}")
                        else:
                            logger.warning(f"PROMPT FILE EMPTY: {base_prompt_path}. Using default config prompt.")
                else:
                    logger.warning(f"PROMPT FILE NOT FOUND: {base_prompt_path}. Using default config prompt.")
            except Exception as e:
                logger.error(f"ERROR loading base prompt file {base_prompt_path}: {e}")
                logger.error(traceback.format_exc())
                logger.warning(f"Using default config prompt due to error.")

    elif PROMPTS_DIR: # Character without a book ID (like little-prince, socrates)
         # Optional: Handle non-book specific characters if they have separate files (e.g., src/prompts/tlp.txt)
         # Could add level logic here too if needed: src/prompts/tlp_a1.txt etc.
         logger.info(f"DEBUG: No specific book ID associated with '{character_id_str}'. Will use default prompt for '{internal_key}'.")
         pass # No specific file path determined for non-book characters here
    else:
        logger.error("CRITICAL: PROMPTS_DIR is not set. Cannot load prompts from files.")

    # 4. Set the final system prompt in the config
    config["system_prompt"] = loaded_prompt_content

    # --- Load Level-Specific Hint Prompt --- 
    # Attempt to load hint prompts like in Story Mode, using book_id context
    hint_prompt_source = "inline default (sandbox fallback)"
    # Define a very basic inline fallback for sandbox if needed
    loaded_hint_prompt = f"You are an assistant helping someone practice conversation with {config.get('name', 'the character')}. Provide a short hint on how to respond." 

    if PROMPTS_DIR and book_id is not None:
        # Construct level-specific hint path
        level_hint_path = os.path.join(PROMPTS_DIR, "books", str(book_id), f"{character_id_str}_{languageLevel}_hint.txt")
        logger.info(f"DEBUG: Attempting level-specific hint prompt: {level_hint_path}")

        try:
            if os.path.isfile(level_hint_path):
                with open(level_hint_path, 'r', encoding='utf-8') as f:
                    file_prompt = f.read().strip()
                    if file_prompt:
                        loaded_hint_prompt = file_prompt
                        hint_prompt_source = f"level hint file ({languageLevel})"
                        logger.info(f"SUCCESS: Loaded hint prompt from level file: {level_hint_path}")
                    else:
                        logger.warning(f"HINT PROMPT FILE EMPTY: {level_hint_path}. Using inline default.")
        except Exception as e:
            logger.error(f"ERROR loading level hint prompt file {level_hint_path}: {e}")
            logger.warning(f"Using inline default hint prompt due to error.")

    # NOTE: No separate fallback to base hint file (`{character_id}_hint.txt`) implemented here for simplicity,
    # but could be added if needed, similar to system prompt logic.

    config["hint_prompt"] = loaded_hint_prompt

    # 5. Log final prompt source and return config
    final_prompt_preview = loaded_prompt_content[:60].replace("\n", " ") + "..."
    final_hint_preview = loaded_hint_prompt[:60].replace("\n", " ") + "..."
    logger.info(f"DEBUG: Returning config for '{internal_key}'. System prompt (from {prompt_source}): '{final_prompt_preview}'")
    logger.info(f"DEBUG: Hint prompt (from {hint_prompt_source}): '{final_hint_preview}'")
    logger.info(f"--- Exiting get_character_config for ID: '{character_id_str}', Level: '{languageLevel}' ---")
    return config 