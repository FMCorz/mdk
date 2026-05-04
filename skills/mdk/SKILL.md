---
name: mdk
description: Explains the Moodle Development Kit—the `mdk` CLI (PyPI moodle-sdk) for local Moodle installs, Docker, tests, and HQ tracker/git workflows. Use when the user mentions MDK or moodle-sdk, refers to a local Moodle dev instance, or is working in a Moodle repository and wants something done with `mdk`.
---

# Moodle Development Kit (MDK)

Help the user work with **MDK**, Moodle’s developer CLI (`mdk`, installed as `moodle-sdk`). Discover commands from the project docs and with `mdk <command> --help`.

## Who uses it

- **Core contributors (Moodle HQ–style):** many instances, integration remote, tracker—`fix`, `backport`, `pull`, `rebase`, `push`, `tracker`. Only assume this when the discussion is clearly upstream (MDL issues, stable branches, security workflow).
- **Everyone else by default:** one or a few local Moodle trees—`create`, `install`, `upgrade`, `run`, `php`, `open`, caches, tests, optional `mdk docker`.

## Agent preferences

1. **Prefer instance-scoped work:** Prefer `cd` to the target Moodle root (`version.php`) so the active instance is unambiguous. If you need the path first, use `mdk info -v path <identifier>`, then `cd`.
2. **MDK settings:** Prefer `mdk config` over reading or manipulating MDK config files directly.
3. **Docker detection:** Only infer Docker vs host when the workflow depends on it and the user has not said. Prefer MDK-native signals such as `mdk config show docker.automaticContainerLookup`, `MDK_DOCKER_NAME`, or clearly MDK-managed containers over generic guesses.
4. **Risky / destructive commands:** do not run `mdk remove` (or pass `remove`’s non-interactive flags) unless the user has **explicitly** confirmed they want that instance destroyed. See **Risky commands**.

## Docker vs host (when it matters)

Guess **only** when the workflow depends on it (e.g. first-time setup path), and unclear from the user's instructions.

- **Likely Docker**:
  - `mdk config show docker.automaticContainerLookup` is `true`, or
  -  `docker ps` shows `moodlehq/moodle-php-apache` containers tied to MDK.
- **Likely host-only**: Classic local Apache/nginx + DB on the machine.

Docker installed alone proves nothing.

## Common goals

| Goal | Direction |
|------|-----------|
| New checkout | `mdk create …` |
| New instance (host) | `mdk create …` → `mdk install`; optional `mdk run dev` |
| New instance (Docker) | `mdk create …` → `mdk docker up …` → `mdk install` with a **db** profile (see that section) |
| Update code | `mdk update …`; add `--upgrade` to run the upgrade |
| Run upgrade | `mdk upgrade …` |
| Caches | `mdk purge …` |
| Dev setup | `mdk run mindev` or `mdk run dev`; optionally follow with `mdk run mincron` |
| Tests | `mdk phpunit`, `mdk behat` |
| Cron | `mdk cron`; single task: `-t <component>:<taskname>` |
| Nuke instance | `mdk remove` (destructive—see **Risky commands**) |
| Uninstall only | `mdk uninstall` |
| Instance info | `mdk info`, `mdk info -l`, `mdk info -v <field> [<identifier>]` |
| MDK settings | `mdk config …` |

**Tracker / git (core)**

| Command | Direction |
|---------|-----------|
| `mdk fix` | Branch from tracker issue |
| `mdk pull` | Patch from issue |
| `mdk push` | Push; `--update-tracker`, `--patch` when relevant |
| `mdk rebase`, `backport` | Across branches/instances |
| `mdk tracker` | Issue summary |

## Commands

Rough groups:

- **Lifecycle:** `create`, `install`, `remove`, `uninstall`, `info`
- **Day-to-day:** `php`, `run`, `upgrade`, `update`, `purge`, `cron`, `open`
- **Tests:** `phpunit`, `behat`
- **Docker:** `mdk docker` — subcommands include:
  - Moodle PHP container: `up`, `down`, `rm`, `stop`, `logs`
  - Postgres (and other docker DB profiles): `db up <profile>` — profile name = a key under **`db`** in `mdk config`.
  - Adminer: `adminer up`, `adminer down`, `adminer open`
  - Selenium: `selenium up`, `selenium down`
- **Toolbox:** `config`
- **HQ:** `fix`, `pull`, `push`, `rebase`, `backport`, `tracker`

### Moodle versions

Arguments requiring a Moodle version take a **branch code** (digits) or `main`, not a dotted release string: e.g. `411` → 4.11, `503` → 5.3, `main` → main branch.

## New instance (Docker)

Use this when the goal is a **new** Moodle tree running in **Docker**.

1. **Checkout** — `mdk create …`
2. **Choose a Docker DB profile** — you must use an MDK **DB profile** (a key under `db` in MDK config). List them with `mdk config show db` and pick the profile you will install against.
3. **Start the database container** — start the DB container for that profile: `mdk docker db up <profile>` (if not already running).
4. **Start the Moodle PHP container** — from that instance’s Moodle root, run `mdk docker up --port <n>`.
5. **Install** — from that instance’s Moodle root, run `mdk install --engine <profile> …` using the same `<profile>` you started in step 3.

### Flags for `mdk docker up`

- `-p` / `--port` — required until the instance is installed. Afterwards MDK can usually infer the host port from `wwwroot`.
- `-v` / `--php` — do not pass unless the user asks for a specific PHP version.

## Behat (Docker)

Assume the Moodle instance is **installed** and usable, with Moodle running in Docker (`mdk docker …`) when relevant.

1. **`$CFG->behat_profiles` in `config.php`** — Required so Behat knows how to reach Selenium on the Docker network. Below matches `mdk docker selenium …` container names (`selenium-firefox`, `selenium-chromium`, `selenium-chrome`) and the usual variants; treat as **recommended**, not mandatory verbatim:

```php
$CFG->behat_profiles = json_decode('{"default":{"browser":"firefox","wd_host":"http:\/\/selenium-firefox:4444\/wd\/hub"},"chromium":{"browser":"chrome","wd_host":"http:\/\/selenium-chromium:4444\/wd\/hub"},"chrome":{"browser":"chrome","wd_host":"http:\/\/selenium-chrome:4444\/wd\/hub"}}', true);
```

2. **Start Selenium** — `mdk docker selenium up --variant <firefox|chrome|chromium>`. If the user gave no preference, prefer **`chrome`**.

3. **Initial Behat setup inside Moodle** — from the instance root, run `mdk behat` **without** `--run` so MDK initialises Behat and prints the suggested command.

4. **Run tests** as requested — examples:

```bash
mdk behat -S -p chrome --run --skip-init --tags @<component>
mdk behat -S -p chrome --run --skip-init --feature relative/path/to/file.feature
mdk behat -S -p chrome --run --skip-init --feature relative/path/to/file.feature --testname "The scenario name"
mdk behat -S -p chrome --run --rerun
```

**Flags:**

- `-S` / `--no-selenium` — Skip MDK’s built-in handling for **non-Docker** Selenium (do use this when Selenium is already provided by `mdk docker selenium`).
- `-p` / `--profile` — Match **`$CFG->behat_profiles`** and the Selenium container you started (`default`, `chrome`, `chromium`, …).
- `--skip-init` — Faster reruns when Behat is already initialised on that instance.
- `--rerun` — Only scenarios that failed last time (`implies --run` in MDK).

## PHPUnit

Assume the Moodle instance is **installed** and you are in that instance’s Moodle root (`version.php`).

1. **Initial setup** — `mdk phpunit` without `-r` initialises the PHPUnit test environment.

2. **Run tests** — use `-r` / `--run`. Narrow scope with a **testsuite** (`-s` / `--testsuite`, a **file** (`-u` / `--unittest`, path relative to the Moodle root), or PHPUnit’s `--filter`.

3. **Faster reruns** — when the environment is already initialised, pass `-k` / `--skip-init`.

**Examples:**

```bash
mdk phpunit -r -w -n -s enrol_manual
mdk phpunit -r --skip-init -u relative/path/tests/example_test.php
mdk phpunit -r -q
```

**Flags:**

- `-r` / `--run` — Run PHPUnit after setup; without it, MDK only initialises and prints the command line it would use.
- `-k` / `--skip-init` — Skip the init step when the instance is already set up.
- `-s` / `--testsuite` — Testsuite name, typically a component or subsystem.
- `-u` / `--unittest` — Test file to run, as a path relative to the Moodle root.
- `-q` / `--stop-on-failure` — Stop on the first failure or error.
- `-w` / `--display-warnings` — Show details for tests that triggered warnings.
- `-n` / `--display-notices` — Show details for tests that triggered notices.

## Bundled `mdk run` scripts

Shipped scripts—invoke `mdk run <name>`. Summary:

| Script | Role |
|--------|------|
| `dev`, `mindev`, `undev` | Toggle dev-oriented Moodle settings |
| `setup` | Chain setup steps for a usable dev instance |
| `setupsecurity` | Security-remote clone helper (HQ-style) |
| `users`, `enrol`, `makecourse` | Test users, enrolment, sample course |
| `webservices`, `external_functions`, `tokens` | Webservices setup / definitions / tokens |
| `version` | Fix downgrade version clashes |
| `jsconfig` | Generate `jsconfig.json` for JS tooling |

Example: `mdk run dev` then `mdk run users` (from the instance root per invariants).

## Verbosity

The `debug` config key sets log level (`mdk config show debug`; default `info`). `mdk --debug` is equivalent to setting that key to `debug` for that run rather than the default `info`. MDK then logs more, including external commands it invokes (e.g. `docker`, `git`, `php` through MDK’s helpers).

## Risky commands

Some MDK operations are **irreversible** and are not moved to a system trash folder.

- **`mdk remove`** — Permanently deletes the instance: it **drops the instance’s database** and **deletes the instance directory tree** (and related symlinks MDK created). Uncommitted work, local branches, and file customisations under that tree are **gone** unless they exist elsewhere (e.g. another remote or backup). This is the main “lose your work” footgun for developers.

**Agents:** never invoke `mdk remove` based on inference or convenience (e.g. “start fresh”). Only run it when the user has **clearly and explicitly** asked to remove / delete / destroy **that** MDK instance (by name or unambiguous reference). Do not use `-y` or `-f` on `remove` to skip confirmation unless the user has explicitly requested non-interactive removal as part of the same instruction.

Apply the same caution to other commands whose primary effect is **destroying data or containers** (for example Docker removal subcommands) when the outcome would be permanent loss of the user’s environment or data.