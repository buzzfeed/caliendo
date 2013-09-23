global side_effect 
side_effect = 1

def baz():
    global side_effect
    side_effect += 1
    return 'baz'

def biz():
    return 'biz'