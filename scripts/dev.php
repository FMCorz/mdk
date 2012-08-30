<?php
/**
 * Sets the instance ready for developers
 */

define('CLI_SCRIPT', true);
require(dirname(__FILE__).'/config.php');

// Set developer level.
set_config('debug', DEBUG_DEVELOPER);

// Disply debug messages
set_config('debugdisplay', 1);

// Any kind of password is allowed.
set_config('passwordpolicy', 0);

// Debug the performance.
set_config('perfdebug', 15);

// Debug the information of the page.
set_config('debugpageinfo', 1);

// Allow themes to be changed from the URL.
set_config('allowthemechangeonurl', 1);

// Adds FirePHP
$firephp = "
// FirePHP
if (@include_once('FirePHPCore/fb.php')) {
    ob_start();
}
";
if ($f = fopen(dirname(__FILE__).'/config.php', 'a')) {
    fputs($f, $firephp);
    fclose($f);
}
