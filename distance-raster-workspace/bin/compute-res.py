#!/usr/bin/env python


from __future__ import division

import click
import fiona as fio


def cell_size(minimum, maximum, res):

    return int((maximum - minimum) / res)



@click.command()
@click.argument('infile')
@click.argument('res', type=click.FLOAT, callback=lambda c, p, v: abs(v))
@click.option(
    '--bbox', callback=lambda c, p, v: tuple([float(c) for c in v.split(' ')]) if v else None
)
def main(infile, res, bbox):

    with fio.open(infile) as src:
        x_min, y_min, x_max, y_max = bbox if bbox else src.bounds

    x_res = res
    y_res = res

    width = cell_size(x_min, x_max, x_res)
    height = cell_size(y_min, y_max, y_res)

    # Make sure the width is divisible by 2
    # Pixel height must also be adjusted to keep square pixels
    if width % 2 is not 0:
        width += 1
        x_res = (x_max - x_min) / width
        y_res = x_res

    width = cell_size(x_min, x_max, x_res)
    height = cell_size(y_min, y_max, y_res)

    click.echo("{0} {1}".format(height, width))
    click.echo("{x_res} {y_res}".format(x_res=x_res, y_res=y_res))


if __name__ == '__main__':
    main()
