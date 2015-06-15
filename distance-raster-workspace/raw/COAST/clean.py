#!/usr/bin/env python


import click
import fiona as fio
import gj2ascii
from pprint import pprint
from shapely.geometry import Polygon
from shapely.geometry import shape
# from osgeo import ogr
# ogr.UseExceptions()



@click.command()
@click.argument('infile')
@click.argument('outfile')
def main(infile, outfile):

    with fio.open(infile) as src, click.progressbar(src) as features:
        for feat in features:
            geom = shape(feat['geometry'])
            if not geom.is_closed:
                print(gj2ascii.render(geom))
                print(geom.is_valid)
                print(geom.is_simple)
                print(geom.coords[0])
                print(geom.coords[-1])
                return


# @click.command()
# @click.argument('infile')
# @click.argument('outfile')
# def main(infile, outfile):
#
#
#     ids = ogr.Open(infile)
#     ilayer = ids.GetLayer()
#     ids


if __name__ == '__main__':
    main()
