# Copyright (c) 2020 Paulo Matos, Igalia S.L
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os
import paramiko
import tempfile

from fuzzinator.config import as_path
from fuzzinator.call import CallableDecorator


class RemoteFileWriterDecorator(CallableDecorator):
    """
    Decorator for SUTs that take input from a file: writes the test input to a
    temporary file and replaces the test input with the name of that file.

    **Mandatory parameter of the decorator:**

      - ``username``: string containing the username to connect to the remote machine
      - ``hostname``: string containing the hostname of the remote machine where the call will take place.
      - ``port``: integer with port number used to connect to host
      - ``filename``: path pattern for the temporary file, which may contain the
        substring ``{uid}`` as a placeholder for a unique string (replaced by
        the decorator).

    The issue returned by the decorated SUT (if any) is extended with the new
    ``'filename'`` property containing the name of the generated file (although
    the file itself is removed).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            call=fuzzinator.call.RemoteSubprocessCall
            call.decorate(0)=fuzzionator.call.RemoteFileWriterDecorator

            [sut.foo.call]
            # assuming that foo takes one file as input specified on command line
            command=/home/alice/foo/bin/foo {test}

            [sut.foo.call.decorate(0)]
            username=lilfuzz
            hostname=machine.away.com
            port=9999
            filename=${fuzzinator:work_dir}/test-{uid}.txt
    """

    def decorator(self, filename, username, hostname, port, **kwargs):
        def wrapper(fn):
            def writer(*args, **kwargs):
                # Create temporary file locally
                file_content = kwargs['test']
                local_file_path = None
                with tempfile.NamedTemporaryFile(delete=False) as t:
                    t.write(file_content)
                    local_file_path = t.name

                # Copy temporary local to remote
                remote_file_path = as_path(filename.format(uid='{pid}-{id}'.format(pid=os.getpid(), id=id(self))))
                if 'filename' in kwargs:
                    # Ensure that the test case will be saved to the directory defined by the
                    # config file and its name will be what is expected by the kwargs.
                    remote_file_path = os.path.join(os.path.dirname(file_path), kwargs['filename'])

                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.WarningPolicy())
                client.connect(hostname, port=port, username=username)

                sftp = client.open_sftp()
                attrs = sftp.put(local_file_path, remote_file_path)
                print(f"file copied to remote with size {attrs.st_size}") 
                
                sftp.close()
                client.close()
                    
                # Remove local temporary
                os.remove(local_file_path)
                
                # Create issue
                kwargs['test'] = remote_file_path
                issue = fn(*args, **kwargs)
                if issue is not None:
                    issue['filename'] = os.path.basename(remote_file_path)

                # Remove remote file
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.WarningPolicy())
                client.connect(hostname, port=port, username=username)

                sftp = client.open_sftp()
                sftp.remove(remote_file_path)

                sftp.close()
                client.close()
                return issue

            return writer
        return wrapper
