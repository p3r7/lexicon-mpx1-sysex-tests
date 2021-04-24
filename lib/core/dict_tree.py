
from functools import reduce # only in Python 3
import operator



## ACCESSORS

def get_in(tree, path):
    return reduce(operator.getitem, path, tree)

def set_in(tree, path, value):
    get_in(tree, path[:-1])[path[-1]] = value
