#!/bin/bash

# Copyright (c) 2021 Paulo Matos, Igalia S.L.
#
# Licensed under the BSD 3-Clause License
# <LICENSE-BSD-3-Clause.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except according to
# those terms.

PREFIX=$1

${PREFIX} Tools/Scripts/set-webkit-configuration --asan --debug --force-optimization-level=O3
${PREFIX} Tools/Scripts/build-jsc --jsc-only

