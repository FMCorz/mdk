<?php
/**
 * Create a set of users
 */

define('CLI_SCRIPT', true);
require(dirname(__FILE__).'/config.php');
require_once($CFG->libdir . '/filelib.php');
require_once($CFG->libdir . '/gdlib.php');

// True to download an avatar.
define('MDK_AVATAR', true);

// Random data.
$CITIES    = ['Perth', 'Brussels', 'London', 'Johannesburg', 'New York', 'Paris', 'Tokyo', 'Manila', 'São Paulo'];
$COUNTRIES = ['AU', 'BE', 'UK', 'SA', 'US', 'FR', 'JP', 'PH', 'BR'];
$DEPARTMENTS = ['Marketing', 'Development', 'Business', 'HR', 'Communication', 'Management'];

// User generator.
$generator = new mdk_randomapi_users_generator();

// Fix admin user.
$admin = $DB->get_record('user', array('username' => 'admin'));
if ($admin && empty($admin->email)) {
    mtrace('Fill admin user\'s email');
    $admin->email = 'admin@example.com';
    $DB->update_record('user', $admin);
}

// Create all the users.
foreach ($generator->get_users() as $user) {
    if (empty($user) || empty($user->username)) {
        continue;
    }
    if ($DB->record_exists('user', array('username' => $user->username, 'deleted' => 0))) {
        continue;
    }

    $locationindex = array_rand($CITIES);

    mtrace('Creating user ' . $user->username);
    $u = create_user_record($user->username, $user->password);
    $u->firstname = $user->firstname;
    $u->lastname = $user->lastname;
    $u->email = $user->email;
    $u->city = !empty($user->city) ? $user->city : $CITIES[$locationindex];
    $u->country = !empty($user->country) ? $user->country : $COUNTRIES[$locationindex];
    $u->lang = 'en';
    $u->description = '';
    $u->url = 'http://moodle.org';
    $u->idnumber = '';
    $u->institution = 'Moodle HQ';
    $u->department = $DEPARTMENTS[array_rand($DEPARTMENTS)];
    $u->phone1 = '';
    $u->phone2 = '';
    $u->address = '';

    // Adds an avatar to the user. Will slow down the process.
    if (MDK_AVATAR && !empty($user->pic)) {
        $url = new moodle_url($user->pic);

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

/**
 * Users generator.
 */
class mdk_users_generator {

    protected $users;

    public function __construct() {
        $this->users = $this->generate_users();
    }

    public function generate_users() {
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

        $id = 3;
        $urlparams = array(
            'size' => 160,
            'force' => 'y',
            'default' => 'wavatar'
        );
        $users = array_map(function($user) use (&$id, $urlparams) {
            $data = (object) array_combine(['username', 'password', 'firstname', 'lastname', 'email'], explode(',', trim($user)));
            $data->pic = new moodle_url('http://www.gravatar.com/avatar/' . md5($id++ . ':' . $data->username), $urlparams);
            return $data;
        }, explode("\n", $data));
        return $users;
    }

    public function get_users() {
        return $this->users;
    }

}

/**
 * Users generator from randomuser.me.
 */
class mdk_randomapi_users_generator extends mdk_users_generator {

    public function generate_users() {
        $curl = new curl([
            'CURLOPT_CONNECTTIMEOUT' => 2,
            'CURLOPT_TIMEOUT' => 5
        ]);
        $json = $curl->get('https://randomuser.me/api/?inc=name,picture,location,nat&results=16');
        $data = json_decode($json);
        if (!$data) {
            return parent::generate_users();
        }

        $usernames = ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 't1', 't2', 't3', 'm1', 'm2', 'm3'];
        $users = array_map(function($user) use (&$usernames) {
            $username = array_shift($usernames);
            return (object) [
                'username' => $username,
                'password' => 'test',
                'firstname' => ucfirst($user->name->first),
                'lastname' => ucfirst($user->name->last),
                'email' => $username . '@example.com',
                'city' => ucfirst($user->location->city),
                'country' => $user->nat,
                'pic' => $user->picture->large
            ];
        }, $data->results);

        return $users;
    }

}
