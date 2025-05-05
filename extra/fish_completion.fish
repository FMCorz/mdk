# Define the main mdk command
complete -c mdk -f

# Common options for all commands
complete -c mdk -s h -l help -d "Show help message"

# Define all the MDK commands
complete -c mdk -n __fish_use_subcommand -a alias -d "Manage your aliases"
complete -c mdk -n __fish_use_subcommand -a backport -d "Backports a branch"
complete -c mdk -n __fish_use_subcommand -a behat -d "Behat related commands"
complete -c mdk -n __fish_use_subcommand -a config -d "Manage MDK configuration"
complete -c mdk -n __fish_use_subcommand -a create -d "Creates new instances"
complete -c mdk -n __fish_use_subcommand -a cron -d "Run cron and scheduled tasks"
complete -c mdk -n __fish_use_subcommand -a doctor -d "Perform various checks"
complete -c mdk -n __fish_use_subcommand -a fix -d "Creates a branch for an MDL"
complete -c mdk -n __fish_use_subcommand -a info -d "Display information about instances"
complete -c mdk -n __fish_use_subcommand -a install -d "Install an instance"
complete -c mdk -n __fish_use_subcommand -a php -d "Invoke PHP commands"
complete -c mdk -n __fish_use_subcommand -a phpunit -d "Run PHPUnit tests"
complete -c mdk -n __fish_use_subcommand -a plugin -d "Plugin related commands"
complete -c mdk -n __fish_use_subcommand -a precheck -d "Run pre-checks on code"
complete -c mdk -n __fish_use_subcommand -a pull -d "Pull a branch from the tracker"
complete -c mdk -n __fish_use_subcommand -a purge -d "Purge the caches"
complete -c mdk -n __fish_use_subcommand -a push -d "Push the branch"
complete -c mdk -n __fish_use_subcommand -a rebase -d "Rebase branches"
complete -c mdk -n __fish_use_subcommand -a remove -d "Delete an instance"
complete -c mdk -n __fish_use_subcommand -a run -d "Run scripts"
complete -c mdk -n __fish_use_subcommand -a tracker -d "Tracker related commands"
complete -c mdk -n __fish_use_subcommand -a uninstall -d "Uninstall an instance"
complete -c mdk -n __fish_use_subcommand -a update -d "Update the codebase"
complete -c mdk -n __fish_use_subcommand -a upgrade -d "Upgrade an instance"

# Alias command subcommands
complete -c mdk -n "__fish_seen_subcommand_from alias" -a list -d "List the aliases"
complete -c mdk -n "__fish_seen_subcommand_from alias" -a show -d "Display an alias"
complete -c mdk -n "__fish_seen_subcommand_from alias" -a add -d "Add an alias"
complete -c mdk -n "__fish_seen_subcommand_from alias" -a remove -d "Remove an alias"
complete -c mdk -n "__fish_seen_subcommand_from alias" -a set -d "Update/add an alias"

# Behat command options
complete -c mdk -n "__fish_seen_subcommand_from behat" -s r -l run -d "Run the tests"
complete -c mdk -n "__fish_seen_subcommand_from behat" -l force -d "Force behat re-init and reset variables in config file"
complete -c mdk -n "__fish_seen_subcommand_from behat" -s f -l feature -d "Path to a feature or argument understood by behat"
complete -c mdk -n "__fish_seen_subcommand_from behat" -s n -l testname -d "Only execute feature elements matching name or regex"
complete -c mdk -n "__fish_seen_subcommand_from behat" -s t -l tags -d "Only execute features with tags matching filter expression"
complete -c mdk -n "__fish_seen_subcommand_from behat" -s j -l no-javascript -d "Do not start Selenium and ignore Javascript"
complete -c mdk -n "__fish_seen_subcommand_from behat" -s D -l no-dump -d "Use standard command without screenshots or output to directory"
complete -c mdk -n "__fish_seen_subcommand_from behat" -s k -l skip-init -d "Start tests quicker when instance is already initialised"
complete -c mdk -n "__fish_seen_subcommand_from behat" -s S -l no-selenium -d "Do not attempt to start Selenium"
complete -c mdk -n "__fish_seen_subcommand_from behat" -l selenium -d "Path to the selenium standalone server to use"
complete -c mdk -n "__fish_seen_subcommand_from behat" -l selenium-download -d "Force download of latest Selenium to cache"
complete -c mdk -n "__fish_seen_subcommand_from behat" -l selenium-verbose -d "Output from selenium in the same window"

# Doctor command options
complete -c mdk -n "__fish_seen_subcommand_from doctor" -l fix -d "Automatically fix all the identified problems"
complete -c mdk -n "__fish_seen_subcommand_from doctor" -l all -d "Run all checks"
complete -c mdk -n "__fish_seen_subcommand_from doctor" -l branch -d "Check the branch checked out on your integration instances"
complete -c mdk -n "__fish_seen_subcommand_from doctor" -l cached -d "Check the cached repositories"
complete -c mdk -n "__fish_seen_subcommand_from doctor" -l dependencies -d "Check various dependencies"
complete -c mdk -n "__fish_seen_subcommand_from doctor" -l directories -d "Check the directories set in the config file"
complete -c mdk -n "__fish_seen_subcommand_from doctor" -l masterbranch -d "Check the status of the master branch"
complete -c mdk -n "__fish_seen_subcommand_from doctor" -l remotes -d "Check the remotes of your instances"
complete -c mdk -n "__fish_seen_subcommand_from doctor" -l symlink -d "Check the symlinks of the instances"
complete -c mdk -n "__fish_seen_subcommand_from doctor" -l wwwroot -d "Check the $CFG->wwwroot of your instances"

# Info command options
complete -c mdk -n "__fish_seen_subcommand_from info" -s e -l edit -d "Edit a configuration value"
complete -c mdk -n "__fish_seen_subcommand_from info" -s i -l integration -d "Used with --list, only display integration instances"
complete -c mdk -n "__fish_seen_subcommand_from info" -s l -l list -d "List the instances"
complete -c mdk -n "__fish_seen_subcommand_from info" -s n -l name-only -d "Used with --list, only display instances name"
complete -c mdk -n "__fish_seen_subcommand_from info" -s s -l stable -d "Used with --list, only display stable instances"
complete -c mdk -n "__fish_seen_subcommand_from info" -s v -l var -d "Variable to output or edit"

# Init command options
complete -c mdk -n "__fish_seen_subcommand_from init" -s f -l force -d "Force the initialisation"

# Config command subcommands
set -l __config_subcommands "edit flatlist list show set"
complete -c mdk -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $__config_subcommands" -a edit -d "Opens the config file in an editor"
complete -c mdk -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $__config_subcommands" -a flatlist -d "Flat list of the settings"
complete -c mdk -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $__config_subcommands" -a list -d "List the settings"
complete -c mdk -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $__config_subcommands" -a show -d "Display one setting"
complete -c mdk -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $__config_subcommands" -a set -d "Set the value of a setting"

# Config set options
complete -c mdk -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from set" -s b -l bool -d "Treat the value passed as a boolean"
complete -c mdk -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from set" -s i -l int -d "Treat the value passed as an integer"
complete -c mdk -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from set" -s s -l string -d "Treat the value passed as a string"

# Plugin command subcommands
complete -c mdk -n "__fish_seen_subcommand_from plugin" -a download -d "Download a plugin"
complete -c mdk -n "__fish_seen_subcommand_from plugin" -a install -d "Install a plugin"
complete -c mdk -n "__fish_seen_subcommand_from plugin" -a uninstall -d "Uninstall a plugin"

# Plugin download options
complete -c mdk -n "__fish_seen_subcommand_from plugin; and __fish_seen_subcommand_from download" -s s -l strict -d "Prevent download of parent version if file not found"
complete -c mdk -n "__fish_seen_subcommand_from plugin; and __fish_seen_subcommand_from download" -s f -l force -d "Override plugin directory if it exists"
complete -c mdk -n "__fish_seen_subcommand_from plugin; and __fish_seen_subcommand_from download" -s c -l no-cache -d "Ignore cached files"

# Plugin install options
complete -c mdk -n "__fish_seen_subcommand_from plugin; and __fish_seen_subcommand_from install" -s s -l strict -d "Prevent download of parent version if file not found"
complete -c mdk -n "__fish_seen_subcommand_from plugin; and __fish_seen_subcommand_from install" -s f -l force -d "Override plugin directory if it exists"
complete -c mdk -n "__fish_seen_subcommand_from plugin; and __fish_seen_subcommand_from install" -s c -l no-cache -d "Ignore cached files"

# Plugin uninstall options
complete -c mdk -n "__fish_seen_subcommand_from plugin; and __fish_seen_subcommand_from uninstall" -s r -l remove-files -d "Remove plugin files and directory"
complete -c mdk -n "__fish_seen_subcommand_from plugin; and __fish_seen_subcommand_from uninstall" -s u -l upgrade -d "Upgrade instance after uninstalling"
complete -c mdk -n "__fish_seen_subcommand_from plugin; and __fish_seen_subcommand_from uninstall" -s n -l no-checkout -d "Don't checkout stable branch before upgrading"

# Precheck command options
complete -c mdk -n "__fish_seen_subcommand_from precheck" -s b -l branch -d "The branch to pre-check"
complete -c mdk -n "__fish_seen_subcommand_from precheck" -s p -l push -d "Push the branch after successful pre-check"

# Backport command options
complete -c mdk -n "__fish_seen_subcommand_from backport" -s b -l branch -d "The branch to backport if not the current one"
complete -c mdk -n "__fish_seen_subcommand_from backport" -s f -l force-push -d "Force the push"
complete -c mdk -n "__fish_seen_subcommand_from backport" -s i -l integration -d "Backport to integration instances"
complete -c mdk -n "__fish_seen_subcommand_from backport" -s p -l push -d "Push the branch after successful backport"
complete -c mdk -n "__fish_seen_subcommand_from backport" -l push-to -d "The remote to push the branch to"
complete -c mdk -n "__fish_seen_subcommand_from backport" -l patch -d "Upload a patch file to the tracker"
complete -c mdk -n "__fish_seen_subcommand_from backport" -s t -l update-tracker -d "Add diff information to the tracker issue"
complete -c mdk -n "__fish_seen_subcommand_from backport" -s v -l versions -d "Versions to backport to"

# Create command options
complete -c mdk -n "__fish_seen_subcommand_from create" -s i -l install -d "Launch installation script after creating the instance"
complete -c mdk -n "__fish_seen_subcommand_from create" -s e -o engine -l dbprofile -d "Database profile to install the instance on"
complete -c mdk -n "__fish_seen_subcommand_from create" -s t -l integration -d "Create an instance from integration"
complete -c mdk -n "__fish_seen_subcommand_from create" -s r -l run -d "Scripts to run after installation"
complete -c mdk -n "__fish_seen_subcommand_from create" -s n -l identifier -d "Use this identifier instead of generating one"
complete -c mdk -n "__fish_seen_subcommand_from create" -s s -l suffix -d "Suffixes for the instance names"
complete -c mdk -n "__fish_seen_subcommand_from create" -s v -l version -d "Version of Moodle"

# Install command options
complete -c mdk -n "__fish_seen_subcommand_from install" -s e -o engine -l dbprofile -d "Database profile to use"
complete -c mdk -n "__fish_seen_subcommand_from install" -s f -l fullname -d "Full name of the instance"
complete -c mdk -n "__fish_seen_subcommand_from install" -s r -l run -d "Scripts to run after installation"

# Cron command options
complete -c mdk -n "__fish_seen_subcommand_from cron" -s k -l keep-alive -d "Keep alive the cron task"
complete -c mdk -n "__fish_seen_subcommand_from cron" -s t -l task -d "The name of scheduled task to run"

# PHPUnit command options
complete -c mdk -n "__fish_seen_subcommand_from phpunit" -s f -l force -d "Force the initialisation"
complete -c mdk -n "__fish_seen_subcommand_from phpunit" -s r -l run -d "Also run the tests"
complete -c mdk -n "__fish_seen_subcommand_from phpunit" -s t -l testcase -d "Testcase class to run"
complete -c mdk -n "__fish_seen_subcommand_from phpunit" -s s -l testsuite -d "Testsuite to run"
complete -c mdk -n "__fish_seen_subcommand_from phpunit" -s u -l unittest -d "Test file to run"
complete -c mdk -n "__fish_seen_subcommand_from phpunit" -s k -l skip-init -d "Allows tests to start quicker when the instance is already initialised"
complete -c mdk -n "__fish_seen_subcommand_from phpunit" -s q -l stop-on-failure -d "Stop execution upon first failure or error"
complete -c mdk -n "__fish_seen_subcommand_from phpunit" -s c -l coverage -d "Creates the HTML code coverage report"
complete -c mdk -n "__fish_seen_subcommand_from phpunit" -l filter -d "Filter to pass through to PHPUnit"
complete -c mdk -n "__fish_seen_subcommand_from phpunit" -l repeat -d "Run tests repeatedly for the given number of times"

# Fix command options
complete -c mdk -n "__fish_seen_subcommand_from fix" -l autofix -d "Auto fix the bug related to the issue number"
complete -c mdk -n "__fish_seen_subcommand_from fix" -s n -l name -d "Name of the instance"

# Run command options
complete -c mdk -n "__fish_seen_subcommand_from run" -s l -l list -d "List the available scripts"
complete -c mdk -n "__fish_seen_subcommand_from run" -s a -l all -d "Runs the script on each instance"
complete -c mdk -n "__fish_seen_subcommand_from run" -s i -l integration -d "Runs the script on integration instances"
complete -c mdk -n "__fish_seen_subcommand_from run" -s s -l stable -d "Runs the script on stable instances"
complete -c mdk -n "__fish_seen_subcommand_from run" -s g -l arguments -d "A list of arguments to pass to the script"

# Remove command options
complete -c mdk -n "__fish_seen_subcommand_from remove" -s y -d "Do not ask for confirmation"
complete -c mdk -n "__fish_seen_subcommand_from remove" -s f -d "Force and do not ask for confirmation"

# Purge command options
complete -c mdk -n "__fish_seen_subcommand_from purge" -s a -l all -d "Purge the cache on each instance"
complete -c mdk -n "__fish_seen_subcommand_from purge" -s i -l integration -d "Purge the cache on integration instances"
complete -c mdk -n "__fish_seen_subcommand_from purge" -s s -l stable -d "Purge the cache on stable instances"
complete -c mdk -n "__fish_seen_subcommand_from purge" -s m -l manual -d "Perform a manual deletion of some cache in dataroot"

# Tracker command options
complete -c mdk -n "__fish_seen_subcommand_from tracker" -l open -d "Open issue in browser"
complete -c mdk -n "__fish_seen_subcommand_from tracker" -s t -l testing -d "Testing mode"

# Function to list Moodle instances for completion with caching
function __mdk_list_instances
    # Cache file path
    set -l cache_file /tmp/mdk_instances_cache
    set -l cache_timeout 300 # 5 minutes in seconds

    # Check if cache exists and is recent enough
    if test -f $cache_file
        set -l current_time (date +%s)
        set -l file_time (stat -c %Y $cache_file)
        set -l time_diff (math $current_time - $file_time)

        # If cache is fresh (less than 5 minutes old), use it
        if test $time_diff -lt $cache_timeout
            cat $cache_file
            return
        end
    end

    # Cache is stale or doesn't exist, regenerate it
    if command -q mdk
        # Get instances and save to cache
        set -l instances (command mdk info -ln 2>/dev/null)
        if test $status -eq 0
            printf "%s\n" $instances >$cache_file
            printf "%s\n" $instances
        end
    end
end

# Function to list behat feature files for an instance
function __mdk_list_behat_features
    set -l moodle_path (mdk info -v path 2> /dev/null)
    if test -n "$moodle_path"; and test -n "$moodle_path" -a -d "$moodle_path"
        find "$moodle_path" -name "*.feature" | sed "s|^$moodle_path/||" | sort
    end
end

# Function to list config settings
function __mdk_list_config_settings
    if command -q mdk
        command mdk config flatlist 2>/dev/null | cut -d':' -f1
    end
end

# Function to list database profiles
function __mdk_list_db_profiles
    if command -q mdk
        command mdk config show db 2>/dev/null | grep ".engine" | cut -d '.' -f 2
    end
end

# Function to list available scripts
function __mdk_list_scripts
    if command -q mdk
        command mdk run -l 2>/dev/null | cut -d ' ' -f 1
    end
end
# Add instance name completion where appropriate
complete -c mdk -n "__fish_seen_subcommand_from backport behat cron info install phpunit plugin purge remove uninstall update upgrade" -a "(__mdk_list_instances)" -d "Moodle instance"

# Add feature file completion for behat command
complete -c mdk -n "__fish_seen_subcommand_from behat; and __fish_contains_opt -s f feature" -a "(__mdk_list_behat_features)" -d "Feature file"

# Add config setting completion for config show and set commands
complete -c mdk -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from show set" -a "(__mdk_list_config_settings)" -d "Config setting"

# Add database profile completion for create command
complete -c mdk -n "__fish_seen_subcommand_from create; and __fish_contains_opt -s e engine dbprofile" -a "(__mdk_list_db_profiles)" -d "Database profile"

# Add database profile completion for install command
complete -c mdk -n "__fish_seen_subcommand_from install; and __fish_contains_opt -s e engine dbprofile" -a "(__mdk_list_db_profiles)" -d "Database profile"

# Add script completion for install and create commands
complete -c mdk -n "__fish_seen_subcommand_from install create; and __fish_contains_opt -s r run" -a "(__mdk_list_scripts)" -d "Script to run"

# Add script completion for run command
complete -c mdk -n "__fish_seen_subcommand_from run; and not __fish_contains_opt -s l list" -a "(__mdk_list_scripts)" -d "Script to run"
