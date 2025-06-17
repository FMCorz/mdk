Moodle Development Kit
======================

A collection of tools to make developers' lives easier.

Requirements
============

- Linux or Mac OS
- Python 3.6
- MySQL, MariaDB or PostgreSQL
- Git v1.7.7 or greater

Most of the tools work on Moodle 1.9 onwards, but some CLI scripts required by MDK might not be available in all versions.

Usage
=====

The commands are called using that form::

    mdk <command> <arguments>

Get some help on a command using::

    mdk <command> --help

Also check the `wiki <https://github.com/FMCorz/mdk/wiki>`_.

Docker support
==============

As at MDK 2.1, partial support for Moodle running in Docker is available. Some commands like ``phpunit``, ``upgrade``, ``run``, ``cron`` are run in the container. The ``behat`` command can also work but still requires some fiddling around. Other commands such as ``install`` will not work.

Set the environment variable ``MDK_DOCKER_NAME`` to the name of the running container, or enable the config ``docker.automaticContainerLookup`` to let MDK look for a matching running container automatically.

Usage examples::

    # One command.
    $ MDK_DOCKER_NAME=sm mdk phpunit

    # Multiple commands.
    $ set -x MDK_DOCKER_NAME sm
    $ mdk run dev
    $ mdk phpunit

    # Enable automatic resolution.
    $ mdk config set docker.automaticContainerLookup true

    # With automatic resolution.
    $ cd /path/to/sm
    $ mdk phpunit

Compatible containers
---------------------

The Docker container must be created using `moodlehq/moodle-php-apache <https://github.com/moodlehq/moodle-php-apache>`_, here is an example::

    # Replace `sm` with the name of your instance.
    set -x INSTANCE_NAME sm

    # This computes the paths of the instance.
    set -x MDK_INSTANCE_DIR (mdk info -v path $INSTANCE_NAME)
    set -x MDK_STORAGE_DIR (mdk config show dirs.storage | python -c 'import sys, pathlib; print(pathlib.Path(sys.stdin.read()).expanduser().resolve(), end="")')

    # Create a Docker network called `moodle`.
    docker network create moodle 2> /dev/null

    # Create and start the docker container, change the port, name and PHP version as needed.
    docker run -d \
        --name $INSTANCE_NAME \
        --network moodle \
        -v $MDK_INSTANCE_DIR:/var/www/html \
        -v $MDK_STORAGE_DIR/$INSTANCE_NAME/moodledata:/var/www/moodledata \
        -v $MDK_STORAGE_DIR/$INSTANCE_NAME/extra/behat:/var/www/behatfaildumps \
        -p 8800:80 moodlehq/moodle-php-apache:8.1

You will want to create databases in the same network, and other services like selenium.

PHP executable
==============

MDK can work with multiple PHP versions through Docker instances. This can cause conflicts in IDEs which refer to the host PHP executable. To correct this, you can reference ``mdk php`` as the PHP executable. And if the path to the PHP executable is required, create an executable as suggested `below <#custom-php-executable>`_.

Note that ``mdk php`` must be called from within the Moodle instance directory tree.

VScode settings
---------------

::

    {
        "php.validate.executablePath": "/path/to/custom/executable/php-mdk"
        "mdlcode.cli.phpPath": "mdk php",
    }

Custom PHP executable
---------------------

On Ubuntu, you could create the file ``php-mdk`` in ``~/.local/bin`` with the following content::

    #!/bin/bash
    mdk php $@

Then make it executable::

    chmod 0700 ~/.local/bin/php-mdk


Installation
============

Python package
--------------

On Debian-based systems, install the following packages::

    sudo apt-get install python-pip libmysqlclient-dev libpq-dev python-dev unixodbc-dev

Use `pip <http://www.pip-installer.org/en/latest/installing.html>`_::

    pip install moodle-sdk --user
    mdk init

Notes
^^^^^

This method does not require ``sudo`` as it installs MDK for the current user. It is assumed that ``~/.local/bin`` is in your PATH (or `equivalent <https://docs.python.org/3/library/site.html#site.USER_BASE>`_).

If it isn't, this snippet for ``~/.profile`` might be useful::

    # Set PATH so it includes user's private local bin if it exists.
    if [ -d "$HOME/.local/bin" ] ; then
        PATH="$HOME/.local/bin:$PATH"
    fi

Homebrew
--------

Using `Homebrew <http://brew.sh/>`_, please refer to this `formula <https://github.com/danpoltawski/homebrew-mdk>`_.


For development
---------------

Clone the repository::

    git clone https://github.com/FMCorz/mdk.git moodle-sdk

On Debian-based systems, you will need to install the following packages::

    sudo apt-get install python-pip libmysqlclient-dev libpq-dev python-dev unixodbc-dev

Then from the directory where you cloned the repository::

    python setup.py develop --user
    mdk init


Shell completion
----------------

Fish completion
^^^^^^^^^^^^^^^

To activate fish completion::

    sudo ln -s /path/to/moodle-sdk/extra/fish_completion ~/config/fish/completions/mdk.fish

Bash completion
^^^^^^^^^^^^^^^

To activate bash completion::

    sudo ln -s /path/to/moodle-sdk/extra/bash_completion /etc/bash_completion.d/moodle-sdk

To activate goto commands (``gt`` and ``gtd``), add the following to ~/.bashrc::

    if [ -f /path/to/moodle-sdk/extra/goto_instance ]; then
        . /path/to/moodle-sdk/extra/goto_instance
        . /path/to/moodle-sdk/extra/goto_instance.bash_completion
    fi


Upgrading
=========

If you installed MDK using PIP, run the following command::

    pip install --user --upgrade moodle-sdk

It is possible that a new version of MDK requires new files, directories, etc... and while we try to make it easy to upgrade, it can happen that some features get broken in your environment. So after each upgrade, consider running the following to get more information::

    mdk doctor --all


Command list
============

* `alias`_
* `backport`_
* `behat`_
* `config`_
* `create`_
* `doctor`_
* `fix`_
* `info`_
* `install`_
* `php`_
* `phpunit`_
* `plugin`_
* `precheck`_
* `purge`_
* `pull`_
* `push`_
* `rebase`_
* `remove`_
* `run`_
* `tracker`_
* `uninstall`_
* `update`_
* `upgrade`_

alias
-----

Set up aliases of your Moodle commands.

**Example**

This line defines the alias 'upall', for 'moodle update --all'

::

    mdk alias add upall "update --all"

backport
--------

Backport a branch to another instance of Moodle.

**Examples**

Assuming we are in a Moodle instance, this backports the current branch to the version 2.2 and 2.3

::

    mdk backport --version 22 23

Backports the branch MDL-12345-23 from the instance stable_23 to the instance stable_22, and pushes the new branch to your remote

::

    mdk backport stable_23 --branch MDL-12345-23 --version 22 --push


behat
-----

Get the instance ready for acceptance testing (Behat), and run the test feature(s).

**Examples**

::

    mdk behat -r --tags=@core_completion


create
------

Create a new instance of Moodle. It will be named according to your config file.

**Examples**

Create a new instance of Moodle 2.1

::

    mdk create --version 21

Create an instance of Moodle 2.2 using PostgreSQL from the integration remote, and run the installation script.

::

    mdk create --version 22 --engine pgsql --integration --install

config
------

Set your MDK settings from the command line.

**Examples**

Show the list of your settings

::

    mdk config list

Change the value of the setting ``dirs.storage`` to ``/var/www/repositories``

::

    mdk config set dirs.storage /var/www/repositories


doctor
------

Perform some checks on the environment to identify possible problems, and attempt to fix them automatically.


fix
---

Create a branch from an issue number on the tracker (MDL-12345) and sets it to track the right branch.

**Examples**

In a Moodle 2.2 instance, this will create (and checkout) a branch named MDL-12345-22 which will track upstream/MOODLE_22_STABLE.

::

    mdk fix MDL-12345
    mdk fix 12345


info
----

Display information about the instances on the system.

**Examples**

List the instances

::

    mdk info --list

Display the information known about the instance *stable_main*

::

    mdk info stable_main


install
-------

Run the command line installation script with all parameters set on an existing instance.

**Examples**

::

    mdk install --engine mysqli stable_main



php
---

Invoke a PHP command in the context of the instance.

**Examples**

::

    mdk php admin/cli/purge_caches.php

phpunit
-------

Get the instance ready for PHPUnit tests, and run the test(s).

**Examples**

::

    mdk phpunit -u repository/tests/repository_test.php


plugin
------

Look for a plugin on moodle.org and downloads it into your instance.

**Example**

::

    mdk plugin download repository_evernote


precheck
--------

Pre-checks a patch on the CI server.

**Example**

::

    mdk precheck


purge
-----

Purge the cache.

**Example**

To purge the cache of all the instances

::

    mdk purge --all


pull
----

Pulls a patch using the information from a tracker issue.

**Example**

Assuming we type that command on a 2.3 instance, pulls the corresponding patch from the issue MDL-12345 in a testing branch

::

    mdk pull --testing 12345


push
----

Shortcut to push a branch to your remote.

**Examples**

Push the current branch to your repository

::

    mdk push

Force a push of the branch MDL-12345-22 from the instance stable_22 to your remote

::

    mdk push --force --branch MDL-12345-22 stable_22


rebase
------

Fetch the latest branches from the upstream remote and rebase your local branches.

**Examples**

This will rebase the branches MDL-12345-xx and MDL-56789-xx on the instances stable_22, stable_23 and stable_main. And push them to your remote if successful.

::

    mdk rebase --issues 12345 56789 --version 22 23 main --push
    mdk rebase --issues MDL-12345 MDL-56789 --push stable_22 stable_23 stable_main


remove
------

Remove an instance, deleting every thing including the database.

**Example**

::

    mdk remove stable_main


run
---

Execute a script on an instance. The scripts are stored in the scripts directory.

**Example**

Set the instance stable_main ready for development

::

    mdk run dev stable_main


tracker
-------

Gets some information about the issue on the tracker.

**Example**

::

    $ mdk tracker 34543
    ------------------------------------------------------------------------
      MDL-34543: New assignment module - Feedback file exists for an
        assignment but not shown in the Feedback files picker
      Bug - Critical - https://moodle.atlassian.net/browse/MDL-34543
      Closed (Fixed) 2012-08-17 07:25
    -------------------------------------------------------[ V: 7 - W: 7 ]--
    Reporter            : Paul Hague (paulhague) on 2012-07-26 08:30
    Assignee            : Eric Merrill (emerrill)
    Peer reviewer       : Damyon Wiese (damyon)
    Integrator          : Dan Poltawski (poltawski)
    Tester              : Tim Barker (timb)
    ------------------------------------------------------------------------


uninstall
---------

Uninstall an instance: removes config file, drops the database, deletes dataroot content, ...


update
------

Fetch the latest stables branches from the upstream remote and pull the changes into the local stable branch.

**Examples**

This updates the instances stable_22 and stable_23

::

    mdk update stable_22 stable_23

This updates all your integration instances and runs the upgrade script of Moodle.

::

    mdk update --integration --upgrade


upgrade
-------

Run the upgrade script of your instance.

**Examples**

The following runs an upgrade on your stable branches

::

    mdk upgrade --stable

This will run an update an each instance before performing the upgrade process

::

    mdk upgrade --all --update

Scripts
=======

You can write custom scripts and execute them on your instances using the command ``mdk run``. MDK looks for the scripts in the *scripts* directories and identifies their type by reading their extension. For example, a script called 'helloworld.php' will be executed as a command line script from the root of an installation.

::

    # From anywhere on the system
    $ mdk run helloworld stable_main

    # Is similar to typing the following command
    $ cp /path/to/script/helloworld.php /path/to/moodle/instances/stable_main
    $ cd /path/to/moodle/instances/stable_main
    $ php helloworld.php

Scripts are very handy when it comes to performing more complexed tasks.

Shipped scripts
---------------

The following scripts are available with MDK:

* ``dev``: Changes a portion of Moodle settings to enable development mode
* ``enrol``: Enrols users in any existing course
* ``external_functions``: Refreshes the definitions of services and external functions
* ``makecourse``: Creates a test course
* ``mindev``: Minimalist set of development settings (performance friendly)
* ``setup``: Setup for development by running a succession of other scripts
* ``tokens``: Lists the webservice tokens
* ``undev``: Reverts the changes made by ``dev`` and ``mindev``
* ``users``: Creates a set of users
* ``version``: Fixes downgrade version conflicts
* ``webservices``: Does all the set up of webservices for you

License
=======

Licensed under the `GNU GPL License <http://www.gnu.org/copyleft/gpl.html>`_
