import nltk
from nltk.corpus import stopwords
import re

nltk.download('stopwords')

"""
This function accepts a text string as an argument, cleans the text and returns a string of just the vocab words joined by a space.
"""
def clean_text(text):
    stop_words = set(stopwords.words('english'))

    # normalize quotes and dashes
    text = text.replace('“', '"').replace('”', '"')
    text = text.replace('‘', "'").replace('’', "'")
    text = text.replace('–', '-').replace('—', '-')

    # remove unwanted characters
    c_text = text.translate(str.maketrans('', '', '()/*\\*><+=~^|#_%\'"'))
    c_text = c_text.translate(str.maketrans('', '', ',.!?;:"'))

    # replace some symbols with words
    c_text = c_text.replace('&', 'and').replace('%', 'percent').replace('@', 'at').replace('-'," ")

    # lowercase and collapse whitespace
    c_text = c_text.lower()
    c_text = re.sub(r'\s+', ' ', c_text).strip()

    # tokenize and remove stop words
    tok_text = c_text.split()
    clean_list = [word for word in tok_text if word not in stop_words]

    return ' '.join(clean_list)