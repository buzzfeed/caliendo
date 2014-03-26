from __future__ import absolute_import
import sys

import os
import dill as pickle

from caliendo.logger import get_logger

logger = get_logger(__name__)

DEFAULT_ROOT = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..')
ROOT = os.environ.get('CALIENDO_CACHE_PREFIX', DEFAULT_ROOT)
CACHE = os.path.join(ROOT, 'cache')
CACHE_ = None

PPROT = pickle.HIGHEST_PROTOCOL

LOCKFILE = os.path.join(ROOT, 'lock')
LOG_FILEPATH = os.path.join(ROOT, 'used')

def record_used(kind, hash):
    """
    Indicates a cachefile with the name 'hash' of a particular kind has been used so it will note be deleted on the next purge.

    :param str kind: The kind of cachefile. One of 'cache', 'seeds', or 'evs'
    :param str hash: The hash for the call descriptor, expected value descriptor, or counter seed.

    :rtype: None
    """
    if os.path.exists(LOG_FILEPATH):
        log = open(os.path.join(ROOT, 'used'), 'a')
    else:
        log = open(os.path.join(ROOT, 'used'), 'w+')

    log.writelines(["%s...%s\n" % (kind, hash)])


def get_packets(cache_type):
    load_cache(True)
    global CACHE_
    packets   = {}
    all_cached = CACHE_[cache_type]
    for hash, all_packets in all_cached:
        packets[hash] = len(all_packets)
    return packets

def delete_io( hash ):
    """
    Deletes records associated with a particular hash

    :param str hash: The hash

    :rtype int: The number of records deleted
    """
    global CACHE_
    load_cache(True)
    record_used('cache', hash)
    num_deleted = len(CACHE_['cache'].get(hash, []))
    if hash in CACHE_['cache']:
        del CACHE_['cache'][hash]
    write_out()
    return num_deleted

def insert_io( args ):
    """
    Inserts a method's i/o into the datastore

    :param dict args: A dictionary of the hash, stack, packet_num, methodname, args, and returnval

    :rtype None:
    """
    global CACHE_
    load_cache()
    hash = args['hash']
    record_used('cache', hash)
    packet_num = args['packet_num']
    if hash not in CACHE_['cache']:
        CACHE_['cache'][hash] = {}
    CACHE_['cache'][hash][packet_num] = pickle.dumps(args, PPROT)
    write_out()

def select_io( hash ):
    """
    Returns the relevant i/o for a method whose call is characterized by the hash

    :param hash: The hash for the CallDescriptor

    :rtype list(tuple( hash, stack, methodname, returnval, args, packet_num )):
    """
    load_cache(True)
    global CACHE_
    res = []
    record_used('cache', hash)
    for d in CACHE_['cache'].get(hash, {}).values():
        d = pickle.loads(d)
        res += [(d['hash'], d['stack'], d['methodname'], d['returnval'], d['args'], d['packet_num'])]
    return res

def select_expected_value(hash):
    load_cache(True)
    global CACHE_
    if not hash:
        return []
    res = []
    record_used('evs', hash)
    evs = CACHE_.get('evs', {})
    values_at_hash = evs.get(hash, [])
    for fr in values_at_hash:
        fr = pickle.loads(fr)
        res += [(fr['call_hash'], fr['expected_value'], fr['packet_num'])]
    return res

def delete_expected_value(hash):
    pass

def insert_expected_value(packet):
    global CACHE_
    load_cache()
    hash = packet['call_hash']
    record_used('evs', hash)
    if hash not in CACHE_['evs']:
        CACHE_['evs'][hash] = []
    CACHE_['evs'][hash].append(pickle.dumps(packet, PPROT))
    write_out()

def insert_test( hash, random, seq ):
    """
    Inserts a random value and sequence for a local call counter

    :param str hash: The hash for the call
    :param str random: A random number for the seed
    :param str seq: An integer from which to increment on the local call

    :rtype None:
    """
    global CACHE_
    load_cache()
    record_used('seeds', hash)
    CACHE_['seeds'][hash] = {'hash': hash, 'random': random, 'seq': seq}
    write_out()

def select_test( hash ):
    """
    Returns the seed values associated with a function call

    :param str hash: The hash for the function call

    :rtype [tuple(<string>, <string>)]:
    """
    load_cache(True)
    global CACHE_
    record_used('seeds', hash)
    d = CACHE_['seeds'].get(hash, {})

    if d:
        return [( d.get('random', None), d.get('seq', None) )]
    else:
        return None


def get_unique_hashes():
    """
    Returns all the hashes for cached calls

    :rtype list(<string>)
    """
    load_cache(True)
    global CACHE_
    return CACHE_['cache'].keys()

def delete_from_directory_by_hashes(cache_type, hashes):
    """
    Deletes all cache files corresponding to a list of hashes from a directory

    :param str directory: The type of cache to delete files for.
    :param list(str) hashes: The hashes to delete the files for

    """
    global CACHE_
    if hashes == '*':
        CACHE_[cache_type] = {}
    for h in hashes:
        if h in CACHE_[cache_type]:
            del CACHE_[cache_type][h]
    write_out()

def read_used():
    """
    Read all hashes that have been used since the last call to purge (or reset_hashes).

    :rtype: dict
    :returns: A dictionary of sets of hashes organized by type
    """
    used_hashes = {"evs": set([]),
                   "cache": set([]),
                   "seeds": set([])}

    with open(LOG_FILEPATH, 'rb') as logfile:
        for line in logfile.readlines():
            kind, hash = tuple(line.split('...'))
            used_hashes[kind].add(hash.rstrip())

    return used_hashes

def read_all():
    """
    Reads all the hashes and returns them in a dictionary by type

    :rtype: dict
    :returns: A dictionary of sets of hashes by type
    """
    global CACHE_
    load_cache(True)
    evs = CACHE_['evs'].keys()
    cache = CACHE_['cache'].keys()
    seeds = CACHE_['seeds'].keys()
    return {"evs"  : evs,
            "cache": cache,
            "seeds": seeds}

def reset_used():
    """
    Deletes all the records of which hashes have been used since the last call to this method.

    """
    with open(LOG_FILEPATH, 'w+') as logfile:
        pass

def purge():
    """
    Deletes all the cached files since the last call to reset_used that have not been used.

    """
    all_hashes = read_all()
    used_hashes = read_used()
    for kind, hashes in used_hashes.items():
        hashes = set(hashes)
        to_remove = set(all_hashes[kind]).difference(hashes)
        delete_from_directory_by_hashes(kind, to_remove)

    reset_used()
    write_out()

def save_stack(stack):
    """
    Saves a stack object to a flatfile.

    :param caliendo.hooks.CallStack stack: The stack to save.

    """
    global CACHE_
    serialized = pickle.dumps(stack, PPROT)
    CACHE_['stacks']["{0}.{1}".format(stack.module, stack.caller)] = serialized
    write_out()

def load_stack(stack):
    """
    Loads the saved state of a CallStack and returns a whole instance given an instance with incomplete state.

    :param caliendo.hooks.CallStack stack: The stack to load

    :returns: A CallStack previously built in the context of a patch call.
    :rtype: caliendo.hooks.CallStack

    """
    global CACHE_
    load_cache(True)
    key = "{0}.{1}".format(stack.module, stack.caller)
    if key in CACHE_['stacks']:
        return pickle.loads(CACHE_['stacks'][key])

def delete_stack(stack):
    """
    Deletes a stack that was previously saved.load_stack

    :param caliendo.hooks.CallStack stack: The stack to delete.
    """
    global CACHE_
    key = "{0}.{1}".format(stack.module, stack.caller)
    if key in CACHE_['stacks']:
        del CACHE_['stacks'][key]
        write_out()

def write_out():
    global CACHE_
    import time
    try:
        while os.path.exists(LOCKFILE):
            sys.stderr.write("Waiting on lock...\n")
            time.sleep(0.01)

        with open(LOCKFILE, 'w+') as lock:
            with open(CACHE, 'w+') as f:
                pickle.dump(CACHE_, f, pickle.HIGHEST_PROTOCOL)
    finally:
        if os.path.exists(LOCKFILE):
            os.unlink(LOCKFILE)
        load_cache(True)

def load_cache(reload=False):
    global CACHE_

    if os.path.exists(CACHE):
        with open(CACHE, 'rb') as f:
            CACHE_ = pickle.load(f)
    else:
        CACHE_ = {'seeds': {},
                  'evs': {},
                  'stacks': {},
                  'cache': {}}


load_cache()
