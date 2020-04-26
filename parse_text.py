import langdetect as ld

def deleteKorean(text):
    new_text = ""
    text = text.replace('(', ' ').replace(')', ' ')
    for word in text.split():
        if(ld.detect(word) != "ko"):
            new_text += word + " "
    return new_text