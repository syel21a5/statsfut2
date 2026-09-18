# -*- coding: utf-8 -*-
import os
import polib

from apply_paywall_translations import translations

for lang, d in translations.items():
    po_path = f"/www/wwwroot/statsfut.com/locale/{lang}/LC_MESSAGES/django.po"
    if not os.path.exists(po_path):
        continue
    
    po = polib.pofile(po_path)
    updated_count = 0
    added_count = 0
    
    # Map existing entries
    entries_by_id = {entry.msgid: entry for entry in po}
    
    for msgid, msgstr in d.items():
        if msgid in entries_by_id:
            entry = entries_by_id[msgid]
            if entry.msgstr != msgstr:
                entry.msgstr = msgstr
                if 'fuzzy' in entry.flags:
                    entry.flags.remove('fuzzy')
                updated_count += 1
        else:
            entry = polib.POEntry(
                msgid=msgid,
                msgstr=msgstr
            )
            po.append(entry)
            entries_by_id[msgid] = entry
            added_count += 1
            
    # Deduplicate entries if any
    unique_entries = []
    seen = set()
    for entry in po:
        if entry.msgid not in seen:
            seen.add(entry.msgid)
            unique_entries.append(entry)
            
    po[:] = unique_entries
    po.save()
    print(f"[{lang}] Updated: {updated_count}, Added: {added_count}, Total unique: {len(po)}")
