#!/usr/bin/env bash


gdal_proximity.py \
    ${1} ${2} \
    -distunits GEO \
    -ot Float32 \
    -co COMPRESS=DEFLATE \
    -co INTERLEAVE=BAND \
    -co TILED=NO \
    -co PREDICTOR=3 \
    -co BIGTIFF=YES
