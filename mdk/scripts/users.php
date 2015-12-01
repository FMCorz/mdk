<?php
/**
 * Create a set of users
 */

define('CLI_SCRIPT', true);
require(dirname(__FILE__).'/config.php');
require_once($CFG->libdir . '/filelib.php');
require_once($CFG->libdir . '/gdlib.php');

// True to download a gravatar.
define('MDK_AVATAR', true);

$data = "s1,test,Eric,Cartman,s1@example.com
s2,test,Stan,Marsh,s2@example.com
s3,test,Kyle,Broflovski,s3@example.com
s4,test,Kenny,McCormick,s4@example.com
s5,test,Butters,Stotch,s5@example.com
s6,test,Clyde,Donovan,s6@example.com
s7,test,Jimmy,Valmer,s7@example.com
s8,test,Timmy,Burch,s8@example.com
s9,test,Wendy,Testaburger,s9@example.com
s10,test,Bebe,Stevens,s10@example.com
t1,test,Herbert,Garrison,t1@example.com
t2,test,Sheila,Brovslovski,t2@example.com
t3,test,Liane,Cartman,t3@example.com
m1,test,Officer,Barbady,m1@example.com
m2,test,Principal,Victoria,m2@example.com
m3,test,Randy,Marsh,m3@example.com";
$users = explode("\n", $data);

// Create all the users.
foreach ($users as $user) {
    if (empty($user)) {
        continue;
    }
    $user = explode(',', $user);
    if ($DB->record_exists('user', array('username' => $user[0], 'deleted' => 0))) {
        continue;
    }

    mtrace('Creating user ' . $user[0]);
    $u = create_user_record($user[0], $user[1]);
    $u->firstname = $user[2];
    $u->lastname = $user[3];
    $u->email = $user[4];
    $u->city = 'Perth';
    $u->country = 'AU';
    $u->lang = 'en';
    $u->description = 'Who\'s your daddy?';
    $u->url = 'http://moodle.org';
    $u->idnumber = '';
    $u->institution = 'Moodle HQ';
    $u->department = 'Rock on!';
    $u->phone1 = '';
    $u->phone2 = '';
    $u->address = '';

    // Adds an avatar to the user. Will slow down the process.
    if (MDK_AVATAR) {
        $params = array(
            'size' => 160,
            'force' => 'y',
            'default' => 'wavatar'
        );
        $url = new moodle_url('http://www.gravatar.com/avatar/' . md5($u->id . ':' . $u->username), $params);

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
            $context = context_user::instance($u->id);
        } else {
            $context = get_context_instance(CONTEXT_USER, $u->id, MUST_EXIST);
        }

        $u->picture = process_new_icon($context, 'user', 'icon', 0, $picture);
    }

    $DB->update_record('user', $u);
}
