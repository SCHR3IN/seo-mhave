#!/bin/bash
# Sitemap generation and cleanup automation script
# Set absolute paths
DOC_ROOT="/home/bitrix/ext_www/mhave.ru"
LOG_FILE="$DOC_ROOT/seo/tasks/m004/sitemap_cron.log"

echo "=== Sitemap Generation and Clean-up run: $(date) ===" >> "$LOG_FILE"

# 1. Run Bitrix native sitemap generation
echo "Running Bitrix generation..." >> "$LOG_FILE"
/usr/bin/php -f "$DOC_ROOT/seo/tasks/m004/run_generation.php" >> "$LOG_FILE" 2>&1
GEN_STATUS=$?

if [ $GEN_STATUS -ne 0 ]; then
    echo "ERROR: Bitrix generation failed with exit code $GEN_STATUS." >> "$LOG_FILE"
    exit 1
fi

# 2. Run post-processing cleanup script
echo "Running sitemap cleanup script..." >> "$LOG_FILE"
/usr/bin/python3 "$DOC_ROOT/seo/tasks/m004/clean_sitemap.py" >> "$LOG_FILE" 2>&1
CLEAN_STATUS=$?

if [ $CLEAN_STATUS -ne 0 ]; then
    echo "ERROR: Sitemap cleanup failed with exit code $CLEAN_STATUS." >> "$LOG_FILE"
    exit 1
fi

echo "Sitemap process completed successfully!" >> "$LOG_FILE"
exit 0
