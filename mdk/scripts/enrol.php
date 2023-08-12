<?php
/**
 * Enrol users in all the courses.
 *
 * Users with username starting with:
 * - s become students
 * - t become teachers
 * - m become managers
 *
 * In every single course on the site.
 */

define('CLI_SCRIPT', true);
require(__DIR__ . '/config.php');
require_once($CFG->libdir . '/accesslib.php');
require_once($CFG->dirroot . '/enrol/manual/lib.php');

function mdk_get_enrol_instance($courseid) {
    global $DB;
    static $coursecache = array();
    if (!isset($coursecache[$courseid])) {
        $coursecache[$courseid] = $DB->get_record('enrol', array('courseid' => $courseid, 'enrol' => 'manual'));
        if (!$coursecache[$courseid]) {
            mtrace("Could not find manual enrolment method for course {$courseid}.");
        }
    }
    return $coursecache[$courseid];
}

function mdk_get_role($username) {
    static $rolecache = array();
    $letter = substr($username, 0, 1);
    switch ($letter) {
        case 's':
            $archetype = 'student';
            break;
        case 't':
            $archetype = 'editingteacher';
            break;
        case 'm':
            $archetype = 'manager';
            break;
        default:
            return false;
    }
    if (!isset($rolecache[$archetype])) {
        $role = get_archetype_roles($archetype);
        $rolecache[$archetype] = reset($role);
    }
    return $rolecache[$archetype];
}

$sql = "SELECT id, username
          FROM {user}
         WHERE (username LIKE 's%'
            OR username LIKE 't%'
            OR username LIKE 'm%')
           AND deleted = 0
           AND username NOT LIKE 'tool_generator_%'";
$users = $DB->get_recordset_sql($sql, array());
$courses = $DB->get_records_select('course', 'id > ?', array(1), '', 'id, startdate');
$plugin = new enrol_manual_plugin();

foreach ($users as $user) {
    mtrace('Enrolling ' . $user->username);
    $role = mdk_get_role($user->username);
    if (!$role) {
        continue;
    }
    foreach ($courses as $course) {
        $instance = mdk_get_enrol_instance($course->id);
        if (!$instance) {
            continue;
        }
        // Enrol the day before the course startdate, because if we create a course today its default
        // startdate is tomorrow, and we would never realise why the enrolments do not work.
        $plugin->enrol_user($instance, $user->id, $role->id, $course->startdate - 86400, 0);
    }
}

$users->close();
