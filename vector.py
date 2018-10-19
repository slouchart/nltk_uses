from math import sqrt


def vect_abs(vector):
    """Computes the L2 norm of a vector"""
    val = 0
    for component in vector:
        val += component ** 2

    return sqrt(val)


def scalar_product(vect1, vect2):
    """Assuming orthonormal base vectors, computes the dot (scalar) product of two vectors"""
    assert len(vect1) == len(vect2)

    j = 0
    sp = 0
    for component in vect1:
        sp += component * vect2[j]
        j += 1

    return sp


def cosine_similarity(vect1, vect2):
    """the scalar product of two vector from the same vector space is geometrically defined as
    u . v = cos(u, v) * |u| * |v|
    the cosine similarity extracts the cosine component from the scalar product divided by
    the product of the L2 norm of each vector"""
    return scalar_product(vect1, vect2) / (vect_abs(vect1) * vect_abs(vect2))


def non_zero_components(vect1):
    """extract all non zero components from otherwise very sparse vectors
    works as a generator"""
    j = 0
    for component in vect1:
        if component != 0.0:
            yield j, component
        j += 1
