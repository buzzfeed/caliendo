from caliendo import pickling
import pickle

a = {
      'a': {
        'b': {
          'c': [{
            'd': {
              'e': {
                'f': {
                  'a': 1,
                  'b': 2,
                  'c': 3
                }
              }
            }
          },{
            'd': {
              'e': {
                'f': {
                  'a': 1,
                  'b': 2,
                  'c': 3
                }
              }
            }
            
          }]
        }
      },
      'b': {
        'a': 1,
        'b': 2
      }
    }

b = pickling.pickle_with_weak_refs(a)
c = pickle.loads(b)
print c


