<?php
/**
 * Create a set of users with phonetic information - in this case, Japanese furigana.
 */

define('CLI_SCRIPT', true);
require(dirname(__FILE__).'/config.php');
require_once($CFG->libdir . '/filelib.php');
require_once($CFG->libdir . '/gdlib.php');

// True to download a gravatar.
define('MDK_AVATAR', true);

$jpdata = "s1,test,森田,忍,もりた,しのぶ
s2,test,羽海野,チカ,うみの,ちか
s3,test,竹本,祐太,たけもと,ゆうた
s4,test,山田,あゆみ,やまだ,あゆみ
s5,test,真山,巧,まやま,たくみ
s6,test,花本,修司,はなもと,しゅうじ
s7,test,花本,はぐみ,はなもと,はぐみ
s8,test,原田,理花,はらだ,りか
s9,test,藤原,拓海,ふじわら,たくみ
s10,test,藤原,文太,ふじわら,ぶんた
s11,test,池谷,浩一郎,いけたに,こういちろう
s12,test,武内,樹,たけうち,いつき
s13,test,高橋,涼介,たかはし,りょうすけ
s14,test,高橋,啓介,たかはし,けいすけ
s15,test,中村,賢太,なかむら,けんた
s16,test,中里,毅,なかざと,たけし
s17,test,庄司,慎吾,しょうじ,しんご
s18,test,佐藤,真子,さとう,まこ
s19,test,須藤,京一,すどう,きょういち
s20,test,岩城,清次,いわき,せいじ";
$jpusers = explode("\n", $jpdata);

$data = "t1,test,Herbert,Garrison,t1@localhost
t2,test,Sheila,Brovslovski,t2@localhost
t3,test,Liane,Cartman,t3@localhost
m1,test,Officer,Barbady,m1@localhost
m2,test,Principal,Victoria,m2@localhost
m3,test,Randy,Marsh,m3@localhost";
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

// Create all the Japanese users.
foreach ($jpusers as $user) {
    if (empty($user)) {
        continue;
    }
    $user = explode(',', $user);
    if ($DB->record_exists('user', array('username' => $user[0], 'deleted' => 0))) {
        continue;
    }

    mtrace('Creating user ' . $user[0]);
    $u = create_user_record($user[0], $user[1]);
    $u->firstname = $user[3];
    $u->lastname = $user[2];
    $u->firstnamephonetic = $user[5];
    $u->lastnamephonetic = $user[4];
    $u->email = $user[0] . '@localhost';
    $u->city = 'Tokyo';
    $u->country = 'JP';
    $u->lang = 'ja';
    $u->description = 'たやすいことではない';
    $u->url = 'http://moodle.org';
    $u->idnumber = '';
    $u->institution = 'Moodle HQ';
    $u->department = 'Extreme Science';
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
