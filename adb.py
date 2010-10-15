#!/usr/bin/env python
# Copyright (C) 2010  Bill Napier <napier@google.com>
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

import os
import subprocess
import tempfile

def _run(args):
    return subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]

class Adb(object):
    def __init__(self, adb):
        self.adb = adb
        self.tmpdir = tempfile.mkdtemp()

    def _adb(self, args):
        return _run([self.adb] + args)

    def shell(self, args):
        return self._adb(['shell'] + args)

    def ls(self, args):
        return self._adb(['ls'] + args)

    def cat(self, args):
        return self.shell(['cat'] + args)

    def pull(self, args):
        return self._adb(['pull'] + args)        

    # This kind of sucks.  It would be much better to talk directly to
    # the adb server and use the sync commands to just pull the file
    # into memory instead of jumping through these hoops.
    def get_file(self, filename):
        local_name = os.path.join(self.tmpdir, filename[1:])
        self.pull([filename, local_name])
        f = open(local_name)
        data = f.read()
        f.close()
        return data

