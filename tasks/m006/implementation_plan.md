# M006: Stabilize child sitemaps

Optimize and stabilize the delivery and generation of the child sitemap files (`sitemap-files.xml` and `sitemap-iblock-9.xml`). This ensures search engines do not experience timeouts or partial content issues when crawling these endpoints.

## User Review Required

> [!IMPORTANT]
> To eliminate Apache and PHP-FPM execution overhead when serving static XML sitemaps, we propose serving them directly via Nginx. We will add a custom configuration file `sitemaps.conf` in Nginx's site-specific settings.

## Open Questions

> [!NOTE]
> 1. Do you want to apply this direct Nginx delivery rule for all `sitemap*.xml` files (including `sitemap.xml` and all iblock sub-sitemaps), or only specifically for `sitemap-files.xml` and `sitemap-iblock-9.xml`? (We recommend applying it to all to improve general site performance under heavy crawling).
> 2. Is there any active testing/staging environment we should verify first, or should we directly apply the Nginx changes to production (with strict syntax checking via `nginx -t` before reload)?
> 3. Do you have a preferred caching duration (e.g., `expires 24h` or `expires 12h`) for the sitemaps served by Nginx?

## Proposed Changes

### Nginx Configuration

#### [NEW] [sitemaps.conf](file:///etc/nginx/bx/site_settings/mhave.ru/sitemaps.conf)
Define location block to intercept all requests to `sitemap*.xml` and serve them directly as static files.
- Enable direct disk read.
- Set appropriate `Content-Type` header.
- Set Cache-Control and Expires headers.
- Disable access logging for sitemaps to reduce IO load.

---

### Task Progress Tracking

#### [NEW] [task.md](file:///home/egor/Документы/Antigravity_Project/mhave.ru/seo/tasks/m006/task.md)
The checklist tracking plan execution progress.

---

### Walkthrough & Documentation

#### [NEW] [walkthrough.md](file:///home/egor/Документы/Antigravity_Project/mhave.ru/seo/tasks/m006/walkthrough.md)
Detailed walkthrough of the changes, verification outputs, and benchmark timings.

## Verification Plan

### Automated/Console Tests
- Verify Nginx configuration syntax using `nginx -t`.
- Reload Nginx via `systemctl reload nginx` (or `service nginx reload`).
- Run sequential `curl` checks with headers display:
  ```bash
  curl -I https://mhave.ru/sitemap-files.xml
  curl -I https://mhave.ru/sitemap-iblock-9.xml
  curl -I https://mhave.ru/sitemap.xml
  ```
- Measure latency and TTFB:
  ```bash
  curl -o /dev/null -s -w 'TTFB: %{time_starttransfer}s | Total: %{time_total}s\n' https://mhave.ru/sitemap-files.xml
  ```

### Manual Verification
- Confirm XML formatting is valid.
- Verify in Yandex Webmaster that sitemaps are accepted and respond with 200 OK.
