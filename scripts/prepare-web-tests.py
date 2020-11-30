# Copyright 2019 Google LLC
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
"""Create public web tests package to use with js_fuzzer."""

# Before any other imports, we must fix the path. Some libraries might expect
# to be able to import dependencies directly, but we must store these in
# subdirectories of common so that they are shared with App Engine.
import os
import re
import subprocess
import time

def clone_git_repository(tests_directory, name, repo_url):
  """Clone a git repo."""
  print('Syncing %s tests.' % name)

  directory = os.path.join(tests_directory, name)
  if not os.path.exists(directory):
    subprocess.check_call(
        ['git', 'clone', '--depth=1', repo_url, name], cwd=tests_directory)

  if os.path.exists(directory):
    subprocess.check_call(['git', 'pull'], cwd=directory)
  else:
    raise Exception('Unable to checkout %s tests.' % name)


def checkout_svn_repository(tests_directory, name, repo_url):
  """Checkout a SVN repo."""
  print('Syncing %s tests.' % name)

  directory = os.path.join(tests_directory, name)
  if not os.path.exists(directory):
    subprocess.check_call(
        ['svn', 'checkout', repo_url, directory], cwd=tests_directory)

  if os.path.exists(directory):
    subprocess.check_call(['svn', 'update', directory], cwd=tests_directory)
  else:
    raise Exception('Unable to checkout %s tests.' % name)


def create_symbolic_link(tests_directory, source_subdirectory,
                         target_subdirectory):
  """Create symbolic link."""
  source_directory = os.path.join(tests_directory, source_subdirectory)
  target_directory = os.path.join(tests_directory, target_subdirectory)
  if not os.path.exists(source_directory):
    raise Exception('Unable to find source directory %s for symbolic link.' %
                    source_directory)

  if os.path.exists(target_directory):
    # Symbolic link already exists, bail out.
    return

  target_parent_directory = os.path.dirname(target_directory)
  if not os.path.exists(target_parent_directory):
    # Create parent dirs if needed, otherwise symbolic link creation will fail.
    os.makedirs(target_parent_directory)

  subprocess.check_call(['ln', '-s', source_directory, target_directory])

def strip_from_left(string, prefix):
  """Strip a prefix from start from string."""
  if not string.startswith(prefix):
    return string
  return string[len(prefix):]

def create_gecko_tests_directory(tests_directory, gecko_checkout_subdirectory,
                                 gecko_tests_subdirectory):
  """Create Gecko tests directory from a Gecko source checkout using links."""
  gecko_checkout_directory = os.path.join(tests_directory,
                                          gecko_checkout_subdirectory)
  if not os.path.exists(gecko_checkout_directory):
    raise Exception(
        'Unable to find Gecko source directory %s.' % gecko_checkout_directory)

  web_platform_sub_directory = 'testing%sweb-platform%s' % (os.sep, os.sep)
  for root, directories, _ in os.walk(gecko_checkout_directory):
    for directory in directories:
      if not re.match('.*tests?$', directory):
        continue

      directory_absolute_path = os.path.join(root, directory)
      sub_directory = strip_from_left(directory_absolute_path,
                                            gecko_checkout_directory + os.sep)
      source_subdirectory = gecko_checkout_subdirectory + os.sep + sub_directory
      target_subdirectory = gecko_tests_subdirectory + os.sep + sub_directory

      if sub_directory.startswith(web_platform_sub_directory):
        # Exclude web-platform tests already included in blink layout tests.
        continue

      create_symbolic_link(tests_directory, source_subdirectory,
                           target_subdirectory)


def main():
  """Main sync routine."""
  tests_archive_name = os.getenv('TESTS_ARCHIVE_NAME')
  tests_directory = os.getenv('TESTS_DIR')

  if not os.path.exists(tests_directory):
    os.mkdir(tests_directory)

  # Sync web tests.
  print('Syncing web tests.')
  src_directory = os.path.join(tests_directory, 'src')
  gclient_file_path = os.path.join(tests_directory, '.gclient')
  if not os.path.exists(gclient_file_path):
    subprocess.check_call(
        ['fetch', '--no-history', 'chromium', '--nosvn=True'],
        cwd=tests_directory)
  if os.path.exists(src_directory):
    subprocess.check_call(['gclient', 'revert'], cwd=src_directory)
    subprocess.check_call(['git', 'pull'], cwd=src_directory)
    subprocess.check_call(['gclient', 'sync'], cwd=src_directory)
  else:
    raise Exception('Unable to checkout web tests.')

  clone_git_repository(tests_directory, 'v8',
                       'https://chromium.googlesource.com/v8/v8')

  clone_git_repository(tests_directory, 'ChakraCore',
                       'https://github.com/Microsoft/ChakraCore.git')

  clone_git_repository(tests_directory, 'gecko-dev',
                       'https://github.com/mozilla/gecko-dev.git')

  clone_git_repository(tests_directory, 'webgl-conformance-tests',
                       'https://github.com/KhronosGroup/WebGL.git')

  checkout_svn_repository(
      tests_directory, 'WebKit/LayoutTests',
      'http://svn.webkit.org/repository/webkit/trunk/LayoutTests')

  checkout_svn_repository(
      tests_directory, 'WebKit/JSTests/stress',
      'http://svn.webkit.org/repository/webkit/trunk/JSTests/stress')

  checkout_svn_repository(
      tests_directory, 'WebKit/JSTests/es6',
      'http://svn.webkit.org/repository/webkit/trunk/JSTests/es6')

  create_gecko_tests_directory(tests_directory, 'gecko-dev', 'gecko-tests')

  tests_archive_local = os.path.join(tests_directory, tests_archive_name)
  if os.path.exists(tests_archive_local):
    os.remove(tests_archive_local)
  create_symbolic_link(tests_directory, 'gecko-dev/js/src/tests',
                       'spidermonkey')
  create_symbolic_link(tests_directory, 'ChakraCore/test', 'chakra')

  # FIXME: Find a way to rename LayoutTests to web_tests without breaking
  # compatability with older testcases.
  create_symbolic_link(tests_directory, 'src/third_party/blink/web_tests',
                       'LayoutTests')

  subprocess.check_call(
      [
          'zip',
          '-r',
          tests_archive_local,
#          'CrashTests',
          'LayoutTests',
          'WebKit',
          'gecko-tests',
          'v8/test/mjsunit',
          'spidermonkey',
          'chakra',
          'webgl-conformance-tests',
          '-x',
          '*.cc',
          '-x',
          '*.cpp',
          '-x',
          '*.py',
          '-x',
          '*.txt',
          '-x',
          '*-expected.*',
          '-x',
          '*.git*',
          '-x',
          '*.svn*',
      ],
      cwd=tests_directory)

if __name__ == '__main__':
  main()
