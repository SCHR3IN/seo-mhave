#!/usr/bin/env python3
import os
import re
import csv
import sys
import time
import ssl
import subprocess
import urllib.request
import urllib.error
from urllib.parse import urlparse, urljoin
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor, as_completed

# Target Domain
DOMAIN = "mhave.ru"
BASE_URL = f"https://{DOMAIN}"
DOC_ROOT = "/home/bitrix/ext_www/mhave.ru"
CONCURRENCY = 15  # Multi-threaded crawling speed

# SSL Unverified Context for SSL bypass if needed
SSL_CONTEXT = ssl._create_unverified_context()

class SEOHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = set()
        self.title = ""
        self.description = ""
        self.h1s = []
        self.canonical = ""
        self.robots = ""
        self.og = {}
        
        self.in_title = False
        self.in_h1 = False
        self.current_h1 = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == 'a':
            href = attrs_dict.get('href')
            if href:
                self.links.add(href.strip())
        elif tag == 'title':
            self.in_title = True
        elif tag == 'meta':
            name = attrs_dict.get('name', '').lower()
            prop = attrs_dict.get('property', '').lower()
            content = attrs_dict.get('content', '').strip()
            
            if name == 'description':
                self.description = content
            elif name == 'robots':
                self.robots = content
            elif prop.startswith('og:'):
                self.og[prop] = content
        elif tag == 'link':
            rel = attrs_dict.get('rel', '').lower()
            if rel == 'canonical':
                self.canonical = attrs_dict.get('href', '').strip()
        elif tag == 'h1':
            self.in_h1 = True
            self.current_h1 = []

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        elif tag == 'h1':
            self.in_h1 = False
            self.h1s.append(" ".join(self.current_h1).strip())

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif self.in_h1:
            self.current_h1.append(data)


class RedirectTracker(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        self.redirects = []

    def redirect_request(self, req, fp, code, msg, hdrs, newurl):
        self.redirects.append((code, newurl))
        return super().redirect_request(req, fp, code, msg, hdrs, newurl)


def run_mysql_query(sql):
    """Executes a MySQL query using subprocess and returns list of dicts."""
    cmd = ["mysql", "-u", "usermhave", "-pS8(4b7C]X2u[E@t", "-h", "localhost", "dbmhave", "-B", "-e", sql]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = res.stdout.strip().split("\n")
        if not lines or (len(lines) == 1 and lines[0] == ""):
            return []
        headers = lines[0].split("\t")
        rows = []
        for line in lines[1:]:
            parts = line.split("\t")
            if len(parts) == len(headers):
                rows.append(dict(zip(headers, parts)))
        return rows
    except Exception as e:
        print(f"Database query error: {e}", file=sys.stderr)
        return []


def normalize_url(url):
    """Normalizes URL, filter out external, admin, and dynamic query params."""
    if not url:
        return None
        
    url_lower = url.lower().strip()
    if url_lower.startswith(('javascript:', 'mailto:', 'tel:', 'whatsapp:', 'tg:', '#')):
        return None
        
    p = urlparse(url)
    domain = p.netloc or DOMAIN
    if domain != DOMAIN and domain != f"www.{DOMAIN}":
        return None
        
    path = p.path
    if not path:
        path = "/"
        
    # Standard normalization of directory slashes
    if not os.path.basename(path) or '.' not in os.path.basename(path):
        if not path.endswith('/'):
            path += '/'
            
    # Clean duplicate slashes
    path = re.sub(r'/+', '/', path)
    
    # Exclude admin and utility routes
    for excl in ['/bitrix/', '/personal/', '/basket/', '/order/', '/auth/', '/search/', '/upload/']:
        if excl in path:
            return None
            
    # Discard common junk path patterns (emails, phone numbers, js calls in path)
    if 'void(' in path or '@' in path or '+' in path:
        return None
        
    # Clean query parameters, but preserve standard smart filters like /filter/.../apply/
    # If it is a catalog filter, we keep the path as-is.
    return f"https://{DOMAIN}{path}"



def extract_db_urls():
    """Extracts all active catalog, brands, blog/articles, and sales URLs from Bitrix tables."""
    print("Extracting URLs from Bitrix database...")
    urls = {}

    # 1. Catalog sections (IBlock 14)
    sections_raw = run_mysql_query("SELECT ID, CODE, IBLOCK_SECTION_ID, NAME FROM b_iblock_section WHERE IBLOCK_ID=14 AND ACTIVE='Y'")
    sections = {}
    for r in sections_raw:
        parent_id = int(r['IBLOCK_SECTION_ID']) if r['IBLOCK_SECTION_ID'] and r['IBLOCK_SECTION_ID'] != 'NULL' else None
        sections[int(r['ID'])] = (r['CODE'], parent_id, r['NAME'])

    def get_section_path(sec_id):
        if not sec_id or sec_id not in sections:
            return ""
        code, parent_id, _ = sections[sec_id]
        if parent_id:
            parent_path = get_section_path(parent_id)
            if parent_path:
                return f"{parent_path}/{code}"
        return code

    for sec_id, (code, _, name) in sections.items():
        path = get_section_path(sec_id)
        url = normalize_url(f"/catalog/{path}/")
        if url:
            urls[url] = {"type": "catalog_section", "source": "DB"}

    # 2. Catalog elements (IBlock 14)
    elements_raw = run_mysql_query("SELECT ID, CODE, IBLOCK_SECTION_ID, NAME FROM b_iblock_element WHERE IBLOCK_ID=14 AND ACTIVE='Y'")
    for r in elements_raw:
        sec_id = int(r['IBLOCK_SECTION_ID']) if r['IBLOCK_SECTION_ID'] and r['IBLOCK_SECTION_ID'] != 'NULL' else None
        sec_path = get_section_path(sec_id) if sec_id else ""
        url = normalize_url(f"/catalog/{sec_path}/{r['CODE']}/")
        if url:
            urls[url] = {"type": "catalog_product", "source": "DB"}

    # 3. Brands (IBlock 9)
    brands_raw = run_mysql_query("SELECT CODE FROM b_iblock_element WHERE IBLOCK_ID=9 AND ACTIVE='Y'")
    for r in brands_raw:
        url = normalize_url(f"/brands/{r['CODE']}/")
        if url:
            urls[url] = {"type": "brand", "source": "DB"}

    # 4. Blog / Articles (IBlock 16) - Mapped to /news/ on site
    articles_raw = run_mysql_query("SELECT CODE FROM b_iblock_element WHERE IBLOCK_ID=16 AND ACTIVE='Y'")
    for r in articles_raw:
        url = normalize_url(f"/news/{r['CODE']}/")
        if url:
            urls[url] = {"type": "article", "source": "DB"}

    # 5. Sales (IBlock 17)
    sales_raw = run_mysql_query("SELECT CODE FROM b_iblock_element WHERE IBLOCK_ID=17 AND ACTIVE='Y'")
    for r in sales_raw:
        url = normalize_url(f"/sales/{r['CODE']}/")
        if url:
            urls[url] = {"type": "promotion", "source": "DB"}

    # 6. Services (IBlock 19)
    services_raw = run_mysql_query("SELECT CODE FROM b_iblock_element WHERE IBLOCK_ID=19 AND ACTIVE='Y'")
    for r in services_raw:
        url = normalize_url(f"/services/{r['CODE']}/")
        if url:
            urls[url] = {"type": "service", "source": "DB"}

    print(f"Extracted {len(urls)} URLs from database.")
    return urls


def parse_sitemaps():
    """Parses local sitemap XML files and returns set of URLs."""
    print("Parsing sitemaps...")
    urls = set()

    def parse_file(filepath):
        if not os.path.exists(filepath):
            return
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            namespace = ''
            if root.tag.startswith('{'):
                namespace = root.tag.split('}')[0] + '}'
            
            if 'sitemapindex' in root.tag:
                for sm in root.findall(f'.//{namespace}sitemap'):
                    loc = sm.find(f'{namespace}loc')
                    if loc is not None and loc.text:
                        filename = loc.text.strip().split('/')[-1]
                        parse_file(os.path.join(DOC_ROOT, filename))
            else:
                for url_node in root.findall(f'.//{namespace}url'):
                    loc = url_node.find(f'{namespace}loc')
                    if loc is not None and loc.text:
                        url = normalize_url(loc.text.strip())
                        if url:
                            urls.add(url)
        except Exception as e:
            print(f"Error parsing {filepath}: {e}", file=sys.stderr)

    parse_file(os.path.join(DOC_ROOT, "sitemap.xml"))
    print(f"Extracted {len(urls)} URLs from sitemaps.")
    return urls


def fetch_url(url):
    """Fetches a URL and returns status, headers, HTML, response time, and followed url."""
    tracker = RedirectTracker()
    https_handler = urllib.request.HTTPSHandler(context=SSL_CONTEXT)
    opener = urllib.request.build_opener(tracker, https_handler)
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (compatible; MHAVECrawler/1.0; +https://mhave.ru/)'}
    )
    
    start_time = time.time()
    try:
        with opener.open(req, timeout=15) as response:
            resp_time = time.time() - start_time
            final_url = response.geturl()
            html_content = response.read().decode('utf-8', errors='ignore')
            status_code = 200
            
            if tracker.redirects:
                status_code = tracker.redirects[0][0]
                
            return {
                'url': url,
                'status_code': status_code,
                'final_url': final_url,
                'resp_time': resp_time,
                'html': html_content,
                'headers': dict(response.info())
            }
    except urllib.error.HTTPError as e:
        resp_time = time.time() - start_time
        print(f"HTTPError fetching {url}: {e.code} - {e.reason}", file=sys.stderr)
        return {
            'url': url,
            'status_code': e.code,
            'final_url': url,
            'resp_time': resp_time,
            'html': e.read().decode('utf-8', errors='ignore') if e.fp else '',
            'headers': dict(e.headers)
        }
    except Exception as e:
        resp_time = time.time() - start_time
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return {
            'url': url,
            'status_code': 0,  # Connection error
            'final_url': url,
            'resp_time': resp_time,
            'html': '',
            'headers': {}
        }



def analyze_page(url, fetch_res, sitemap_set, db_urls):
    """Parses page HTML and returns comprehensive SEO metadata dict."""
    html = fetch_res['html']
    status_code = fetch_res['status_code']
    
    parser = SEOHTMLParser()
    if status_code == 200 and html:
        try:
            parser.feed(html)
        except Exception as e:
            print(f"Error parsing HTML for {url}: {e}", file=sys.stderr)
            
    # Check robots directives from header
    robots_header = fetch_res['headers'].get('X-Robots-Tag', '').lower()
    robots_directive = parser.robots.lower() or robots_header
    
    # Identify type
    url_type = "static_page"
    db_info = db_urls.get(url)
    if db_info:
        url_type = db_info['type']
    elif '/catalog/' in url:
        if '/filter/' in url:
            url_type = "catalog_filter"
        else:
            url_type = "catalog_other"
            
    # Check action
    action = "leave"
    if status_code != 200:
        action = "redirect" if status_code in [301, 302] else "delete"
    elif "noindex" in robots_directive:
        if url in sitemap_set:
            action = "fix"  # Should not be in sitemap if noindex
        else:
            action = "leave"
    elif not parser.title or not parser.description:
        action = "fix"
        
    return {
        'url': url,
        'status_code': status_code,
        'response_time': round(fetch_res['resp_time'], 3),
        'url_type': url_type,
        'title': parser.title.strip(),
        'description': parser.description,
        'h1': parser.h1s[0] if parser.h1s else '',
        'canonical': parser.canonical or fetch_res['final_url'],
        'robots': robots_directive or 'index, follow',
        'og_title': parser.og.get('og:title', ''),
        'og_description': parser.og.get('og:description', ''),
        'og_image': parser.og.get('og:image', ''),
        'in_sitemap': 'Y' if url in sitemap_set else 'N',
        'in_database': 'Y' if url in db_urls else 'N',
        'action': action,
        'links': [normalize_url(urljoin(url, l)) for l in parser.links if normalize_url(urljoin(url, l))]
    }


def main():
    start_time = time.time()
    
    # 1. Collect Seed URLs
    db_urls = extract_db_urls()
    sitemap_urls = parse_sitemaps()
    
    all_urls = set(db_urls.keys()) | sitemap_urls
    all_urls.add(f"{BASE_URL}/")
    all_urls.add(f"{BASE_URL}/catalog/")
    all_urls.add(f"{BASE_URL}/brands/")
    all_urls.add(f"{BASE_URL}/news/")
    all_urls.add(f"{BASE_URL}/sales/")
    all_urls.add(f"{BASE_URL}/services/")
    
    # Clean None values if any
    all_urls = {u for u in all_urls if u}
    
    # Queue for crawl loop
    crawled_urls = {}
    queue = list(all_urls)
    
    print(f"Beginning crawl of {len(queue)} initial URLs...")
    
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        while queue:
            print(f"Processing batch of {len(queue)} URLs...")
            futures = {executor.submit(fetch_url, url): url for url in queue}
            next_queue = set()
            
            for fut in as_completed(futures):
                url = futures[fut]
                try:
                    res = fut.result()
                    # Analyze and extract metadata
                    page_meta = analyze_page(url, res, sitemap_urls, db_urls)
                    crawled_urls[url] = page_meta
                    
                    # If it is a valid HTML 200, discover new links
                    if res['status_code'] == 200:
                        for link in page_meta['links']:
                            if link not in crawled_urls and link not in next_queue:
                                next_queue.add(link)
                except Exception as e:
                    print(f"Exception fetching {url}: {e}", file=sys.stderr)
            
            # Continue queue with discovered links
            queue = list(next_queue)
            
    # Post-process: Detect duplicate titles and descriptions
    print("Post-processing metadata duplicates...")
    titles = {}
    descriptions = {}
    
    for url, meta in crawled_urls.items():
        t = meta['title'].lower()
        d = meta['description'].lower()
        if t:
            titles[t] = titles.get(t, 0) + 1
        if d:
            descriptions[d] = descriptions.get(d, 0) + 1
            
    # Update action if duplicate
    for url, meta in crawled_urls.items():
        t = meta['title'].lower()
        d = meta['description'].lower()
        if (t and titles.get(t, 0) > 1) or (d and descriptions.get(d, 0) > 1):
            if meta['action'] == 'leave':
                meta['action'] = 'fix'
                
    # Save to CSV
    csv_file = os.path.join(DOC_ROOT, "seo", "url_registry.csv")
    print(f"Writing registry of {len(crawled_urls)} URLs to {csv_file}...")
    
    columns = [
        'url', 'status_code', 'response_time', 'url_type', 'title', 
        'description', 'h1', 'canonical', 'robots', 
        'og_title', 'og_description', 'og_image', 
        'in_sitemap', 'in_database', 'action'
    ]
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for url, meta in sorted(crawled_urls.items()):
            row = {col: meta.get(col, '') for col in columns}
            writer.writerow(row)
            
    elapsed = time.time() - start_time
    print(f"Crawl completed in {elapsed:.2f} seconds. Unified registry saved successfully.")

if __name__ == "__main__":
    main()
