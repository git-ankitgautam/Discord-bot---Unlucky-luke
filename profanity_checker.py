import re

def profanity_check(search_string):
    # Convert to lowercase and use regex to find all word sequences (ignores punctuation)
    cleaned_string = re.findall(r'\b\w+\b', search_string.lower())
    with open("profanity_wordslist.txt") as file:
        document_Text = file.read()
        for word in document_Text.splitlines():
            if word in cleaned_string:
                return True
        return False