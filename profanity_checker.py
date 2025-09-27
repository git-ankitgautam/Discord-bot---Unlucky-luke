import re

# Load once at start
with open("profanity_wordslist.txt") as f:
    # Use a set for fast lookup, lowercase all words
    PROFANITY_WORDS = set(word.strip().lower() for word in f if word.strip())

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
        '2': 'z',
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
    return False
