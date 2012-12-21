import os
import cPickle as pickle

from caliendo.logger import get_logger

logger = get_logger(__name__)

CACHE_DIRECTORY = os.path.abspath(__name__).replace( 'caliendo.db.flatfiles', '' ) + 'cache/'
SEED_DIRECTORY = os.path.abspath(__name__).replace('caliendo.db.flatfiles', '' ) + 'seeds/'

if not os.path.exists( CACHE_DIRECTORY ):
    os.makedirs(CACHE_DIRECTORY)
if not os.path.exists( SEED_DIRECTORY ):
    os.makedirs(SEED_DIRECTORY)

def insert_io( args ):
    """
    Inserts a method's i/o into the datastore

    :param dict args: A dictionary of the hash, stack, packet_num, methodname, args, and returnval

    :rtype None:
    """
    hash = args['hash']
    packet_num = args['packet_num']
    filepath = CACHE_DIRECTORY + hash + "_" + str( packet_num )
    try:
        f = None
        with open(filepath, "w+") as f:
            pickle.dump(args, f)
    except IOError:
        logger.warning( "Caliendo failed to open " + filepath + ", check file permissions." )

def select_io( hash ):
    """
    Returns the relevant i/o for a method whose call is characterized by the hash

    :param hash: The hash for the CallDescriptor

    :rtype list(tuple( hash, stack, methodname, returnval, args, packet_num )):
    """
    if not hash:
        return []
    file_list = os.listdir(CACHE_DIRECTORY)
    fi = lambda filename: True if hash in filename else False
    packets = [ os.path.join( CACHE_DIRECTORY, filename ) for filename in sorted( filter( fi, file_list ) ) ]
    res = [ ]
    for packet in packets:
        try:
            f = None
            with open(packet, "rb") as f:
                d = pickle.load( f )
                res += [(d['hash'], d['stack'], d['methodname'], d['returnval'], d['args'], d['packet_num'] )]
        except IOError:
            logger.warning( "Caliendo failed to open " + packet + " for reading." )

    if not res:
        return []
    return res

def insert_test( hash, random, seq ):
    """
    Inserts a random value and sequence for a local call counter

    :param str hash: The hash for the call
    :param str random: A random number for the seed
    :param str seq: An integer from which to increment on the local call

    :rtype None:
    """

    filepath = SEED_DIRECTORY + hash
    try:
        f = None
        with open(filepath, "w+") as f:
            pickle.dump({'hash': hash, 'random': random, 'seq': seq }, f)
    except IOError:
        logger.warning( "Caliendo failed to open " + filepath + ", check file permissions." )

def select_test( hash ):
    """
    Returns the seed values associated with a function call

    :param str hash: The hash for the function call

    :rtype [tuple(<string>, <string>)]:
    """
    filepath = SEED_DIRECTORY + hash
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
    file_list = os.listdir(CACHE_DIRECTORY)
    f = lambda filename: True if hash in filename else False
    packets = [ os.path.join( CACHE_DIRECTORY, filename ) for filename in sorted( filter( f, file_list ) ) ]
    res = 0
    for packet in packets:
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