
from itertools import chain
import re


def modular_range(modulus, start, end):
    start = start % modulus
    end = end % modulus
    if start <= end:
        return range(start, end)
    return chain(range(start, modulus), range(end))


def is_hexcode(code):
    if not isinstance(code, str):
        logging.info('hexcode input is not a string')
        return False
    match = re.fullmatch(r'#?[0-9a-fA-F]{6}', code)
    if match:
        return True
    logging.info('hexcode string is invalid')
    return False 
