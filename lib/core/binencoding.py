


## BINARY ENCODING

def neg_complement_maybe(v):
    if v<0:
        return 256 + v
    return v

def nibblize(v, size=2):
    v = neg_complement_maybe(v)
    v_str = hex(v)[2:]
    v_arr = [int(v, 16) for v in reversed(v_str)]
    while len(v_arr) < size:
        v_arr.append(0)
    return v_arr

def nibblize_str(v_str, size=None):
    v_arr = []
    for c in v_str:
        c_nibble = nibblize(ord(c))
        v_arr.append(c_nibble[0])
        v_arr.append(c_nibble[1])
    if size:
        while size > len(v_arr)/2:
            v_arr.append(0)
            v_arr.append(0)
            v_arr = v_arr[:size]
    return v_arr



## BINARY DECODING

def unnibblize(v_arr):
    v_arr = [hex(v)[2:] for v in reversed(v_arr)]
    v_hex_str = ''.join(v_arr)
    return int(v_hex_str, 16)

def unnibblize_str(v_arr):
    out = ""
    it=iter(v_arr)
    for v1, v2 in zip(it, it):
        v1 = hex(v1)[-1]
        v2 = hex(v2)[-1]
        v = v2 + v1
        out += chr(int(v, 16))
    return out



## FN ROUTING

def nibble_fn_for_type(t):
    if t == 'int':
        nibble_fn = nibblize
    elif t == 'str':
        nibble_fn = nibblize_str
    else:
        nibble_fn = nibblize
    return nibble_fn

def unnibble_fn_for_type(t):
    if t == 'int':
        unnibble_fn = unnibblize
    elif t == 'str':
        unnibble_fn = unnibblize_str
    else:
        unnibble_fn = unnibblize
    return unnibble_fn
