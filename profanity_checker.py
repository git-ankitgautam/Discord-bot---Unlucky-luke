import re

def clean_and_tokenize(input_string):
    # Convert to lowercase and use regex to find all word sequences (ignores punctuation)
    words = re.findall(r'\b\w+\b', input_string.lower())
    return words


def profanity_check(search_string):
    cleaned_string = clean_and_tokenize(search_string)
    with open("profanity_wordslist.txt") as file:
        document_Text = file.read()
        for word in document_Text.splitlines():
            if word in cleaned_string:
                return True
        return False