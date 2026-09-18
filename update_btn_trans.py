# -*- coding: utf-8 -*-
import re

updates = {
    'pt_BR': {
        "Testar 7 Dias Sem Risco": "Testar 7 Dias Sem Risco",
        "Compra 100% Segura": "Compra 100% Segura"
    },
    'pt': {
        "Testar 7 Dias Sem Risco": "Testar 7 Dias Sem Risco",
        "Compra 100% Segura": "Compra 100% Segura"
    },
    'es': {
        "Testar 7 Dias Sem Risco": "Probar 7 Días Sin Riesgo",
        "Compra 100% Segura": "Compra 100% Segura"
    },
    'de': {
        "Testar 7 Dias Sem Risco": "7 Tage risikofrei testen",
        "Compra 100% Segura": "100% sicherer Kauf"
    }
}

for lang, d in updates.items():
    po_path = f"/www/wwwroot/statsfut.com/locale/{lang}/LC_MESSAGES/django.po"
    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()

    for msgid, msgstr in d.items():
        pattern = re.compile(r'(msgid\s+"' + re.escape(msgid) + r'"\s*\nmsgstr\s+)(?:".*?"|"""[\s\S]*?""")', re.MULTILINE)
        if pattern.search(content):
            content = pattern.sub(r'\1"' + msgstr + '"', content)
        else:
            content += f'\n\nmsgid "{msgid}"\nmsgstr "{msgstr}"\n'

    with open(po_path, 'w', encoding='utf-8') as f:
        f.write(content)

print("Translations updated successfully.")
