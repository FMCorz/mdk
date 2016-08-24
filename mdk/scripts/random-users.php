<?php
/**
 * Create a set of users with random names and pictures. Also fixes admin with missing email.
 *
 * User names are s1, s2 etc or t1, t2 or m1, m2 - all passwords are test.
 */

define('CLI_SCRIPT', true);
require(dirname(__FILE__).'/config.php');
require_once($CFG->libdir . '/filelib.php');
require_once($CFG->libdir . '/gdlib.php');

// How many of each.
$STUDENTS = 20;
$TEACHERS = 3;
$MANAGERS = 2;


/**
 * Fetch a new user record from the API
 */
function get_random_user() {
    $json = file_get_contents('https://randomuser.me/api/');
    $fields = json_decode($json);
    $fields = reset($fields->results);

    return $fields;
}

/**
 * Download and process a profile picture ready to be set in a user record.
 */
function download_picture($fields, $userid) {
    global $CFG;

    $url = new moodle_url($fields->picture->large);

    // Temporary file name
    if (empty($CFG->tempdir)) {
        $tempdir = $CFG->dataroot . "/temp";
    } else {
        $tempdir = $CFG->tempdir;
    }
    $picture = $tempdir . '/' . 'mdk_script_users.jpg';

    download_file_content($url->out(false), null, null, false, 5, 2, false, $picture);

    // Ensures retro compatibility
    if (class_exists('context_user')) {
        $context = context_user::instance($userid);
    } else {
        $context = get_context_instance(CONTEXT_USER, $userid, MUST_EXIST);
    }

    $picture = process_new_icon($context, 'user', 'icon', 0, $picture);

    return $picture;
}

/**
 * Create a set of accounts with a given prefix.
 */
function create_accounts($howmany, $prefix) {
    global $DB;

    for ($i = 0; $i < $howmany; $i++) {
        $user = get_random_user();
        $num = $i + 1;
        $username = $prefix . $num;
        echo "Creating user $username " . $user->name->first . ' ' . $user->name->last . ' ' . $username . "@example.com\n";
        $record = create_user_record($username, 'test');
        $record->email = $username . '@example.com';
        $record->firstname = ucfirst($user->name->first);
        $record->lastname = ucfirst($user->name->last);

        $record->picture = download_picture($user, $record->id);

        $DB->update_record('user', $record);
    }
}

// First get the admin user and see if they have an email.

$admin = $DB->get_record('user', array('username' => 'admin'));

if (!$admin) {
    die("Could not find admin user.");
}

// Fix admin user that is incomplete.
if (empty($admin->email)) {
    $user = get_random_user();
    echo "Fixing admin user admin " . $user->name->first . ' ' . $user->name->last . ' ' . $user->email . "\n";
    $admin->email = $user->email;
    $admin->firstname = ucfirst($user->name->first);
    $admin->lastname = ucfirst($user->name->last);

    $admin->picture = download_picture($user, $admin->id);

    $DB->update_record('user', $admin);
}

// Now create the test accounts.

create_accounts($STUDENTS, 's');
create_accounts($TEACHERS, 't');
create_accounts($MANAGERS, 'm');
