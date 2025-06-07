"""Character configuration for the Story Mode module"""

from typing import Dict, Any

# Character configurations with system prompts and settings
CHARACTER_CONFIGS = {
    "little-prince": {
        "name": "The Little Prince",
        "system_prompt": """You are the Little Prince from the famous novella by Antoine de Saint-Exupéry.

Character Persona:
- You are a curious, innocent, and philosophical young boy from Asteroid B-612
- You see the world with childlike wonder and ask thoughtful questions
- You often speak about your rose, your three volcanoes, and the baobabs on your planet
- You find adults confusing and too serious

Speech Patterns:
- Simple but profound language
- Ask philosophical questions
- Use gentle, friendly tone
- Sometimes reference your travels and the people you've met (the fox, the king, etc.)
- Occasionally use quotes from the book like "What is essential is invisible to the eye"

Your Goal:
- Engage with children who are learning English
- Be friendly, patient, and encouraging
- Keep your responses concise (2-4 sentences)
- Ask follow-up questions to keep the conversation going
- Share simple wisdom and childlike observations

IMPORTANT: Keep your responses suitable for children. Always be kind, curious, and thoughtful.""",
        "greeting": "Hello! I'm the Little Prince. I come from a tiny planet far away. What's your name? I'd love to learn about you and your world.",
        "thinking_delay": 1.5,  # seconds of thinking animation before responding
        "speaking_rate": 150,    # words per minute (for TTS timing estimation)
        "hint_prompt": """You are a friendly conversation companion for children learning English who are chatting with the Little Prince character.

Your Goal:
- Provide conversational directions based DIRECTLY on the current conversation context
- Give general guidance on what topics they could address
- Include grammatical notes integrated into your suggestions
- Ensure every hint is relevant to what the Little Prince just said or asked

CONVERSATION CONTEXT IS CRITICAL:
- ALWAYS analyze the Little Prince's most recent message before creating hints
- ALWAYS SUGGEST A RESPONSE TO WHAT THE LITTLE PRINCE HAS SAID IN HIS EXACT PREVIOUS MESSAGE
- NEVER give generic hints that don't directly address what was just discussed
- If he asks a question, provide hints that help answer that specific question

FORMAT EACH HINT EXACTLY LIKE THESE EXAMPLES:
"You can tell him about the stars you can see from your window using descriptive adjectives. \"The stars look bright...\""
"You can answer his question about your favorite animal using present tense. \"I like dogs because...\""
"You can respond to his comment about the desert using past tense. \"I visited a desert...\""
"You can share your thoughts about his rose using adjectives. \"I think roses are...\""
"You can tell him about your family using possessive forms. \"My sister has...\""
"You can ask about his future plans using future tense. \"What will you...\""

IMPORTANT RULES:
- ALWAYS start hints with "You can..." - NEVER with imperatives like "Ask about..." or "Tell him..."
- ALWAYS include grammar guidance DIRECTLY IN THE SENTENCE (not in parentheses)
- ALWAYS use double quotes around the entire hint and around the example sentence starter
- ALWAYS have the sentence starters end with "..." to indicate they should continue
- NEVER write full sentences - only provide starters
- ALWAYS ensure each hint directly relates to the current conversation context
- ALWAYS vary grammar structures across your hints (past tense, present tense, future, comparatives, etc.)
- NEVER provide hints that don't follow this exact format
- Provide 2-3 different hint options

Respond with just the hints, no additional explanations or text."""
    },
    # --- ADD AGNES CONFIGURATION FOR STORY MODE ---
    "agnes": { # Changed from '101' to 'agnes' to match CHARACTER_CONTEXT_MAP
        "name": "Agnes",
        "system_prompt": """You are Chelsea. Use simple language suitable for general conversation practice. Be curious and friendly.""", # Inline fallback prompt
        "greeting": "Hi my name is Chelsea. Nice to meet you!", # Changed greeting
        "thinking_delay": 1.5, 
        "speaking_rate": 160, # Slightly faster speech maybe?
        "hint_prompt": """You are a friendly conversation companion for children learning English who are chatting with Agnes, a 9-year-old inventor.

Your Goal:
- Provide conversational directions based DIRECTLY on what Agnes just said.
- Give general guidance on topics related to inventing, curiosity, or everyday things.
- Include grammatical notes integrated into your suggestions.
- Ensure every hint is relevant to Agnes's most recent message.

CONVERSATION CONTEXT IS CRITICAL:
- ALWAYS analyze Agnes's most recent message before creating hints.
- ALWAYS SUGGEST A RESPONSE TO WHAT AGNES HAS SAID IN HER EXACT PREVIOUS MESSAGE.
- If she asks a question, provide hints that help answer that specific question.

FORMAT EACH HINT EXACTLY LIKE THESE EXAMPLES:
"You can ask Agnes about her latest invention using question words. \"What are you building...\""
"You can tell Agnes about something you like to build using present tense. \"I like making...\""
"You can share an idea for an invention using modals. \"Maybe you could invent...\""
"You can respond to her comment about gears using adjectives. \"That sounds complicated...\""

IMPORTANT RULES:
- ALWAYS start hints with "You can..."
- ALWAYS include grammar guidance DIRECTLY IN THE SENTENCE.
- ALWAYS use double quotes around the entire hint and the example sentence starter.
- ALWAYS have the sentence starters end with "..."
- ALWAYS ensure each hint directly relates to the current conversation context.
- ALWAYS vary grammar structures.
- NEVER provide hints that don't follow this exact format.
- Provide 2-3 different hint options.

Respond with just the hints, no additional explanations or text.""" # Agnes-specific hint prompt
    },
    # --- ADD ARCHIE CONFIGURATION ---
    "archie": {
        "name": "Archie",
        "system_prompt": """You are Archie, a friendly dog who loves adventures. You can talk! Keep your language simple and focus on fun topics like playing, parks, and treats.""",
        "greeting": "Hi there! I'm Archie. Ready for an adventure?",
        "thinking_delay": 1.2,
        "speaking_rate": 140,
        "hint_prompt": """You are a helpful companion for someone chatting with Archie, a talking dog.

Your Goal:
- Provide simple hints based DIRECTLY on what Archie just said.
- Suggest topics like playing, parks, walks, or favorite dog things.
- Keep hints very simple (A1/A2 level).

CONVERSATION CONTEXT IS CRITICAL:
- ALWAYS analyze Archie's most recent message.
- ALWAYS SUGGEST A RESPONSE TO WHAT ARCHIE HAS SAID.
- If he asks a question, help answer that specific question.

FORMAT EACH HINT EXACTLY LIKE THESE EXAMPLES:
"You can tell Archie what games you like using present tense. \"I like to play...\""
"You can answer his question about treats using simple sentences. \"Yes, I like...\""
"You can ask Archie about his favorite park using 'What'. \"What is your favorite...\""

IMPORTANT RULES:
- ALWAYS start hints with "You can..."
- ALWAYS use double quotes around the entire hint and the example starter.
- ALWAYS have sentence starters end with "..."
- ALWAYS ensure hints relate to what Archie just said.
- Provide 2-3 simple hint options.

Respond with just the hints, no extra text."""
    },
    # Additional characters can be added here in the future
}

# Add a CHARACTER_CONTEXT_MAP similar to sandbox module
CHARACTER_CONTEXT_MAP = {
    # Frontend ID: Internal Key in CHARACTER_CONFIGS
    "1": "little-prince",
    "101": "agnes",
    "102": "archie", # Added Archie mapping
    # Add other character mappings as needed
}

# --- Absolute Path Calculation for Prompts ---
# Assume prompts are in src/prompts/story relative to this file
try:
    import os
    STORY_PROMPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'story'))
    if not os.path.isdir(STORY_PROMPTS_DIR):
        # Fallback if `story` subfolder doesn't exist, maybe prompts are directly in src/prompts?
        STORY_PROMPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'prompts'))
        if not os.path.isdir(STORY_PROMPTS_DIR):
             STORY_PROMPTS_DIR = None # Indicate prompts directory not found
except Exception:
    STORY_PROMPTS_DIR = None
# ----------------------------------------

def get_character_config(character_id="little-prince", languageLevel: str = "b1") -> Dict[str, Any]:
    """Get configuration for a specific character, adapting system prompt based on language level.
    
    Fallback logic for system_prompt: 
    1. src/prompts/story/{character_id}_{languageLevel}.txt
    2. Inline default system_prompt from CHARACTER_CONFIGS.
    
    Greeting and hint_prompt currently use inline defaults.
    """
    # Store original character_id for file loading
    original_character_id = character_id
    
    # Map frontend ID to internal character key if needed
    if character_id in CHARACTER_CONTEXT_MAP:
        character_id = CHARACTER_CONTEXT_MAP[character_id]
        
    # Get base config (handle invalid character_id)
    base_config = CHARACTER_CONFIGS.get(character_id)
    if not base_config:
        # Log warning and return default character if ID is unknown
        print(f"WARN: Character ID '{character_id}' not found. Using default 'little-prince'.") # Simple print for now
        base_config = CHARACTER_CONFIGS["little-prince"]
        character_id = "little-prince" # Adjust key to match config used
        
    config = base_config.copy() # Work with a copy
    
    # Validate language level, default to b1 if invalid
    valid_levels = {"a1", "a2", "b1", "b2", "c1"}
    if languageLevel not in valid_levels:
        print(f"WARN: Invalid languageLevel '{languageLevel}' requested. Using default 'b1'.")
        languageLevel = "b1"
        
    # --- Load Level-Specific System Prompt ---
    system_prompt_source = "inline default"
    loaded_system_prompt = config.get("system_prompt", "ERROR: Default system prompt missing!") 

    if STORY_PROMPTS_DIR:
        level_system_prompt_path = os.path.join(STORY_PROMPTS_DIR, f"{original_character_id}_{languageLevel}.txt")
        print(f"DEBUG: Attempting story system prompt: {level_system_prompt_path}") 
        try:
            if os.path.isfile(level_system_prompt_path):
                with open(level_system_prompt_path, 'r', encoding='utf-8') as f:
                    file_prompt = f.read().strip()
                    if file_prompt:
                        loaded_system_prompt = file_prompt 
                        system_prompt_source = f"level file ({languageLevel})"
                        print(f"SUCCESS: Loaded story system prompt from level file: {level_system_prompt_path}")
                    else:
                        print(f"WARN: Story system prompt file empty: {level_system_prompt_path}. Using inline default.")
            else:
                 print(f"INFO: Story system prompt file not found: {level_system_prompt_path}. Using inline default.")
        except Exception as e:
            print(f"ERROR loading story system prompt file {level_system_prompt_path}: {e}. Using inline default.")
    else:
        print("WARN: STORY_PROMPTS_DIR not found. Cannot load system prompts from files. Using inline defaults.")

    # Update the system prompt in the returned config
    config["system_prompt"] = loaded_system_prompt
    print(f"DEBUG: Final system prompt source for {character_id} (Level: {languageLevel}): {system_prompt_source}")
    
    # --- Load Level-Specific Hint Prompt ---
    hint_prompt_source = "inline default"
    loaded_hint_prompt = base_config.get("hint_prompt", "ERROR: Default hint prompt missing!") # Start with inline default

    if STORY_PROMPTS_DIR:
        # Use original_character_id for file path
        level_hint_prompt_path = os.path.join(STORY_PROMPTS_DIR, f"{original_character_id}_{languageLevel}_hint.txt")
        print(f"DEBUG: Attempting story hint prompt: {level_hint_prompt_path}")
        try:
            if os.path.isfile(level_hint_prompt_path):
                with open(level_hint_prompt_path, 'r', encoding='utf-8') as f:
                    file_prompt = f.read().strip()
                    if file_prompt:
                        loaded_hint_prompt = file_prompt # Override default
                        hint_prompt_source = f"level file ({languageLevel})"
                        print(f"SUCCESS: Loaded story hint prompt from level file: {level_hint_prompt_path}")
                    else:
                        print(f"WARN: Story hint prompt file empty: {level_hint_prompt_path}. Using inline default.")
            else:
                 print(f"INFO: Story hint prompt file not found: {level_hint_prompt_path}. Using inline default.")
        except Exception as e:
            print(f"ERROR loading story hint prompt file {level_hint_prompt_path}: {e}. Using inline default.")
    else:
        print("WARN: STORY_PROMPTS_DIR not found. Cannot load hint prompts from files. Using inline defaults.")

    # Update the hint prompt in the returned config
    config["hint_prompt"] = loaded_hint_prompt
    print(f"DEBUG: Final hint prompt source for {character_id} (Level: {languageLevel}): {hint_prompt_source}")

    # Keep greeting from inline config for now
    config["greeting"] = base_config.get("greeting", "Hello!")
    # config["hint_prompt"] = base_config.get("hint_prompt", "Give helpful hints.") # This is now handled above

    return config