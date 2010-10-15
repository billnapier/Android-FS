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

import os, stat, errno
# pull in some spaghetti to make this stuff work without fuse-py being installed
try:
    import _find_fuse_parts
except ImportError:
    pass
import fuse
from fuse import Fuse

import adb

MODE = 0
SIZE = 1
TIME = 2
NAME = 3

def parse_line(line):
    cols = line.split(' ')
    if len(cols) == NAME + 1:
        return {
            'name': cols[NAME],
            'mode': int(cols[MODE], 16),
            'size': int(cols[SIZE], 16),
            'time': int(cols[TIME], 16),
            }
    return None

if not hasattr(fuse, '__version__'):
    raise RuntimeError, \
        "your fuse-py doesn't know of fuse.__version__, probably it's too old."

fuse.fuse_python_api = (0, 2)

hello_path = '/hello'
hello_str = 'Hello World!\n'

class MyStat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0

class AdbFile(object):
    def __init__(self, a, path, flags, *mode):
        self.adb = a
        self.path = path
        self.data = self.adb.get_file(path)
        self.datalen = len(self.data)        

    def read(self, size, offset):
        if self.data:
            if offset < self.datalen:
                if offset + size > self.datalen:
                    size = self.datalen - offset
                return self.data[offset:offset+size]
        return -errno.ENOENT

class AndroidFS(Fuse):
    def __init__(self, *args, **kw):       
        Fuse.__init__(self, *args, **kw)

        self.adb = adb.Adb('/home/napier/bin/adb')

        class wrapped_file_class (AdbFile):
            def __init__(self2, *a, **kw):
                AdbFile.__init__(self2, self.adb, *a, **kw)
        
        self.file_class = wrapped_file_class

        self.cache = { }
    
    def get_entries(self, path):
        entries = self.cache.get(path, {})
        if not entries:
            for entry in self.adb.ls([path]).split('\n'):
                dir = parse_line(entry)
                if dir:
                    entries[dir['name']] = dir
            self.cache[path] = entries
        return entries

    def get_entry(self, path):
        dirname = os.path.dirname(path)
        filename = os.path.basename(path)
        entries = self.get_entries(dirname)
        return entries.get(filename, None)
           
    def getattr(self, path):
        st = MyStat()
        entry = self.get_entry(path)
        if entry:
            mode = entry['mode']
            st.st_mode = entry['mode']
            st.st_size = entry['size']
            st.st_atime = entry['time']
            st.st_mtime = entry['time']
            st.st_ctime = entry['time']
            return st            
        else:
            return -errno.ENOENT

    def readdir(self, path, offset):
        entries = self.get_entries(path)
        for (k, v) in entries.iteritems():
            yield fuse.Direntry(k)

def main():
    usage="""
Userspace hello example

""" + Fuse.fusage
    server = AndroidFS(version="%prog " + fuse.__version__,
                     usage=usage,
                     dash_s_do='setsingle')

    server.parse(errex=1)
    server.main()

if __name__ == '__main__':
    main()
