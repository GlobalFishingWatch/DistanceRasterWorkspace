#!/usr/bin/env python


import click
import math
import numpy as np
import rasterio as rio


@click.command()
@click.argument('flipped')
@click.argument('normal')
@click.argument('outfile')
def main(flipped, normal, outfile):

    with rio.open(flipped) as flip, rio.open(normal) as norm:
        assert flip.shape == norm.shape

        height, width = flip.shape

        meta = {
            'count': 1,
            'driver': 'GTiff',
            'height': height,
            'width': width,
            'nodata': -9999,
            'dtype': rio.float32,
            'TILED': 'NO',
            'COMPRESS': 'DEFLATE',
            'INTERLEAVE': 'BAND',
            'BIGTIFF': 'YES',
            'PREDICTOR': '3',
            'crs': flip.crs,
            'affine': flip.affine,
            'transform': rio.guard_transform(flip.affine)
        }
        with rio.open(outfile, 'w', **meta) as dst:
            length = len([i for i in flip.block_windows()])
            with click.progressbar(flip.block_windows(), length=length) as block_windows:
                for block, window in block_windows:
                    flip_row = flip.read(indexes=1, window=window)
                    norm_row = norm.read(indexes=1, window=window)
                    mid_point = flip_row.shape[1] / 2
                    reversed_row = np.concatenate(
                        (flip_row[0][mid_point:], flip_row[0][:mid_point])
                    )

                    out = np.minimum(reversed_row, norm_row)

                    block_affine = dst.window_transform(window)
                    rlat = block_affine.c * math.pi / 180

                    dst.write(out, indexes=1, window=window)


if __name__ == '__main__':
    main()
