# -*- coding: utf-8 -*-

# Resource object code
#
# Created by: The Resource Compiler for PyQt5 (Qt v5.15.1)
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore

qt_resource_data = b"\
\x00\x00\x00\x98\
\x89\
\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d\x49\x48\x44\x52\x00\
\x00\x00\x19\x00\x00\x00\x0b\x08\x06\x00\x00\x00\x8a\xf7\x26\xf3\
\x00\x00\x00\x04\x73\x42\x49\x54\x08\x08\x08\x08\x7c\x08\x64\x88\
\x00\x00\x00\x4f\x49\x44\x41\x54\x38\x8d\x63\x70\x70\x70\xf8\xcf\
\xc0\xc0\x40\x33\xec\xe0\xe0\xf0\x9f\x85\x01\x0a\xea\x8d\x19\xa8\
\x0e\x1a\xcf\x32\x30\x1c\x38\x70\x80\x81\x89\xfa\x46\x23\x00\xcc\
\xe1\x34\xb5\x04\x06\x46\x2d\x19\xc4\x96\x34\x9e\xa5\x9d\x25\x8c\
\xd0\xcc\xc8\x70\xe0\xc0\x01\x9a\x59\x02\xcf\x8c\x0e\x0e\x0e\x34\
\xb3\x04\x00\xe7\x39\x25\x7e\x68\x38\xf0\x69\x00\x00\x00\x00\x49\
\x45\x4e\x44\xae\x42\x60\x82\
"

qt_resource_name = b"\
\x00\x07\
\x02\xba\x65\x26\
\x00\x6c\
\x00\x65\x00\x64\x00\x5f\x00\x6f\x00\x66\x00\x66\
\x00\x0b\
\x05\x2c\x23\x87\
\x00\x6c\
\x00\x65\x00\x64\x00\x5f\x00\x6f\x00\x66\x00\x66\x00\x2e\x00\x70\x00\x6e\x00\x67\
"

qt_resource_struct_v1 = b"\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x01\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x02\
\x00\x00\x00\x14\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\
"

qt_resource_struct_v2 = b"\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x01\
\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x02\
\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x14\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\
\x00\x00\x01\x7f\x5b\x4f\xba\x10\
"

qt_version = [int(v) for v in QtCore.qVersion().split('.')]
if qt_version < [5, 8, 0]:
    rcc_version = 1
    qt_resource_struct = qt_resource_struct_v1
else:
    rcc_version = 2
    qt_resource_struct = qt_resource_struct_v2

def qInitResources():
    QtCore.qRegisterResourceData(rcc_version, qt_resource_struct, qt_resource_name, qt_resource_data)

def qCleanupResources():
    QtCore.qUnregisterResourceData(rcc_version, qt_resource_struct, qt_resource_name, qt_resource_data)

qInitResources()