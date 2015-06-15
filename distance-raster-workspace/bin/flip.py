#!/usr/bin/env python


from copy import deepcopy

import click
import fiona as fio
from shapely.affinity import translate
from shapely.geometry import shape
from shapely.geometry import asShape
from shapely.geometry import Polygon
from shapely.geometry import mapping

import gj2ascii


bbox = Polygon([[-180, -85], [-180, 85], [180, 85], [180, -85]])


@click.command()
@click.argument('infile')
@click.argument('outfile')
@click.option(
    '-f', '--format', '--driver', metavar='NAME', default='GeoJSON',
    help='Output format name.'
)
def main(infile, outfile, driver):

    with fio.open(infile) as src:
        meta = src.meta
        meta['driver'] = driver

    with fio.open(infile) as src, fio.open(outfile, 'w', **meta) as dst:
        with click.progressbar(src) as features:
            for feat in features:

                east = deepcopy(feat)
                west = deepcopy(feat)

                east_geom = shape(east['geometry'])
                west_geom = shape(west['geometry'])

                # if 'Point' not in asShape(feat['geometry']).type:
                #     east_geom = east_geom.simplify(0.0001).buffer(0)
                #     west_geom = west_geom.simplify(0.0001).buffer(0)

                east_geom = translate(east_geom, xoff=180)
                west_geom = translate(west_geom, xoff=-180)

                if not east_geom.is_empty:
                    east['geometry'] = mapping(east_geom)
                    dst.write(east)

                if not west_geom.is_empty:
                    west['geometry'] = mapping(west_geom)
                    dst.write(west)


if __name__ == '__main__':
    main()
