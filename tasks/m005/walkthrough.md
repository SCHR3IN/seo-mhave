# Walkthrough - Soft 404 Resolution (Task M005)

## Overview
This task resolves the Soft 404 issue with the `/contacts/stores/` path. Instead of returning 200 OK or 301 redirects, invalid store pages now return a proper **HTTP 404 Not Found** status code. We also updated navigation menus and sitemaps to prevent indexing of deprecated/orphaned paths.

## Key Changes
1. **Bitrix 404 Page Config**:
   - Page: `/contacts/stores/index.php`
   - Initialized Bitrix Core (`prolog_before.php`) prior to sending headers.
   - Forced HTTP status code to 404 using `CHTTP::SetStatus("404 Not Found")`.
   - Set `@define("ERROR_404","Y")` to inform Bitrix of the 404 status.
   - Rendered standard site 404 layout.

2. **Navigation Menu Cleanup**:
   - Modified `.bottom5.menu.php` and `info/.left.menu.php` to point the "Магазины" link from `/contacts/stores/` to `/contacts/`.

3. **Catalog Component Store Path**:
   - Changed `STORE_PATH` parameter in `/catalog/index.php` from `"/contacts/stores/#store_id#/"` to `"/contacts/"`.

4. **Sitemap Generation & Verification**:
   - Executed sitemap generation and automated clean-up run on the production server.
   - Verified that both `/contacts/stores/` and `/contacts/stores/moskva/404/` are correctly excluded from `/sitemap.xml`.

## Verification Results
- **`/contacts/stores/` Headers**:
  ```http
  HTTP/2 404 
  server: nginx
  content-type: text/html; charset=UTF-8
  content-length: 157202
  ```
- **`/contacts/stores/moskva/404/` Headers**:
  ```http
  HTTP/2 404 
  server: nginx
  content-type: text/html; charset=UTF-8
  content-length: 157321
  ```
- **Sitemap Exclusion**:
  Running `curl -s https://mhave.ru/sitemap.xml | grep -i 'contacts/stores'` returned no matches, confirming the path is fully excluded from the public sitemap.
