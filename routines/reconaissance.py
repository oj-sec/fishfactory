# Basic reconaissance module for Fishfactory

from playwright.sync_api import sync_playwright
import hashlib
from urllib.parse import urlparse
import requests
import base64
import mmh3
import socket
import ssl

def run(playwright, target, timeout=20000) -> None:

    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    page.set_default_timeout(timeout)

    stored_headers = []
    page.on("request", lambda request: stored_headers.append(request.headers))

    observations = {}

    page.goto(target)
    page.wait_for_load_state()        

    observations['title'] = page.title()
    observations['finalUrl'] = page.url

    screenshot_data = (page.screenshot(full_page=True))
    screenshot_hash = hashlib.sha256(screenshot_data).hexdigest()

    with open(f"screenshots/{screenshot_hash}", 'wb') as s:
        s.write(screenshot_data)
    
    observations['screenshotHash'] = screenshot_hash
    observations['faviconData'] = retrieve_favicons(page, stored_headers[0])
    ssl_fingerprint = get_ssl_fingerprint(page)
    observations['sslFingerprint'] = ssl_fingerprint

    domain = urlparse(target).netloc
    ip = socket.gethostbyname(domain)

    observations['domain'] = domain
    observations['ip'] = ip

    browser.close()

    return observations

def retrieve_favicons(page, headers):

    favicon_candidate_hrefs = []
    url_prefix = page.url.split("/")[0]
    domain = str(urlparse(page.url).netloc)
    
    # Handle web root case
    favicon_candidate_hrefs.append(url_prefix + "//" + domain + "/favicon.ico")
    favicon_candidate_hrefs.append(url_prefix + "//" + domain + "/favicon.png")

    # Handle tag case
    link_tags = page.locator('link').all()
    a_tags = page.locator('a').all()
    all_tags = list(dict.fromkeys(link_tags + a_tags))

    for item in all_tags:
        href = item.get_attribute('href')
        rel = item.get_attribute("rel")
        if href and "favicon" in href:
            favicon_candidate_hrefs.append(href)
        if rel and "favicon" in rel:
            favicon_candidate_hrefs.append(rel)
        elif href and href.endswith("ico"):
            favicon_candidate_hrefs.append(href)
        elif rel and rel.endswith("ico"):
            favicon_candidate_hrefs.append(rel)
        elif rel and "icon" in rel:
            favicon_candidate_hrefs.append(href)
        elif rel and "shortcut" in rel:
            favicon_candidate_hrefs.append(href)

    favicon_candidate_hrefs = list(dict.fromkeys(favicon_candidate_hrefs))

    # Ensure absolute paths
    for i in range(len(favicon_candidate_hrefs)):
        if not favicon_candidate_hrefs[i].startswith("http"):
            favicon_candidate_hrefs[i] = page.url.rstrip("/") + "/" + favicon_candidate_hrefs[i]

    favicons = download_favicons(favicon_candidate_hrefs, headers)

    return favicons
    
def download_favicons(candidates, headers):

    favicon_data = []

    for url in candidates:

        try:
            req = requests.get(url, headers=headers, timeout=3, verify=False)
            if "Content-Type" in req.headers.keys() or "content-type" in req.headers.keys():
                if "image" in req.headers['Content-Type'] or "image" in req.headers['content-type']:
                    if req:
                        favicon_data_encoded = base64.encodebytes(req.content)
                        favicon_hash = str(mmh3.hash(favicon_data_encoded))
                        temp = {}
                        temp['faviconUrl'] = url
                        temp['faviconHash'] = favicon_hash
                        favicon_data.append(temp)
                        with open(f"favicons/{favicon_hash}", 'wb') as f:
                            f.write(base64.b64decode(favicon_data_encoded))
        except:
            pass

    return favicon_data

def get_ssl_fingerprint(page):

    # Retrieve SSL certificate
    ssl_fingerprint = ""
    if page.url.startswith("https://"):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)

        ctx = ssl.create_default_context()
        domain = urlparse(page.url).netloc
        wrappedSocket = ctx.wrap_socket(sock, server_hostname=domain)

        try:
            wrappedSocket.connect((domain, 443))
        except:
            response = False
        else:
            der_cert = wrappedSocket.getpeercert(True)
            thumb_sha1 = hashlib.sha1(der_cert).hexdigest()
            ssl_fingerprint = thumb_sha1
    
    return ssl_fingerprint

def start(target, config=None):

    with sync_playwright() as playwright:

        try:
            return run(playwright, target)
        except:
            return 1
