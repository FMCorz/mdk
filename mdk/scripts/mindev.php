<?php
/**
 * Sets the instance ready for developers.
 *
 * This script does not turn all developer settings on,
 * only a subset in order to keep performance to its maximum.
 *
 * Don't forget that you'll have to purge caches more often!
 */

define('CLI_SCRIPT', true);
require(dirname(__FILE__).'/config.php');

function mdk_set_config($name, $value, $plugin = null) {
    set_config($name, $value, $plugin);
    $value = is_bool($value) ? (int) $value : $value;

    if ($plugin) {
        // Make a fancy name.
        $name = "$plugin/$name";
    }
    mtrace("Setting $name to $value");
}

// Set developer level.
mdk_set_config('debug', DEBUG_DEVELOPER);

// Display debug messages.
mdk_set_config('debugdisplay', 1);

// Increase session lifetime to forever.
mdk_set_config('sessiontimeout', 52 * WEEKSECS);

// Any kind of password is allowed.
mdk_set_config('passwordpolicy', 0);

// Allow web cron.
mdk_set_config('cronclionly', 0);

// Debug the performance.
mdk_set_config('perfdebug', 15);

// Debug the information of the page.
mdk_set_config('debugpageinfo', 1);

// Allow themes to be changed from the URL.
mdk_set_config('allowthemechangeonurl', 1);

// Disable modintro for lazy devs.
mdk_set_config('requiremodintro', 0, 'book');
mdk_set_config('requiremodintro', 0, 'folder');
mdk_set_config('requiremodintro', 0, 'imscp');
mdk_set_config('requiremodintro', 0, 'page');
mdk_set_config('requiremodintro', 0, 'resource');
mdk_set_config('requiremodintro', 0, 'url');

// Disabling user tours.
$DB->set_field('tool_usertours_tours', 'enabled', 0);

//
// Now we make sure that the performance-heavy related settings are disabled.
//

// Disable theme designer mode.
mdk_set_config('themedesignermode', 0);

// Cache JavaScript.
mdk_set_config('cachejs', 0);

// Use string caching.
mdk_set_config('langstringcache', 0);

// Use YUI combo loading.
mdk_set_config('yuicomboloading', 1);

// Don't cache templates.
mdk_set_config('cachetemplates', 0);
