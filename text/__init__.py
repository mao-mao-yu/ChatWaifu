""" from https://github.com/keithito/tacotron """
from text import cleaners
from text.symbols import symbols, symbols_dic


# Mappings from symbol to numeric ID and vice versa:
# _symbol_to_id = {s: i for i, s in enumerate(symbols)}
# _id_to_symbol = {i: s for i, s in enumerate(symbols)}

def text_to_sequence(text, cleaner_names):
    '''Converts a string of text to a sequence of IDs corresponding to the symbols in the text.
      Args:
        text: string to convert to a sequence
        cleaner_names: names of the cleaner functions to run the text through
      Returns:
        List of integers corresponding to the symbols in the text
    '''
    sequence = []
    symbols_ = symbols_dic.get(cleaner_names[0])
    if symbols_ is None:
        _symbol_to_id = {s: i for i, s in enumerate(symbols)}
    else:
        _symbol_to_id = {s: i for i, s in enumerate(symbols_)}

    clean_text = _clean_text(text, cleaner_names)
    for symbol in clean_text:
        if symbol not in _symbol_to_id.keys():
            continue
        symbol_id = _symbol_to_id[symbol]
        sequence += [symbol_id]
    return sequence


def cleaned_text_to_sequence(cleaned_text, cleaner_names):
    '''Converts a string of text to a sequence of IDs corresponding to the symbols in the text.
      Args:
        cleaned_text: string to convert to a sequence
        cleaner_names: cleaner_name list
      Returns:
        List of integers corresponding to the symbols in the text
    '''
    symbols_ = symbols_dic.get(cleaner_names[0])
    if symbols_ is None:
        _symbol_to_id = {s: i for i, s in enumerate(symbols)}
    else:
        _symbol_to_id = {s: i for i, s in enumerate(symbols_)}

    sequence = [_symbol_to_id[symbol] for symbol in cleaned_text if symbol in _symbol_to_id.keys()]
    return sequence


def sequence_to_text(sequence, cleaner_names):
    '''Converts a sequence of IDs back to a string'''
    result = ''
    _id_to_symbol = {i: s for i, s in enumerate(symbols_dic.get(cleaner_names[0]))}
    for symbol_id in sequence:
        s = _id_to_symbol[symbol_id]
        result += s
    return result


def _clean_text(text, cleaner_names):
    for name in cleaner_names:
        cleaner = getattr(cleaners, name)
        # print(cleaner)
        if not cleaner:
            raise Exception('Unknown cleaner: %s' % name)
        text = cleaner(text)
    return text
