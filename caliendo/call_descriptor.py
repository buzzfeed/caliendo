import cPickle as pickle
import copy_reg
import types
import sys

from caliendo import config
from caliendo import pickling

if config.should_use_caliendo():
    from caliendo.db.flatfiles import insert_io, select_io, delete_io

def fetch( hash ):
    """
    Fetches CallDescriptor from the local database given a hash key representing the call. If it doesn't exist returns None.

    :param str hash: The sha1 hexdigest to look the CallDescriptor up by.

    :rtype: CallDescriptor corresponding to the hash passed or None if it wasn't found.
    """
    res = select_io( hash )

    if res:
      p = { 'methodname': '', 'returnval': '', 'args': '', 'stack': '' }
      for packet in res:
        hash, stack, methodname, returnval, args, packet_num = packet
        p['methodname'] = p['methodname'] + methodname
        p['returnval']  = p['returnval'] + returnval
        p['args']       = p['args'] + args
        p['stack']      = p['stack'] + stack
                             
      return CallDescriptor( hash = hash,
                             stack = p['stack'],
                             method = p['methodname'],
                             returnval = pickle.loads( str( p['returnval'] ) ),
                             args = pickle.loads( str( p['args'] ) ) )
    return None


class CallDescriptorBuffer:
  def __init__(self, methodname, args, returnval, stack):

    try:
        args                   = pickling.pickle_with_weak_refs(args)
    except:
        args               = pickling.pickle_with_weak_refs(tuple([]))

    returnval              = pickling.pickle_with_weak_refs(returnval)

    self.__data            = "".join([ methodname, args, returnval, stack ])
    self.__methodname_len  = len( methodname )
    self.__args_len        = len( args )
    self.__returnval_len   = len( returnval )
    self.__stack_len       = len( stack )
    self.length            = self.__methodname_len + self.__args_len + self.__returnval_len + self.__stack_len
    self.char              = 0

  def next(self):
    if self.char + 1 > self.length:
      raise StopIteration

    c         = self.__data[ self.char ]
    attr      = self.attr()
    self.char = self.char + 1

    return c, attr

  def __iter__(self):
    return self

  def attr(self):
    if self.char < self.__methodname_len:
      return 'methodname'
    elif self.char < self.__methodname_len + self.__args_len:
      return 'args'
    elif self.char < self.__methodname_len + self.__args_len + self.__returnval_len:
      return 'returnval'
    else:
      return 'stack'


class CallDescriptor:
    """
    This is a basic model representing a function call. It saves the method name,
    a hash key for lookups, the arguments, and return value. This way the call can
    be handled cleanly and referenced later.
    """
    def __init__( self, hash='', stack='', method='', returnval='', args='', kwargs='' ):
        """
        CallDescriptor initialiser.

        :param str hash: A hash of the method, order of the call, and arguments.
        :param str method: The name of the method being called.
        :param mixed returnval: The return value of the method. If this isn't pickle-able there will be a problem.
        :param mixed args: The arguments for the method. If these aren't pickle-able there will be a problem.
        """

        self.hash       = hash
        self.stack      = stack
        self.methodname = method
        self.returnval  = returnval
        self.args       = args
        self.kwargs     = kwargs

    def __empty_packet(self, packet_num):
        return {
            'hash': '',
            'packet_num': packet_num,
            'methodname': '',
            'args': '',
            'returnval': '',
            'stack': ''
          }

    def __enumerate_packets(self):
        max_packet_size  = 1024 * 1024 # ~2MB depending on the size of a char, prolly more like 4MB for 4b char size. MySQL default limit is 16
        buffer           = CallDescriptorBuffer( self.methodname, self.args, self.returnval, self.stack )
        packet_num       = 0
        packets          = [ ]
        while buffer.char < buffer.length:
            p = self.__empty_packet( packet_num )
            packet_length = 0
            for char, attr in buffer:
                p[attr] += char
                packet_length += 1
                if packet_length == max_packet_size:
                    break
            packets.append( p )
            packet_num += 1

        return packets

    def enumerate(self):
        self.__enumerate_packets()

    def save( self ):
        """
        Save method for the CallDescriptor.

        If the CallDescriptor matches a past CallDescriptor it updates the existing
        database record corresponding to the hash. If it doesn't already exist it'll
        be INSERT'd.
        """
        packets = self.__enumerate_packets( )
        delete_io( self.hash )
        for packet in packets:
            packet['hash'] = self.hash
            insert_io( packet )

        return self # Supports chaining
