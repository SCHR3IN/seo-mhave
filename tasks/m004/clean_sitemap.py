#!/usr/bin/env python3
import os
import re
import sys
import ssl
import urllib.request
import urllib.error
import urllib.robotparser
from urllib.parse import urlparse, urljoin
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor, as_completed

DOC_ROOT = "/home/bitrix/ext_www/mhave.ru"
DOMAIN = "mhave.ru"
BASE_URL = f"https://{DOMAIN}"
CONCURRENCY = 10
TIMEOUT = 10

# Bypass SSL errors if any
SSL_CONTEXT = ssl._create_unverified_context()

class RobotsMetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = ""
        self.robots = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'meta':
            name = attrs_dict.get('name', '').lower()
            content = attrs_dict.get('content', '').strip()
            if name == 'robots':
                self.robots = content
        elif tag == 'link':
            rel = attrs_dict.get('rel', '').lower()
            if rel == 'canonical':
                self.canonical = attrs_dict.get('href', '').strip()

def normalize_url(url):
    """Normalize URL and discard external or static resources."""
    if not url:
        return None
    url = url.strip()
    p = urlparse(url)
    domain = p.netloc or DOMAIN
    if domain != DOMAIN and domain != f"www.{DOMAIN}":
        return None
    path = p.path or "/"
    # Clean multiple slashes
    path = re.sub(r'/+', '/', path)
    # Ensure trailing slash for directories (paths without file extension)
    if not os.path.basename(path) or '.' not in os.path.basename(path):
        if not path.endswith('/'):
            path += '/'
    
    # We should reconstruct URL to secure HTTPS with no www
    return f"https://{DOMAIN}{path}"

def get_sitemap_urls():
    """Extract all unique URLs from sitemap-*.xml files."""
    urls = set()
    sitemap_pattern = re.compile(r'^sitemap-.*\.xml$')
    
    for filename in os.listdir(DOC_ROOT):
        if sitemap_pattern.match(filename):
            filepath = os.path.join(DOC_ROOT, filename)
            print(f"Parsing sitemap file: {filename}")
            try:
                tree = ET.parse(filepath)
                root = tree.getroot()
                namespace = ''
                if root.tag.startswith('{'):
                    namespace = root.tag.split('}')[0] + '}'
                
                for url_node in root.findall(f'.//{namespace}loc'):
                    if url_node.text:
                        url = normalize_url(url_node.text)
                        if url:
                            urls.add(url)
            except Exception as e:
                print(f"Error parsing sitemap {filename}: {e}", file=sys.stderr)
    return urls

def validate_url(url, rp):
    """Validate URL status, canonical, meta robots, and robots.txt."""
    parsed = urlparse(url)
    
    # 1. Check Robots.txt
    if not rp.can_fetch("*", url):
        return False, "disallowed by robots.txt"
        
    # 2. Check blacklist patterns
    if "?oid=" in url or "oid=" in parsed.query:
        return False, "contains SKU parameter oid"
    if "/contacts/stores/moskva/404/" in parsed.path:
        return False, "excluded Moscow soft 404 store page"
    if parsed.path in ["/404.php", "/500.html"]:
        return False, "system error page"
    if any(x in parsed.path for x in ["/auth/", "/basket/", "/login/", "/order/", "/personal/", "/sharebasket/"]):
        return False, "system directory"
        
    # 3. Check HTTP Status, Canonical and Meta Robots
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; MHAVECleaner/1.0; +https://mhave.ru/)'}
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=SSL_CONTEXT) as response:
            status = response.getcode()
            if status != 200:
                return False, f"HTTP status {status}"
                
            # Parse HTML for robots and canonical tags
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                return True, "valid non-html file (200)"
                
            html = response.read().decode('utf-8', errors='ignore')
            parser = RobotsMetaParser()
            parser.feed(html)
            
            # Check meta robots noindex
            robots_meta = parser.robots.lower()
            if "noindex" in robots_meta:
                return False, f"meta robots noindex: '{parser.robots}'"
                
            # Check canonical tag
            if parser.canonical:
                canonical_full = urljoin(url, parser.canonical)
                normalized_canonical = normalize_url(canonical_full)
                normalized_current = normalize_url(url)
                if normalized_canonical != normalized_current:
                    return False, f"non-canonical URL (canonical points to: {normalized_canonical})"
            
            return True, "valid"
            
    except urllib.error.HTTPError as e:
        return False, f"HTTP status {e.code}"
    except Exception as e:
        return False, f"connection/fetch error: {e}"

def main():
    print("Initializing robots.txt parser...")
    rp = urllib.robotparser.RobotFileParser()
    try:
        rp.set_url(f"{BASE_URL}/robots.txt")
        rp.read()
    except Exception as e:
        print(f"Warning: Failed to fetch robots.txt: {e}. Proceeding without robots.txt restrictions.")
        # Create dummy robots parser that allows everything
        class DummyRobotsParser:
            def can_fetch(self, useragent, url):
                return True
        rp = DummyRobotsParser()
        
    raw_urls = get_sitemap_urls()
    print(f"Found {len(raw_urls)} unique raw URLs in Bitrix sub-sitemaps.")
    
    valid_urls = []
    excluded_urls = []
    
    print(f"Validating URLs with concurrency={CONCURRENCY}...")
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = {executor.submit(validate_url, url, rp): url for url in raw_urls}
        for fut in as_completed(futures):
            url = futures[fut]
            try:
                is_valid, reason = fut.result()
                if is_valid:
                    valid_urls.append(url)
                    print(f" [OK] {url}")
                else:
                    excluded_urls.append((url, reason))
                    print(f" [EXCLUDE] {url} - {reason}")
            except Exception as e:
                excluded_urls.append((url, f"validation error: {e}"))
                print(f" [ERROR] {url} - {e}")
                
    # Sort valid URLs for consistency
    valid_urls.sort()
    
    # Save excluded URLs to a log file
    log_file = os.path.join(DOC_ROOT, "seo", "sitemap_cleanup.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "w", encoding="utf-8") as lf:
        lf.write("=== EXCLUDED SITEMAP URLS ===\n")
        for url, reason in sorted(excluded_urls):
            lf.write(f"{url} | {reason}\n")
    print(f"Logged {len(excluded_urls)} exclusions to {log_file}")
    
    # Generate flat sitemap.xml
    output_path = os.path.join(DOC_ROOT, "sitemap.xml")
    print(f"Writing clean sitemap.xml ({len(valid_urls)} URLs) to {output_path}...")
    
    # Build XML
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for url in valid_urls:
        url_node = ET.SubElement(urlset, "url")
        loc_node = ET.SubElement(url_node, "loc")
        loc_node.text = url
        
    # Write to file
    tree = ET.ElementTree(urlset)
    ET.indent(tree, space="  ", level=0)
    with open(output_path, "wb") as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(f, encoding="utf-8", xml_declaration=False)
        
    print("Sitemap optimization and generation complete!")

if __name__ == "__main__":
    main()
