import glob
import re
import json
from pathlib import Path

pages = sorted(glob.glob('*.html'))
issues = []

for p in pages:
    content = Path(p).read_text(encoding='utf-8')
    
    # 1. Canonical
    canonical = re.search(r'<link\s+rel="canonical"\s+href="(.*?)"', content)
    if not canonical:
        issues.append(f'{p}: Missing canonical')
    elif not canonical.group(1).startswith('https://pasionnoticias.proxserverabner.site/'):
        issues.append(f'{p}: Invalid canonical {canonical.group(1)}')
        
    # 2. Open Graph
    if 'property="og:locale" content="es_AR"' not in content:
        issues.append(f'{p}: Missing og:locale es_AR')
    if 'property="og:site_name" content="DUELO"' not in content:
        issues.append(f'{p}: Missing og:site_name DUELO')
    if 'property="og:image:secure_url"' not in content:
        issues.append(f'{p}: Missing og:image:secure_url')
        
    # 3. Twitter
    if 'name="twitter:card" content="summary_large_image"' not in content:
        issues.append(f'{p}: Missing twitter:card summary_large_image')
        
    # 4. Favicon & Manifest
    if 'href="/favicon.ico"' not in content:
        issues.append(f'{p}: Missing /favicon.ico')
    if 'href="/site.webmanifest"' not in content:
        issues.append(f'{p}: Missing /site.webmanifest')
        
    # 5. Schema JSON-LD
    ld_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
    if not ld_match:
        issues.append(f'{p}: Missing JSON-LD')
    else:
        try:
            data = json.loads(ld_match.group(1))
            graph = data.get('@graph', [])
            types = [item.get('@type') for item in graph]
            if 'NewsMediaOrganization' not in types:
                issues.append(f'{p}: JSON-LD missing NewsMediaOrganization')
            if p.startswith('noticia-') and 'NewsArticle' not in types:
                issues.append(f'{p}: JSON-LD missing NewsArticle')
            if p != 'index.html' and 'BreadcrumbList' not in types:
                issues.append(f'{p}: JSON-LD missing BreadcrumbList')
        except Exception as e:
            issues.append(f'{p}: Invalid JSON-LD - {e}')

    # 6. Heading check (single h1)
    h1s = re.findall(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL)
    if len(h1s) != 1:
        issues.append(f'{p}: Expected 1 h1, found {len(h1s)}')

if issues:
    print(f'Found {len(issues)} issues:')
    for iss in issues:
        print(' -', iss)
else:
    print('ALL 16 PAGES PASSED TECHNICAL SEO AUDIT!')
