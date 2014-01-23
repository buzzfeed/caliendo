import tempfile
import time
import weakref
import unittest
import subprocess
import hashlib
import pickle
import sys
import os

os.environ['USE_CALIENDO'] = 'True'

from subprocess import PIPE
from caliendo.db.flatfiles import STACK_DIRECTORY, save_stack, load_stack, delete_stack
from caliendo.call_descriptor import CallDescriptor, fetch
from caliendo.facade import patch, Facade, Wrapper, get_hash, cache
from caliendo.hooks import CallStack, Hook
from caliendo import Ignore
from caliendo.util import recache, serialize_args, serialize_item

import caliendo

from nested.bazbiz import baz
from foobar import bazbiz
from api import foobarfoobiz, foobarfoobaz, foobar, foobiz
from test.api.services.bar import find as find_bar
from test.api.myclass import MyClass

recache()

myfile = tempfile.NamedTemporaryFile(delete=False)
myfile.write("0")
myfile.close()
def callback(cd):
    with open(myfile.name, 'rb') as toread:
        contents = toread.read()
    if contents:
        val = int(contents) + 1
    else:
        val = 0
    with open(myfile.name, 'w+') as towrite:
        towrite.write(str(val))

def callback2(cd):
    assert cd.hash == 'fake-hash2'

def callback3(cd):
    assert cd.hash == 'fake-hash3'

def gkeyword(x=1, y=1, z=1):
    CallOnceEver().update()
    return x + y + z

class TestModel:
    def __init__(self, a, b):
        setattr( self, 'a', a )
        setattr( self, 'b', b )

class CallOnceEver:
    __die = 0
    def update(self):
        if self.__die:
            raise Exception("NOPE!")
        else:
            self.__die = 1
            return 1

class CallsServiceInInit:
    __die = 0
    def __init__(self):
        if self.__die:
            raise Exception("NOPE!")
        else:
            self.__die = 1

    def methoda(self):
        return 'a'

    def nested_init(self):
        return CallsServiceInInit()


class TestA:
    def getb(self):
        return TestB()

class TestB:
    def getc(self):
        return TestC()

class TestC:
    __private_var   = 0
    lambda_function = lambda s, x: x * 2
    test_a_class    = TestA
    some_model      = TestModel( a=1, b=2 )
    primitive_a     = 'a'
    primitive_b     = 1
    primitive_c     = [ 1 ]
    primitive_d     = { 'a': 1 }

    def methoda(self):
        return "a"
    def methodb(self):
        return "b"
    def update(self):
        return "c"
    def increment(self):
        self.__private_var = self.__private_var + 1
        return self.__private_var

class LazyBones(dict):
    def __init__(self):
        self.store = {}

    def __getattr__(self, attr):
        if attr == 'c':
            return lambda : TestC()
        else:
            self.store[attr] = None
            return self.store[attr]

def bar_find_called(cd):
    assert cd.methodname == 'find'
    assert cd.args[0] == 10
    assert cd.returnval.count('bar') == 10

def biz_find_called(cd):
    assert cd.methodname == 'find'
    assert cd.args[0] == 10
    assert cd.returnval.count('biz') == 10
    raise Exception('biz find done')

def foo_find_called(cd):
    assert cd.methodname == 'find'
    assert cd.args[0] == 10
    assert cd.returnval.count('foo') == 10

class  CaliendoTestCase(unittest.TestCase):
    def setUp(self):
        caliendo.util.register_suite()
        stackfiles = os.listdir(STACK_DIRECTORY)
        for f in stackfiles:
            filepath = os.path.join(STACK_DIRECTORY, f)
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_callback_in_patch(self):

        def run_test():
            @patch('test.api.services.bar.find', callback=bar_find_called)
            @patch('test.api.services.biz.find', callback=biz_find_called)
            @patch('test.api.services.foo.find', callback=foo_find_called)
            def test():
                foobarfoobiz.find(10)

            try:
                test()
            finally:
                os._exit(0)

        for i in range(2):
            pid = os.fork()
            if pid:
                os.waitpid(pid, 0)
            else:
                try:
                    run_test()
                except Exception, e:
                    self.assertEquals(str(e), 'biz find done')

    def test_call_descriptor(self):
        hash      = hashlib.sha1( "adsf" ).hexdigest()
        method    = "mymethod"
        returnval = {'thisis': [ 'my', 'return','val' ] }
        args      = ( 'a', 'b', 'c' )
        #self, hash='', stack='', method='', returnval='', args='', kwargs='' ):
        cd = CallDescriptor(
            hash=hash,
            stack='',
            method=method,
            returnval=returnval,
            args=args )

        cd.save()

        self.assertEqual( cd.hash, hash )
        self.assertEqual( cd.methodname, method )
        self.assertEqual( cd.returnval, returnval )
        self.assertEqual( cd.args, args )

        cd = fetch( hash )

        self.assertEqual( cd.hash, hash )
        self.assertEqual( cd.methodname, method )
        self.assertEqual( cd.returnval, returnval )
        self.assertEqual( cd.args, args )

    def test_serialize_basics(self):
        basic_list = [ 'a', 'b', 'c' ]
        basic_dict = { 'a': 1, 'b': 2, 'c': 3 }
        nested_list = [ [ 0, 1, 2 ], [ 3, 4, 5 ] ]
        nested_dict = { 'a': { 'a': 1, 'b': 2 }, 'b': { 'c': 3, 'd': 4 } }
        list_of_nested_dicts = [ { 'a': { 'a': 1, 'b': 2 }, 'b': { 'c': 3, 'd': 4 } } ]

        s_basic_list = serialize_item(basic_list)
        s_basic_args_list = serialize_args(basic_list)
        s_basic_dict = serialize_item(basic_dict)
        s_nested_list = serialize_item(nested_list)
        s_nested_args_list = serialize_args(nested_list)
        s_nested_dict = serialize_item(nested_dict)
        s_list_of_nested_dicts = serialize_item(list_of_nested_dicts)
        s_args_list_of_nested_dicts = serialize_args(list_of_nested_dicts)

        assert s_basic_list == str(['a', 'b', 'c'])
        assert s_basic_args_list == str(['a', 'b', 'c'])
        assert s_basic_dict == str(["['1', 'a']", "['2', 'b']", "['3', 'c']"])
        assert s_nested_list == str(["['0', '1', '2']", "['3', '4', '5']"])
        assert s_nested_args_list == str(["['0', '1', '2']", "['3', '4', '5']"])
        assert s_nested_dict == str(['[\'["[\\\'1\\\', \\\'a\\\']", "[\\\'2\\\', \\\'b\\\']"]\', \'a\']', '[\'["[\\\'3\\\', \\\'c\\\']", "[\\\'4\\\', \\\'d\\\']"]\', \'b\']'])
        assert s_list_of_nested_dicts == str(['[\'[\\\'["[\\\\\\\'1\\\\\\\', \\\\\\\'a\\\\\\\']", "[\\\\\\\'2\\\\\\\', \\\\\\\'b\\\\\\\']"]\\\', \\\'a\\\']\', \'[\\\'["[\\\\\\\'3\\\\\\\', \\\\\\\'c\\\\\\\']", "[\\\\\\\'4\\\\\\\', \\\\\\\'d\\\\\\\']"]\\\', \\\'b\\\']\']'])
        assert s_args_list_of_nested_dicts == str(['[\'[\\\'["[\\\\\\\'1\\\\\\\', \\\\\\\'a\\\\\\\']", "[\\\\\\\'2\\\\\\\', \\\\\\\'b\\\\\\\']"]\\\', \\\'a\\\']\', \'[\\\'["[\\\\\\\'3\\\\\\\', \\\\\\\'c\\\\\\\']", "[\\\\\\\'4\\\\\\\', \\\\\\\'d\\\\\\\']"]\\\', \\\'b\\\']\']'])

    def test_serialize_iterables(self):
        target_set = set([5, 3, 4, 2, 7, 6, 1, 8, 9, 0])
        def gen():
            for i in range(10):
                yield i
        target_generator = gen()
        target_frozenset = frozenset([5, 3, 4, 2, 7, 6, 1, 8, 9, 0])

        s_set = serialize_args(target_set)
        s_gen = serialize_args(target_generator)
        s_frozenset = serialize_args(target_frozenset)

        assert s_set == s_gen
        assert s_gen == s_frozenset
        assert s_frozenset == str(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'])


    def test_serialize_nested_lists(self):
        a = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        b = [[7, 8, 9], [4, 5, 6], [1, 2, 3]]
        c = [[6, 4, 5], [1, 3, 2], [9, 8, 7]]

        s_a__item = serialize_item(a)
        s_b__item = serialize_item(b)
        s_c__item = serialize_item(c)

        assert s_a__item == s_b__item
        assert s_b__item == s_c__item
        assert s_c__item == str(["['1', '2', '3']", "['4', '5', '6']", "['7', '8', '9']"])

        s_a__args = serialize_args(a)
        s_b__args = serialize_args(b)
        s_c__args = serialize_args(c)

        assert s_a__args != s_b__args
        assert s_a__args != s_c__args
        assert s_b__args != s_c__args
        assert s_a__args == str(["['1', '2', '3']", "['4', '5', '6']", "['7', '8', '9']"])
        assert s_b__args == str(["['7', '8', '9']", "['4', '5', '6']", "['1', '2', '3']"])
        assert s_c__args == str(["['4', '5', '6']", "['1', '2', '3']", "['7', '8', '9']"])



    def test_serialize_nested_lists_of_nested_lists(self):
        a = [[[1, 2, 3], [4, 5, 6]], [7, 8, 9]]
        b = [[7, 8, 9], [[4, 5, 6], [1, 2, 3]]]
        c = [[[6, 4, 5], [1, 3, 2]], [9, 8, 7]]

        s_a__item = serialize_item(a)
        s_b__item = serialize_item(b)
        s_c__item = serialize_item(c)

        assert s_a__item == s_b__item
        assert s_b__item == s_c__item
        assert s_c__item == str(['["[\'1\', \'2\', \'3\']", "[\'4\', \'5\', \'6\']"]', "['7', '8', '9']"])

        s_a__args = serialize_args(a)
        s_b__args = serialize_args(b)
        s_c__args = serialize_args(c)

        assert s_a__args != s_b__args
        assert s_a__args == s_c__args
        assert s_b__args != s_c__args
        assert s_a__args == str(['["[\'1\', \'2\', \'3\']", "[\'4\', \'5\', \'6\']"]', "['7', '8', '9']"])
        assert s_b__args == str(["['7', '8', '9']", '["[\'1\', \'2\', \'3\']", "[\'4\', \'5\', \'6\']"]'])
        assert s_c__args == str(['["[\'1\', \'2\', \'3\']", "[\'4\', \'5\', \'6\']"]', "['7', '8', '9']"])

    def test_serialize_dicts(self):
        a = {'a': 1, 'b': 2, 'c': 3}
        b = {'c': 3, 'a': 1, 'b': 2}
        c = {'c': 3, 'b': 2, 'a': 1}
        d = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8}
        e = {'b': 2, 'a': 1, 'h': 8, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'c': 3}
        f = {'e': 5, 'a': 1, 'h': 8, 'd': 4, 'b': 2, 'f': 6, 'g': 7, 'c': 3}

        s_a = serialize_item(a)
        s_b = serialize_item(b)
        s_c = serialize_item(c)
        s_d = serialize_item(d)
        s_e = serialize_item(e)
        s_f = serialize_item(f)

        assert s_a == s_b
        assert s_b == s_c
        assert s_c == str(["['1', 'a']", "['2', 'b']", "['3', 'c']"])

        assert s_d == s_e
        assert s_e == s_f
        assert s_f == str(["['1', 'a']", "['2', 'b']", "['3', 'c']", "['4', 'd']", "['5', 'e']", "['6', 'f']", "['7', 'g']", "['8', 'h']"])

    def test_serialize_models(self):
        a = TestModel('a', 'b')
        b = [TestModel('a', 'b'), TestModel('b', 'c'), TestModel('c', 'd')]
        c = {'c': TestModel('a', 'b'), 'b': TestModel('b', 'c'), 'a': TestModel('c', 'd')}
        d = set([TestModel('a', 'b'), TestModel('b', 'c'), TestModel('c', 'd')])

        s_a = serialize_item(a)
        s_b = serialize_args(b)
        s_c = serialize_item(c)
        s_d = serialize_args(d)

        assert s_a == 'TestModel'
        assert s_b == str(['TestModel', 'TestModel', 'TestModel'])
        assert s_c == str(["['TestModel', 'a']", "['TestModel', 'b']", "['TestModel', 'c']"])
        assert s_d == str(['TestModel', 'TestModel', 'TestModel'])

    def test_serialize_methods(self):
        a = lambda *args, **kwargs: 'foo'
        def b():
            return 'bar'
        class C:
            def c(self):
                return 'biz'

        assert serialize_item(a) == '<lambda>'
        assert serialize_item(b) == 'b'
        assert serialize_item(C().c) == 'c'
        assert serialize_args([a]) == str(['<lambda>'])
        assert serialize_args([b]) == str(['b'])
        assert serialize_args([C().c, 1, '2', [3], {'four': 4}]) == str(['c', '1', '2', "['3']", '["[\'4\', \'four\']"]'])

    def test_fetch_call_descriptor(self):
        hash      = hashlib.sha1( "test1" ).hexdigest()
        method    = "test1"
        returnval = { }
        args      = ( )

        cd = CallDescriptor( hash=hash, stack='', method=method, returnval=returnval, args=args )
        cd.save( )

        cd = fetch( hash )
        self.assertEquals( cd.hash, hash )
        self.assertEquals( cd.methodname, method )

        hash      = hashlib.sha1( "test1" ).hexdigest()
        method    = "test2"
        cd.methodname = method
        cd.save( )

        cd = fetch( hash )
        self.assertEquals( cd.hash, hash )
        self.assertEquals( cd.methodname, method )

        hash      = hashlib.sha1( "test3" ).hexdigest()
        method    = "test3"
        cd.hash   = hash
        cd.methodname = method
        cd.save( )

        cd = fetch( hash )
        self.assertEquals( cd.hash, hash )
        self.assertEquals( cd.methodname, method )

    def test_facade(self):
        mtc = TestC( )
        mtc_f = Facade( mtc )

        self.assertEquals( mtc.methoda( ), mtc_f.methoda( ) )
        self.assertEquals( mtc.methodb( ), mtc_f.methodb( ) )
        self.assertEquals( mtc_f.methoda( ), "a" )

        self.assertEquals( mtc_f.increment( ), 1 )
        self.assertEquals( mtc_f.increment( ), 2 )
        self.assertEquals( mtc_f.increment( ), 3 )
        self.assertEquals( mtc_f.increment( ), 4 )

    def test_update(self):
        o = CallOnceEver()
        test = self

        def test(fh):
            Facade( o )
            result = o.update()
            fh.write(str(result == 1))
            fh.close()
            os._exit(0)

        outputs = [ tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False) ]

        for output in outputs:
            pid = os.fork()
            if pid:
                os.waitpid(pid, 0)
            else:
                test(output)

        expected = ['True', 'True', 'True']
        result   = []

        for output in outputs:
            output.close()

            fh = open(output.name)
            result.append(fh.read())
            fh.close()

            os.remove(output.name)

        self.assertEqual(result, expected)

    def test_recache(self):
        mtc = TestC( )
        mtc_f = Facade( mtc )

        hashes = []

        self.assertEquals( mtc.methoda( ), mtc_f.methoda( ) )
        self.assertIsNotNone(mtc_f.last_cached)
        hashes.append( mtc_f.last_cached )
        self.assertEquals( mtc.methodb( ), mtc_f.methodb( ) )
        self.assertIsNotNone(mtc_f.last_cached)
        hashes.append( mtc_f.last_cached )
        self.assertEquals( mtc_f.methoda( ), "a" )
        self.assertIsNotNone(mtc_f.last_cached)
        hashes.append( mtc_f.last_cached )

        self.assertEquals( mtc_f.increment( ), 1 )
        self.assertIsNotNone(mtc_f.last_cached)
        hashes.append( mtc_f.last_cached )
        self.assertEquals( mtc_f.increment( ), 2 )
        self.assertIsNotNone(mtc_f.last_cached)
        hashes.append( mtc_f.last_cached )
        self.assertEquals( mtc_f.increment( ), 3 )
        self.assertIsNotNone(mtc_f.last_cached)
        hashes.append( mtc_f.last_cached )
        self.assertEquals( mtc_f.increment( ), 4 )
        self.assertIsNotNone(mtc_f.last_cached)
        hashes.append( mtc_f.last_cached )

        # Ensure hashes are now in db:
        for hash in hashes:
            self.assertIsNotNone(hash, "Hash is none. whoops.")
            cd = fetch( hash )
            self.assertTrue( cd is not None, "%s was not found" % hash )
            self.assertEquals( cd.hash, hash, "%s was not found" % hash )

        # Delete some:
        caliendo.util.recache( 'methodb', 'caliendo_test.py' )
        caliendo.util.recache( 'methoda', 'caliendo_test.py' )

        # Ensure they're gone:
        methodb = hashes[0]
        methoda = hashes[1]
        cd = fetch( methodb )

        self.assertIsNone( cd, "Method b failed to recache." )
        cd = fetch( methoda )

        self.assertIsNone( cd, "Method a failed to recache." )

        # Ensure the rest are there:
        hashes = hashes[3:]
        for hash in hashes:
            cd = fetch( hash )
            self.assertEquals( cd.hash, hash )

        # Delete them ALL:
        caliendo.util.recache()

        #Ensure they're all gone:
        for hash in hashes:
            cd = fetch( hash )
            self.assertIsNone( cd )

    def test_chaining(self):
        a = TestA()
        b = a.getb()
        c = b.getc()

        self.assertEquals( a.__class__, TestA )
        self.assertEquals( b.__class__, TestB )
        self.assertEquals( c.__class__, TestC )

        a_f = Facade(TestA())
        b_f = a_f.getb()
        c_f = b_f.getc()

        self.assertEquals( a_f.__class__, Facade(a).__class__ )
        self.assertEquals( b_f.__class__, Facade(a).__class__ )
        self.assertEquals( c_f.__class__, Facade(a).__class__ )

        self.assertEquals( 'a', c_f.methoda() )

    def test_various_attribute_types(self):
        c = Facade(TestC())

        # 'Primitives'
        self.assertEquals( c.primitive_a, 'a' )
        self.assertEquals( c.primitive_b, 1 )
        self.assertEquals( c.primitive_c, [ 1 ] )
        self.assertEquals( c.primitive_d, { 'a': 1 } )

        # Instance methods
        self.assertEquals( c.methoda(), 'a' )
        self.assertEquals( c.methodb(), 'b' )

        # Lambda functions
        self.assertEquals( c.lambda_function( 2 ), 4 )

        # Models
        self.assertEquals( c.some_model.a, 1 )
        self.assertEquals( c.some_model.b, 2 )

        # Classes
        self.assertEquals( c.test_a_class( ).wrapper__unwrap( ).__class__, TestA )

    def test_various_attribute_types_after_chaining(self):
        c = Facade(TestA()).getb().getc()

        # 'Primitives'
        self.assertEquals( c.primitive_a, 'a' )
        self.assertEquals( c.primitive_b, 1 )
        self.assertEquals( c.primitive_c, [ 1 ] )
        self.assertEquals( c.primitive_d, { 'a': 1 } )

        # Instance methods
        self.assertEquals( c.methoda(), 'a' )
        self.assertEquals( c.methodb(), 'b' )

        # Lambda functions
        self.assertEquals( c.lambda_function( 2 ), 4 )

        # Models
        self.assertEquals( c.some_model.a, 1 )
        self.assertEquals( c.some_model.b, 2 )

        # Classes
        self.assertEquals( c.test_a_class( ).wrapper__unwrap( ).__class__, TestA )

    def test_model_interface(self):
        a = Facade(TestA())

        a.attribute_a = "a"
        a.attribute_b = "b"
        a.attribute_c = "c"

        self.assertEquals( a.attribute_a, "a")
        self.assertEquals( a.attribute_b, "b")
        self.assertEquals( a.attribute_c, "c")

    def test_exclusion_list(self):
        # Ignore an instance:
        a = Facade(TestA())

        b = a.getb()
        self.assertEquals( b.__class__, Wrapper )

        a.wrapper__ignore( TestB )
        b = a.getb()
        self.assertEquals( b.__class__, TestB )

        a.wrapper__unignore( TestB )
        b = a.getb()
        self.assertEquals( b.__class__, Wrapper )

        # Ignore a class:
        c = Facade(TestC())

        self.assertTrue( c.test_a_class().__class__, Wrapper )

        c.wrapper__ignore( TestA )
        a = c.test_a_class()
        self.assertTrue( isinstance( a, TestA ) )

    def test_lazy_load(self):
        # Write class where a method is defined using __getattr__
        lazy = Facade(LazyBones())
        c = lazy.c()
        self.assertEquals( c.__class__, Wrapper )
        self.assertEquals( c.wrapper__unwrap().__class__, TestC )
        self.assertEquals( c.methoda(), 'a' )

    def test_service_call_in__init__(self):
        test = self

        def test(fh):
            o = Facade( cls=CallsServiceInInit )
            result = o.methoda()
            fh.write(str(result == 'a'))
            fh.close()
            os._exit(0)

        outputs = [ tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False) ]

        for output in outputs:
            pid = os.fork()
            if pid:
                os.waitpid(pid, 0)
            else:
                test(output)

        expected = ['True', 'True', 'True']
        result   = []

        for output in outputs:
            output.close()

            fh = open(output.name)
            result.append(fh.read())
            fh.close()

            os.remove(output.name)

        self.assertEqual(result, expected)

    def test_service_call_in_nested__init__(self):
        test = self

        def test(fh):
            o = Facade( cls=CallsServiceInInit )
            result = o.nested_init().methoda()
            fh.write(str(result == 'a'))
            fh.close()
            os._exit(0)

        outputs = [ tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False) ]

        for output in outputs:
            pid = os.fork()
            if pid:
                os.waitpid(pid, 0)
            else:
                test(output)

        expected = ['True', 'True', 'True']
        result   = []

        for output in outputs:
            output.close()

            fh = open(output.name)
            result.append(fh.read())
            fh.close()

            os.remove(output.name)

        self.assertEqual(result, expected)

    def test_mock_weak_ref(self):
        import pickle
        import weakref

        class A:
            def methoda(self):
                return 'a'

        a = A()
        b = A()
        c = A()

        a.b = b
        a.ref_b = weakref.ref(b)
        a.ref_c = weakref.ref(c)

        test = self

        def test(fh):
            o = Facade( a )
            result = o.methoda()
            fh.write(str(result == 'a'))
            fh.close()
            os._exit(0)

        outputs = [ tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False) ]

        for output in outputs:
            pid = os.fork()
            if pid:
                os.waitpid(pid, 0)
            else:
                test(output)

        expected = ['True', 'True', 'True']
        result   = []

        for output in outputs:
            output.close()

            fh = open(output.name)
            result.append(fh.read())
            fh.close()

            os.remove(output.name)

        self.assertEqual(result, expected)

    def test_truncation(self):
        from caliendo import pickling
        pickling.MAX_DEPTH = 2
        cls = TestA()
        a = {
          'a': {
            'b': {
              'c': [{
                'd': {
                  'e': {
                    'f': {
                      'a': weakref.ref(cls),
                      'b': 2,
                      'c': 3
                    }
                  }
                }
              },{
                'd': {
                  'e': {
                    'f': {
                      'a': 1,
                      'b': 2,
                      'c': 3
                    }
                  }
                }
              }]
            }
          },
          'b': {
            'a': 1,
            'b': 2
          }
        }
        b = pickle.loads(pickling.pickle_with_weak_refs(a))
        self.assertEquals( b, {'a': {'b': {'c': [{}, {}]}}, 'b': {'a': 1, 'b': 2}} )

    def test_cache_positional(self):

        def positional(x, y, z):
            CallOnceEver().update()
            return x + y + z

        def test(fh):
            result = cache( positional, args=(1,2,3) )
            fh.write(str(result == 6))
            fh.close()
            os._exit(0)

        outputs = [ tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False) ]

        for output in outputs:
            pid = os.fork()
            if pid:
                os.waitpid(pid, 0)
            else:
                test(output)

        expected = ['True', 'True', 'True']
        result   = []

        for output in outputs:
            output.close()

            fh = open(output.name)
            result.append(fh.read())
            fh.close()

            os.remove(output.name)

        self.assertEqual(result, expected)

    def test_cache_keyword(self):
        def keyword(x=1, y=1, z=1):
            CallOnceEver().update()
            return x + y + z

        def test(fh):
            result = cache( keyword, kwargs={ 'x': 1, 'y': 2, 'z': 3 } )
            fh.write(str(result == 6))
            fh.close()
            os._exit(0)

        outputs = [ tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False) ]

        for output in outputs:
            pid = os.fork()
            if pid:
                os.waitpid(pid, 0)
            else:
                test(output)

        expected = ['True', 'True', 'True']
        result   = []

        for output in outputs:
            output.close()

            fh = open(output.name)
            result.append(fh.read())
            fh.close()

            os.remove(output.name)

        self.assertEqual(result, expected)

    def test_cache_mixed(self):
        def mixed(x, y, z=1):
            CallOnceEver().update()
            return x + y + z

        def test(fh):
            result = cache( mixed, args=(1,2), kwargs={'z': 3 } )
            fh.write(str(result == 6))
            fh.close()
            os._exit(0)

        outputs = [ tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False) ]

        for output in outputs:
            pid = os.fork()
            if pid:
                os.waitpid(pid, 0)
            else:
                test(output)

        expected = ['True', 'True', 'True']
        result   = []

        for output in outputs:
            output.close()

            fh = open(output.name)
            result.append(fh.read())
            fh.close()

            os.remove(output.name)

        self.assertEqual(result, expected)


    @patch('test.nested.bazbiz.baz', 'biz')
    def test_patch_sanity(self):
        b = baz()
        assert b == 'biz', "Value is %s" % b

    @patch('test.nested.bazbiz.baz', 'boz')
    def test_patch_context_a(self):
        b = baz()
        assert b == 'boz', "Expected boz got %s" % b


    @patch('test.nested.bazbiz.baz', 'bar')
    def test_patch_context_b(self):
        b = baz()
        assert b == 'bar', "Expected bar got %s" % b

    @patch('test.nested.bazbiz.baz', 'biz')
    def test_patch_depth(self):
        b = bazbiz()
        assert b == 'bizbiz', "Expected bizbiz, got %s" % bazbiz()

    @patch('test.nested.bazbiz.baz')
    def test_patched_cache(self):
        def mixed(x, y, z=1):
            CallOnceEver().update()
            return x + y + z

        def test(fh):
            result = baz()
            fh.write(str(result == 'baz'))
            fh.close()
            os._exit(0)

        outputs = [ tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False) ]

        for output in outputs:
            pid = os.fork()
            if pid:
                os.waitpid(pid, 0)
            else:
                test(output)

        expected = ['True', 'True', 'True']
        result   = []

        for output in outputs:
            output.close()

            fh = open(output.name)
            result.append(fh.read())
            fh.close()

            os.remove(output.name)

        self.assertEqual(result, expected)


    @patch('test.api.services.bar.find')
    @patch('test.api.services.baz.find')
    @patch('test.api.services.biz.find')
    @patch('test.api.services.foo.find')
    def test_multiple_overlapping_services_a(self):
        foobarfoobiz.find(10)

    @patch('test.api.services.bar.find')
    @patch('test.api.services.baz.find')
    @patch('test.api.services.biz.find')
    @patch('test.api.services.foo.find')
    def test_multiple_overlapping_services_b(self):
        foobarfoobaz.find(10)
        foobarfoobiz.find(10)
        foobar.find(10)
        foobarfoobaz.find(10)

    @patch('test.api.services.bar.find')
    @patch('test.api.services.baz.find')
    @patch('test.api.services.biz.find')
    @patch('test.api.services.foo.find')
    def test_multiple_overlapping_services_c(self):
        foobiz.find(10)
        foobar.find(10)

    @patch('test.api.services.bar.find', side_effect=Exception("Blam"))
    def test_side_effect_raises_exceptions(self):
        try:
            foobiz.find(10)
            foobar.find(10)
        except:
            assert sys.exc_info()[1].message == 'Blam'

    @patch('test.api.services.bar.find', rvalue='la', side_effect=Exception('Boom'))
    def test_side_effect_raises_exceptions_with_rvalue(self):
        try:
            find_bar(10)
        except:
            assert sys.exc_info()[1].message == 'Boom'

    @patch('test.api.services.bar.find', rvalue='la', side_effect=lambda a: a)
    def test_side_effect_overrides_rvalue(self):
        rvalue = find_bar(10)
        assert rvalue == 10, "Expected la, got %s" % rvalue

    @patch('test.api.myclass.MyClass.foo', rvalue='bar')
    def test_patching_instance_methods_with_rvalue(self):
        mc = MyClass()
        bar = mc.foo()
        assert bar == 'bar', "Got '%s' expected 'bar'" % bar

    def test_unpatching_instance_method_with_side_effect_as_exception(self):
        @patch('test.api.myclass.MyClass.foo', side_effect=Exception('Boom!'))
        def test_exception_side_effect():
            try:
                MyClass().foo()
            except Exception as e:
                assert e.message == 'Boom!'

        @patch('test.api.myclass.MyClass.foo')
        def test_unpatched():
            foo = MyClass().foo()
            assert foo == 'foo', foo  # should not execute side effect

        test_exception_side_effect()
        test_unpatched()

    def test_unpatching_instance_method_with_side_effect_as_callable(self):
        @patch('test.api.myclass.MyClass.foo', side_effect=lambda s: 'side effect')
        def test_callback_side_effect():
            foo = MyClass().foo()
            assert foo == 'side effect', foo

        @patch('test.api.myclass.MyClass.foo')
        def test_unpatched():
            foo = MyClass().foo()
            assert foo == 'foo', foo  # should not execute side effect

        test_callback_side_effect()
        test_unpatched()

    def test_unpatching_instance_method_with_return_value(self):
        @patch('test.api.myclass.MyClass.foo', rvalue='bar')
        def test_return_value_effect():
            foo = MyClass().foo()
            assert foo == 'bar', foo

        @patch('test.api.myclass.MyClass.foo')
        def test_unpatched():
            foo = MyClass().foo()
            assert foo == 'foo', foo  # should not execute side effect

        test_return_value_effect()
        test_unpatched()

    def test_patching_instance_methods_with_cache_and_binary_garbage(self):
        def mixed(x, y, z=1):
            CallOnceEver().update()
            return x + y + z

        checker = tempfile.NamedTemporaryFile(delete=False)
        bin_file = tempfile.NamedTemporaryFile()
        bin_file.write(os.urandom(1024*1024))
        binary_garbage = bin_file.read()

        @patch('test.api.myclass.MyClass.foo')
        def test(self, fh, checker):
            from test.api import myclass
            c = MyClass()
            result = c.foo(bar=binary_garbage)
            c.foo()
            c.foo()
            with open(checker.name, 'w+') as fp:
                fp.write(str(myclass.side_effect))
            fh.write(str(result == 'foo'))
            fh.close()
            os._exit(0)

        outputs = [ tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False) ]

        for output in outputs:
            pid = os.fork()
            if pid:
                os.waitpid(pid, 0)
            else:
                test(self, output, checker)

        expected = ['True', 'True', 'True']
        result   = []

        for output in outputs:
            output.close()

            fh = open(output.name)
            result.append(fh.read())
            fh.close()

            os.remove(output.name)

        with open(checker.name, 'rb') as fp:
            check = fp.read()
            assert check == "0", "It was: <%s>\n" % check

        os.unlink(checker.name)

        self.assertEqual(result, expected)

    def test_patching_instance_methods_with_cache(self):
        def mixed(x, y, z=1):
            CallOnceEver().update()
            return x + y + z

        checker = tempfile.NamedTemporaryFile(delete=False)

        @patch('test.api.myclass.MyClass.foo')
        def test(self, fh, checker):
            from test.api.myclass import side_effect
            c = MyClass()
            result = c.foo()
            c.foo()
            c.foo()
            with open(checker.name, 'w+') as fp:
                fp.write(str(side_effect))
            fh.write(str(result == 'foo'))
            fh.close()
            os._exit(0)

        outputs = [ tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False),
                    tempfile.NamedTemporaryFile(delete=False) ]

        for output in outputs:
            pid = os.fork()
            if pid:
                os.waitpid(pid, 0)
            else:
                test(self, output, checker)

        expected = ['True', 'True', 'True']
        result   = []

        for output in outputs:
            output.close()

            fh = open(output.name)
            result.append(fh.read())
            fh.close()

            os.remove(output.name)

        with open(checker.name, 'rb') as fp:
            check = fp.read()
            assert check == "0", "It was: <%s>\n" % check

        os.unlink(checker.name)

        self.assertEqual(result, expected)

    def test_tests_with_shell(self):
        shell_tests = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'expected_value.py')
        p = subprocess.Popen(" ".join([sys.executable, shell_tests]), stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
        comm = p.communicate()
        assert comm[0] == '>>> >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> ', "START:" + comm[0] + ":END"

    @patch('caliendo.counter.get_from_trace_for_cache', rvalue=0)
    def test_get_hash(self):
        test_trace_string = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod'

        assert get_hash([1], test_trace_string, {}) == '80fc8e13f14767be1bc9761ca531bc8f543dc1df'
        assert get_hash([1], test_trace_string, {'a': 1}) == 'a069396bd820b613cec07caf272e76210a90f1e6'
        assert get_hash([1], test_trace_string, {'a': ''}) == '98e9df9aeb5444fcb1ffebb7d8fe66a6531df324'
        assert get_hash([1], test_trace_string, {'a': None}) == '0b6098dcac4e5245ef0a76d29802ca43253cc802'
        assert get_hash([1], test_trace_string, {'a': 'A', 'b': 'B'}) == '499ad514047403a5af5ee67e1fe995941cdefcbd'
        assert get_hash([1], test_trace_string, {'a': 'A', 'b': 'B', 'c': 'C'}) == 'ae87cdd7347fe57430d39d9406d60d85517c264e'

        assert get_hash([1, '2'], test_trace_string, {}) == 'f2f66daa0c6d8f69073e3fad3e889516af135105'
        assert get_hash([1, '2'], test_trace_string, {'a': 'A'}) == '9f9c943c2772abf1fe692948a10daaa081836f44'
        assert get_hash([1, '2'], test_trace_string, {'a': '123123'}) == 'b570c7daae91f71d0220d9d502c56dde81c00c9c'
        assert get_hash([1, '2'], test_trace_string, {'a': None}) == 'bd355fe16807cb855ef6ca7932e1991c50e4a4f0'
        assert get_hash([1, '2'], test_trace_string, {'a': 'A', 'b': 'B'}) == '30ab8caa63b1001aae5ec7a8f1eecb236bf360fd'
        assert get_hash([1, '2'], test_trace_string, {'a': 'A', 'b': 'B', 'c': 'C'}) == '7ee9b5b535ce2212d58070a8f8955fd29d1dd23e'

        assert get_hash([1, '2', 'three'], test_trace_string, {}) == '827b468ee4155d49dc12bda9be7ae21b4c2cdfcc'
        assert get_hash([1, '2', 'three'], test_trace_string, {'a': 'A'}) == 'be8756e803916483a52a930431f989d938c33fbb'
        assert get_hash([1, '2', 'three'], test_trace_string, {'a': ''}) == 'a1f21358d577ee458b35ed9543ec8772ef171f5a'
        assert get_hash([1, '2', 'three'], test_trace_string, {'a': None}) == '4938719f4707b4e3e8cdf9fb5c2a8a72d8ef3df2'
        assert get_hash([1, '2', 'three'], test_trace_string, {'a': 'A', 'b': 111}) == 'd8b2cebf5b9ea0f646772e8d796110a8488402e1'
        assert get_hash([1, '2', 'three'], test_trace_string, {'a': 'A', 'b': 'B', 'c': 0.00001}) == '02a2935a139d74cdae967e14023046b1f0c78a9f'

        assert get_hash([1, '2', 'three', [4]], test_trace_string, {}) == '59ebdee80725eebddabb91a34f69df5db03f75ac'
        assert get_hash([1, '2', 'three', [4]], test_trace_string, {'a': 'A'}) == '0ec096116fb0be1aeca09a3b49ff8c873c697bf6'
        assert get_hash([1, '2', 'three', [4]], test_trace_string, {'a': ''}) == 'de20ee14a351f21fad0bd3b533285da4f04a8f33'
        assert get_hash([1, '2', 'three', [4]], test_trace_string, {'a': None}) == '0e1148e63e0129406d1fcbc3f969b5af444562ff'
        assert get_hash([1, '2', 'three', [4]], test_trace_string, {'a': 'A', 'b': None, 'c': 'C'}) == '140b05129f201e8b0e8236938e5fab401bd8b88b'
        assert get_hash([1, '2', 'three', [4]], test_trace_string, {'a': 'A', 'b': 'B', 'c': []})


    @patch('caliendo.counter.get_from_trace', rvalue=1)
    def test_args_are_ignored(self):
        args = (1, 2, 3, 4)
        kwargs = {'a': 1, 'b': 2}
        trace_string = ""
        i_args = [0, 1]
        i_kwargs = ['b']
        a = get_hash(args, trace_string, kwargs, ignore=Ignore(i_args, i_kwargs))
        args = (2, 3, 3, 4)
        b = get_hash(args, trace_string, kwargs, ignore=Ignore(i_args, i_kwargs))
        args = ('elf', 'deer', 3, 4)
        kwargs = {'a': 1, 'b': 6}
        c = get_hash(args, trace_string, kwargs, ignore=Ignore(i_args, i_kwargs))
        args = (2, 2, 2, 2)
        d = get_hash(args, trace_string, kwargs, ignore=Ignore(i_args, i_kwargs))
        args = (1, 2, 3, 4)
        kwargs = {'a': 5, 'b': 2}
        e = get_hash(args, trace_string, kwargs, ignore=Ignore(i_args, i_kwargs))
        assert a == b
        assert b == c
        assert c != d
        assert e != d

    def test_call_hooks(self):
        def test(waittime):
            time.sleep(waittime)
            cs = CallStack(gkeyword)
            cache(gkeyword, kwargs={ 'x': 1, 'y': 2, 'z': 3 }, call_stack=cs, callback=callback)
            cs.save()


            os._exit(0)

        for i in range(3):
            pid = os.fork()
            if pid:
                os.waitpid(pid, 0)
            else:
                test(i * 0.1)

        with open(myfile.name) as f:
            self.assertEquals(f.read(), '2')

    def test_load_and_save_stack(self):
        cs = CallStack(self.test_load_and_save_stack)

        h1 = Hook('fake-hash2', callback2)
        h2 = Hook('fake-hash3', callback3)

        cs.add_hook(h1)
        cs.add_hook(h2)

        assert len(cs.hooks) == 2
        assert len(cs.calls) == 0
        assert cs.hooks['fake-hash2'].hash == 'fake-hash2'
        assert cs.hooks['fake-hash3'].hash == 'fake-hash3'

        delete_stack(cs)

        save_stack(cs)
        loaded = load_stack(cs)

        assert len(loaded.hooks) == 2
        assert len(loaded.calls) == 0
        assert loaded.hooks['fake-hash2'].hash == 'fake-hash2'
        assert loaded.hooks['fake-hash3'].hash == 'fake-hash3'

if __name__ == '__main__':
    unittest.main()

