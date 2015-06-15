#!/usr/bin/env bash


NAME="coastline"
RES=5000


rm input/*
rm done/*
rm temp/*

# Move prime-meridian
echo "${NAME}: Rotating prime meridian..."
./bin/flip.py \
    raw/${NAME}.shp \
    temp/${NAME}-flipped.geojson

# Reproject
echo "${NAME}: Reprojecting..."
ogr2ogr \
    input/${NAME}.geojson \
    raw/${NAME}.shp \
    -explodecollections \
    -wrapdateline \
    -progress \
    -clipsrc -179.9 -84.9 179.9 84.9 \
    -t_srs EPSG:3857 \
    -f GeoJSON
echo "${NAME}: Reprojecting flipped..."
ogr2ogr \
    input/${NAME}-flipped.geojson \
    temp/${NAME}-flipped.geojson \
    -explodecollections \
    -wrapdateline \
    -progress \
    -clipsrc -179.9 -84.9 179.9 84.9 \
    -t_srs EPSG:3857 \
    -f GeoJSON
exit
#./bin/reproject_vector.py \
#    raw/${NAME}.shp \
#    input/${NAME}.geojson
#echo "${NAME}: Reprojecting flipped..."
#./bin/reproject_vector.py \
#    temp/${NAME}-flipped.geojson \
#    input/${NAME}-flipped.geojson

# Rasterize
echo "${NAME}: Rasterizing..."
WIDTH_HEIGHT=$(./bin/get_height_width.py --res ${RES} --bbox $(fio info bbox.geojson --bounds))
gdal_rasterize \
    input/${NAME}.geojson \
    temp/burn-${NAME}.tif \
    -at \
    -burn 1 \
    -ot Byte \
    -co COMPRESS=DEFLATE \
    -co INTERLEAVE=BAND \
    -co BIGTIFF=YES \
    -co TILED=NO \
    -co PREDICTOR=2 \
    -te $(fio info bbox.geojson --bounds) \
    -ts ${WIDTH_HEIGHT}
echo "${NAME}: Rasterizing flipped..."
gdal_rasterize \
    input/${NAME}-flipped.geojson \
    temp/burn-${NAME}-flipped.tif \
    -at \
    -burn 1 \
    -ot Byte \
    -co COMPRESS=DEFLATE \
    -co INTERLEAVE=BAND \
    -co BIGTIFF=YES \
    -co TILED=NO \
    -co PREDICTOR=2 \
    -te $(fio info bbox.geojson --bounds) \
    -ts ${WIDTH_HEIGHT}

# Compute proximity
echo "${NAME}: Computing proximity..."
./bin/prox.sh \
    temp/burn-${NAME}.tif \
    temp/prox-${NAME}.tif
echo "${NAME}: Computing flipped proximity..."
./bin/prox.sh \
    temp/burn-${NAME}-flipped.tif \
    temp/prox-${NAME}-flipped.tif

# Merge
echo "${NAME}: Merging..."
./bin/merge.py \
    temp/prox-${NAME}-flipped.tif \
    temp/prox-${NAME}.tif \
    temp/merged-${NAME}.tif

# Reproject
echo "${NAME}: Warping..."
gdalwarp \
    temp/merged-${NAME}.tif \
    done/${NAME}.tif \
    -t_srs EPSG:4326 \
    -co COMPRESS=DEFLATE \
    -co INTERLEAVE=BAND \
    -co PREDICTOR=3 \
    -co BIGTIFF=YES \
    -co TILED=YES \
    -co ZLEVEL=9 \
    -multi \
    -wo NUM_THREADS=ALL_CPU

# Overview
echo "${NAME}: Overview..."
gdaladdo \
    -r nearest \
    done/${NAME}.tif \
        2 4 8 16 32 \
        --config COMPRESS DEFLATE \
        --config INTERLEAVE BAND \
        --config PREDICTOR 3 \
        --config BIGTIFF YES \
        --config TILED YES \
        --config ZLEVEL 9
