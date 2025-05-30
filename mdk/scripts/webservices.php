<?php
/**
 * Entirely enables the Web Services.
 */

define('CLI_SCRIPT', true);
require(dirname(__FILE__).'/config.php');
require_once($CFG->libdir.'/testing/generator/data_generator.php');
require_once($CFG->libdir.'/accesslib.php');
require_once($CFG->libdir.'/externallib.php');
require_once($CFG->dirroot.'/webservice/lib.php');

// We don't really need to be admin, except to be able to see the generated tokens
// in the admin settings page, while logged in as admin.
if (class_exists(\core\cron::class)) {
    \core\cron::setup_user();
} else {
    cron_setup_user();
}

// Enable the Web Services.
set_config('enablewebservices', 1);

// Enable mobile web services.
set_config('enablemobilewebservice', 1);

// Enable Web Services documentation.
set_config('enablewsdocumentation', 1);

// Enable each protocol.
set_config('webserviceprotocols', 'amf,rest,soap,xmlrpc,restful');

// Enable mobile service.
$webservicemanager = new webservice();
$mobileservice = $webservicemanager->get_external_service_by_shortname(MOODLE_OFFICIAL_MOBILE_SERVICE);
$mobileservice->enabled = 1;
$webservicemanager->update_external_service($mobileservice);

// Enable capability to use REST protocol.
assign_capability('webservice/rest:use', CAP_ALLOW, $CFG->defaultuserroleid, SYSCONTEXTID, true);

// Rename Web Service user that was created with test username, whoops.
$legacyuser = $DB->get_record('user', ['username' => 'testtete']);
if ($legacyuser) {
    $DB->update_record('user', ['id' => $legacyuser->id, 'username' => 'mdkwsuser']);
}

// Create the Web Service user.
$user = $DB->get_record('user', ['username' => 'mdkwsuser']);
if (!$user) {
    $user = new stdClass();
    $user->username = 'mdkwsuser';
    $user->firstname = 'Web';
    $user->lastname = 'Service';
    $user->password = 'test';

    $dg = new testing_data_generator();
    $user = $dg->create_user($user);
}

// Rename role that was create with test shortname.
if ($legacyroleid = $DB->get_field('role', 'id', ['shortname' => 'testtete'])) {
    $DB->update_record('role', ['id' => $legacyroleid, 'shortname' => 'mdkwsrole']);
}

// Create a role for Web Services with all permissions.
if (!$roleid = $DB->get_field('role', 'id', ['shortname' => 'mdkwsrole'])) {
    $roleid = create_role('MDK Web Service', 'mdkwsrole', 'MDK: All permissions given by default.', '');
}

// Allow context levels.
$context = context_system::instance();
set_role_contextlevels($roleid, array($context->contextlevel));

// Assign all permissions.
if (method_exists($context, 'get_capabilities')) {
    $capabilities = $context->get_capabilities();
} else{
    $capabilities = fetch_context_capabilities($context);
}
foreach ($capabilities as $capability) {
    assign_capability($capability->name, CAP_ALLOW, $roleid, $context->id, true);
}

// Allow role switches.
$allows = get_default_role_archetype_allows('assign', 'manager');

foreach ($allows as $allowid) {
    if ($DB->record_exists('role_allow_assign', ['roleid' => $roleid, 'allowassign' => $allowid])) {
        continue;
    }
    core_role_set_assign_allowed($roleid, $allowid);
}

// Mark dirty.
role_assign($roleid, $user->id, $context->id);
$context->mark_dirty();

// Create a new service with all functions for the user.
$webservicemanager = new webservice();
if (!$service = $DB->get_record('external_services', array('shortname' => 'mdk_all'))) {
    $service = new stdClass();
    $service->name = 'MDK: All functions';
    $service->shortname = 'mdk_all';
    $service->enabled = 1;
    $service->restrictedusers = 1;
    $service->downloadfiles = 1;
    $service->uploadfiles = 1;
    $service->id = $webservicemanager->add_external_service($service);
}
$functions = $webservicemanager->get_not_associated_external_functions($service->id);
foreach ($functions as $function) {
    $webservicemanager->add_external_function_to_service($function->name, $service->id);
}
if (!$webservicemanager->get_ws_authorised_user($service->id, $user->id)) {
    $adduser = new stdClass();
    $adduser->externalserviceid = $service->id;
    $adduser->userid = $user->id;
    $webservicemanager->add_ws_authorised_user($adduser);
}

// Generate a token for the user.
if (!$token = $DB->get_field('external_tokens', 'token', array('userid' => $user->id, 'externalserviceid' => $service->id))) {
    $token = external_generate_token(EXTERNAL_TOKEN_PERMANENT, $service->id, $user->id, $context, 0, '');
}
mtrace('User \'webservice\' token: ' . $token);
