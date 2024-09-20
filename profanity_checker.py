def profanity_check(search_string):
    with open("profanity_wordslist.txt") as file:
        document_Text = file.read()
        for word in document_Text.splitlines():
            if word in search_string:
                return True
        return False
        