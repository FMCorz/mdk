Moodle Development Kit
======================

A collection of tools meant to make developers' lives easier.

Requirements
------------

- Python 2.7
- MySQL or PostgreSQL

Most of the tools work on Moodle 1.9 onwards, but some CLI tools required by MDK might not be available in all versions.

Usage
-----

The commands are called using that form:

    moodle <command> <arguments>

Get some help on a command using:

    moodle <command> --help

Installation
------------

### 1. Clone the repository

    git clone git://github.com/FMCorz/mdk.git

### 2. Check permissions

In the freshly cloned repository, each `moodle-<command>.py` and `moodle` must be executable.

    chmod +x moodle moodle-*.py

### 3. Make MDK accessible

Create a symbolic link to the `moodle` bash script in your bin directory

    ln -s /path/to/mdk/moodle /usr/local/bin

Alternatively you could add to directory where `moodle` is in your environment variable $PATH.

### 4. Config file

Copy the config file `config-dist.json` to `config.json`.

Here are some settings that you will have to set:

- dirs.www: This is typically the directory where points http://localhost/. You need write access in that directory as a symbolic link to your Moodle instance will ve created there. 
- dirs.storage: This is the directory where will be stored your instances of Moodle and their data. Each instance of Moodle will have its own folder in which you will find moodledata and the web directory. You obviously need write access in this directory.
- dirs.moodle: This folder will be used by MDK to store some data like a copy of the remotes, or backup files, etc...
- db.*: The information to connect to your database.
- remotes.mine: The URL to your personal repository.

There are quite a lot more other settings which you could play with, read through the config file to find them out.

### 5. Done

Try the following command to create and install a typical Stable Master instance:

    moodle create -i

Now you should be able to access it from http://localhost/stablemaster, or type the following command the list it:

    moodle list

Command list
------------

### - alias

Set up aliases of your Moodle commands.

**Example**

This line defines the alias 'upall', for 'moodle update --all'
    
    moodle alias add upall "update --all"

### - backport

Backport a branch to another instance of Moodle.

**Examples**

Assuming we are in a Moodle instance, this backports the current branch to the version 2.2 and 2.3

    moodle backport --version 22 23

Backports the branch MDL-12345-23 from the instance stable_23 to the instance stable_22, and pushes the new branch to your remote

    moodle backport stable_23 --branch MDL-12345-23 --version 22 --push

### - backup

Backup a whole instance so that it can be restored later.

**Examples**

Backup the instance named stable_master

    moodle backup stable_master

List the backups

    moodle backup --list

Restore the second backup of the instance stable_master

    moodle backup --restore stable_master_02

### - check

Perform some checks on the environment to identify possible problems.

### - create

Create a new instance of Moodle. It will be named according to your config file.

**Examples**

Create a new instance of Moodle 2.1

    moodle create --version 21

Create an instance of Moodle 2.2 using PostgreSQL from the integration remote, and run the installation script.

    moodle create --version 22 --engine pgsql --integration --install

### - config

Set your MDK settings from the command line.

**Examples**

Show the list of your settings
     
    moodle config list

Change the value of the setting 'dirs.storage' to '/var/www/repositories'

    moodle config set dirs.storage /var/www/repositories

### - fix

Create a branch from an issue number on the tracker (MDL-12345) and sets it to track the right branch.

**Examples**

In a Moodle 2.2 instance, this will create (and checkout) a branch named MDL-12345-22 which will track upstream/MOODLE_22_STABLE.

    moodle fix MDL-12345
    moodle fix 12345


### - info

Display information about the instances on the system.

**Examples**

List the instances

    moodle info --list

Display the information known about the instance *stable_master*

    moodle info stable_master


### - install

Run the command line installation script with all parameters set on an existing instance.

**Examples**

    moodle install --engine mysqli stable_master


### - phpunit

Get the instance ready for PHP Unit tests.


### - purge

Purge the cache.

**Example**

To purge the cache of all the instances

    moodle purge --all


### - push

Shortcut to push a branch to your remote.

**Examples**

Push the current branch to your repository

    moodle push

Force a push of the branch MDL-12345-22 from the instance stable_22 to your remote

    moodle push --force --branch MDL-12345-22 stable_22


### - rebase

Fetch the latest branches from the upstream remote and rebase your local branches.

**Examples**

This will rebase the branches MDL-12345-xx and MDL-56789-xx on the instances stable_22, stable_23 and stable_master. And push them to your remote if successful.

    moodle rebase --issues 12345 56789 --version 22 23 master --push
    moodle rebase --issues MDL-12345 MDL-56789 --push stable_22 stable_23 stable_master


### - remove

Remove an instance, deleting every thing including the database.

**Example**

    moodle remove stable_master


### - run

Execute a script on an instance. The scripts are stored in the scripts directory.

**Example**

Set the instance stable_master ready for development

    moodle run dev stable_master


### - update

Fetch the latest stables branches from the upstream remote and pull the changes into the local stable branch.

**Examples**

This updates the instances stable_22 and stable_23

    moodle update stable_22 stable_23

This updates all your integration instances and runs the upgrade script of Moodle.

    moodle update --integration --upgrade


### - upgrade

Run the upgrade script of your instance

**Examples**

The following runs an upgrade on your stable branches

    moodle upgrade --stable

This will run an update an each instance before performing the upgrade process

    moodle upgrade --all --update

Scripts
-------

You can write custom scripts and execute them on your instances using the command `moodle run`. MDK looks for the scripts in the _scripts_ directory and identifies their type by reading their extension. For example, a script called 'helloworld.php' will be executed as a command line script from the root of an installation.

    # From anywhere on the system
    $ moodle run helloworld stable_master

    # Is similar to typing the following command in /var/www/stable_master
    $ php helloworld.php

Scripts are very handy when it comes to performing more complexed tasks.

License
-------

Licensed under the [GNU GPL License](http://www.gnu.org/copyleft/gpl.html)
