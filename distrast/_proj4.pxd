"""Proj.4 interface"""


cdef extern from "geodesic.h":

    struct geod_geodesic:
        pass

    void geod_init(geod_geodesic* g, double a, double f)

    void geod_inverse(geod_geodesic* g,
            double lat1, double lon1, double lat2, double lon2,
            double* ps12, double* pazi1, double* pazi2)
