<?php
/**
 * Sets the instance ready for developers.
 *
 * When you add a setting here, please update undev.php.
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

// Enable theme designer mode.
mdk_set_config('themedesignermode', 1);

// Do not cache JavaScript.
mdk_set_config('cachejs', 0);

// Prevent core_string_manager application caching
mdk_set_config('langstringcache', 0);

// Do not use YUI combo loading.
mdk_set_config('yuicomboloading', 0);

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
