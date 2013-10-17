from test.api.foobar import find as find_foobar
from test.api.foobiz import find as find_foobiz

def find(how_many):
    return zip(find_foobar(how_many), find_foobiz(how_many))