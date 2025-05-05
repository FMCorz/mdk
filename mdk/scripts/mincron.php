<?php
/**
 * Disable scheduled tasks that may unnecessary slow down cron runs during development.
 */

define('CLI_SCRIPT', true);
require(dirname(__FILE__) . '/config.php');

$tasks = [
    '\core\task\h5p_get_content_types_task',
    '\core\task\check_for_updates_task',
    '\core\task\automated_backup_task',
    '\core\task\registration_cron_task',
    '\core\task\search_index_task',
    '\core\task\search_optimize_task',
    '\core\task\stats_cron_task'
];

$componentstodisable = [
    'tool_analytics',
    'tool_brickfield',
    'tool_langimport',
    'tool_monitor',
    'mod_bigbluebuttonbn',
    'mod_imscp',
];

[$insql, $inparams] = $DB->get_in_or_equal($componentstodisable);
$records = $DB->get_fieldset_select('task_scheduled', 'classname', "component $insql", $inparams);

$tasks = array_merge($tasks, array_values($records));
sort($tasks);
foreach ($tasks as $task) {
    mtrace('Disabling task ' . $task);
    $task = \core\task\manager::get_scheduled_task($task);
    $task->set_disabled(true);
    \core\task\manager::configure_scheduled_task($task);
}
