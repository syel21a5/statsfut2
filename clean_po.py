# -*- coding: utf-8 -*-
import os
import re

from apply_paywall_translations import translations

def clean_and_update_po(po_path, trans_dict):
    if not os.path.exists(po_path):
        return
    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into header and blocks
    # Header is everything up to the first blank line followed by msgid
    parts = re.split(r'\n(?=msgid\s+)', content)
    header = parts[0]
    blocks = parts[1:]

    entries = {} # msgid -> full block text
    for b in blocks:
        m = re.search(r'msgid\s+"(.*)"', b)
        if not m:
            continue
        msgid = m.group(1)
        # Parse multi-line msgid if needed
        # Just use raw msgid as key
        entries[msgid] = b

    # Now update translations
    for msgid, msgstr in trans_dict.items():
        escaped_id = msgid.replace('\\', '\\\\').replace('"', '\\"')
        escaped_str = msgstr.replace('\\', '\\\\').replace('"', '\\"')
        
        # Look if exists in entries
        found = False
        for eid in list(entries.keys()):
            # check if matches
            if eid == escaped_id or eid == msgid:
                # Replace msgstr
                block = entries[eid]
                block = re.sub(r'msgstr\s+"[^"]*"', f'msgstr "{escaped_str}"', block)
                entries[eid] = block
                found = True
                break
        
        if not found:
            new_block = f'msgid "{escaped_id}"\nmsgstr "{escaped_str}"\n'
            entries[escaped_id] = new_block

    # Reconstruct file
    new_content = header.rstrip() + '\n\n' + '\n\n'.join(entries.values()).rstrip() + '\n'
    with open(po_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Cleaned and updated {po_path}, total unique entries: {len(entries)}")

for lang, d in translations.items():
    po_path = f"/www/wwwroot/statsfut.com/locale/{lang}/LC_MESSAGES/django.po"
    clean_and_update_po(po_path, d)
