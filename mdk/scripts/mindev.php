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

// Adds FirePHP
$firephp = "
// FirePHP
if (@include_once('FirePHPCore/fb.php')) {
    ob_start();
}
";
$conffile = dirname(__FILE__) . '/config.php';
if ($content = file_get_contents($conffile)) {
    if (strpos($content, "include_once('FirePHPCore/fb.php')") === false) {
        if ($f = fopen($conffile, 'a')) {
            fputs($f, $firephp);
            fclose($f);
        }
    }
}

//
// Now we make sure that the performance-heavy related settings are disabled.
//

// Disable theme designer mode.
mdk_set_config('themedesignermode', 0);

// Cache JavaScript.
mdk_set_config('cachejs', 1);

// Use string caching.
mdk_set_config('langstringcache', 1);

// Use YUI combo loading.
mdk_set_config('yuicomboloading', 1);

