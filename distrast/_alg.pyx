#cython: boundscheck=False, wraparound=False, nonecheck=False


import numpy as np
cimport numpy as np

from distrast cimport _proj4


def _looper(float[:, :] data, float[:, :] edges, float nodata):

    cdef float[:] distances = np.empty(data.shape[0], dtype=np.float32)
    cdef float wx
    cdef float wy
    cdef float ex
    cdef float ey
    cdef int w
    cdef int e
    cdef float dist
    cdef float comp_dist
    geod = pyproj.Geod(ellps='WGS84')

    for w in range(data.shape[0]):
        wx = data[w, 0]
        wy = data[w, 1]
        dist = -1
        for e in range(edges.shape[0]):
            ex = edges[e, 0]
            ey = edges[e, 1]
            try:
                comp_dist = geod.inv(
                    lons1=wx,
                    lats1=wy,
                    lons2=ex,
                    lats2=ey)[2]
            except ValueError:
                comp_dist = nodata

            if comp_dist == -1 and dist != nodata:
                dist = comp_dist
            elif dist < comp_dist:
                dist = comp_dist

        distances[w] = dist

    return np.asarray(distances)


def _orig_looper(float[:, :] data, float[:, :] edges):

    cdef float[:] distances = np.empty(data.shape[0], dtype=np.float32)
    cdef float wx
    cdef float wy
    cdef float ex
    cdef float ey
    cdef int w
    cdef int e
    cdef float dist = 1.23

    with nogil:
        for w in range(data.shape[0]):
            wx = data[w, 0]
            wy = data[w, 1]
            for e in range(edges.shape[0]):
                ex = edges[e, 0]
                ey = edges[e, 1]
                distances[w] = dist

    return np.asarray(distances)
