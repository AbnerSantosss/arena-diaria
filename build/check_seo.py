import glob
import re
import html

pages = glob.glob('*.html')
print(f'Checking {len(pages)} HTML pages:')
all_pass = True
for p in sorted(pages):
    with open(p, encoding='utf-8') as f:
        content = f.read()
    title_match = re.search(r'<title>(.*?)</title>', content)
    title = html.unescape(title_match.group(1)) if title_match else ''
    desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content)
    desc = html.unescape(desc_match.group(1)) if desc_match else ''
    
    t_len = len(title)
    d_len = len(desc)
    t_ok = 50 <= t_len <= 60
    d_ok = 150 <= d_len <= 160
    status = 'OK  ' if (t_ok and d_ok) else 'FAIL'
    if not (t_ok and d_ok):
        all_pass = False
    print(f'{status} | Title: {t_len:2d} | Desc: {d_len:3d} | {p}')
    if not t_ok:
        print(f'   Title ({t_len}): "{title}"')
    if not d_ok:
        print(f'   Desc  ({d_len}): "{desc}"')

print(f'\nALL PASS: {all_pass}')
