import re

import langid

from text.japanese import japanese_to_romaji_with_accent, japanese_to_ipa, japanese_to_ipa2, japanese_to_ipa3
from text.mandarin import number_to_chinese, chinese_to_bopomofo, latin_to_bopomofo, chinese_to_romaji, \
    chinese_to_lazy_ipa
from text.english import english_to_ipa2


def japanese_cleaners(text):
    text = japanese_to_romaji_with_accent(text)
    text = re.sub(r'([A-Za-z])$', r'\1.', text)
    return text


def japanese_cleaners2(text):
    symbol_li = ['（', '）', '《', '》', '「', '」', '：', '#']
    for i in symbol_li:
        text = re.sub(i, ' ', text)
    return japanese_cleaners(text).replace('ts', 'ʦ').replace('...', '…')


def chinese_cleaners(text):
    '''Pipeline for Chinese text'''
    text = number_to_chinese(text)
    text = chinese_to_bopomofo(text)
    symbol_li = ['（', '）', '《', '》', '「', '」', '：', '#']
    for i in symbol_li:
        text = re.sub(i, ' ', text)
    text = latin_to_bopomofo(text)
    text = re.sub(r'([ˉˊˇˋ˙])$', r'\1。', text)
    return text


def zh_ja_mixture_cleaners(text):
    symbol_li = ['（', '）', '《', '》', '「', '」', '：', '#']
    for i in symbol_li:
        text = re.sub(i, ' ', text)
    text = re.sub(r'\[ZH\](.*?)\[ZH\]',
                  lambda x: chinese_to_romaji(x.group(1)) + ' ', text)
    text = re.sub(r'\[JA\](.*?)\[JA\]', lambda x: japanese_to_romaji_with_accent(
        x.group(1)).replace('ts', 'ʦ').replace('u', 'ɯ').replace('...', '…') + ' ', text)
    text = re.sub(r'\s+$', '', text)
    text = re.sub(r'([^\.,!\?\-…~])$', r'\1.', text)
    return text


def cje_cleaners(text):
    text = re.sub(r'\[ZH\](.*?)\[ZH\]', lambda x: chinese_to_lazy_ipa(x.group(1)).replace(
        'ʧ', 'tʃ').replace('ʦ', 'ts').replace('ɥan', 'ɥæn') + ' ', text)
    text = re.sub(r'\[JA\](.*?)\[JA\]', lambda x: japanese_to_ipa(x.group(1)).replace('ʧ', 'tʃ').replace(
        'ʦ', 'ts').replace('ɥan', 'ɥæn').replace('ʥ', 'dz') + ' ', text)
    text = re.sub(r'\[EN\](.*?)\[EN\]', lambda x: english_to_ipa2(x.group(1)).replace('ɑ', 'a').replace(
        'ɔ', 'o').replace('ɛ', 'e').replace('ɪ', 'i').replace('ʊ', 'u') + ' ', text)
    text = re.sub(r'\s+$', '', text)
    text = re.sub(r'([^\.,!\?\-…~])$', r'\1.', text)
    return text


if __name__ == '__main__':
    c_text = "大家好，我是大学生"
    j_text = "こんにちは、私は大学生です"
    e_text = "Hello,I am a university student"
    def add_lang(text):
        lang = langid.classify(text)[0].upper()
        return f"[{lang}]{text}[{lang}]"
    cleaned_text = cje_cleaners(add_lang(c_text))
    print(cleaned_text)
    cleaned_text = cje_cleaners(add_lang(j_text))
    print(cleaned_text)
    cleaned_text = cje_cleaners(add_lang(e_text))
    print(cleaned_text)
