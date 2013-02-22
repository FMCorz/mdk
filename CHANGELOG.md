Changelog
=========

v0.3
----

* New command `behat` which is equivalent to `phpunit`
* New command `pull` to fetch a patch from a tracker issue
* New script `webservices` to entirely enable the web services
* `push` now updates the Git information on the tracker issue (Thanks to Damyon Wiese)
* `phpunit` can also run the tests after initialising the environment
* `update --update-cache` can proceed with the updates after updating the cached remotes
* `info` can be used to edit settings ($CFG properties) in config.php
* `init` has been a bit simplified
* Basic support of shell commands in aliases
* The settings in config.json are read from different locations, any missing setting will be read from config-dist.json
* Bug fixes
