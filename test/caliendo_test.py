from caliendo.facade import CallDescriptor, Facade
from caliendo import *
import tempfile
import unittest
import hashlib
import sys
import os

class CallOnceEver:
    __die = 0
    def update(self):
        if self.__die:
            raise Exception("NOPE!")
        else:
            self.__die = 1
            return 1

class TestC:
    __private_var = 0
    def methoda(self):
        return "a"
    def methodb(self):
        return "b"
    def update(self):
        return "c"
    def increment(self):
        self.__private_var = self.__private_var + 1
        return self.__private_var

class  CaliendoTestCase(unittest.TestCase):

    def test_call_descriptor(self):
        hash      = hashlib.sha1( "adsf" ).hexdigest()
        method    = "mymethod"
        returnval = {'thisis': [ 'my', 'return','val' ] }
        args      = ( 'a', 'b', 'c' )

        cd = CallDescriptor(
            hash=hash,
            method=method,
            returnval=returnval,
            args=args )

        cd.save() 

        self.assertEqual( cd.hash, hash )
        self.assertEqual( cd.methodname, method )
        self.assertEqual( cd.returnval, returnval )
        self.assertEqual( cd.args, args )

        cd = fetch_call_descriptor( hash )

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

        cd = CallDescriptor( hash=hash, method=method, returnval=returnval, args=args )
        cd.save( )

        cd = fetch_call_descriptor( hash )
        self.assertEquals( cd.hash, hash )
        self.assertEquals( cd.methodname, method )

        hash      = hashlib.sha1( "test1" ).hexdigest()
        method    = "test2"
        cd.methodname = method
        cd.save( )

        cd = fetch_call_descriptor( hash )
        self.assertEquals( cd.hash, hash )
        self.assertEquals( cd.methodname, method )

        hash      = hashlib.sha1( "test3" ).hexdigest()
        method    = "test3"
        cd.hash   = hash
        cd.methodname = method
        cd.save( )

        cd = fetch_call_descriptor( hash )
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

if __name__ == '__main__':
    unittest.main()

