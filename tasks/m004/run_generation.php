<?php
$_SERVER['DOCUMENT_ROOT'] = '/home/bitrix/ext_www/mhave.ru';
require($_SERVER['DOCUMENT_ROOT'].'/bitrix/modules/main/include/prolog_before.php');

if (!CModule::IncludeModule('seo')) {
    echo "Failed to load seo module\n";
    exit;
}

use Bitrix\Seo\Sitemap\Generator;
use Bitrix\Seo\Sitemap\Type\Step;

echo "Starting sitemap generation for ID 1...\n";

$generator = new Generator(1);
$step = Step::getFirstStep();
$state = [];

$generator->init($step, $state);

while ($generator->getStep() < Step::STEPS[Step::STEP_INDEX]) {
    $currentStep = $generator->getStep();
    echo "Running step " . $currentStep . "... (" . $generator->getStatusMessage() . ")\n";
    
    $ok = $generator->run();
    if (!$ok) {
        echo "Error: Generator failed at step " . $currentStep . "\n";
        exit(1);
    }
    
    $step = $generator->getStep();
    $state = $generator->getState();
    $generator->init($step, $state);
}

echo "Sitemap generation completed successfully!\n";
