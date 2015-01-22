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
    }
    return $coursecache[$courseid];
}

function mdk_get_role($username) {
    static $rolecache = array();

    if (!preg_match('/^[stm]\d+$/', $username)) {
        // Only enrol users we created with mdk.
        return false;
    }

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

// Use regexp to match only valid usernames (if supported).
if ($DB->sql_regex_supported()) {
    $sql = "SELECT id, username
              FROM {user}
             WHERE username ".$DB->sql_regex()." ?";
    $params = array('^[stm][0-9]+$');
} else {
    $match = $DB->sql_like('username', '?');
    $sql = "SELECT id, username
              FROM {user}
             WHERE ( ".
             $DB->sql_like('username', ':student')." OR ".
             $DB->sql_like('username', ':teacher')." OR ".
             $DB->sql_like('username', ':manager')." )
             AND deleted = 0";
    $params = array('student' => 's%', 'teacher' => 't%', 'manager' => 'm%');
}

$users = $DB->get_recordset_sql($sql, $params);
$courses = $DB->get_records_select('course', 'id > ?', array(1), '', 'id, startdate');
$plugin = new enrol_manual_plugin();

foreach ($users as $user) {
    $role = mdk_get_role($user->username);
    if (!$role) {
        continue;
    }
    mtrace('Enrolling ' . $user->username);
    foreach ($courses as $course) {
        $instance = mdk_get_enrol_instance($course->id);
        // Enrol the day before the course startdate, because if we create a course today its default
        // startdate is tomorrow, and we would never realise why the enrolments do not work.
        $plugin->enrol_user($instance, $user->id, $role->id, $course->startdate - 86400, 0);
    }
}

$users->close();
