# -*- coding: utf-8 -*-
import re

updates = {
    'pt_BR': {
        "Upgrade to StatsFut Premium for exclusive advanced football analytics, corner stats, card analysis and statistical predictions.": "Assine o StatsFut Premium para análises avançadas de futebol, escanteios, cartões e projeções estatísticas exclusivas.",
        "Get access to mathematical modeling (Poisson + xG), statistical predictions with high win-rate, Live Pressure Radar, and Ready-to-use tickets verified daily.": "Tenha acesso a modelos matemáticos (Poisson + xG), análises estatísticas com alta assertividade, Radar de Pressão Ao Vivo e Bilhetes Prontos validados diariamente.",
        "Perfect to start using our smart predictions and statistics": "Perfeito para começar com nossas análises e estatísticas do sistema",
        "Full Smart Scanner (Goals, Cards, Corners)": "Scanner Inteligente do Sistema (Gols, Cartões, Escanteios)",
        "Smart Scanner (Pre-game filters & picks)": "Scanner Inteligente (Filtros pré-jogo e seleções)",
        "Test StatsFut Premium with complete peace of mind. If you are not satisfied with the analytical tools, system tips, or live radar within the first 7 days, request a full refund with one click. No questions asked.": "Teste o StatsFut Premium com tranquilidade total. Se você não gostar das ferramentas analíticas, dicas do sistema ou do radar ao vivo nos primeiros 7 dias, solicite 100% de reembolso com 1 clique. Sem burocracia.",
        "How do the Ready Tickets and System Predictions work?": "Como funcionam os Bilhetes Prontos e as Projeções do Sistema?",
        "Our mathematical model simulates every fixture using Poisson distribution, recent xG momentum, referee profiles, and game state metrics to identify positive expected value (+EV) markets before bookmakers adjust.": "Nosso modelo matemático simula cada partida usando Distribuição de Poisson, momento de xG recente, perfil de árbitros e métricas de jogo para encontrar valor esperado positivo (+EV) antes das casas ajustarem as odds."
    },
    'pt': {
        "Upgrade to StatsFut Premium for exclusive advanced football analytics, corner stats, card analysis and statistical predictions.": "Assine o StatsFut Premium para análises avançadas de futebol, escanteios, cartões e projeções estatísticas exclusivas.",
        "Get access to mathematical modeling (Poisson + xG), statistical predictions with high win-rate, Live Pressure Radar, and Ready-to-use tickets verified daily.": "Tenha acesso a modelos matemáticos (Poisson + xG), análises estatísticas com alta assertividade, Radar de Pressão Ao Vivo e Bilhetes Prontos validados diariamente.",
        "Perfect to start using our smart predictions and statistics": "Perfeito para começar com nossas análises e estatísticas do sistema",
        "Full Smart Scanner (Goals, Cards, Corners)": "Scanner Inteligente do Sistema (Gols, Cartões, Escanteios)",
        "Smart Scanner (Pre-game filters & picks)": "Scanner Inteligente (Filtros pré-jogo e seleções)",
        "Test StatsFut Premium with complete peace of mind. If you are not satisfied with the analytical tools, system tips, or live radar within the first 7 days, request a full refund with one click. No questions asked.": "Teste o StatsFut Premium com tranquilidade total. Se você não gostar das ferramentas analíticas, dicas do sistema ou do radar ao vivo nos primeiros 7 dias, solicite 100% de reembolso com 1 clique. Sem burocracia.",
        "How do the Ready Tickets and System Predictions work?": "Como funcionam os Bilhetes Prontos e as Projeções do Sistema?",
        "Our mathematical model simulates every fixture using Poisson distribution, recent xG momentum, referee profiles, and game state metrics to identify positive expected value (+EV) markets before bookmakers adjust.": "Nosso modelo matemático simula cada partida usando Distribuição de Poisson, momento de xG recente, perfil de árbitros e métricas de jogo para encontrar valor esperado positivo (+EV) antes das casas ajustarem as odds."
    },
    'es': {
        "Upgrade to StatsFut Premium for exclusive advanced football analytics, corner stats, card analysis and statistical predictions.": "Actualiza a StatsFut Premium para estadísticas avanzadas, córners, tarjetas y pronósticos estadísticos exclusivos.",
        "Get access to mathematical modeling (Poisson + xG), statistical predictions with high win-rate, Live Pressure Radar, and Ready-to-use tickets verified daily.": "Accede a modelos matemáticos (Poisson + xG), pronósticos estadísticos de alta efectividad, Radar de Presión en Vivo y Boletos Listos verificados a diario.",
        "Perfect to start using our smart predictions and statistics": "Perfecto para comenzar con nuestras estadísticas y pronósticos del sistema",
        "Full Smart Scanner (Goals, Cards, Corners)": "Escáner Inteligente del Sistema (Goles, Tarjetas, Córners)",
        "Smart Scanner (Pre-game filters & picks)": "Escáner Inteligente (Filtros pre-partido y selecciones)",
        "Test StatsFut Premium with complete peace of mind. If you are not satisfied with the analytical tools, system tips, or live radar within the first 7 days, request a full refund with one click. No questions asked.": "Prueba StatsFut Premium con total tranquilidad. Si no estás satisfecho con nuestras herramientas analíticas, consejos del sistema o radar en los primeros 7 días, solicita el reembolso completo con un clic.",
        "How do the Ready Tickets and System Predictions work?": "¿Cómo funcionan los Boletos Listos y las Proyecciones del Sistema?",
        "Our mathematical model simulates every fixture using Poisson distribution, recent xG momentum, referee profiles, and game state metrics to identify positive expected value (+EV) markets before bookmakers adjust.": "Nuestro modelo matemático simula cada encuentro usando Poisson, xG reciente y perfiles de árbitros para identificar valor positivo (+EV) antes que las casas de apuestas."
    },
    'de': {
        "Upgrade to StatsFut Premium for exclusive advanced football analytics, corner stats, card analysis and statistical predictions.": "Upgrade auf StatsFut Premium für erweiterte Fußballanalysen, Ecken, Karten und statistische Prognosen.",
        "Get access to mathematical modeling (Poisson + xG), statistical predictions with high win-rate, Live Pressure Radar, and Ready-to-use tickets verified daily.": "Erhalte Zugriff auf mathematische Poisson-Modelle, statistische Prognosen mit hoher Trefferquote, Live-Druckradar und täglich verifizierte Wettscheine.",
        "Perfect to start using our smart predictions and statistics": "Perfekt für den Start mit unseren System-Prognosen und Statistiken",
        "Full Smart Scanner (Goals, Cards, Corners)": "Vollständiger Smart-Scanner des Systems (Tore, Karten, Ecken)",
        "Smart Scanner (Pre-game filters & picks)": "Smart-Scanner (Pre-Match-Filter & Tipps)",
        "Test StatsFut Premium with complete peace of mind. If you are not satisfied with the analytical tools, system tips, or live radar within the first 7 days, request a full refund with one click. No questions asked.": "Teste StatsFut Premium völlig risikofrei. Wenn du mit den Analysetools, System-Tipps oder dem Radar in den ersten 7 Tagen nicht zufrieden bist, erhältst du 100% deines Geldes zurück.",
        "How do the Ready Tickets and System Predictions work?": "Wie funktionieren die fertigen Wettscheine und System-Prognosen?",
        "Our mathematical model simulates every fixture using Poisson distribution, recent xG momentum, referee profiles, and game state metrics to identify positive expected value (+EV) markets before bookmakers adjust.": "Unser mathematisches Modell simuliert jedes Spiel mittels Poisson-Verteilung, xG-Dynamik und Schiedsrichterdaten, um Value-Wetten (+EV) zu identifizieren."
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

print("Translations updated without AI terms.")
