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
    hash = args['hash']
    packet_num = args['packet_num']
    filepath = CACHE_DIRECTORY + hash + "_" + str( packet_num )
    try:
        f = None
        with open(filepath, "w+") as f:
            pickle.dump(args, f)
    except IOError:
        logger.warning( "Caliendo failed to open " + filepath + ", check file permissions." )
    finally:
        if f:
            f.close()

def select_io( hash ):
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
        finally:
            if f:
                f.close()
    if not res:
        return []
    return res

def insert_test( hash, random, seq ):
    filepath = SEED_DIRECTORY + hash
    try:
        f = None
        with open(filepath, "w+") as f:
            pickle.dump({'hash': hash, 'random': random, 'seq': seq }, f)
    except IOError:
        logger.warning( "Caliendo failed to open " + filepath + ", check file permissions." )
    finally:
        if f:
            f.close()

def select_test( hash ):
    filepath = SEED_DIRECTORY + hash
    try:
        f = None
        res = None
        with open(filepath, "rb") as f:
            d = pickle.load(f)
            res = ( d['random'], d['seq'] )
    except IOError:
        logger.warning( "Caliendo failed to read " + filepath )
    finally:
        if f:
            f.close()
    if res:
        return [res]
    return None

def delete_io( hash ):
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
    return list( set( [ filename.split("_")[0] for filename in os.listdir(CACHE_DIRECTORY) ] ) )