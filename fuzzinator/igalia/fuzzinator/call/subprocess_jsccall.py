# Copyright (c) 2021 Paulo Matos, Igalia S.L.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except

import logging
import os
import random
import string

from fuzzinator.call import NonIssue, SubprocessCall


# List of possible arguments for the call
# chosen randomly
JSC_MULTI_ARGS = ["--jitPolicyScale=0",
                  "--useJIT=false",
                  "--forceGCSlowPaths=true",
                  "--forceEagerCompilation=1",
                  "--useConcurrentGC=0",
                  "--useConcurrentJIT=0",
                  "--returnEarlyFromInfiniteLoopsForFuzzing=1 --earlyReturnFromInfiniteLoopsLimit=1000000",
                  "--verifyGC=true"]

class FormatPlaceholder:
    def __init__(self, key):
        self.key = key

    def __format__(self, spec):
        result = self.key
        if spec:
            result += ":" + spec
        return "{" + result + "}"

class FormatDict(dict):
    def __missing__(self, key):
        return FormatPlaceholder(key)

# Function executes exactly like SubprocessCall but adds,
# randomly arguments from JSC_MULTI_ARGS
def SubprocessJSCCall(command, cwd=None, env=None, no_exit_code=None, test=None,
                      timeout=None, **kwargs):
    # If we are reducing or validating, then kwargs will contain the
    # issues fields, and we add the options field before returning from
    # this function when an issue is found.
    # We check if options exists and if it does we use it, otherwise
    # we randomly select a set of options.
    if 'options' not in kwargs:
        # Add the args randomly
        options_list = random.sample(JSC_MULTI_ARGS,
                                 k=random.randint(0, len(JSC_MULTI_ARGS)))
                  
        # Build options
        options = ' '.join(options_list)
    else:
        options = kwargs['options']
        
    formatter = string.Formatter()
    
    # cannot use `.format` because it's partial
    # format: key 'test' is not yet defined
    mapping = FormatDict(options=options)
    command = formatter.vformat(command, (), mapping)

    issue = SubprocessCall(command, cwd, env, no_exit_code, test, timeout)
    if issue:
        kwargs['options'] = options

    # Call SubprocessCall
    return issue

