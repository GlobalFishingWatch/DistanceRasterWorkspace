#!/usr/bin/env python


from __future__ import division

import affine
import click
import fiona as fio
import numpy as np
import rasterio as rio
from rasterio.features import rasterize


@click.command()
@click.argument('infile')
@click.argument('outfile')
@click.option(
    '--res', type=click.FLOAT, required=True,
    help='Output raster resolution.'
)
@click.option(
    '--bbox', nargs=4, type=click.FLOAT, required=True,
    help='Only process data within this window.'
)
def main(infile, outfile, bbox, res):

    """
    Rasterize vector with constraints.
    """

    x_min, y_min, x_max, y_max = bbox

    width = int((x_max - x_min) / res)
    if width % 2 is not 0:
        width += 1
        res = (x_max - x_min) / width
    height = int((y_max - y_min) / res)

    with fio.open(infile) as src:
        aff = affine.Affine(res, 0.0, x_min,
                            0.0, -res, y_max)
        meta = {
            'driver': 'GTiff',
            'count': 1,
            'crs': src.crs,
            'affine': aff,
            'transform': rio.guard_transform(aff),
            'COMPRESS': 'DEFLATE',
            'INTERLEAVE': 'BAND',
            'BIGTIFF': 'YES',
            'TILED': 'NO',
            'PREDICTOR': '2',
            'dtype': rio.ubyte,
            'nodata': None,
            'width': width,
            'height': height
        }

        print(width)
        print(height)
        exit()

    with fio.open(infile) as src, rio.open(outfile, 'w', **meta) as dst:
        length = len([i for i in dst.block_windows()])
        with click.progressbar(dst.block_windows(), length=length) as block_windows:
            for _, window in block_windows:
                aff = dst.window_transform(window)
                ((row_min, row_max), (col_min, col_max)) = window
                x_min, y_min = aff * (col_min, row_max)
                x_max, y_max = aff * (col_max, row_min)
                data = np.zeros((row_max - row_min, col_max - col_min))
                try:
                    data = rasterize(
                        shapes=(feat['geometry'] for feat in src.filter(bbox=(x_min, y_min, x_max, y_max))),
                        fill=0,
                        out=data,
                        transform=aff,
                        all_touched=True,
                        default_value=1,
                        dtype=dst.meta['dtype']
                    )
                except ValueError:
                    pass
                dst.write(data, window=window)

"""
rasterize(
    shapes,
    out_shape=None,
    fill=0,
    out=None,
    output=None,
    transform=Affine(1.0, 0.0, 0.0, 0.0, 1.0, 0.0),
    all_touched=False,
    default_value=1,
    dtype=None
)
"""




if __name__ == '__main__':
    main()
