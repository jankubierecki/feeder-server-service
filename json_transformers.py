import json


def binary_to_dict(b):
    jsn = ''.join(chr(int(x, 2)) for x in b.split())
    d = json.loads(jsn)
    return d


def dict_to_binary(d):
    s = json.dumps(d)
    binary = ' '.join(format(ord(letter), 'b') for letter in s)
    return str.encode(binary)
