UPDATE mdl_config SET value = DEBUG_DEVELOPER WHERE name = 'debug' LIMIT 1;
UPDATE mdl_config SET value = 0 WHERE name = 'passwordpolicy' LIMIT 1;
UPDATE mdl_config SET value = 15 WHERE name = 'perfdebug' LIMIT 1;
UPDATE mdl_config SET value = 1 WHERE name = 'debugpageinfo' LIMIT 1;
UPDATE mdl_config SET value = 1 WHERE name = 'allowthemechangeonurl' LIMIT 1;