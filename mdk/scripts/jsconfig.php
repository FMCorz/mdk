<?php
// This file is part of Moodle - http://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Moodle is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Moodle.  If not, see <http://www.gnu.org/licenses/>.

/**
 * The jsconfig Configuration Generator for MDK and Moodle.
 *
 * The jsconfig file is used by the JavaScript LSP, which is used by vscode and other IDEs.
 *
 * @copyright 2022 Andrew Lyons <andrew@nicols.co.uk>
 */
class jsconfig {

    protected $config;

    protected $ignoreddirs = [
        'CVS' => true,
        '_vti_cnf' => true,
        'amd' => true,
        'classes' => true,
        'db' => true,
        'fonts' => true,
        'lang' => true,
        'pix' => true,
        'simpletest' => true,
        'templates' => true,
        'tests' => true,
        'yui' => true,
    ];

    public function build(): void {
        if ($this->buildWithGrunt()) {
            echo "Built using Grunt task.\n";
        } else {
            $this->generateConfiguration();
        }
    }

    protected function buildWithGrunt(): bool {
        if (!file_exists(__DIR__ . '/.grunt/tasks/jsconfig.js')) {
            return false;
        }

        $command = "npx grunt jsconfig";
        $result = null;
        exec($command, $output, $result);
        if ($result === 0) {
            return true;
        }

        echo "Error encountered whilst building.\n";
        echo "Command: '{$command}'\n";
        echo "Return code: {$result}\n";
        echo "Error details follow:\n";
        echo "======\n";
        echo implode("\n", $output);
        echo "\n======\n\n";

        return false;
    }

    protected function generateConfiguration(): void {
        $this->config = (object) [
            'compilerOptions' => (object) [
                'baseUrl' => '.',
                'paths' => [
                    'core/*' => ['lib/amd/src/*'],
                ],
                'target' => 'es2015',
                'allowSyntheticDefaultImports' => false,
            ],
            'exclude' => [
                'node_modules',
            ],
            'include' => [
                'lib/amd/src/**/*',
            ],
        ];

        $this->loadComponents();
        $this->processSubsystems();
        $this->processPluginTypes((array) $this->componentList->plugintypes);

        ksort($this->config->compilerOptions->paths);
        sort($this->config->include);

        $this->writeConfiguration('jsconfig.json');
    }

    protected function loadComponents(): void {
        $componentSrc = file_get_contents(__DIR__ . "/lib/components.json");
        $this->componentList = json_decode($componentSrc);
    }

    protected function processSubsystems(): void {
        foreach ((array) $this->componentList->subsystems as $type => $path) {
            if ($path === null) {
                continue;
            }

            if (!empty($this->ignoreddirs[$type])) {
                continue;
            }

            $fulldir = "{$path}/amd/src";
            $this->config->include[] = "{$fulldir}/**/*";
            $this->config->compilerOptions->paths["core_{$type}/*"] = ["{$fulldir}/*"];
        }
    }

    protected function processPluginTypes(array $plugintypes): void {
        foreach ($plugintypes as $type => $path) {
            if ($path === null) {
                continue;
            }

            $items = new \DirectoryIterator(__DIR__ . "/{$path}");
            foreach ($items as $item) {
                if ($item->isDot() or !$item->isDir()) {
                    continue;
                }

                $pluginname = $item->getFilename();

                if (!$this->is_valid_plugin_name($type, $pluginname)) {
                    continue;
                }

                $fulldir = "{$path}/{$pluginname}/amd/src";
                $this->config->include[] = "{$fulldir}/**/*";
                $this->config->compilerOptions->paths["{$type}_{$pluginname}/*"] = ["{$fulldir}/*"];

                if (file_exists("{$path}/{$pluginname}/db/subplugins.json")) {
                    $subplugins = json_decode(file_get_contents("{$path}/{$pluginname}/db/subplugins.json"));
                    $this->processPluginTypes((array) $subplugins->plugintypes);
                }
            }
        }
    }

    protected function writeConfiguration(string $filepath): void {
        echo "Writing jsconfig configuration for jsconfig to {$filepath}\n";
        $configuration = json_encode($this->config, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
        file_put_contents(__DIR__ . DIRECTORY_SEPARATOR . $filepath, $configuration . "\n");
        $this->ensureGitIgnore($filepath);
    }

    protected function is_valid_plugin_name(string $plugintype, string $pluginname): bool {
        if ($plugintype === 'auth' and $pluginname === 'db') {
            // Special exception for this wrong plugin name.
            return true;
        } else if (!empty($this->ignoreddirs[$pluginname])) {
            return false;
        }

        if ($plugintype === 'mod') {
            // Modules must not have the same name as core subsystems.
            if (isset($this->componentList->subsystems->{$pluginname})) {
                return false;
            }

            // Modules MUST NOT have any underscores,
            // component normalisation would break very badly otherwise!
            return (bool)preg_match('/^[a-z][a-z0-9]*$/', $pluginname);

        } else {
            return (bool)preg_match('/^[a-z](?:[a-z0-9_](?!__))*[a-z0-9]+$/', $pluginname);
        }
    }

    protected function ensureGitIgnore(string $filepath): void {
        $gitignorepath = __DIR__ . '/.git/info/exclude';

        echo "Checking {$gitignorepath} for {$filepath}...";
        $lines = explode("\n", file_get_contents($gitignorepath));
        foreach ($lines as $line) {
            if ($line === $filepath) {
                // The file is already present.
                echo " already present.\n";
                return;
            }
        }

        echo " Not found - adding.\n";

        // File not present in the local gitignore.
        // Add it.
        $lines[] = '# Ignore the jsconfig.json file used by vscode (MDK).';
        $lines[] = $filepath;
        $lines[] = '';

        $content = implode("\n", $lines);

        file_put_contents($gitignorepath, $content);
    }
}

(new jsconfig())->build();
