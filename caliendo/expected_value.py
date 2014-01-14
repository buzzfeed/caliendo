import cPickle as pickle
import sys
import copy_reg
import types
import inspect
from hashlib import sha1

import caliendo
from caliendo import config
from caliendo import pickling
from caliendo import util
from caliendo import prompt
from caliendo import counter

if config.should_use_caliendo():
    from caliendo.db.flatfiles import select_expected_value, delete_expected_value, insert_expected_value

def get_or_store(observed_value):
    caller = inspect.stack()[2][3]
    trace_string = util.get_stack(caller)
    counter_value = counter.get_from_trace_for_ev(trace_string)
    call_hash = sha1("%s.%s" % (trace_string,
                                counter_value)).hexdigest()

    ev = fetch(call_hash)
    if not ev or (config.CALIENDO_PROMPT and prompt.should_modify_expected_value(caller)):
        ev = ExpectedValue(call_hash=call_hash,
                           expected_value=prompt.modify_expected_value(observed_value, caller))
        ev.save()

    return ev.expected_value

def is_true_under(handle, observed_value):
    stored = get_or_store(observed_value)
    return handle(stored, observed_value)

def is_equal_to(observed_value):
    return get_or_store(observed_value) == observed_value

def is_greater_than(observed_value):
    return get_or_store(observed_value) > observed_value

def is_less_than(observed_value):
    return get_or_store(observed_value) < observed_value

def contains(observed_value, el):
    return el in get_or_store(observed_value)

def does_not_contain(observed_value, el):
    return el not in get_or_store(observed_value)

def fetch( call_hash ):
    """
    Fetches CallDescriptor from the local database given a hash key representing the call. If it doesn't exist returns None.

    :param str hash: The sha1 hexdigest to look the CallDescriptor up by.

    :rtype: CallDescriptor corresponding to the hash passed or None if it wasn't found.
    """
    res = select_expected_value(call_hash)
    if not res:
        return None

    last_packet_number = -1
    expected_value = ""
    for packet in res:
        call_hash, expected_value_fragment, packet_num = packet
        expected_value += expected_value_fragment
        if packet_num <= last_packet_number:
            raise Exception("Received expected_value data out of order!")

        last_packet_number = packet_num

    return ExpectedValue( call_hash      = call_hash,
                          expected_value = pickle.loads(str(expected_value)) )

class ExpectedValueBuffer:
    def __init__(self, expected_value):
        returnval   = pickling.pickle_with_weak_refs(expected_value)
        self.__data = returnval
        self.length = len(self.__data)
        self.char   = 0

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
        return 'expected_value'

class ExpectedValue:

    def __init__(self, call_hash, expected_value):
        self.call_hash = call_hash
        self.expected_value = expected_value

    def __empty_packet(self, packet_num):
        return {
            'call_hash': self.call_hash,
            'packet_num': packet_num,
            'expected_value': ''
          }

    def __enumerate_packets(self):
        max_packet_size  = 1024 * 1024 # ~2MB, prolly more like 4MB for 4b char size. MySQL default limit is 16
        buffer           = ExpectedValueBuffer(self.expected_value)
        packet_num       = 0
        packets          = [ ]
        while buffer.char < buffer.length:
            p = self.__empty_packet(packet_num)
            packet_length = 0
            for char, attr in buffer:
                p[attr] += char
                packet_length += 1
                if packet_length == max_packet_size:
                    break
            packets.append( p )
            packet_num += 1

        return packets

    def save( self ):
        """
        Save method for the ExpectedValue of a call.

        """
        packets = self.__enumerate_packets()
        delete_expected_value(self.call_hash)
        for packet in packets:
            packet['call_hash'] = self.call_hash
            insert_expected_value(packet)

        return self
