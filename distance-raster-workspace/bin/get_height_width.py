#!/usr/bin/env python


import click


@click.command()
@click.option(
    '--bbox', nargs=4, type=click.FLOAT,
    help='Bounding box.'
)
@click.option(
    '--res', type=click.FLOAT,
    help='Desired resolution'
)
def main(bbox, res):

    """
    Compute the correct height/width for -ts.
    """

    x_min, y_min, x_max, y_max = bbox

    width = int((x_max - x_min) / res)
    if width % 2 is not 0:
        width += 1
        res = (x_max - x_min) / width
    height = int((y_max - y_min) / res)

    click.echo("%s %s" % (width, height))


if __name__ == '__main__':
    main()
