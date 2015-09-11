<?php

define('CLI_SCRIPT', true);
require(dirname(__FILE__).'/config.php');
require_once($CFG->libdir.'/clilib.php');
require("$CFG->dirroot/version.php");

// Purge caches to ensure that all version information is up-to-date.
purge_all_caches();

cli_separator();
cli_heading('Update all version numbers');

$possiblecandidates = array();

// Check that the main version hasn't changed.
$versiondifference = false;
if ((float)$CFG->version !== $version) {
    $versiondifference = true;
}

$pluginmanager = core_plugin_manager::instance();
$plugininfo = $pluginmanager->get_plugins();
foreach ($plugininfo as $plugins) {
    foreach ($plugins as $key => $plugin) {
        $statuscode = $plugin->get_status();
        if ($statuscode == "downgrade") {
            $possiblecandidates[] = $plugin;
        }
    }
}

// Fix everything.
if ($versiondifference) {
    set_config('version', $version);
    mtrace('Main version updated');
}
if (!empty($possiblecandidates)) {

    foreach ($possiblecandidates as $plugin) {
        $name = $plugin->type . '_' . $plugin->name;
        set_config('version', $plugin->versiondisk, $name);
        mtrace($plugin->displayname . ' updated.');
    }
}
