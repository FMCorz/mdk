Custom scripts
==============

This directory is meant to host scripts to be run on an instance. They are called using the command `run`.

The format of the script is recognised using its extension.

Formats
-------

### PHP

PHP scripts will be executed from the web directory of an instance. They will be executed as any other CLI script.

Directories
-----------

The scripts are looked for in each of the following directories until found:
- (Setting dirs.moodle)/scripts
- ~/.moodle-sdk/scripts
- /etc/moodle-sdk/scripts
- /path/to/moodle-sdk/scripts