<?php
$_SERVER['DOCUMENT_ROOT'] = '/home/bitrix/ext_www/mhave.ru';
require($_SERVER['DOCUMENT_ROOT'].'/bitrix/modules/main/include/prolog_before.php');

if (!CModule::IncludeModule('seo')) {
    echo "Failed to load seo module\n";
    exit;
}

$sitemap = \Bitrix\Seo\SitemapTable::getById(1)->fetch();
if (!$sitemap) {
    echo "Sitemap ID 1 not found\n";
    exit;
}

$settings = unserialize($sitemap['SETTINGS']);

// Exclude Iblock 15 (SKU elements)
$settings['IBLOCK_ACTIVE'][15] = 'N';
$settings['IBLOCK_ELEMENT'][15] = 'N';

$newSettings = serialize($settings);

$res = \Bitrix\Seo\SitemapTable::update(1, array('SETTINGS' => $newSettings));
if ($res->isSuccess()) {
    echo "Successfully updated sitemap settings!\n";
} else {
    echo "Failed to update sitemap settings: " . implode(', ', $res->getErrorMessages()) . "\n";
}

$sitemapUpdated = \Bitrix\Seo\SitemapTable::getById(1)->fetch();
$settingsUpdated = unserialize($sitemapUpdated['SETTINGS']);
echo "=== UPDATED IBLOCK_ACTIVE FOR 15 ===\n";
echo "IBLOCK_ACTIVE[15] = " . $settingsUpdated['IBLOCK_ACTIVE'][15] . "\n";
echo "IBLOCK_ELEMENT[15] = " . $settingsUpdated['IBLOCK_ELEMENT'][15] . "\n";
