import os
import sys
import cPickle as pickle

from caliendo.logger import get_logger

logger = get_logger(__name__)

DEFAULT_ROOT = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..')
ROOT = os.environ.get('CALIENDO_CACHE_PREFIX', None) or DEFAULT_ROOT 
CACHE_DIRECTORY = os.path.join(ROOT, 'cache')
SEED_DIRECTORY = os.path.join(ROOT, 'seeds')
EV_DIRECTORY = os.path.join(ROOT, 'evs')

if not os.path.exists( CACHE_DIRECTORY ):
    os.makedirs(CACHE_DIRECTORY)
if not os.path.exists( SEED_DIRECTORY ):
    os.makedirs(SEED_DIRECTORY)
if not os.path.exists(EV_DIRECTORY):
    os.makedirs(EV_DIRECTORY)

def insert_io( args ):
    """
    Inserts a method's i/o into the datastore

    :param dict args: A dictionary of the hash, stack, packet_num, methodname, args, and returnval

    :rtype None:
    """
    hash = args['hash']
    packet_num = args['packet_num']
    filepath = os.path.join(CACHE_DIRECTORY, "%s_%s" % (hash, packet_num))
    try:
        with open(filepath, "w+") as f:
            pickle.dump(args, f)
    except IOError:
        logger.warning( "Caliendo failed to open " + filepath + ", check file permissions." )

def get_packets(directory):
    file_list = os.listdir(directory)
    packets   = {}
    for filename in file_list:
        try:
            hash, packet_num = tuple(filename.split('_'))
            if hash in packets:
                packets[hash] += 1
            else:
                packets[hash] = 1
        except:
            pass
    return packets

def get_filenames_for_hash(directory, hash):
    packets = get_packets(directory)
    if hash not in packets:
        return []
    return [os.path.abspath(os.path.join(directory, "%s_%s" % (hash, i)))
            for i in range(packets[hash])]

def select_io( hash ):
    """
    Returns the relevant i/o for a method whose call is characterized by the hash

    :param hash: The hash for the CallDescriptor

    :rtype list(tuple( hash, stack, methodname, returnval, args, packet_num )):
    """
    res = []
    if not hash:
        return res

    for packet in get_filenames_for_hash(CACHE_DIRECTORY, hash):
        try:
            with open(packet, "rb") as f:
                d = pickle.load(f)
                res += [(d['hash'], d['stack'], d['methodname'], d['returnval'], d['args'], d['packet_num'])]
        except IOError:
            logger.warning( "Caliendo failed to open " + packet + " for reading." )

    return res

def select_expected_value(hash):
    if not hash:
        return []
    res = []
    for packet in get_filenames_for_hash(EV_DIRECTORY, hash):
        try:
            with open(packet, "rb") as f:
                fr = pickle.load(f)
                res += [(fr['call_hash'], fr['expected_value'], fr['packet_num'])]
        except IOError:
            logger.warning("Failed to open %s" % packet)
    return res

def delete_expected_value(hash):
    pass

def insert_expected_value(packet):
    hash = packet['call_hash']
    packet_num = packet['packet_num']
    ev = packet['expected_value']
    try:
        with open(os.path.join(EV_DIRECTORY, "%s_%s" % (hash, packet_num)), "w+") as f:
            pickle.dump({'call_hash': hash, 'expected_value': ev, 'packet_num': packet_num}, f)
    except IOError:
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
        with open(os.path.join(SEED_DIRECTORY, hash), "w+") as f:
            pickle.dump({'hash': hash, 'random': random, 'seq': seq }, f)
    except IOError:
        logger.warning( "Failed to open %s" % hash)

def select_test( hash ):
    """
    Returns the seed values associated with a function call

    :param str hash: The hash for the function call

    :rtype [tuple(<string>, <string>)]:
    """
    filepath = os.path.join(SEED_DIRECTORY, hash)
    try:
        f = None
        res = None
        with open(filepath, "rb") as f:
            d = pickle.load(f)
            res = ( d['random'], d['seq'] )
    except IOError:
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
    for packet in get_filenames_for_hash(CACHE_DIRECTORY, hash):
        try:
            os.remove(packet)
            res = res + 1
        except:
            logger.warning( "Failed to remove file: " + packet )
    return res

def get_unique_hashes():
    """
    Returns all the hashes for cached calls

    :rtype list(<string>)
    """
    return list( set( [ filename.split("_")[0] for filename in os.listdir(CACHE_DIRECTORY) ] ) )
