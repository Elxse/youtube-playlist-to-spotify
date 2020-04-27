#!usr/bin/env python3

# parse_text.py -- to keep the main information/text of a song title or artist

import langdetect as ld
import re

def removeNonAlphabet(text):
    """Remove non alphabet and non digit character of the string.

    Exemple:
        내가 처음 만져본 강아지 (Love me) --> Love me
    """
    return re.sub("[^a-zA-Z0-9]+", " ", text).strip()

def removeFeatAndFollowingText(text):
    """Remove featuring information of the song title or artist.

    Exemple:
        Winter Flower (Feat. RM of BTS) --> winter flower
    """
    def indexOf(element, list_element):
        try:
            index_element = list_element.index(element)
            return index_element
        except ValueError:
            return -1

    text_list = text.lower().split()

    ind_feat = indexOf("feat", text_list)
    ind_ft = indexOf("ft", text_list)

    if ind_feat != -1:
        return " ".join(text_list[:ind_feat])
    elif ind_ft != -1:
        return " ".join(text_list[:ind_ft])
    else:
        return " ".join(text_list)
    
def mainText(text):
    """Only keeps the decisive information of a song title or artist when searching about it.
    
    Exemples:
        작은 것들을 위한 시 (Boy With Luv) (feat. Halsey) --> boy with luv
    """
    return(removeFeatAndFollowingText(removeNonAlphabet(text)))

if __name__ == "__main__":
    text = "작은 것들을 위한 시 (Boy With Luv) (ft. Halsey)" 
    text2 = "\"You Were Beautiful(예뻤어)\""
    text3 = "Winter Flower (Feat. RM of BTS)"
    print(mainText(text))
    print(mainText(text2))
    print(mainText(text3))