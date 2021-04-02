#!/bin/bash
# Copyright (c) Facebook, Inc. and its affiliates. All rights reserved.
set -ex

mkdir -p packaging/out

for PYTORCH_VERSION in 1.8.0
do
    for PV in 3.7 3.8
    do
        export CONDA_PYTORCH_CONSTRAINT="- pytorch>=$PYTORCH_VERSION"
        export PYTORCH_VERSION_NODOT=${PYTORCH_VERSION//./}
        PYTHON_VERSION=$PV bash packaging/build_conda.sh
    done
done

cd packaging/out
conda convert -p win-64 linux-64/*.tar.bz2
conda convert -p osx-64 linux-64/*.tar.bz2
cd -

ls -Rl packaging

for dir in  win-64 osx-64 linux-64
do
    this_out_dir=packaging/output_files/$dir
    mkdir -p $this_out_dir
    cp packaging/out/$dir/*.tar.bz2 $this_out_dir
done

ls -Rl packaging