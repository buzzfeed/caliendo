import inspect
import tempfile
import unittest
import hashlib
import sys
import os

os.environ['USE_CALIENDO'] = 'True'

from caliendo import config

import caliendo
from caliendo.call_descriptor import CallDescriptor, fetch
from caliendo.facade import Facade
from caliendo.facade import Wrapper
from caliendo.util import serialize_args

USE_CALIENDO = config.should_use_caliendo( )
CONFIG       = config.get_database_config( )

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

class  CaliendoTestCase(unittest.TestCase):

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

    def test_serialize_args(self):
        basic_list = [ 'a', 'b', 'c' ]
        basic_dict = { 'a': 1, 'b': 2, 'c': 3 }
        nested_list = [ [ 0, 1, 2 ], [ 3, 4, 5 ] ]
        nested_dict = { 'a': { 'a': 1, 'b': 2 }, 'b': { 'c': 3, 'd': 4 } }
        list_of_nested_dicts = [ { 'a': { 'a': 1, 'b': 2 }, 'b': { 'c': 3, 'd': 4 } } ]

        s_basic_list = str( serialize_args( ( basic_list, ) ) )
        s_basic_dict = str( serialize_args( ( basic_dict, ) ) )
        s_nested_list = str( serialize_args( ( nested_list, ) ) )
        s_nested_dict = str( serialize_args( ( nested_dict, ) ) )
        s_list_of_nested_dicts = str( serialize_args( ( list_of_nested_dicts, ) ) )

        self.assertEquals( s_basic_list, '["[\'a\', \'b\', \'c\']"]' )
        self.assertEquals( s_basic_dict, '["frozenset([(\'a\', 1), (\'b\', 2), (\'c\', 3)])"]' )
        self.assertEquals( s_nested_list, '[\'[[0, 1, 2], [3, 4, 5]]\']' )
        self.assertEquals( s_nested_dict, '[None]' ) # Fix this one!
        self.assertEquals( s_list_of_nested_dicts, '["[{\'a\': {\'a\': 1, \'b\': 2}, \'b\': {\'c\': 3, \'d\': 4}}]"]' )

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
            op = Facade( o )
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
        hashes.append( mtc_f.last_cached )
        self.assertEquals( mtc.methodb( ), mtc_f.methodb( ) )
        hashes.append( mtc_f.last_cached )
        self.assertEquals( mtc_f.methoda( ), "a" )
        hashes.append( mtc_f.last_cached )

        self.assertEquals( mtc_f.increment( ), 1 )
        hashes.append( mtc_f.last_cached )
        self.assertEquals( mtc_f.increment( ), 2 ) 
        hashes.append( mtc_f.last_cached )
        self.assertEquals( mtc_f.increment( ), 3 ) 
        hashes.append( mtc_f.last_cached )
        self.assertEquals( mtc_f.increment( ), 4 )
        hashes.append( mtc_f.last_cached )

        # Ensure hashes are now in db:
        for hash in hashes:
            cd = fetch( hash )
            self.assertEquals( cd.hash, hash )

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

if __name__ == '__main__':
    unittest.main()

