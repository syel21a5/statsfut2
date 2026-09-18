# -*- coding: utf-8 -*-
import os
import re

from apply_paywall_translations import translations

for lang, d in translations.items():
    po_path = f"/www/wwwroot/statsfut.com/locale/{lang}/LC_MESSAGES/django.po"
    if not os.path.exists(po_path):
        continue
        
    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()

    updated = 0
    added = 0

    for msgid, msgstr in d.items():
        escaped_id = msgid.replace('\\', '\\\\').replace('"', '\\"')
        escaped_str = msgstr.replace('\\', '\\\\').replace('"', '\\"')
        
        # Look for msgid "..."
        pattern = re.compile(r'(msgid\s+"' + re.escape(escaped_id) + r'"\s*\nmsgstr\s+)(?:".*?"|"""[\s\S]*?""")', re.MULTILINE)
        
        if pattern.search(content):
            content = pattern.sub(r'\1"' + escaped_str + '"', content)
            updated += 1
        else:
            content += f'\n\nmsgid "{escaped_id}"\nmsgstr "{escaped_str}"\n'
            added += 1

    with open(po_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[{lang}] Updated: {updated}, Appended: {added}")
