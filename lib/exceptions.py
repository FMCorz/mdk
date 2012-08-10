#!/usr/bin/env python
# -*- coding: utf-8 -*-

class BackupDirectoryExistsException(Exception):
    pass

class BackupDBExistsException(Exception):
    pass

class BackupDBEngineNotSupported(Exception):
    pass
