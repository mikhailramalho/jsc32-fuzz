# Copyright 2020 Paulo Matos, Igalia S.L.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Check which tests timeout."""

# Point this script to a folder with js files and a timeout,
# and it will recursively call JSC on the file and report if it times out.
# Timeouts are potential candidates for removal from the fuzzing set.

import glob
import sys
import os
import subprocess

timeout=int(sys.argv[1])
root=sys.argv[2]
print('Looking for JS files under {}'.format(root))
for fileloc in glob.iglob(os.path.join(root, '**', '*.js'), recursive=True):
    proc = subprocess.Popen(["jsc", fileloc], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        outs, errs = proc.communicate(timeout=timeout)
        print('{}: {}'.format(fileloc, proc.returncode))
    except subprocess.TimeoutExpired:
        print('{}: TIMEOUT'.format(fileloc))
        proc.kill()
        outs, errs = proc.communicate()

    
