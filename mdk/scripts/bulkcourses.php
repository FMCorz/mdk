<?php
/**
 * Create a whole bunch of courses.
 */

define('CLI_SCRIPT', true);
define('NO_OUTPUT_BUFFERING', true);

define('BULKCOURSES_DEBUG', true);

require(dirname(__FILE__).'/config.php');
require_once($CFG->libdir. '/clilib.php');

// CLI options.
list($options, $unrecognized) = cli_get_params(
    array(
        'help' => false,
        'count' => false,
        'size' => false,
        'fixeddataset' => false,
        'filesizelimit' => false,
        'quiet' => false
    ),
    array(
        'h' => 'help'
    )
);

// Display help.
if (!empty($options['help']) || empty($options['count'])) {
    echo "
Utility to bulk create test courses with pseudo-random names that make sense.

Not for use on live sites; only works if debugging is set to DEVELOPER level,
and there's no way to bypass that because you would have to be *crazy* to run
this on a live server.

Options:
--count          Number of courses to generate (required)
--size           Size of course to create XS, S, M, L, XL, or XXL (default: XS)
--fixeddataset   Use a fixed data set instead of randomly generated data
--filesizelimit  Limits the size of the generated files to the specified bytes
--quiet          Do not show any output

-h, --help     Print out this help
";
    // Exit with error unless we're showing this because they asked for it.
    exit(empty($options['help']) ? 1 : 0);
}

// Check debugging is set to developer level.
if (!debugging('', DEBUG_DEVELOPER)) {
    cli_error(get_string('error_notdebugging', 'tool_generator'));
}

// Get options.
$sizename = $options['size'];
if (empty($options['size'])) {
    $sizename = 'XS';
}
$coursecount = intval($options['count']);
$quiet = $options['quiet'];
$fixeddataset = $options['fixeddataset'];
$filesizelimit = $options['filesizelimit'];

// Check size.
try {
    $size = tool_generator_course_backend::size_for_name($sizename);
} catch (coding_exception $e) {
    cli_error("Invalid size ($sizename). Use --help for help.");
}

function romanic_number($integer, $upcase = true)
{
    $table = array(
        'M'=>1000,
        'CM'=>900,
        'D'=>500,
        'CD'=>400,
        'C'=>100,
        'XC'=>90,
        'L'=>50,
        'XL'=>40,
        'X'=>10,
        'IX'=>9,
        'V'=>5,
        'IV'=>4,
        'I'=>1);
    $return = '';
    while($integer > 0)
    {
        foreach($table as $rom=>$arb)
        {
            if($integer >= $arb)
            {
                $integer -= $arb;
                $return .= $rom;
                break;
            }
        }
    }

    return $return;
}

$coursecodeprefixes = array(
    'CSP',
    'CSG',
    'ENS',
    'JLS',
    'CHN',
    'ENG',
    'HIS',
    'CMM',
    'POL'
);

$coursenamepools = array(

    // CSP
    array(
        'Data Structures',
        'Graphics Programming',
        'Security Programming'
    ),

    // CSG
    array(
        'Project Methods'
    ),

    // ENS
    array(
        'Mathematics'
    ),

    // JLS
    array(
        'Japanese'
    ),

    // CHN
    array(
        'Chinese'
    ),

    // ENG
    array(
        'English',
        'Literature'
    ),

    // HIS
    array(
        'History'
    ),

    // CMM
    array(
        'Communications'
    ),

    // POL
    array(
        'Political Thought',
        'Public Policy'
    )

);

$courselevels = array(
    array('Introductory'),
    array('Intermediate'),
    array('Advanced'),
    array('Post-graduate')
);

if (!$quiet) {
    echo "Desired course count: $coursecount\n";
}

$coursenames = array();

$coursenamelevels_empty = array();
for ($i = 0; $i < count ($coursenamepools); $i++) {
    $thisarray = array();
    for ($j = 0; $j < count($coursenamepools[$i]); $j++) {
        $thisarray[] = 0;
    }
    $coursenamelevels_empty[] = $thisarray;
}

$MAX_LEVEL = 4;
$coursenamenumbers_by_level = array();
for ($i = 0; $i < $MAX_LEVEL; $i++) {
    $coursenamenumbers_by_level[] = $coursenamelevels_empty;
}

while (count($coursenames) < $coursecount) {

    $course = new stdClass();

    // Name parts.
    $part_codeprefix = "SOU";
    $part_level = 3;
    $part_namecore = "Soup-making";
    $part_number = "I";

    // CODE PREFIX
    // Randomly select a course code prefix to use.
    $codeprefixidx = (rand() % count($coursecodeprefixes));

    // Get the human-readable code prefix.
    $part_codeprefix = $coursecodeprefixes[$codeprefixidx];

    // LEVEL
    // Figure out what the level should be.
    $part_level = rand() % $MAX_LEVEL;

    // NAME CORE
    // Randomly select a name core to use.
    $namecoreidx = (rand() % count($coursenamepools[$codeprefixidx]));

    // Get the human-readable name core.
    $part_namecore = $coursenamepools[$codeprefixidx][$namecoreidx];

    // NUMBER
    // Figure out the level to use.
    $suffixnum = ++$coursenamenumbers_by_level[$part_level][$codeprefixidx][$namecoreidx];
    $part_number = romanic_number($suffixnum);

    // CODE NUMBER
    $part_codenumber = ($part_level + 1) * 100;
    // Figure out the next available number.
    $codenumber = 0;
    foreach ($coursenamenumbers_by_level[$part_level][$codeprefixidx] as $key => $value) {
            $codenumber += $value;
    }
    $part_codenumber += $codenumber;

    // NAME PREFIX
    $part_nameprefix = $courselevels[$part_level][0];
    if (count($courselevels[$part_level]) > 1) {
        $part_nameprefix = $courselevels[$part_level][rand() % count($courselevels[$part_level])];
    }

    // Concatenate the name together from parts.
    $course->shortname = $part_codeprefix . $part_codenumber;
    $course->fullname = implode(
        ' ',
        array(
            $course->shortname,
            $part_nameprefix,
            $part_namecore,
            $part_number
        )
    );
    $coursenames[] = $course;

}

// Build the courses.
foreach ($coursenames as $course) {

    // Check shortname.
    if ($error = tool_generator_course_backend::check_shortname_available($course->shortname)) {
        cli_error($error);
    }

    // Switch to admin user account.
    \core\session\manager::set_user(get_admin());

    // Do backend code to generate course.
    // First, check the number of parameters the tool_generator_course_backend constructor takes.
    $constructor = new ReflectionMethod('tool_generator_course_backend', '__construct');
    $backend = null;
    switch ($constructor->getNumberOfParameters()) {
        case 5:
            // Extant Moodle as of March 4, 2015.
            $backend = new tool_generator_course_backend(
                $course->shortname,
                $size,
                $fixeddataset,
                $filesizelimit,
                empty($options['quiet'])
            );
            break;
        case 8:
            // Moodle with MDL-49224 integrated.
            $backend = new tool_generator_course_backend(
                $course->shortname,
                $size,
                $fixeddataset,
                $filesizelimit,
                empty($options['quiet']),
                $course->fullname,
                ' ',
                FORMAT_HTML
            );
            break;
        default:
            // Do nothing!
            break;
    }

    if ($backend) {
        $backend->make();
    }
}

// Let the user know at the end what's been created.
if (!$quiet) {
    echo "Generated course names:\n";

    foreach ($coursenames as $course) {
        printf(
            "%s (%s)\n",
            $course->shortname,
            $course->fullname
        );
    }
}
