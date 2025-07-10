import json

def json_to_netscape(json_cookies, output_path='cookies.txt'):
    lines = []
    for c in json_cookies:
        domain = c.get('domain', '')
        include_subdomains = 'TRUE' if domain.startswith('.') else 'FALSE'
        path = c.get('path', '/')
        secure = 'TRUE' if c.get('secure', False) else 'FALSE'
        expires = int(c.get('expirationDate', 0)) if c.get('expirationDate') else 0
        name = c.get('name', '')
        value = c.get('value', '')
        line = '\t'.join([
            domain,
            include_subdomains,
            path,
            secure,
            str(expires),
            name,
            value
        ])
        lines.append(line)
    with open(output_path, 'w') as f:
        f.write("# Netscape HTTP Cookie File\n")
        for l in lines:
            f.write(l + '\n')
    print(f"Saved {len(lines)} cookies to {output_path}")

# Usage example:
with open('kick_cookies.json', 'r') as f:
    json_cookies = json.load(f)

json_to_netscape(json_cookies, 'cookies.txt')
