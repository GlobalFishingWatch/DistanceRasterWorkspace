#!/usr/bin/env python


import functools
import itertools as it
import math
import multiprocessing as mp
import os
import subprocess

import affine
import click
import fiona as fio
import numpy as np
import pyproj
import rasterio as rio
from rasterio.errors import RasterioIOError
from rasterio.rio import options as rio_options
from scipy.ndimage.morphology import binary_erosion


def _cb_res(ctx, value, param):
    if not param or len(param) == 2:
        return param
    elif len(param) == 1:
        return param[0], param[0]
    else:
        raise click.BadParameter("can only supply once or twice")


def _cb_nodata(ctx, value, param):
    if value.lower() == 'none':
        return None
    else:
        try:
            return float(value)
        except ValueError:
            raise click.BadParameter(
                "could not convert to float: {}".format(value))


def runner(func, tasks, jobs):
    if jobs == 1:
        return map(func, tasks)
    else:
        return mp.Pool(jobs).imap_unordered(func, tasks)


def index2coord(idx, transform):
    return reversed(idx) * transform


def _mp_edge_coords(kwargs):

    data = kwargs['data']
    transform = kwargs['transform']

    if data.max() == 0:
        return None
    else:

        p = np.pad(data, 1, mode='constant', constant_values=0)

        edges = (p ^ binary_erosion(p)).astype(np.ubyte)
        edges = edges[1:-1, 1:-1]
        edges[0] = 0
        edges[-1] = 0
        edges[:, 0] = 0
        edges[:, -1] = 0

        edge_indexes = np.vstack(np.nonzero(edges)).transpose()

        translate = functools.partial(index2coord, transform=transform)
        return np.apply_along_axis(translate, 1, edge_indexes)


def _mp_distance(kwargs):
    data = kwargs['data']
    geod = kwargs['geod']
    transform = kwargs['transform']
    edge_coords = kwargs['edge_coords']
    nodata = kwargs['nodata']
    dtype = kwargs['dtype']

    if data.min() > 0:
        nd = np.empty(data.shape, dtype=dtype)
        nd.fill(nodata)
        return nd
    else:

        out = np.zeros(data.shape, dtype=dtype)

        # Take the input raster data, and make water 1 and non-water 0
        # Convert to an array of `(row, col)` arrays
        # Convert to an array of `(lon, lat)` arrays
        data = data.astype(np.bool).astype(np.ubyte)
        data = np.vstack(np.nonzero(data)).transpose()
        data = np.apply_along_axis(
            functools.partial(index2coord, transform=transform),
            1,
            data)

        print("")
        print("-=-=-=-=-=-")
        print(edge_coords.shape)
        lons2 = edge_coords[0]
        lats2 = edge_coords[1]

        for lon, lat in data:

            lons1 = np.empty(lons2.shape)
            lons1.fill(lon)

            lats1 = np.empty(lats2.shape)
            lats1.fill(lat)

            print("")
            print("-=-=-=-=-=-")
            print(lons2.shape)
            print(lats2.shape)
            print(lons1.shape)
            print(lats1.shape)

            distances = geod.inv(
                lons1=lons1,
                lats1=lats1,
                lons2=lons2,
                lats2=lats2)[2]

            print("")
            print("-=-=-=-=-=-")
            print(distances)
            import time
            time.sleep(10000)

            min_idx = np.argmin(distances)
            n_coords = edge_coords[min_idx]
            nc, nr = transform * n_coords
            out[nr][nc] = distances[min_idx].item()

        return out


@click.command()
@click.argument('infiles', nargs=-1)
@click.option(
    '--outfile', '-o', required=True,
    help="Output datasource.")
@click.option(
    '--res', multiple=True, type=click.FLOAT, default=None, callback=_cb_res,
    help="Output dataset resolution in units of coordinate "
         "reference system. Pixels assumed to be square if this option "
         "is used once, otherwise use: "
         "--res pixel_width --res pixel_height.")
@click.option(
    '--shape', nargs=2, type=click.INT, default=None,
    help="Output datasource shape in rows and columns.")
@click.option(
    '--bounds', nargs=4, type=click.FLOAT, default=(-180, -90, 180, 90),
    show_default=True,
    help="Target datasource bounds.")
@click.option(
    '--crs', default='EPSG:4326', show_default=True,
    help="Target spatial reference system.")
@click.option(
    '--all-touched', is_flag=True,
    help="Enable 'all touched' rasterization.")
@click.option(
    '--driver', metavar='NAME', default='GTiff', show_default=True,
    help="Output raster driver.")
@click.option(
    '--blocksize', type=click.INT, default=256, show_default=True,
    help="Raster block size for windowed processing.  Driver must support "
         "internal tiling.")
@click.option(
    '--dtype', type=click.Choice([rio.float32, rio.float64]),
    default=rio.float32, show_default=True,
    help="Output data type.")
@click.option(
    '--scale', type=click.FLOAT, default=None, show_default=True,
    help="Scale output values by this factor.  Useful for converting units.  "
         "By default output values are meters.")
@click.option(
    '--nodata', type=click.FLOAT, default=-9999, show_default=True,
    help="Output nodata value.  Use 'None' to disable.")
@click.option(
    '--jobs', type=click.IntRange(1, mp.cpu_count()), default=1, show_default=1,
    help="Process data across N cores.  Each core operates on a single window.")
@rio_options.creation_options
def cli(
        infiles, outfile, res, shape, crs, bounds, all_touched, driver,
        blocksize, creation_options, dtype, scale, nodata, jobs):

    """
    Compute a global distance raster that wraps the dateline.
    """

    # try:
    #     with rio.open(outfile) as src:
    #         raise click.ClickException("Output datasource exists.")
    # except RasterioIOError:
    #     pass

    xmin, ymin, xmax, ymax = bounds
    creation_options = {
        k.upper(): v.upper() for k, v in creation_options.items()}
    creation_options.update(
        BLOCKXSIZE=blocksize,
        BLOCKYSIZE=blocksize,
        TILED='YES')

    if res and not shape:
        xres, yres = res
        width = int(math.ceil((xmax - xmin) / xres))
        height = int(math.ceil((ymax - ymin) / yres))
    elif shape and not res:
        height, width = shape
        xres = (xmax - xmin) / width
        yres = (ymax - ymin) / width
    else:
        raise click.ClickException("need '--res' or '--shape'")

    transform = affine.Affine(xres, 0.0, xmin,
                              0.0, -yres, ymax)

    if os.path.exists(outfile):
        print("Skipping rasterize")
    else:
        for ds in infiles:
            for layer in fio.listlayers(ds):
                print("Rasterizing {}:{}".format(ds, layer))
                cmd = [
                    'gdal_rasterize',
                    '-q',
                    ds, '-l', layer,
                    outfile,
                    '-of', driver,
                    '-tap',
                    '-tr', str(xres), str(yres),
                    '-burn', '1',
                    '-ot', 'Byte',
                    '-co', 'BLOCKXSIZE={}'.format(blocksize),
                    '-co', 'BLOCKYSIZE={}'.format(blocksize),
                    '-co', 'BIGTIFF=IF_NEEDED',
                    '-co', 'INTERLEAVE=BAND',
                    '-co', 'COMPRESS=DEFLATE',
                    '-co', 'NBITS=1'
                ]
                cmd.extend(['-te'] + list(map(str, bounds)))
                if all_touched:
                    cmd.append('-at')
                result = subprocess.check_output(cmd)
                if result:
                    print(result)

    with rio.open(outfile, 'r+') as src:

        tasks = ({
            'data': src.read(1, window=window),
            'transform': src.window_transform(window)
        } for _, window in src.block_windows())

        num_windows = len(list(src.block_windows()))
        with click.progressbar(tasks, length=num_windows) as proc:
            results = filter(
                lambda x: x is not None,
                runner(_mp_edge_coords, proc, jobs))
            first = next(results)

            # raise ValueError("The append below is jacked")
            edge_coords = functools.reduce(
                functools.partial(np.append, axis=0),
                results)

        geod = pyproj.Geod(ellps='WGS84')
        tasks = ({
            'data': src.read(1, window=window),
            'geod': geod,
            'transform': src.window_transform(window),
            'edge_coords': edge_coords,
            'nodata': nodata,
            'dtype': dtype
        } for block, window in src.block_windows())

        with click.progressbar(tasks, length=num_windows) as proc:
            results = runner(_mp_distance, proc, jobs)
            print("-=-=-=-=-=-=-")
            print(next(results))
            return

        profile = {
            'height': height,
            'width': width,
            'nodata': nodata,
            'dtype': dtype,
            'crs': crs,
            'count': 1,
            'driver': driver,
            'transform': transform
        }
        profile.update(**creation_options)


if __name__ == '__main__':
    cli()
