from test.api.foobar import find as find_foobar
from test.api.foobaz import find as find_foobaz

def find(how_many):
    return zip(find_foobar(how_many), find_foobaz(how_many))