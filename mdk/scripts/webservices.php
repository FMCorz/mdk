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
cron_setup_user();

// Enable the Web Services.
set_config('enablewebservices', 1);

// Enable Web Services documentation.
set_config('enablewsdocumentation', 1);

// Enable each protocol.
set_config('webserviceprotocols', 'amf,rest,soap,xmlrpc');

// Create the Web Service user.
$user = $DB->get_record('user', array('username' => 'testtete'));
if (!$user) {
    $user = new stdClass();
    $user->username = 'testtete';
    $user->firstname = 'Web';
    $user->lastname = 'Service';
    $user->password = 'test';

    $dg = new testing_data_generator();
    $user = $dg->create_user($user);
}

// Create a role for Web Services with all permissions.
if (!$roleid = $DB->get_field('role', 'id', array('shortname' => 'testtete'))) {
    $roleid = create_role('Web Service', 'testtete', 'MDK: All permissions given by default.', '');
}
$context = context_system::instance();
set_role_contextlevels($roleid, array($context->contextlevel));
role_assign($roleid, $user->id, $context->id);
if (method_exists($context, 'get_capabilities')) {
    $capabilities = $context->get_capabilities();
} else{
    $capabilities = fetch_context_capabilities($context);
}
foreach ($capabilities as $capability) {
    assign_capability($capability->name, CAP_ALLOW, $roleid, $context->id, true);
}
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
