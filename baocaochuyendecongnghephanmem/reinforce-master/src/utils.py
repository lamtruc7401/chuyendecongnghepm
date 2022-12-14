import math
from collections import defaultdict
import copy
import numpy as np
import constants


def dotProduct(a, b):
    """ dot product of two vectors """
    return sum(x * y for (x, y) in zip(a, b))


def magnitude(a):
    """ magnitude of vector """
    return math.sqrt(dotProduct(a, a))


def distance(a, b):
    """distance of two points in space"""
    return math.sqrt(sum((y-x)**2 for x, y in zip(a, b)))


def normalize(vec):
    """ normalize vec to unit vector:  ||vec'|| = 1 """
    return [x * 1.0 / magnitude(vec) for x in vec]


def angle(vec):
    """ angle of vector in degrees (compared with [0, 1]) """
    a = angleBetween([0, 1], vec)
    return 360 - a if vec[0] < 0 else a


def angleBetween(a, b):
    """angle between two vectors"""
    a = normalize(a)
    b = normalize(b)
    return math.degrees(math.acos(dotProduct(a, b) / (magnitude(a) * magnitude(b))))


def combine(c, x1, d, x2):
    """linear combination of two sparse vectors: c(x1) + d(x2)
    """
    out = x1
    if c == 1:
        for f, v in x2.iteritems():
            out[f] = out[f] + d * v
            if math.isnan(out[f]):
                raise
    else:
        for f in set(x1.keys()) | set(x2.keys()):
            out[f] = (c * x1[f]) + (d * x2[f])
            if math.isnan(out[f]):
                raise
    return out


def discretizeLocation(x, y):
    """converts continuous coordinates in R^2 to discrete location measurement 

    does so by converting game board to grid of 10x10 pixel squares, then
      gives the index of the square that (x, y) is in
    """
    row_delta = constants.SCREEN_SIZE[0] / 10
    col_delta = constants.SCREEN_SIZE[1] / 10
    x_grid = x / row_delta
    y_grid = y / col_delta
    return x_grid + y_grid * 10


def discretizeAngle(vec):
    """buckets the continuous angle of a vector into one of 16 discrete angle categories
    """
    return int(utils.angle(vec) / 10)


def set_bit(bv, i):
    """sets bit i of a bit vector"""
    return bv | (1 << i)


def serializeBinaryVector(vec, use_bricks=False):
    """serializes a binary sparse vector"""
    if use_bricks:
        return '|'.join(sorted(vec.keys()))
    else:
        return '|'.join(k for k in sorted(vec.keys()) if 'brick' not in k)


def serializeList(l):
    """serializes list"""
    return tuple(sorted(l))


def deserializeAction(a):
    """deserializes a list"""
    return list(a)


def allSame(l):
    """test if all elements of l are identical"""
    return all(x == l[0] for x in l)


def dictToNpMatrix(d):
    """converts python dict to np matrix"""
    return np.asmatrix([d[k] for k in sorted(d)])


def sigmoid(x):
    """sigmoid function"""
    return 1.0 / (1 + math.exp(-x))
