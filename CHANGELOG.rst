Changelog
=========

v2.1.4
-----

- Update Jira authentication for the migration to Jira Cloud - Andrew Lyons
- Use the `main` branch for the `doctor --masterbranch` command - Jun Pataleta
- Minor syntax fixes - Jayce Birrell, Jun Pataleta

v2.1.3
-----

- `mdk behat` now supports `--profile` and `--rerun`
- A new `mdk php` command.
- Remove dependence on `pkg_resources`
- README file formatting improvements
- Fish shell completions support

v2.1.2
-----

- Behat command updates

  - Remove support for 10+ year-old Moodle versions in the Behat command
  - `--no-selenium` argument to skip Selenium handling
  - `--skip-init` argument for quicker runs

- Various docker and webservice support fixes
- Disabling of the `backup`, `css`, and `js` commands for future removal
- Update for Moodle 5.0 development - Jun Pataleta

v2.1.1
-----

- Formatting fixes in the `README` file
- Fix for ``mdk fix`` when checking out an issue with an existing ``*-master`` branch - Jun Pataleta
- Minor syntax and missing import fixes - Jun Pataleta
- Fixes related to the removal of the `master` branch in `moodle.git` - Jun Pataleta

  - Removal of references to the `master` branch in the `README` file
  - Removal of the fallback logic to `master`, especially when creating a new instance
  - Remove syncing of the local `master` branch with the `main` branch

- Support automatic resolution of the docker container name

v2.1.0
-----

- YAPF support
- Centralise execution of Moodle-bound scripts
- Initial support for Moodle running in Docker
- Composer install fixes
- The ``webservices`` script now enables ``webservice_restful`` plugin when available
- New ``cron`` command
- New script ``mincron`` to reduce the number of tasks running during cron

v2.0.14
-----

- Update config for Moodle 4.5 development
- Add the ability to use new Selenium Grid - Huong Nguyen
- Clean up tracker fields belonging to legacy Moodle versions

v2.0.13
-----

- `mdk fix` - No need to prompt which branch to check out if `-master` when the `-main` branch already exists - Andrew Lyons
- Fix the calculation of the plugin version during plugin installation - Philipp Imhof
- Fix `undev` script to use correct theme settings location for 4.4 and up - Jun Pataleta
- Fix error preventing MDK from creating new instances when it's freshly installed - Huong Nguyen

v2.0.12
-----

- Update `master` and `main` tracker field names to point to the renamed `Pull Main xx` fields
- `tools.stableBranch` should be checking for the `main` branch at the remote
- Make sure to sync `master` to `main` during `mdk update` of master/main instances
- Check for customised `wording.prefixMaster` and sync `wording.prefixMain` if necessary

v2.0.11
-----

- Fix rendering of correct version options for the `backport`, `create`, and `rebase` commands - Jun Pataleta
- Include VScode setting to autoformat with yapf
- Add support for Moodle's `main` branch - Jun Pataleta

v2.0.10
-----

- Fixed typo for the 403 entry in `config-dist.json` - Jun Pataleta

v2.0.9
-----

- Disable user tours when running `dev` and `mindev` scripts
- Make use of GitHub whitespace ignore parameter in push URLs - Andrew Lyons
- Remove `--dev` arg from composer install - Andrew Lyons
- Update config for Moodle 4.4 development

v2.0.8
------

- Update config for Moodle 4.3 development

v2.0.7
------

- Update config for Moodle 4.2 development - Huong Nguyen

v2.0.6
------

- Make yes or no prompts equal - Adrian Perez
- Add vscode script to generate jsconfig.json - Andrew Nicols
- Tracker command argument to open Jira ticket in default browser - Dongsheng Cai
- Fix plugin version for Moodle minor versions greater than 9 - Philipp Imhof
- Avoid PHP Notice "Undefined variable: DB" in PHPUnit setup - David Mudrák
- Specify Git path during initialization - Adrian Perez

v2.0.5
------
- Update config for Moodle 4.1 development
- Removing FirePHP from dev script in favour of declaring $DB
- Adding experimental setting to clone with --shared flag
- Clone a single branch when initally cloning repository
- Replace git://github.com URLs with https://github.com - Jun Pataleta

v2.0.4
------
- Development scripts to increase session timeout to forever
- Rewrite git://github.com URLs as https://github.com - Andrew Lyons

v2.0.3
------
- Update config for Moodle 3.11 development

v2.0.2
------
- Update config for Moodle 3.10 development
- Fix TypeError when downloading patch file on python3 - Jake Dallimore

v2.0.1
------
- forceCfg now accepts non-scalar values. - David Mudrák
- Import database libraries only when necessary. - Morgan Harris
- Fixed fetching of Selenium release data. - Mick Hawkins

v2.0.0
------
- Added support for Python 3.6
- Dropped support for Python 2
- Script `webservices` enables the Mobile services
- Fixed issue when installing plugins from local repository

v1.7.6
------
- Language caching is no longer enabled in `mindev` script
- JavaScript caching is no longer enabled in `mindev` script
- Selenium versions to download were not accurately identified

v1.7.5
------
- Add support for repeating tests - Jun Pataleta
- Fix typos in error/warning messages - Luca Bösch
- Set cachetemplates config value for dev/undev scripts - Jun Pataleta
- Add ability to define custom $CFG->prefix for new instances - David Mudrák
- Removed extra dot being added to the filename of generated mdk run script - David Mudrák
- Enable mobile web services in webservices script

v1.7.4
------
- Update config for Moodle 3.7 - Jun Pataleta
- Add plugin uninstall functionality - Adrian Greeve

v1.7.3
------
- Update config for Moodle 3.6 - Andrew Nicols
- Invalidate config caches before reading plugin versions - David Mudrák


v1.7.2
------

- Update config for Moodle 3.5 - Jun Pataleta
- Detect which SQL Server Driver is installed - Jun Pataleta
- Improve type handling of values set using the config command
- Support for setting URL of specific branches in config
- Tidy up the version script - Andrew Nicols
- Automatically build distributed phpunit.xml files for each component - David Mudrák
- Make mdk precheck work again - David Mudrák

v1.7.1
------

- Fix missing assignment of the sqlsrv cursor - Jun Pataleta

v1.7.0
------

- Support creation of instances running on SQL Server. - Jun Pataleta
- Warn the user if the keyring module can't be loaded - David Mudrák

v1.6.4
------

- Update config for Moodle 3.4 - Jun Pataleta
- Add .idea to .gitignore - Jun Pataleta


v1.6.3
------

- New script ``tokens`` to list external tokens
- Ignore non-warning logging messages from keyring.backend
- Script to set-up a 'security' repository - David Monllao
- Always display precheck URL - David Mudrak

v1.6.2
------

- Update config for Moodle 3.3 - Jun Pataleta
- MySQL UTF-8 byte characters fix - Dan Poltawski

v1.6.1
------

- New script ``mindev`` for minimal development settings
- New script ``setup`` for bulk set-up for development
- Scripts can call other scripts
- Handle Behat path changes from 3.2.2 - Rajesh Taneja

v1.6.0
------

- Script ``users`` uses randomuser.me - Damyon Wiese
- Script ``users`` prefills admin details - Damyon Wiese
- Minor bug fixes and improvements

v1.5.8
------

- Minor bug fixes and improvements

v1.5.7
------

- Minor bug fixes and improvements

v1.5.6
------

- Update default config for Moodle 3.2 development
- Minor bug fixes and improvements

v1.5.5
------

- Added support for grunt CSS - Andrew Nicols
- Added support for Behat 3.x - Rajesh Taneja
- Fixed automatic download of Selenium - Jetha Chan
- Travis bug fixes - Dan Poltawski
- Bug fixes

v1.5.4
------

- New argument ``--skip-init`` added to ``phpunit``
- New argument ``--stop-on-failure`` added to ``phpunit``
- Script ``users`` uses @example.com for email addresses
- Bug fixes

v1.5.3
------

- Really include ``phpunit`` does not require '_testuite' as suffix of the test suites

v1.5.2
------

- Update default config for Moodle 3.0 release
- New script to refresh the services and external functions
- ``phpunit`` does not require '_testuite' as suffix of the test suites
- New script to fix the version numbers - Adrian Greeve

v1.5.1
------

- Update default config for Moodle 2.9 release

v1.5
----

- New ``precheck`` command
- ``phpunit`` can run a whole test suite - Andrew Nicols
- ``tracker`` can add comments to an issue - Andrew Nicols
- ``tracker`` can add/remove labels to an issue - Andrew Nicols
- ``config flatlist`` has an optional ``--grep`` argument

v1.4
----

- ``js`` supports generation of YUI Docs - Andrew Nicols
- New setting ``forceCfg`` to add $CFG values to config.php upon install - David Mudrak
- ``js shift`` watcher does not die when compilation fails
- ``js shift`` output improved
- ``behat`` uses new mechanism for 2.6 instances
- ``behat`` can be used with Oracle
- ``behat`` logs Selenium output to a file
- ``behat`` supports output of progress, failures, screenshots, etc...
- ``behat`` does not override ``behat_wwwroot`` unless told to
- ``behat`` can force the initialisation
- ``phpunit`` can be used with Oracle
- ``phpunit`` does not automatically run without ``--run``
- ``phpunit`` supports generation of code coverage
- ``doctor`` supports ``--symlink`` checks
- ``doctor`` supports ``--masterbranch`` checks

v1.3
----

- Changed directory structure to make MDK a python package
- Dev scripts disable string caching - David Mudrak
- Added support for MariaDB
- ``phpunit`` accepts the parameter ``--filter`` - Andrew Nicols

v1.2
----

- New ``js`` command

v1.1
----

- Sub processes are killed when using CTRL + C
- Default alias ``theme`` to set a theme - Andrew Nicols
- ``config`` has a new sub command ``edit``

v1.0
----

- Dropped official support for Python 2.6
- Moving forward by using ``pip`` for external dependencies
- New command ``css`` for CSS related tasks
- New script to ``enrol`` users
- ``push`` and ``backport`` commands can upload patches to the tracker
- ``pull`` can be forced to check for patches rather than pull branches
- Command ``check`` was renamed ``doctor``
- ``doctor`` can check for dependencies
- Support for sourcemaps when compiling LESS - Andrew Nicols
- Exit with error code 1 when an exception is thrown
- ``run`` can pass arguments to scripts
- Faster clone of cache on first ``init``
- ``phpunit`` accepts a testcase as argument
- ``.noupgrade`` file can be used not to upgrade an instance
- ``behat`` can run tests by name - Andrew Nicols
- ``remove`` accepts ``-f`` as an argument - Andrew Nicols
- The script ``less`` is deprecated
- ``backport`` command resolves conflicts with CSS from LESS in theme_bootstrapbase

v0.5
----

- New command ``uninstall`` to uninstall an instance
- New command ``plugin`` to install plugins
- ``push`` and ``backport`` can specify the HEAD commit when updating the tracker
- Updating the tracker smartly guesses the HEAD commit
- ``behat`` can force the download of the latest Selenium
- New setting not to use the cache repositories as remote
- ``purge`` can manually purge cache without using the shipped CLI

v0.4.2
------

- Updating tracker issue uses short hashes
- ``create`` accepts a custom instance identifier
- More verbose ``dev`` script
- New script ``undev`` to revert the changes of the script ``dev``
- ``pull`` has an option to fetch only
- New script ``less`` to compile the less files from bootstrapbase
- ``run`` can execute shell scripts
- Auto complete for ``behat`` -f
- Auto complete for ``phpunit`` -u
- Shipping a bash script ``extra/goto_instance`` to jump to instances with auto complete

v0.4.1
------

- ``config`` can display objects (eg. ``mdk config show wording``)
- ``config`` output is ordered alphabetically
- ``info`` output is ordered alphabetically
- ``init`` does not show the default password between brackets
- ``init`` does not fail because of missing directories
- ``run`` was permanently failing
- ``tracker`` failed when an issue was unassigned

v0.4
----

- New command ``tracker`` to fetch information from the tracker
- ``alias`` support arguments for bash aliases
- ``alias`` can update aliases
- ``backport`` works locally
- ``backport`` can update tracker Git info
- ``behat`` can limit features to test
- ``behat`` can disable itself
- ``check`` can fix problems
- ``check`` checks remote URLs
- ``check`` checks $CFG->wwwroot
- ``check`` checks the branch checked out on integration instances
- ``create`` accepts multiple versions
- ``create`` accepts multiple suffixes
- ``phpunit`` can limit testing to one file
- ``pull`` can download patch from the tracker
- ``pull`` can checkout the remote branch
- ``push`` checks that the branch and MDL in commit message match
- ``rebase`` can update tracker Git info
- ``run`` can list the available scripts
- Cached repositories are mirrors
- Removed use of Bash script to launch commands
- Deprecated moodle-*.py files
- Instances can be installed on https
- Improved debugging


v0.3
----

- New command ``behat`` which is equivalent to ``phpunit``
- New command ``pull`` to fetch a patch from a tracker issue
- New script ``webservices`` to entirely enable the web services
- ``push`` now updates the Git information on the tracker issue (Thanks to Damyon Wiese)
- ``phpunit`` can also run the tests after initialising the environment
- ``update --update-cache`` can proceed with the updates after updating the cached remotes
- ``info`` can be used to edit settings ($CFG properties) in config.php
- ``init`` has been a bit simplified
- Basic support of shell commands in aliases
- The settings in config.json are read from different locations, any missing setting will be read from config-dist.json
- Bug fixes
