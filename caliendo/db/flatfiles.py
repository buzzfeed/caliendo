import os
import sys
import cPickle as pickle
import dill

from caliendo.logger import get_logger

logger = get_logger(__name__)

DEFAULT_ROOT = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..')
ROOT = os.environ.get('CALIENDO_CACHE_PREFIX', DEFAULT_ROOT)
CACHE_DIRECTORY = os.path.join(ROOT, 'cache')
SEED_DIRECTORY = os.path.join(ROOT, 'seeds')
EV_DIRECTORY = os.path.join(ROOT, 'evs')
STACK_DIRECTORY = os.path.join(ROOT, 'stacks')
LOG_FILEPATH = os.path.join(ROOT, 'used')

if not os.path.exists( CACHE_DIRECTORY ):
    os.makedirs(CACHE_DIRECTORY)
if not os.path.exists( SEED_DIRECTORY ):
    os.makedirs(SEED_DIRECTORY)
if not os.path.exists(EV_DIRECTORY):
    os.makedirs(EV_DIRECTORY)
if not os.path.exists(STACK_DIRECTORY):
    os.makedirs(STACK_DIRECTORY)

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

def insert_io( args ):
    """
    Inserts a method's i/o into the datastore

    :param dict args: A dictionary of the hash, stack, packet_num, methodname, args, and returnval

    :rtype None:
    """
    hash = args['hash']

    record_used('cache', hash)

    packet_num = args['packet_num']
    filepath = os.path.join(CACHE_DIRECTORY, "%s_%s" % (hash, packet_num))

    try:
        with open(filepath, "w+") as f:
            pickle.dump(args, f)
    except IOError:
        if not os.environ.get('CALIENDO_TEST_SUITE', None):
            logger.warning( "Caliendo failed to open " + filepath + ", check file permissions." )

def get_packets(directory):
    file_list = os.listdir(directory)

    packets   = {}
    for filename in file_list:
        hash, packet_num = tuple(filename.split('_'))
        if hash in packets:
            packets[hash] += 1
        else:
            packets[hash] = 1

    return packets

def get_filenames_for_hash(directory, hash):
    packets = get_packets(directory)
    paths = []

    if hash not in packets:
        return []

    for i in range(packets[hash]):
      filename = "%s_%s" % (hash, i)
      path = os.path.abspath(os.path.join(directory, filename))
      paths.append(path)

    return paths

def select_io( hash ):
    """
    Returns the relevant i/o for a method whose call is characterized by the hash

    :param hash: The hash for the CallDescriptor

    :rtype list(tuple( hash, stack, methodname, returnval, args, packet_num )):
    """
    res = []
    if not hash:
        return res

    record_used('cache', hash)

    for packet in get_filenames_for_hash(CACHE_DIRECTORY, hash):
        try:
            with open(packet, "rb") as f:
                d = pickle.load(f)
                res += [(d['hash'], d['stack'], d['methodname'], d['returnval'], d['args'], d['packet_num'])]
        except IOError:
            if not os.environ.get('CALIENDO_TEST_SUITE', None):
                logger.warning( "Caliendo failed to open " + packet + " for reading." )

    return res

def select_expected_value(hash):
    if not hash:
        return []
    res = []
    record_used('evs', hash)
    for packet in get_filenames_for_hash(EV_DIRECTORY, hash):
        try:
            with open(packet, "rb") as f:
                fr = pickle.load(f)
                res += [(fr['call_hash'], fr['expected_value'], fr['packet_num'])]
        except IOError:
            if not os.environ.get('CALIENDO_TEST_SUITE', None):
                logger.warning("Failed to open %s" % packet)
    return res

def delete_expected_value(hash):
    pass

def insert_expected_value(packet):
    hash = packet['call_hash']
    packet_num = packet['packet_num']
    ev = packet['expected_value']
    record_used('evs', hash)
    try:
        filename = "%s_%s" % (hash, packet_num)
        filepath = os.path.join(EV_DIRECTORY, filename)
        with open(filepath, "w+") as f:
            pickle.dump({'call_hash': hash,
                         'expected_value': ev,
                         'packet_num': packet_num},
                         f)
    except IOError:
        if not os.environ.get('CALIENDO_TEST_SUITE', None):
            logger.warning("Failed to open %s" % hash)

def insert_test( hash, random, seq ):
    """
    Inserts a random value and sequence for a local call counter

    :param str hash: The hash for the call
    :param str random: A random number for the seed
    :param str seq: An integer from which to increment on the local call

    :rtype None:
    """
    try:
        with open(os.path.join(SEED_DIRECTORY, "%s_%s" % (hash, 0)), "w+") as f:
            record_used('seeds', hash)
            pickle.dump({'hash': hash, 'random': random, 'seq': seq }, f)
    except IOError:
        if not os.environ.get('CALIENDO_TEST_SUITE', None):
            logger.warning( "Failed to open %s" % hash)

def select_test( hash ):
    """
    Returns the seed values associated with a function call

    :param str hash: The hash for the function call

    :rtype [tuple(<string>, <string>)]:
    """
    filepath = os.path.join(SEED_DIRECTORY, "%s_%s" % (hash, 0))
    try:
        f = None
        res = None
        record_used('seeds', hash)
        with open(filepath, "rb") as f:
            d = pickle.load(f)
            res = ( d['random'], d['seq'] )
    except IOError:
        if not os.environ.get('CALIENDO_TEST_SUITE', None):
            logger.warning( "Caliendo failed to read " + filepath )

    if res:
        return [res]
    return None

def delete_io( hash ):
    """
    Deletes records associated with a particular hash

    :param str hash: The hash

    :rtype int: The number of records deleted
    """
    res = 0
    record_used('cache', hash)
    for packet in get_filenames_for_hash(CACHE_DIRECTORY, hash):
        try:
            os.remove(packet)
            res = res + 1
        except:
            if not os.environ.get('CALIENDO_TEST_SUITE', None):
                logger.warning( "Failed to remove file: " + packet )
    return res

def get_unique_hashes():
    """
    Returns all the hashes for cached calls

    :rtype list(<string>)
    """
    return list( set( [ filename.split("_")[0] for filename in os.listdir(CACHE_DIRECTORY) ] ) )

def delete_from_directory_by_hashes(directory, hashes):
    """
    Deletes all cache files corresponding to a list of hashes from a directory

    :param str directory: The directory to delete the files from
    :param list(str) hashes: The hashes to delete the files for

    """
    files = os.listdir(directory)
    if hashes == '*':
        for f in files:
            os.unlink(os.path.join(directory, f))
    for f in files:
        for h in hashes:
            if h in f:
                os.unlink(os.path.join(directory, f))

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
    evs = set(get_packets(EV_DIRECTORY).keys())
    cache = set(get_packets(CACHE_DIRECTORY).keys())
    seeds = set(get_packets(SEED_DIRECTORY).keys())
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
        to_remove = all_hashes[kind].difference(hashes)
        if kind == 'evs':
            delete_from_directory_by_hashes(EV_DIRECTORY, to_remove)
        elif kind == 'cache':
            delete_from_directory_by_hashes(CACHE_DIRECTORY, to_remove)
        elif kind == 'seeds':
            delete_from_directory_by_hashes(SEED_DIRECTORY, to_remove)

    reset_used()

def save_stack(stack):
    """
    Saves a stack object to a flatfile.

    :param caliendo.hooks.CallStack stack: The stack to save.

    """
    path = os.path.join(STACK_DIRECTORY, '%s.%s' % (stack.module, stack.caller))
    with open(path, 'w+') as f:
        dill.dump(stack, f)

def load_stack(stack):
    """
    Loads the saved state of a CallStack and returns a whole instance given an instance with incomplete state.

    :param caliendo.hooks.CallStack stack: The stack to load

    :returns: A CallStack previously built in the context of a patch call.
    :rtype: caliendo.hooks.CallStack

    """
    path = os.path.join(STACK_DIRECTORY, '%s.%s' % (stack.module, stack.caller))
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return dill.load(f)
    return None

def delete_stack(stack):
    """
    Deletes a stack that was previously saved.load_stack

    :param caliendo.hooks.CallStack stack: The stack to delete.
    """
    path = os.path.join(STACK_DIRECTORY, '%s.%s' % (stack.module, stack.caller))
    if os.path.exists(path):
        os.unlink(path)
