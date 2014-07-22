Custom scripts
==============

This directory is meant to host scripts to be run on an instance. They are called using the command ``run``.

The format of the script is recognised using its extension.

Formats
-------

### PHP

PHP scripts will be executed from the web directory of an instance. They will be executed as any other CLI script.

### Shell

Shell scripts will be executed from the web directory of an instance. They will be made executable and run on their own. If you need to access information about the instance from within the shell script, retrieve it using `mdk info`.

Directories
-----------

The scripts are looked for in each of the following directories until found:
- (Setting dirs.moodle)/scripts
- ~/.moodle-sdk/scripts
- /etc/moodle-sdk/scripts
- /path/to/moodle-sdk/scripts