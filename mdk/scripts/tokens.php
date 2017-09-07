<?php
/**
 * Lists the external tokens.
 */

define('CLI_SCRIPT', true);
require(__DIR__ . '/config.php');

$tokens = $DB->get_recordset_sql("
    SELECT t.*, u.username, s.shortname AS sshortname, s.name AS sname
      FROM {external_tokens} t
      JOIN {user} u
        ON t.userid = u.id
      JOIN {external_services} s
        ON t.externalserviceid = s.id
  ORDER BY sname ASC, username ASC
");

mtrace(sprintf("%s %13s %20s", 'User ID', 'Username', 'Token'));
mtrace('');

$lastexternalserviceid = null;
$format = "[%' 5d] %' 16s: %s";
foreach ($tokens as $token) {
    if ($lastexternalserviceid != $token->externalserviceid) {
        $title = sprintf("%s [%s]", $token->sname, $token->sshortname);
        $lastexternalserviceid && mtrace('');
        mtrace($title);
        mtrace(str_repeat('-', strlen($title)));
        $lastexternalserviceid = $token->externalserviceid;
    }

    mtrace(sprintf($format, $token->userid, $token->username, $token->token));
}
$tokens->close();
