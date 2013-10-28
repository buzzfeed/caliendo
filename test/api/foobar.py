from test.api.services.foo import find as find_foo
from test.api.services.bar import find as find_bar

def find(how_many):
    return zip(find_foo(how_many), find_bar(how_many))