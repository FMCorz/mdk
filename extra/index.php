<?php

define('STABLE', 1);
define('INTEGRATION', 2);
define('FEATURE', 4);

if (isset($_GET['phpunit'])) {
    mdk::fetch_phpunit_status($_GET['phpunit']);
}

class mdk {
    public static function get_instance() {
        if (!isset($_GET['instance'])) {
            return;
        }
        return self::sanitize_instance($_GET['instance']);
    }

    public static function sanitize_instance($instance) {
        // Only alphanumeric and some symbols.
        return preg_replace('/[^a-zA-Z0-9_\-]/', '', $instance);
    }

    public static function get_instance_dir($instance) {
        $instancedir = getcwd() . DIRECTORY_SEPARATOR . $instance;
        if (!file_exists($instancedir)) {
            return;
        }
        return $instancedir;
    }

    public static function fetch_phpunit_status($type = "progress") {
        $instance = self::get_instance();

        if (!$instance) {
            header('HTTP/1.1 403 Forbidden');
            echo "No instance requested\n";
            die;
        }

        $dir = self::get_instance_dir($instance);
        if (!$dir) {
            header('HTTP/1.1 404 Not Found');
            echo $dir;
            die;
        }

        $file = $dir . DIRECTORY_SEPARATOR . 'phpunit' . DIRECTORY_SEPARATOR . 'status.json';
        if (!file_exists($file)) {
            header('HTTP/1.1 404 Not Found');
            echo $file;
            die;
        }

        $start = isset($_GET['start']) ? $_GET['start'] : 0;

        $json = file_get_contents($file);
        $json = "[" . preg_replace('/}{/', '},{', $json) . "]";
        $content = json_decode($json);
        if (!is_array($content)) {
            die;
        }

        $output = new stdClass();
        $output->status = '';
        $output->failures = array();
        $output->testcount = 0;
        $output->totaltests = 0;

        $thisrun = 0;
        foreach ($content as $item) {
            if ($item->event == 'suiteStart') {
                if ($item->suite == '') {
                    $output->totaltests += $item->tests;
                } else {
                    $thisrun = $item->tests;
                }
            } else if ($item->event == 'test') {
                if ($item->status == 'pass') {
                    $output->status .= '.';
                    $output->testcount++;
                    $thisrun--;
                } else {
                    $output->status .= 'F';
                    $output->failures = $item;
                    $output->testcount += $thisrun;
                }
            }
        }
        echo json_encode($output);
        die;
    }

    public static function get_instances() {

        static $instances = null;

        if ($instances !== null) {
            return $instances;
        }

        // Assume that we are in the mdk extras directory.
        $path = dirname(getcwd());
        $dirs = scandir($path);

        // Instances have three types:
        $instances = array(
            FEATURE => array(),
            INTEGRATION => array(),
            STABLE => array(),
        );

        foreach ($dirs as $dir) {
            $name = $dir;
            $fulldir = $path . DIRECTORY_SEPARATOR . $dir;
            if ($dir == '.' || $dir == '..' || !is_dir($fulldir)) {
                continue;
            }
            if (!file_exists($fulldir . "/lib/moodlelib.php")) {
                continue;
            }

            $type = 'stable';

            if (preg_match('/^s.*/', $name)) {
                $type = STABLE;
            } else if (preg_match('/^i.*/', $name)) {
                $type = INTEGRATION;
            } else {
                $type = FEATURE;
            }

            $instances[$type][$fulldir] = $name;
        }

        return $instances;
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Moodle SDK Web Interface</title>

    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/css/bootstrap.min.css">

    <!-- Optional theme -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/css/bootstrap-theme.min.css">

    <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
    <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
      <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->

    <!-- Font Awesome icons -->
    <link href="//maxcdn.bootstrapcdn.com/font-awesome/4.2.0/css/font-awesome.min.css" rel="stylesheet">
    <style>
        table td,
        table th {
            text-align: center;
            min-width: 110px;
        }

        .tab-content {
            overflow: auto;
        }

        .tab-content iframe {
            width: 100%;
            height: 100%;
        }

        .container {
            max-width: 730px;
        }

        .type-label,
        .btn-mdk > span {
            min-width: 23px;
            min-height: 23px;
        }

        .type-label,
        .btn-mdk {
            padding: 6px;
        }

        .type-label {
            display: block;
            padding: 6px 16px;
            font-size: 18px;
            line-height: 1.33;
            border-radius: 6px;
            border: 1px;
        }
        pre {
            white-space: pre-wrap !important;
        }
    </style>

</head>
<body>

    <div class="container">
        <div class="page-header">
            <h1>Moodle SDK</h1>
        </div>
        <div class="panel panel-default">
            <!-- Default panel contents -->
            <div class="panel-heading">Detected MDK Instances</div>
            <!-- Table -->
            <table class="table">
                <thead>
                    <tr>
                        <th>Instance</th>
                        <th>Type</th>
                        <th>MDK Extra</th>
                        <th>PHPUnit</th>
                        <th>Behat</th>
                    </tr>
                </thead>
                <tbody>
<?php

$instances = mdk::get_instances();
foreach ($instances as $instancetype => $instancelist) {
    switch ($instancetype) {
        case FEATURE:
            $type = 'Feature';
            break;
        case INTEGRATION:
            $type = 'Integration';
            break;
        case STABLE:
        default:
            $type = 'Stable';
            break;
    }
    foreach ($instancelist as $instance => $name) {
echo <<<EOF
            <tr data-instance="{$name}">
                <td>
                    <a href="../{$name}">
                        <button type="button" class="btn btn-lg btn-mdk btn-primary btn-block">{$name}</button>
                    </a>
                </td>
                <td>
                    <span class="label label-info type-label">{$type}</span>
                </td>
                <td>
                    <a href="{$name}">
                        <button type="button" class="btn btn-lg btn-mdk btn-info"><span class="glyphicon glyphicon-log-in"></span></button></a>
EOF;
echo <<<EOF
                </td>
                <td>
EOF;
echo <<<EOF
                    <a href="{$name}/phpunit">
                        <button type="button" class="btn btn-lg btn-mdk btn-info"><span class="glyphicon glyphicon-log-in"></span></button></a>
                    <a href="{$name}/phpunit/status.tap">
                        <button type="button" class="livelogs phpunit btn btn-lg btn-mdk btn-info" data-toggle="modal" data-target="#phpunit">
                            <span class="glyphicon glyphicon-play-circle"></span>
                        </button>
                    </a>
EOF;
echo <<<EOF
                </td>
                <td>
EOF;
echo <<<EOF
                    <a href="{$name}/behat">
                        <button type="button" class="btn btn-lg btn-mdk btn-info"><span class="glyphicon glyphicon-log-in"></span></button></a>
                    <a href="{$name}/behat/pretty.txt">
                        <button type="button" class="livelogs behat btn btn-lg btn-mdk btn-info" data-toggle="modal" data-target="#behat">
                            <span class="glyphicon glyphicon-play-circle"></span>
                        </button></a>
EOF;
echo <<<EOF
                </td>
            </tr>
EOF;
    }
}

?>
                        </tbody>
                    </div>
                </div>
            </table>
        </div>
    </div>

    <!-- PHPUnit Live Logs Modal -->
    <div class="modal " id="phpunit" tabindex="-1" role="dialog" aria-labelledby="phpunitLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>
                    <h4 class="modal-title" id="phpunitLabel">PHPUnit Logs <small class="instancename"></small></h4>
                </div>
                <div class="modal-body">
                    <div role="tabpanel">

                        <!-- Nav tabs -->
                        <ul class="nav nav-tabs" role="tablist">
                            <li role="presentation" class="active"><a data-action="poll" data-fullpath="" data-phpunit="progress" data-results-processor="phpunitResultsProcessor" href="#phpunit-progress" aria-controls="phpunit-progress" role="tab" data-toggle="tab">Progress</a></li>
                            <li role="presentation"><a data-action="poll" data-fullpath="" data-phpunit="fails" data-results-processor="phpunitResultsProcessor" href="#phpunit-fails" aria-controls="phpunit-fails" role="tab" data-toggle="tab">Fails</a></li>
                        </ul>

                        <!-- Tab panes -->
                        <div class="tab-content">
                            <div role="tabpanel" class="tab-pane active" id="phpunit-progress"><pre></pre></div>
                            <div role="tabpanel" class="tab-pane" id="phpunit-fails"><pre></pre></div>
                        </div>

                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-lg btn-mdk btn-default" data-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal -->
    <div class="modal " id="behat" tabindex="-1" role="dialog" aria-labelledby="behatLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>
                    <h4 class="modal-title" id="behatLabel">Behat Logs <small class="instancename"></small></h4>
                </div>
                <div class="modal-body">
                    <div role="tabpanel">

                        <!-- Nav tabs -->
                        <ul class="nav nav-tabs" role="tablist">
                            <li role="presentation" class="active"><a data-action="poll" data-instancepath="behat/progress.txt" href="#behat-progress" aria-controls="behat-progress" role="tab" data-toggle="tab">Progress</a></li>
                            <li role="presentation" class=""><a data-action="poll" data-instancepath="behat/fails.txt" href="#behat-fails" aria-controls="behat-fails" role="tab" data-toggle="tab">Fails</a></li>
                            <li role="presentation" class=""><a data-action="poll" data-instancepath="behat/pretty.txt" href="#behat-pretty" aria-controls="behat-pretty" role="tab" data-toggle="tab">Pretty</a></li>
                            <li role="presentation" class=""><a data-action="browse" data-path="behat" href="#behat-browse" aria-controls="behat-browse" role="tab" data-toggle="tab">Browse</a></li>
                        </ul>

                        <!-- Tab panes -->
                        <div class="tab-content">
                            <div role="tabpanel" class="tab-pane active" id="behat-progress"><pre></pre></div>
                            <div role="tabpanel" class="tab-pane" id="behat-fails"><pre></pre></div>
                            <div role="tabpanel" class="tab-pane" id="behat-pretty"><pre></pre></div>
                            <div role="tabpanel" class="tab-pane" id="behat-browse"></div>
                        </div>

                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-lg btn-mdk btn-default" data-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    </div>


    <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.js"></script>
    <!-- Latest compiled and minified JavaScript -->
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/js/bootstrap.js"></script>
    <script>
        var page = {
            updater: null,

            init: function() {
                $('.modal').on('shown.bs.modal', function(e) {
                    var clickedRegion = $( e.relatedTarget ),
                        clickedButton = clickedRegion.closest('button'),
                        row = clickedRegion.closest('tr'),
                        instance = row.data('instance'),
                        modal = $(e.target);

                    // Note the instance on the modal.
                    modal.data('instance', instance);

                    // And set the instance name.
                    modal.find('.instancename').html(instance);

                    // Show the panel content.
                    page.showPanelContent();

                    // Hack to update the height.
                    $(this).closest('.modal').find('.tab-content').css('maxHeight', $(window).height() - 255);
                });

                $('.modal a[data-toggle="tab"]').on('shown.bs.tab', function(e) {
                    // Show the panel content.
                    page.showPanelContent();

                    // Hack to update the height.
                    $(this).closest('.modal').find('.tab-content').css('maxHeight', $(window).height() - 255);
                });

                $('table').delegate('.livelogs', 'click', function(e) {
                    e.preventDefault();
                });

            },

            showPanelContent: function(options) {
                // Cancel any active timeout.
                window.clearTimeout(page.updater);

                // Get the active dialogue.
                var dialog = $( '.modal:visible' );
                if (typeof dialog === 'undefined') {
                    return;
                }

                var instance = dialog.data('instance');

                    // Get the active tab.
                var tab = dialog.find( '.nav-tabs .active a' ),

                    // Get the active tab-content.
                    tabContent = dialog.find( '.tab-content .active' ),

                    // Find out what the tab action is.
                    action = tab.data('action');

                if (typeof action === 'undefined') {
                    return;
                }

                if (action === 'poll') {
                    var path;

                    // First check for an instancepath.
                    path = tab.data('instancepath');
                    if (typeof path !== 'undefined') {
                        path = instance + '/' + path;
                    } else {
                        path = tab.data('fullpath');
                    }

                    // Still no path. Return.
                    if (typeof path === 'undefined') {
                        return;
                    }

                    var data = {
                            instance: instance,
                            now: $.now()
                        },
                        tabData = tab.data();

                    for (var attr in tabData) {
                        var attrType = typeof tabData[attr];
                        if (attrType !== "function" && attrType !== "object" && attrType !== "array") {
                            data[attr] = tabData[attr];
                        }
                    }

                    $.ajax({
                        url: path,
                        data: data,
                        ajaxSend: function() {
                            // TODO Add the loading spinner.
                        }
                    }).done(function(data) {
                        var resultProcessor = tab.data('results-processor');
                        if (resultProcessor && $.isFunction(page[resultProcessor])) {
                            data = page[resultProcessor].apply(this, [tab, tabContent, data]);
                        }
                        tabContent.find( 'pre' ).html(data.toString());
                    }).always(function() {
                        // Remove the loading spinner.
                        // Run the query again after a brief pause.
                        page.updater = setTimeout(page.showPanelContent, 200);
                    });
                } else if (action === 'browse') {
                    var path = tab.data('path');
                    tabContent.empty().append($("<iframe />").attr('src', instance + '/' + path));
                }
            },
            phpunitResultsProcessor: function(tab, tabContent, data) {
                var type = tab.data('phpunit'),
                    content = $.parseJSON(data);
                if (type == 'progress') {
                    return content.status;
                } else if (type == 'fails') {
                    // Update the start point.
                    return content.failures;
                }
            }
        };
        page.init();

    </script>
</body>
</html>
