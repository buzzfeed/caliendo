from hashlib import sha1

from caliendo import config

if config.should_use_caliendo():
    from caliendo.db.flatfiles import insert_test, select_test

class Counter:
    __counters = { }

    def get_from_trace(self, trace):
        key = sha1( trace ).hexdigest()
        if key in self.__counters:
            t = self.__counters[ key ]
            self.__counters[ key ] = t + 1
            return t
        else:
            t = self.__get_seed_from_trace( trace )
            if not t:
                t = self.__set_seed_by_trace( trace )

        self.__counters[ key ] = t + 1
        return t

    def __get_seed_from_trace(self, trace):
        key = sha1( trace ).hexdigest()
        res = select_test( key )
        if res:
            r, seq = res[0]
            return seq
        return None

    def __set_seed_by_trace(self, trace):
        key = sha1( trace ).hexdigest()
        t = 0
        insert_test( hash=key, random=t, seq=t )
        seq = self.__get_seed_from_trace( trace )
        return seq

counter = Counter()
