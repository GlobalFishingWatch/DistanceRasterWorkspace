#!/usr/bin/env python


import click
import fiona as fio
from fiona.transform import transform_geom
from shapely.geometry import mapping
from shapely.geometry import Polygon
from shapely.geometry import shape


@click.command()
@click.argument('infile')
@click.argument('outfile')
def main(infile, outfile):

    """
    Reproject a layer to web mercator.
    """

    # Cache stuff we need later
    bbox = Polygon([[-180, -85], [-180, 85], [180, 85], [180, -85]])
    with fio.open(infile) as src:
        meta = src.meta.copy()
        meta['crs'] = 'EPSG:3857'
        meta['driver'] = 'GeoJSON'

    with fio.open(infile) as src, fio.open(outfile, 'w', **meta) as dst, click.progressbar(src) as features:

        for feat in features:

            geom = shape(feat['geometry'].copy()).intersection(bbox)

            feat['geometry'] = transform_geom(src.crs, dst.crs, mapping(geom))
            dst.write(feat)


if __name__ == '__main__':
    main()
