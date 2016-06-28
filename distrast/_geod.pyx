"""Geod representation"""


from distrast cimport _proj4

cdef class Geod:

    cdef _proj4.geod_geodesic geod

    def distance(self, double lon, double lat):
        pass
