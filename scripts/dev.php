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

// Do not cache JavaScript.
set_config('cachejs', 0);

// Do not use YUI combo loading.
set_config('yuicomboloading', 0);

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
