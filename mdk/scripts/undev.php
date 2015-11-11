<?php
/**
 * Reset the dev settings to their defaults.
 * See dev.php
 */

define('CLI_SCRIPT', true);
require(dirname(__FILE__).'/config.php');
require_once($CFG->libdir . '/adminlib.php');

function mdk_set_config($name, $value, $plugin = null) {
    set_config($name, $value, $plugin);
    $value = is_bool($value) ? (int) $value : $value;

    if ($plugin) {
        // Make a fancy name.
        $name = "$plugin/$name";
    }
    mtrace("Setting $name to $value");
}

// Load all the settings.
if (class_exists('\core\session\manager')) {
    \core\session\manager::set_user(get_admin());
} else {
    session_set_user(get_admin());
}
$adminroot = admin_get_root();


// Debugging settings.
$settingspage = $adminroot->locate('debugging', true);
$settings = $settingspage->settings;

// Set developer level.
$default = $settings->debug->get_defaultsetting();
mdk_set_config('debug', $default);

// Display debug messages.
$default = $settings->debugdisplay->get_defaultsetting();
mdk_set_config('debugdisplay', $default);

// Debug the performance.
$default = $settings->perfdebug->get_defaultsetting();
mdk_set_config('perfdebug', $default);

// Debug the information of the page.
$default = $settings->debugpageinfo->get_defaultsetting();
mdk_set_config('debugpageinfo', $default);


// Site policies settings.
$settingspage = $adminroot->locate('sitepolicies', true);
$settings = $settingspage->settings;

// Any kind of password is allowed.
$default = $settings->passwordpolicy->get_defaultsetting();
mdk_set_config('passwordpolicy', $default);

// Allow web cron.
$default = $settings->cronclionly->get_defaultsetting();
mdk_set_config('cronclionly', $default);


// Theme settings.
$settingspage = $adminroot->locate('themesettings', true);
$settings = $settingspage->settings;

// Allow themes to be changed from the URL.
$default = $settings->allowthemechangeonurl->get_defaultsetting();
mdk_set_config('allowthemechangeonurl', $default);

// Enable designer mode.
$default = $settings->themedesignermode->get_defaultsetting();
mdk_set_config('themedesignermode', $default);


// Language settings.
$settingspage = $adminroot->locate('langsettings', true);
$settings = $settingspage->settings;

// Restore core_string_manager application caching.
$default = $settings->langstringcache->get_defaultsetting();
mdk_set_config('langstringcache', $default);


// Javascript settings.
$settingspage = $adminroot->locate('ajax', true);
$settings = $settingspage->settings;

// Do not cache JavaScript.
$default = $settings->cachejs->get_defaultsetting();
mdk_set_config('cachejs', $default);

// Do not use YUI combo loading.
$default = $settings->yuicomboloading->get_defaultsetting();
mdk_set_config('yuicomboloading', $default);

// Restore modintro for conciencious devs.
$resources = array('book', 'folder', 'imscp', 'page', 'resource', 'url');
foreach ($resources as $r) {
    $settingpage = $adminroot->locate('modsetting' . $r, true);
    $settings = $settingpage->settings;
    if (isset($settings->requiremodintro)) {
        $default = $settings->requiremodintro->get_defaultsetting();
        mdk_set_config('requiremodintro', $default, $r);
    }
}
