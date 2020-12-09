# Copyright (c) 2020 Paulo Matos, Igalia S.L
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os
import paramiko
import socket
import subprocess
import sys

from fuzzinator.config import as_bool, as_dict, as_pargs, as_path
from fuzzinator import Controller
from fuzzinator.call import NonIssue

logger = logging.getLogger(__name__)

def SubprocessRemoteCall(username, hostname, port, command, env=None, no_exit_code=None, test=None,
                   timeout=None, **kwargs):
    """
    Remote subprocess invocation-based call of a SUT that takes test input on its
    command line. (See :class:`fuzzinator.call.FileWriterDecorator` for SUTs
    that take input from a file.)

    **Mandatory parameter of the SUT call:**

      - ``username``: string containing the username to connect to the remote machine
      - ``hostname``: string containing the hostname of the remote machine where the call will take place.
      - ``port``: integer with port number used to connect to host
      - ``command``: string to pass to the child shell as a command to run (all
        occurrences of ``{test}`` in the string are replaced by the actual test
        input).

    **Optional parameters of the SUT call:**

      - ``env``: if not ``None``, a dictionary of variable names-values to
        update the environment with.
      - ``no_exit_code``: makes possible to force issue creation regardless of
        the exit code.
      - ``timeout``: run subprocess with timeout.

    **Result of the SUT call:**

      - If the child process exits with 0 exit code, no issue is returned.
      - Otherwise, an issue with ``'exit_code'``, ``'stdout'``, and ``'stderr'``
        properties is returned.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            call=fuzzinator.call.RemoteSubprocessCall

            [sut.foo.call]
            # assuming that {test} is something that can be interpreted by foo as
            # command line argument
            username=lilfuzz
            hostname=machine.away.com
            port=9999
            command=/home/alice/foo/bin/foo {test}
            env={"BAR": "1"}
    """
    env = {} if env is None else env
    no_exit_code = as_bool(no_exit_code)
    timeout = int(timeout) if timeout else None
    issue = {}

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.WarningPolicy())

    # Need to copy necessary artifacts to remote before executing
    # the call. Can we add a pre-execution step of sorts?
    
    try:
        client.connect(hostname, port=port, username=username)
        print("after connect", file=sys.stderr)
        cmd = command.format(test=test)
        
        print(f"executing {cmd} (env: {env}) with timeout {timeout} secs", file=sys.stderr)

        chan = client.get_transport().open_session(timeout=timeout)
        chan.settimeout(timeout)
        chan.update_environment(env)
        chan.exec_command(cmd)
        stdout = chan.makefile("r")
        stderr = chan.makefile_stderr("r")
        
        print("after exec_command", file=sys.stderr)
        returncode = chan.recv_exit_status()
        print(f"after getting returncode: {returncode}", file=sys.stderr) 
        # returncode might be -1 if no exit status is provided by the server, see
        # http://docs.paramiko.org/en/stable/api/channel.html#paramiko.channel.Channel.recv_exit_status

        # stdout and stderr are paramiko ChannelFile objects
        # with __repr__() methods
        logger.debug('%s\n%s', str(stdout), str(stderr))

        issue = {
            'exit_code': returncode,
            'stdout': str(stdout),
            'stderr': str(stderr),
        }
        print("issue: %s\n", issue)
        client.close()
        if no_exit_code or returncode != 0:
            return issue
    except socket.timeout:
        print("TIMEOUT", file=sys.stderr)
        logger.debug('Timeout expired in the SUT\'s remote subprocess runner.')
        client.close()

    return NonIssue(issue) if issue else None
