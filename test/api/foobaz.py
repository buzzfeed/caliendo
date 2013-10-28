from test.api.services.foo import find as find_foo
from test.api.services.baz import find as find_baz

def find(how_many):
    return zip(find_foo(how_many), find_baz(how_many))