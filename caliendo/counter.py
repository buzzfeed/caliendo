from hashlib import sha1
import os

from caliendo import config

if config.should_use_caliendo():
    from caliendo.db.flatfiles import insert_test, select_test

__counters = { }

def get_from_trace_for_ev(trace):
    if os.environ.get('CALIENDO_DISABLE_EV_COUNTER', False) == 'True':
        return 0
    return get_from_trace(trace)

def get_from_trace_for_cache(trace):
    if os.environ.get('CALIENDO_DISABLE_CACHE_COUNTER', False) == 'True':
        return 0
    return get_from_trace(trace)

def get_from_trace(trace):
    key = sha1( trace ).hexdigest()
    if key in __counters:
        t = __counters[ key ]
        __counters[ key ] = t + 1
        return t
    else:
        t = __get_seed_from_trace( trace )
        if not t:
            t = __set_seed_by_trace( trace )

    __counters[ key ] = t + 1
    return t

def __get_seed_from_trace( trace):
    key = sha1( trace ).hexdigest()
    res = select_test( key )
    if res:
        r, seq = res[0]
        return seq
    return None

def __set_seed_by_trace( trace):
    key = sha1( trace ).hexdigest()
    t = 0
    insert_test( hash=key, random=t, seq=t )
    seq = __get_seed_from_trace( trace )
    return seq

