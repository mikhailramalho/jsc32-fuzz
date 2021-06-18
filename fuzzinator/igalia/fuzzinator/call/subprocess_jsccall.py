# Copyright (c) 2021 Paulo Matos, Igalia S.L.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except

import logging
import os
import random

from fuzzinator.config import as_bool, as_dict, as_pargs, as_path
from fuzzinator import Controller
from fuzzinator.call import NonIssue, SubprocessCall

logger = logging.getLogger(__name__)

# List of possible arguments for the call
# chosen randomly
JSC_MULTI_ARGS = ["--jitPolicyScale=0",
                  "--forceEagerCompilation=1",
                  "--useConcurrentGC=0",
                  "--useConcurrentJIT=0",
                  "--returnEarlyFromInfiniteLoopsForFuzzing=1 --earlyReturnFromInfiniteLoopsLimit=1000000",
                  "--verifyGC=true"]

# Function executes exactly like SubprocessCall but adds,
# randomly arguments from JSC_MULTI_ARGS
def SubprocessJSCCall(binary, cwd=None, env=None, no_exit_code=None, test=None,
                      timeout=None, **kwargs):
    # Add the args randomly
    smp = random.sample(JSC_MULTI_ARGS,
                        k=random.randint(0, len(JSC_MULTI_ARGS)))
                  
    # Rebuild command
    newcommand = []
    newcommand.append(binary)
    newcommand += smp
    newcommand.append('{test}')
    newcommand = ' '.join(newcommand)
    
    # Call SubprocessCall
    issue = SubprocessCall(newcommand, cwd, env, no_exit_code, test, timeout)
    if issue: # a non-issue is always false
        issue['command'] = newcommand
        
    return issue

