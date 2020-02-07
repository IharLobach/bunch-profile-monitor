def length_output(val):
    if isinstance(val,float) or isinstance(val,int):
        return "{:.3f}".format(val)
    if isinstance(val,str):
        return val
    else:
        raise TypeError