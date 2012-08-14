# Moodle Development Kit

A collection of tools meant to make developers' lives easier.

## Requirements

- Python 2.7
- Moodle 2.x
- MySQL or PostgreSQL

The tools should work on Moodle 1.9 but have not really been tested yet.

## Usage

The commands are called using that form:

    moodle <command> <arguments>

Get some help on a command using:

    moodle <command>  --help

## Installation

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

Read through the config file to find out what you have to set up.

The most important are the directories (`dirs`), database access (`db`) and your repository (`remotes.mine`).

If you already have instances installed and a way of naming your branches, you will have to update the `wording` part. Use extra care with the regular expressions!

### 5. Done

If you already have instances installed, and your settings are correct, try the following command.

    moodle info --list

## Commands list

### backport

Backport a branch to another instance of Moodle.

__Examples__

Assuming we are in a Moodle instance, this backports the current branch to the version 2.2 and 2.3

    moodle backport --version 22 23

Backports the branch MDL-12345-23 from the instance stable_23 to the instance stable_22, and pushes the new branch to your remote

    moodle backport stable_23 --branch MDL-12345-23 --version 22 --push

### backup

Backup a whole instance so that it can be restored later.

__Examples__

Backup the instance named stable_master

    moodle backup stable_master

List the backups

    moodle backup --list

Restore the second backup of the instance stable_master

    moodle backup --restore stable_master_02

### create

Create a new instance of Moodle. It will be named according to your config file.

__Examples__

Create a new instance of Moodle 2.1

    moodle create --version 21

Create an instance of Moodle 2.2 using PostgreSQL from the integration remote, and run the installation script.

    moodle create --version 22 --engine pgsql --integration --install

### fix

Create a branch from an issue number on the tracker (MDL-12345) and sets it to track the right branch.

__Examples__

In a Moodle 2.2 instance, this will create a branch named MDL-12345-22 which will track origin/MOODLE_22_STABLE.

    moodle fix MDL-12345
    moodle fix 12345

### info

Display information about the instances on the system.

__Examples__

List the instances

    moodle info --list

Display the information known about the instance *stable_master*

    moodle info stable_master

### install

Run the command line installation script with all parameters set on an existing instance.

__Examples__

    moodle install --engine mysqli stable_master

### phpunit

Get the instance ready for PHP Unit tests.

### push

Shortcut to push a branch to your remote.

__Examples__

Push the current branch to your repository

    moodle push

Force a push of the branch MDL-12345-22 from the instance stable_22 to your remote

    moodle push --force --branch MDL-12345-22 stable_22

### rebase

Fetch the latest branches from origin and rebase your local branches.

__Examples__

This will rebase the branches MDL-12345-xx and MDL-56789-xx on the instances stable_22, stable_23 and stable_master. And push them to your remote if successful.

    moodle rebase --issues 12345 56789 --version 22 23 master --push
    moodle rebase --issues MDL-12345 MDL-56789 --push stable_22 stable_23 stable_master

### remove

Remove an instance, deleting every thing including the database.

__Examples__

    moodle remove stable_master

### update

Fetch the latest stables branches from the origin and pull the changes into the local stable branch.

__Examples__

This updates the instances stable_22 and stable_23

    moodle update stable_22 stable_23

This updates all your integration instances and runs the upgrade script of Moodle.

    moodle update --integration --upgrade

### upgrade

Run the upgrade script of your instance

__Examples__

The following runs an upgrade on your stable branches

    moodle upgrade --stable

This will run an update an each instance before performing the upgrade process

    moodle upgrade --all --update

## License

Licensed under the GNU GPL License http://www.gnu.org/copyleft/gpl.html
