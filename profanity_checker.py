import re

# Load once at start
with open("profanity_wordslist.txt") as f:
    RAW_PROFANITY_WORDS = [word.strip().lower() for word in f if word.strip()]

# Split exact words and wildcard patterns for faster checks
PROFANITY_WORDS = {word for word in RAW_PROFANITY_WORDS if "*" not in word}
PROFANITY_PATTERNS = [
    re.compile(re.escape(word).replace(r"\*", ".*"))
    for word in RAW_PROFANITY_WORDS
    if "*" in word
]

# Leetspeak mapping function
def normalize_leetspeak(text):
    substitutions = {
        '4': 'a',
        '@': 'a',
        '8': 'b',
        '3': 'e',
        '1': 'i',
        '!': 'i',
        '0': 'o',
        '$': 's',
        '5': 's',
        '7': 't',
        '+': 't',
        '2': 'z'
    }
    return ''.join(substitutions.get(c, c) or '' for c in text)

def profanity_check(search_string):
    # Normalize input string (lowercase + leetspeak)
    normalized = normalize_leetspeak(search_string.lower())
    # Tokenize words using word boundaries
    words = re.findall(r'\b\w+\b', normalized)
    # Check if any normalized word is in profanity set
    for word in words:
        if word in PROFANITY_WORDS:
            return True
    # Check wildcard patterns against words and full normalized text
    for pattern in PROFANITY_PATTERNS:
        if pattern.search(normalized):
            return True
    return False
