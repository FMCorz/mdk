<?php
// This file is part of Moodle - http://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Moodle is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Moodle.  If not, see <http://www.gnu.org/licenses/>.

/**
 * Script to refresh the services and external functions.
 *
 * @package    mdk
 * @copyright  2015 Frédéric Massart - FMCorz.net
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

define('CLI_SCRIPT', true);
require('config.php');
require($CFG->libdir . '/upgradelib.php');

mtrace('Updating services of core');
external_update_descriptions('moodle');

$plugintypes = core_component::get_plugin_types();
foreach ($plugintypes as $plugintype => $dir) {
    $plugins = core_component::get_plugin_list($plugintype);
    foreach ($plugins as $plugin => $dir) {
        $component = $plugintype . '_' . $plugin;
        mtrace('Updating services of ' . $component);
        external_update_descriptions($component);
    }
}

external_update_services();

