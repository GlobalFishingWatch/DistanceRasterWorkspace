#!/usr/bin/env python


"""
Clean up geometries
"""


import click
import fiona as fio
from shapely import wkt
from shapely.geometry import mapping
from shapely.geometry import shape
try:
    from osgeo import ogr
except ImportError:
    import ogr
ogr.UseExceptions()


def gj2geom(geojson):

    """
    Convert a GeoJSON geometry into an OGR geometry.
    """

    return ogr.CreateGeometryFromWkt(wkt.dumps(shape(geojson)))


def geom2gj(geometry):

    """
    Convert an OGR geometry into a GeoJSON geometry.
    """

    return mapping(wkt.loads(geometry.ExportToWkt()))


@click.command()
@click.argument('infile')
@click.argument('outfile')
def main(infile, outfile):

    with fio.drivers():
        with fio.open(infile) as src, \
                fio.open(outfile, 'w', **src.meta) as dst, \
                click.progressbar(src) as features:
            for feat in features:
                ogr_geom = gj2geom(feat['geometry'])
                ogr_geom.CloseRings()
                feat['geometry'] = geom2gj(ogr_geom)
                dst.write(feat)


if __name__ == '__main__':
    main()
