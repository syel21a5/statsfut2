import os
import sys
import time
import json
import urllib.request
import urllib.error
import argparse
import requests
from playwright.sync_api import sync_playwright
try:
    from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, concatenate_videoclips
except ImportError:
    from moviepy import VideoFileClip, AudioFileClip, ImageClip, concatenate_videoclips

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def print_banner():
    print("=" * 60)
    print("      STATSFUT - GERADOR DE VÍDEOS DINÂMICOS COM SINCRONIZAÇÃO IA    ")
    print("=" * 60)
    print("Este script grava a tela do navegador executando uma coreografia")
    print("sincronizada de forma INTELIGENTE pela IA baseada no seu roteiro!")
    print("A tela branca inicial de carregamento será cortada automaticamente.")
    print("=" * 60)

def load_deepseek_api_key():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("DEEPSEEK_API_KEY="):
                    return line.strip().split("DEEPSEEK_API_KEY=")[1].strip()
    return os.environ.get("DEEPSEEK_API_KEY")

def analyze_script_timeline(api_key, roteiro_text, audio_duration, audio_path, json_path=None):
    import re
    import os
    import math
    import json
    
    # 1. Obter palavras e timestamps (via JSON do Kaggle ou fallback local Whisper)
    audio_words = []
    
    if json_path and os.path.exists(json_path):
        print(f"\n[MÁQUINA] [ACELERAÇÃO HÍBRIDA] Lendo cronograma pré-processado pela IA do Kaggle: {json_path}")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            audio_words = data.get("words", [])
            if data.get("duration"):
                audio_duration = data["duration"]
    else:
        # FALLBACK PARA WHISPER LOCAL
        import imageio_ffmpeg
        ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
        os.environ["PATH"] += os.pathsep + ffmpeg_dir
        import whisper

        print("\n[MÁQUINA] [MODO LENTO] Iniciando escuta com Inteligência Artificial (OpenAI Whisper) localmente...")
        
        model_dir = "E:\\WHISPER_MODELS"
        os.makedirs(model_dir, exist_ok=True)
        print(f"  - Carregando cérebro Whisper (Modelo: tiny) a partir de: {model_dir}")
        model = whisper.load_model("tiny", download_root=model_dir)
        
        from moviepy import AudioFileClip
        temp_audio_clip = AudioFileClip(audio_path)
        audio_duration = temp_audio_clip.duration
        temp_audio_clip.close()
        
        print(f"  - Ouvindo o arquivo de áudio para capturar milissegundos exatos: {audio_path}")
        result = model.transcribe(audio_path, word_timestamps=True, language="pt")
        
        for segment in result['segments']:
            for word in segment.get('words', []):
                clean = re.sub(r'[^\w\s]', '', word['word'].lower().strip())
                if clean:
                    audio_words.append({
                        "text": clean,
                        "start": word['start'],
                        "end": word['end']
                    })
        audio_duration = result['segments'][-1]['words'][-1]['end'] if result.get('segments') else audio_duration
        
    print("\n[MÁQUINA] Cruzando os tempos do áudio com as tags do roteiro via Busca Direta de Foco...")
    
    # 1. Isolar apenas a parte do roteiro da máquina
    # 1. Isolar apenas a parte do roteiro da máquina
    machine_idx = roteiro_text.find("TEXTO DA MÁQUINA (COPIE TUDO AQUI ABAIXO")
    if machine_idx == -1:
        machine_idx = roteiro_text.find("TEXTO DA M")
    if machine_idx == -1:
        machine_idx = roteiro_text.find("ROTEIRO DA MÁQUINA")
        
    if machine_idx != -1:
        roteiro_text = roteiro_text[machine_idx:]
            
    roteiro_text = re.sub(r'👇.*?👇', '', roteiro_text)
    roteiro_text = roteiro_text.replace("TEXTO DA MÁQUINA (COPIE TUDO AQUI ABAIXO E COLE NO ARQUIVO roteiro.txt)", "")
    

    # 3. Limpar o roteiro e mapear onde as tags ocorrem
    tags = []
    sum_of_previous_tags_length = 0
    clean_roteiro_text = re.sub(r'\[(.*?)\]', '', roteiro_text)

    for match in re.finditer(r'\[(.*?)\]', roteiro_text):
        tag_content = match.group(1).strip()
        tag_start = match.start()
        tag_end = match.end()
        
        is_off = (tag_content.upper() == 'OFF')
        foco_text = ""
        anchor_words = []
        full_words_after = []
        
        if tag_content.upper().startswith('FOCO:'):
            foco_text = tag_content[5:].strip()
            # Pega as palavras imediatamente APÓS a tag no roteiro
            text_after = roteiro_text[tag_end:]
            full_words_after = text_after.split()[:25] # Pega até 25 palavras originais (com as pequenas) para cálculo de offset massivo
            words_after = [w for w in re.sub(r'[^\w\s]', '', text_after.lower()).split() if len(w) > 3]
            if words_after:
                anchor_words = words_after[:12] # Guarda até 12 âncoras para segurança extrema!
        
        # Também extrai âncoras para tags [ABA:] para calcular o momento exato da troca de aba
        if tag_content.upper().startswith('ABA:'):
            text_after = roteiro_text[tag_end:]
            full_words_after = text_after.split()[:25]
            words_after = [w for w in re.sub(r'[^\w\s]', '', text_after.lower()).split() if len(w) > 1]
            if words_after:
                anchor_words = words_after[:12]
                
        tags.append({
            "content": tag_content,
            "is_off": is_off,
            "foco_text": foco_text,
            "anchor_words": anchor_words,
            "full_words_after": full_words_after,
            "char_idx": tag_start,
            "clean_char_idx": tag_start - sum_of_previous_tags_length
        })
        sum_of_previous_tags_length += (tag_end - tag_start)

    events = []
    
    # Busca a primeira aba definida no roteiro para iniciar o vídeo na tela certa
    current_tab = "gols"
    for t in tags:
        if t["content"].upper().startswith('ABA:'):
            current_tab = t["content"][4:].strip().lower()
            break
            
    events.append({
        "time": 0.0,
        "selector": "", 
        "tab": current_tab,
        "description": "Início da análise",
        "has_text": ""
    })

    search_start_idx = 0
    
    for i, t in enumerate(tags):
        tag_content = t["content"]
        is_off = t["is_off"]
        foco_text = t["foco_text"]
        anchor_words = t["anchor_words"]
        full_words_after = t["full_words_after"]
        
        if tag_content.upper().startswith('ABA:'):
            new_tab = tag_content[4:].strip().lower()
            
            # Só cria evento se for uma troca de aba real (não a primeira que já foi tratada no início)
            if new_tab != current_tab:
                # Calcula o timestamp exato da troca usando as âncoras do Whisper
                best_idx = -1
                matched_word = ""
                estimated_idx = int((t["clean_char_idx"] / len(clean_roteiro_text)) * len(audio_words))
                window_start = max(search_start_idx, estimated_idx - 250)
                window_end = min(len(audio_words), estimated_idx + 250)
                
                if anchor_words:
                    for aw in anchor_words:
                        closest_dist = float('inf')
                        for j in range(window_start, window_end):
                            w = audio_words[j]['text'].lower()
                            if aw == w or (len(aw) > 3 and aw in w):
                                dist = abs(j - estimated_idx)
                                if dist < closest_dist:
                                    closest_dist = dist
                                    best_idx = j
                                    matched_word = aw
                        if best_idx != -1:
                            break
                
                if best_idx != -1:
                    clean_full_words = [re.sub(r'[^\w\s]', '', w.lower()) for w in full_words_after]
                    aw_offset = 0
                    for k, cw in enumerate(clean_full_words):
                        if not cw: continue
                        if cw == matched_word or (len(matched_word) > 3 and matched_word in cw):
                            aw_offset = k
                            break
                    start_idx = max(search_start_idx, best_idx - aw_offset)
                    event_time = audio_words[start_idx]['start']
                    search_start_idx = best_idx + 1
                else:
                    event_time = (t["clean_char_idx"] / len(clean_roteiro_text)) * audio_duration
                
                events.append({
                    "tag_idx": i,
                    "is_off": False,
                    "time": round(event_time, 2),
                    "selector": "",
                    "tab": new_tab,
                    "description": f"Troca para aba {new_tab}",
                    "has_text": ""
                })
                print(f"  [ABA] Evento de troca para '{new_tab}' em {event_time:.2f}s")
            
            current_tab = new_tab
            continue
            
        if is_off:
            continue
            
        if foco_text:
            best_idx = -1
            matched_word = ""
            
            # Estima o ponto do áudio baseado na posição do caractere no texto limpo (sem tags)
            estimated_idx = int((t["clean_char_idx"] / len(clean_roteiro_text)) * len(audio_words))
            
            # Procura num raio de 250 palavras para trás e 250 palavras para frente (pois as tags inflam o texto)
            window_start = max(search_start_idx, estimated_idx - 250)
            window_end = min(len(audio_words), estimated_idx + 250)
            
            if anchor_words:
                for aw in anchor_words:
                    closest_dist = float('inf')
                    for j in range(window_start, window_end):
                        w = audio_words[j]['text'].lower()
                        if aw == w or (len(aw) > 3 and aw in w):
                            dist = abs(j - estimated_idx)
                            if dist < closest_dist:
                                closest_dist = dist
                                best_idx = j
                                matched_word = aw
                    if best_idx != -1:
                        break # Achou uma das âncoras válidas!
                        
            if best_idx != -1:
                # Recuperar o offset real da palavra ancorada
                clean_full_words = [re.sub(r'[^\w\s]', '', w.lower()) for w in full_words_after]
                aw_offset = 0
                for k, cw in enumerate(clean_full_words):
                    if not cw: continue
                    if cw == matched_word or (len(matched_word) > 3 and matched_word in cw):
                        aw_offset = k
                        break
                        
                # Subtrai o offset para voltar ao início da frase
                start_idx = max(search_start_idx, best_idx - aw_offset)
                event_time = audio_words[start_idx]['start']
                search_start_idx = best_idx + 1
            else:
                event_time = (t["clean_char_idx"] / len(clean_roteiro_text)) * audio_duration
                
            events.append({
                "tag_idx": i,
                "is_off": False,
                "time": round(event_time, 2),
                "selector": "", 
                "tab": current_tab,
                "description": foco_text,
                "has_text": foco_text
            })

    # 4. Inserir os OFFs perfeitamente cronometrados ANTES do próximo Foco
    final_events = []
    final_events.append(events[0])
    
    for i in range(1, len(events)):
        prev_event = events[i-1]
        curr_event = events[i]
        
        # Ignora o Início da análise para não botar OFF nele
        if i > 1:
            # Apaga o destaque 0.5 segundos antes do próximo foco iniciar, criando um pulo perfeito
            off_time = curr_event["time"] - 0.5
            if off_time <= prev_event["time"]:
                off_time = curr_event["time"] - 0.1
                
            final_events.append({
                "time": round(off_time, 2),
                "selector": "", 
                "tab": prev_event["tab"],
                "description": "Limpar Destaque",
                "has_text": "CLEAR_HIGHLIGHTS"
            })
            
        final_events.append(curr_event)

    # Último OFF da tela
    if len(final_events) > 1:
        final_events.append({
            "time": round(audio_duration - 0.5, 2),
            "selector": "", 
            "tab": final_events[-1]["tab"],
            "description": "Limpar Destaque",
            "has_text": "CLEAR_HIGHLIGHTS"
        })
        
    events = final_events

    
    # Remove redundâncias de início
    if len(events) > 1 and events[1]["time"] < 1.0:
        events.pop(0)

    print(f"  [SUCESSO] Cronograma matemático gerado com {len(events)} eventos focais.")
    for e in events:
        print(f"    - {e['time']}s: Aba [{e['tab']}] -> Foco: '{e['description']}'")
        
    return events

def run_choreography(page, total_duration, timeline=None):
    print("\n[2/4] Iniciando coreografia de gravação de tela de cinema...")
    
    # Injetar CSS de destaque premium na página e funções JS de rolagem linear suave/troca de abas
    page.evaluate("""
        const style = document.createElement('style');
        style.innerHTML = `
            @keyframes sf-pulse-border {
                0%, 100% { box-shadow: 0 0 15px rgba(249, 115, 22, 0.6); transform: scale(1.02); }
                50% { box-shadow: 0 0 35px rgba(249, 115, 22, 1), 0 0 60px rgba(249, 115, 22, 0.6); transform: scale(1.05); }
            }
            .sf-highlight {
                animation: sf-pulse-border 1.2s ease-in-out infinite !important;
                border: 4px solid #f97316 !important;
                background: rgba(249, 115, 22, 0.25) !important;
                border-radius: 12px !important;
                z-index: 99999 !important;
                position: relative !important;
            }
            .sf-highlight::after {
                content: '' !important;
                position: absolute !important;
                top: 0 !important;
                left: 0 !important;
                right: 0 !important;
                bottom: 0 !important;
                background: rgba(249, 115, 22, 0.25) !important;
                border-radius: 8px !important;
                pointer-events: none !important;
                z-index: 9999 !important;
            }
            
            /* Ocultar cabeçalhos desnecessários e focar estritamente nas probabilidades */
            header, nav, .navbar, .country-flags-bar, .flags-container, footer, .footer,
            .match-header-top, .breadcrumb, .match-info-banner, .league-banner {
                display: none !important;
            }
            
            /* Ajustes de Enquadramento Mobile & Nitidez de Contraste */
            html, body {
                width: 1080px !important;
                max-width: 1080px !important;
                overflow-x: hidden !important;
                background-color: #0b111e !important;
                margin: 0 !important;
                padding: 0 !important;
            }
            body {
                zoom: 1.35 !important;
                filter: contrast(1.12) brightness(1.05) !important;
            }
            .container, .container-fluid, .premium-dashboard, main, .main-content {
                max-width: 100% !important;
                width: 100% !important;
                margin: 0 !important;
                padding: 10px !important;
            }
            /* Esconder elementos abaixo de Margins e Halves */
            .h2h-section, .lineups-section, .standings-section, .comments-section, .news-section {
                display: none !important;
            }
            /* Aumentar contraste das fontes pequenas do tema dark */
            td, th, span, p, .text-muted {
                font-weight: 600 !important;
                color: #f8fafc !important;
                text-shadow: 0 1px 2px rgba(0,0,0,0.8) !important;
            }
        `;
        document.head.appendChild(style);

        // Rolagem de cinema linear e suave com Promise
        window.sf_smooth_scroll_to = function(targetY, durationMs) {
            return new Promise((resolve) => {
                const startY = window.scrollY;
                const difference = targetY - startY;
                const startTime = performance.now();

                function step() {
                    const now = performance.now();
                    const elapsed = now - startTime;
                    const progress = Math.min(elapsed / durationMs, 1);
                    
                    // Ease in-out quadratic formula
                    const ease = progress < 0.5 
                        ? 2 * progress * progress 
                        : -1 + (4 - 2 * progress) * progress;

                    window.scrollTo(0, startY + difference * ease);

                    if (progress < 1) {
                        window.requestAnimationFrame(step);
                    } else {
                        resolve();
                    }
                }
                window.requestAnimationFrame(step);
            });
        };

        // Troca de abas multilíngue ultra-robusta com fallback de manipulação direta de classes no DOM
        window.sf_switch_tab = function(tabName) {
            try {
                // 1. Tentar chamar a função JS nativa
                if (typeof switchMarketTab === 'function') {
                    try {
                        switchMarketTab(tabName);
                        return true;
                    } catch (innerErr) {
                        console.warn("Erro ao chamar switchMarketTab nativo:", innerErr);
                    }
                }

                // 2. Tentar clique direto por onclick contendo o nome do mercado
                let btn = document.querySelector(`button[onclick*='${tabName}']`);
                if (btn) {
                    try {
                        btn.click();
                        return true;
                    } catch (clickErr) {
                        console.warn("Erro ao clicar no botão:", clickErr);
                    }
                }

                // 3. Fallback absoluto: Forçar manipulação de classes no DOM diretamente
                console.log("Forçando troca de abas via manipulação direta de DOM para:", tabName);
                
                // Mapear tabNames em português e inglês para robustez
                const possibleNames = [tabName];
                if (tabName === 'escanteios') possibleNames.push('corners', 'cantos');
                if (tabName === 'especiais') possibleNames.push('specials', 'combos');
                if (tabName === 'cartoes') possibleNames.push('cards', 'cartões');
                if (tabName === 'gols') possibleNames.push('goals', 'halves');
                if (tabName === 'chutes') possibleNames.push('shots');
                if (tabName === 'lays') possibleNames.push('trade', 'lays');

                let matchedBtn = null;
                document.querySelectorAll('.market-tab-btn, button').forEach(b => {
                    const txt = b.textContent.toLowerCase();
                    const clickAttr = b.getAttribute('onclick') || '';
                    
                    const matches = possibleNames.some(name => clickAttr.includes(name) || txt.includes(name));
                    if (matches) {
                        matchedBtn = b;
                    }
                });

                if (matchedBtn) {
                    console.log("Forçando clique na aba:", matchedBtn.textContent);
                    matchedBtn.click();
                    return true;
                }

                return false;
            } catch (e) {
                console.error("Erro geral ao trocar aba:", e);
            }
            return false;
        };

        // Foca em um elemento específico com rolagem e destaque
        window.sf_focus_element = async function(selector, tabName, hasText) {
            // 1. Limpa destaques anteriores com transição suave
            document.querySelectorAll('.sf-highlight').forEach(el => {
                el.classList.remove('sf-highlight');
                el.style.transition = 'all 0.5s ease';
            });
            
            // 2. Troca de aba se necessário
            if (tabName) {
                // Sobe suavemente até o menu de abas para o espectador ver o clique acontecendo!
                const tabMenu = document.querySelector('.market-tabs, .market-tab-btn');
                if (tabMenu) {
                    const rect = tabMenu.getBoundingClientRect();
                    const targetY = window.scrollY + rect.top - 120;
                    await window.sf_smooth_scroll_to(Math.max(0, targetY), 1200);
                }
                
                window.sf_switch_tab(tabName);
                await new Promise(r => setTimeout(r, 1200)); // Aguarda carregamento
            }
            
            // 3. Busca em 2 passes: primeiro texto exato, depois números com word-boundary
            let el = null;
            if (hasText && hasText.trim() !== "") {
                let originalText = hasText.toLowerCase().replace(/\\s+/g, ' ').trim();
                let targetText = originalText;
                
                // Mapeamento de termos (Inglês da IA -> Português do Site)
                const aliases = {
                    'btts': 'ambas',
                    'ambas marcam': 'ambas',
                    'over': 'mais de',
                    'under': 'menos de',
                    'chance dupla': 'dupla'
                };
                for (let key in aliases) {
                    if (targetText.includes(key)) {
                        targetText = targetText.replace(key, aliases[key]);
                    }
                }
                
                const specificWidgets = document.querySelectorAll('.hbar-row, .mini-widget, .combo-pill, .lay-row, .tug-row, .mg-row, .card-pill, .stat-card-premium, .insight-chip, .prob-box');
                
                // PASSE 1: Texto exato (mais confiável)
                let matches = [];
                for (let e of specificWidgets) {
                    if (e.offsetParent === null) continue; // Ignora elementos ocultos (em outras abas)
                    if (!e.textContent) continue;
                    const eText = e.textContent.toLowerCase().replace(/\\s+/g, ' ').trim();
                    
                    if (eText.includes(targetText) || targetText.includes(eText) ||
                        eText.includes(originalText) || originalText.includes(eText)) {
                        matches.push(e);
                    }
                }
                
                if (matches.length === 1) {
                    el = matches[0];
                } else if (matches.length > 1) {
                    // Se achou mais de um, tenta encontrar o que tem a maior porcentagem
                    let maxPct = -1;
                    let bestEl = matches[0];
                    for (let m of matches) {
                        const pctMatch = m.textContent.match(/(\d+)%/);
                        if (pctMatch) {
                            const pct = parseInt(pctMatch[1]);
                            if (pct > maxPct) {
                                maxPct = pct;
                                bestEl = m;
                            }
                        }
                    }
                    el = bestEl;
                }
                
                // PASSE 2: Números com word-boundary (evita que "47" bata em "1.47")
                if (!el) {
                    const numbers = targetText.match(/\\d+(\\.\\d+)?/g);
                    if (numbers && numbers.length > 0) {
                        for (let e of specificWidgets) {
                            if (e.offsetParent === null) continue; // Ignora elementos ocultos (em outras abas)
                            if (!e.textContent) continue;
                            const eText = e.textContent.toLowerCase().replace(/\\s+/g, ' ').trim();
                            let allFound = true;
                            for (let num of numbers) {
                                // Word-boundary: o número não pode estar grudado em outro dígito ou ponto
                                const regex = new RegExp('(?<![0-9.])' + num.replace('.', '\\\\.') + '(?![0-9])', 'g');
                                if (!regex.test(eText)) { allFound = false; break; }
                            }
                            if (allFound) { el = e; break; }
                        }
                    }
                }
            }
            
            // 4. Fallback para CSS purista se o texto falhar
            if (!el && selector) {
                let cleanSelector = selector;
                if (selector.startsWith('#tab-')) {
                    const parts = selector.split(' ');
                    if (parts.length > 1) {
                        cleanSelector = parts.slice(1).join(' ');
                    }
                }
                el = document.querySelector(cleanSelector) || document.querySelector(selector);
            }

            // 5. Destaca e rola até o elemento
            if (el) {
                console.log("[SF-FOCUS] Elemento focado com sucesso:", hasText, el);
                el.classList.add('sf-highlight');
                const rect = el.getBoundingClientRect();
                const targetY = window.scrollY + rect.top - (window.innerHeight - rect.height) / 2;
                await window.sf_smooth_scroll_to(Math.max(0, targetY), 1500); // 1.5s rolagem suave
                return true;
            } else {
                console.warn("[SF-FOCUS] Elemento NÃO encontrado para o termo:", hasText);
                // Fallback: se o elemento não for achado, rola até o painel ativo correspondente
                const activeTab = document.querySelector('.market-tab-content.active');
                if (activeTab) {
                    const rect = activeTab.getBoundingClientRect();
                    const targetY = window.scrollY + rect.top - 80;
                    await window.sf_smooth_scroll_to(Math.max(0, targetY), 1200);
                }
            }
            return false;
        };

        window.sf_clear_highlights = function() {
            document.querySelectorAll('.sf-highlight').forEach(el => el.classList.remove('sf-highlight'));
        };
    """)

    if not timeline:
        print("  - Usando cronograma de sincronização padrão...")
        timeline = [
            {"time": 0.0, "selector": ".premium-dashboard, .match-hero-minimal, .match-hero", "tab": "gols", "description": "Topo da página"},
            {"time": total_duration * 0.10, "selector": ".ring-group", "tab": "gols", "description": "Anéis de Gols"},
            {"time": total_duration * 0.35, "selector": ".btts-pie-box, .result-box", "tab": "gols", "description": "BTTS e HT Goals"},
            {"time": total_duration * 0.55, "selector": ".corner-team-panel", "tab": "escanteios", "description": "Escanteios"},
            {"time": total_duration * 0.70, "selector": ".combo-pill, .stat-card-premium", "tab": "especiais", "description": "Especiais & Combos"},
            {"time": total_duration * 0.85, "selector": ".ia-panel-modern", "tab": "gols", "description": "Resumo da IA"}
        ]

    # Ordenar cronograma pelo tempo
    timeline = sorted(timeline, key=lambda x: x["time"])
    current_tab = "gols"

    start_time = time.time()
    for i, event in enumerate(timeline):
        target_time = event["time"]
        selector = event.get("selector", "")
        tab = event.get("tab", "")
        description = event.get("description", "")
        has_text = event.get("has_text", "")
        
        elapsed = time.time() - start_time
        sleep_needed = target_time - elapsed
        if sleep_needed > 0:
            time.sleep(sleep_needed)
            
        print(f"  -> Evento [{i+1}/{len(timeline)}]: {description} (~{target_time:.1f}s)")
        
        # Executa foco completo ou limpa a tela se for a tag [OFF]
        if has_text == "CLEAR_HIGHLIGHTS":
            page.evaluate("window.sf_clear_highlights()")
        else:
            page.evaluate(f"window.sf_focus_element({json.dumps(selector)}, {json.dumps(tab) if tab != current_tab else 'null'}, {json.dumps(has_text)})")
            
        current_tab = tab
        
    # Aguarda o restante do tempo total
    elapsed = time.time() - start_time
    remaining = total_duration - elapsed
    if remaining > 0:
        time.sleep(remaining)
        
    # Limpa destaques e sobe
    page.evaluate("window.sf_clear_highlights()")
    page.evaluate("window.sf_smooth_scroll_to(0, 2000)")
    time.sleep(2.0)

    actual_duration = time.time() - start_time
    print(f"\n[SUCESSO] Coreografia finalizada em {actual_duration:.2f}s (esperado: {total_duration:.2f}s)")

def capture_video_recording(match_url, temp_dir, duration, timeline=None):
    print("\n[1/4] Iniciando gravação de tela automatizada no Playwright...")
    video_temp_path = None
    loading_duration = 0.0

    with sync_playwright() as p:
        print("  - Lançando navegador (chromium)...")
        browser = p.chromium.launch(headless=True)
        
        # Viewport perfeito 1080x1920 nativo sem espaço vazio lateral
        context = browser.new_context(
            viewport={"width": 1080, "height": 1920},
            record_video_dir=temp_dir,
            record_video_size={"width": 1080, "height": 1920},
            is_mobile=True,
            has_touch=True,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            locale="pt-BR"
        )
        
        page = context.new_page()
        
        page.on("console", lambda msg: print(f"  [BROWSER] {msg.text}"))
        def block_ads(route):
            url = route.request.url.lower()
            if any(ad_domain in url for ad_domain in ['googleads', 'doubleclick', 'googlesyndication', 'adsystem', 'adsbygoogle']):
                route.abort()
            else:
                route.continue_()
                
        page.route("**/*", block_ads)
        
        start_loading = time.time()
        print(f"  - Acessando página da partida com AdBlocker ativado: {match_url}")
        try:
            page.goto(match_url, wait_until="networkidle", timeout=60000)
        except Exception:
            print("  [AVISO] Timeout na carga de rede, tentando prosseguir...")

        # Força a troca para a aba inicial antes de começar a gravar os segundos iniciais
        initial_tab = timeline[0].get("tab", "gols") if timeline else "gols"
        if initial_tab != "gols":
            try:
                page.evaluate(f"try {{ switchMarketTab('{initial_tab}'); }} catch(e) {{}}")
            except Exception:
                pass

        time.sleep(3) # Aguarda gráficos
        loading_duration = time.time() - start_loading

        # Remover cookies consent banner e modais do Statsfut de forma absoluta para manter o vídeo limpo
        page.evaluate("""
            // Remover banners de consentimento de cookies
            document.querySelectorAll("div, section, p, button, a").forEach(el => {
                const txt = el.textContent.toLowerCase();
                const id = el.id.toLowerCase();
                const cls = el.className.toLowerCase();
                if (txt.includes("cookie") || txt.includes("cookies") || id.includes("cookie") || cls.includes("cookie") || txt.includes("consent")) {
                    if (el.tagName !== 'BODY' && el.tagName !== 'HTML') {
                        el.remove();
                    }
                }
            });
            // Remover modais normais
            document.querySelectorAll('.video-script-modal, .modal-backdrop, .modal').forEach(e => e.remove());
            
            // Forçar remoção visual de caixas de anúncio que já possam estar no HTML
            document.querySelectorAll('ins.adsbygoogle, .ad-container, [id^="google_ads_iframe"]').forEach(e => {
                e.style.display = 'none';
                e.remove();
            });
            
            // Ocultar botões internos de Roteiro para não aparecerem no vídeo
            document.querySelectorAll("button[onclick*='openVideoScriptModal']").forEach(btn => {
                let wrapper = btn.closest('.ms-auto');
                if(wrapper) wrapper.style.display = 'none';
                else btn.style.display = 'none';
            });
            
            // Ocultar a barra lateral, cabeçalhos gerais e barra de bandeiras
            document.querySelectorAll('aside, .sidebar, .left-sidebar, #sidebar, nav, header, .col-lg-3, .col-md-3').forEach(e => {
                if(e) e.style.display = 'none';
            });

            // Ocultar cabeçalhos desnecessários da página (topo, bandeiras, hero e seo)
            document.querySelectorAll('main.main-content > header').forEach(e => e.style.display = 'none');
            document.querySelectorAll('main.main-content > div.d-flex.flex-wrap').forEach(e => e.style.display = 'none'); // Barra de bandeiras
            document.querySelectorAll('main.main-content > div.row.align-items-center.mb-4').forEach(e => e.style.display = 'none'); // Topo da partida
            document.querySelectorAll('.match-hero-premium, .seo-match-text').forEach(e => e.style.display = 'none');
            document.querySelectorAll('.market-tabs').forEach(e => e.style.display = 'none');
            document.querySelectorAll('.glass-panel.mt-4.mb-4, .ad-slot-inline, footer').forEach(e => e.style.display = 'none');
            
            // Ajustar layout para Shorts/Reels/TikTok: 100% preenchimento, sem margens pretas
            const style = document.createElement('style');
            style.innerHTML = `
                html, body {
                    background-color: #0b1120 !important;
                    overflow-x: hidden !important;
                    width: 100% !important;
                    margin: 0 !important;
                    padding: 0 !important;
                }
                .main-content {
                    margin-left: 0 !important;
                    padding: 0 !important;
                    width: 100% !important;
                    max-width: 100% !important;
                }
                .container, main, .container-fluid, .col-lg-9, .col-md-9 {
                    max-width: 100% !important;
                    width: 100% !important;
                    margin: 0 !important;
                    padding: 10px !important;
                    flex: 0 0 100% !important;
                }
                /* Ocultar elementos desnecessários no vídeo */
                footer, .useful-links-box, .bottom-match-ad, .breadcrumb, #sidebar, aside,
                header, nav, .navbar, .country-flags-bar, .flags-container, .top-header-statsfut,
                .match-hero-premium, .match-header-card, .match-info-banner, .league-banner, .seo-match-text, .market-tabs,
                .h2h-section, .lineups-section, .standings-section, .comments-section, .news-section {
                    display: none !important;
                }
                /* Zoom focado exclusivamente nas estatísticas essenciais */
                #tab-gols {
                    zoom: 1.28 !important;
                }
                .row.g-2.mb-4 {
                    zoom: 1.28 !important;
                }
                /* Aumentar contraste e brilho das fontes pequenas */
                td, th, span, p, .text-muted {
                    font-weight: 600 !important;
                    color: #f8fafc !important;
                    text-shadow: 0 1px 2px rgba(0,0,0,0.8) !important;
                }
            `;
            document.head.appendChild(style);
        """)
        time.sleep(1)
        loading_duration += 1.0

        # Inicia a coreografia de cinema
        run_choreography(page, duration, timeline)

        video_temp_path = page.video.path()
        
        context.close()
        browser.close()
        
    return video_temp_path, loading_duration

def merge_video_audio(video_path, audio_path, output_path, loading_duration, thumb_path=None, outro_path=None):
    print("\n[3/4] Mesclando gravação de tela e áudio da narração (com Capa e Outro)...")
    
    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(audio_path)
    
    print(f"  - Vídeo gravado (com loading): {video_clip.duration:.2f}s | Áudio original: {audio_clip.duration:.2f}s")
    print(f"  - Cortando {loading_duration:.2f}s iniciais de tela branca...")
    
    # Corta o início em branco
    if hasattr(video_clip, 'subclipped'):
        video_clip = video_clip.subclipped(loading_duration, loading_duration + audio_clip.duration)
    else:
        video_clip = video_clip.subclip(loading_duration, loading_duration + audio_clip.duration)
    
    if hasattr(video_clip, 'with_audio'):
        video_clip = video_clip.with_audio(audio_clip)
    else:
        video_clip = video_clip.set_audio(audio_clip)
        
    clips_sequence = []
    
    # 1. Capa / Thumbnail nos primeiros 1.2 segundos (Permite ao YouTube Shorts pegar a capa pronta!)
    if thumb_path and os.path.exists(thumb_path):
        print(f"  - Inserindo Capa/Thumbnail profissional no Frame 0: {thumb_path}")
        thumb_clip = ImageClip(thumb_path).set_duration(1.2)
        clips_sequence.append(thumb_clip)
        
    # 2. Conteúdo Dinâmico (Coreografia gravada no StatsFut)
    clips_sequence.append(video_clip)
    
    # 3. Card Final de Conversão (Outro / Telegram & Site) nos últimos 4 segundos
    if outro_path and os.path.exists(outro_path):
        print(f"  - Inserindo Card Final de Conversão (Outro): {outro_path}")
        outro_clip = ImageClip(outro_path).set_duration(4.0)
        clips_sequence.append(outro_clip)
        
    if len(clips_sequence) > 1:
        final_clip = concatenate_videoclips(clips_sequence, method="compose")
    else:
        final_clip = video_clip
    
    print("\n[4/4] Renderizando arquivo MP4 final para o YouTube Shorts / TikTok (2K Quad-HD Ultra Bitrate)...")
    final_clip.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        bitrate="12000k",
        preset="medium",
        ffmpeg_params=["-crf", "16", "-pix_fmt", "yuv420p"],
        threads=4,
        logger="bar"
    )
    
    video_clip.close()
    audio_clip.close()
    final_clip.close()

def main():
    parser = argparse.ArgumentParser(description="Gerador Automático de Vídeos Statsfut")
    parser.add_argument("--url", type=str, help="URL da partida no Statsfut")
    parser.add_argument("--audio", type=str, help="Caminho para o arquivo de áudio (.mp3)")
    parser.add_argument("--roteiro", type=str, help="Caminho para o arquivo de texto com o roteiro")
    parser.add_argument("--json", type=str, help="Caminho para o cronograma JSON processado pelo Kaggle", default=None)
    parser.add_argument("--thumb", type=str, help="Caminho para a Capa/Thumbnail", default=None)
    parser.add_argument("--outro", type=str, help="Caminho para o Card de Encerramento", default=None)
    
    args = parser.parse_args()

    clear_screen()
    print_banner()

    # URL da partida
    if args.url:
        match_url = args.url
        print(f"URL recebida via CMD: {match_url}")
    else:
        print("Digite ou cole a URL da partida do Statsfut (ex: http://127.0.0.1:8000/match/123/...):")
        match_url = input("> ").strip()

    if not match_url:
        print("[ERRO] A URL é obrigatória!")
        sys.exit(1)

    # Arquivo de áudio da narração
    if args.audio:
        audio_path = args.audio
        print(f"Áudio recebido via CMD: {audio_path}")
    else:
        print("\nArraste e solte o arquivo de áudio (.mp3) ou digite o caminho:")
        audio_path = input("> ").strip().replace('"', '').replace("'", "")

    if not audio_path or not os.path.exists(audio_path):
        print(f"[ERRO] Arquivo de áudio não encontrado no caminho: {audio_path}")
        sys.exit(1)

    # Coleta de roteiro opcional
    roteiro_text = ""
    if args.roteiro:
        print(f"Roteiro recebido via CMD: {args.roteiro}")
        if os.path.exists(args.roteiro):
            with open(args.roteiro, "r", encoding="utf-8") as f:
                roteiro_text = f.read().strip()
        else:
            print(f"[ERRO] Arquivo de roteiro não encontrado: {args.roteiro}")
            sys.exit(1)
    else:
        print("\n[OPCIONAL] Cole o texto do Roteiro de Narração para sincronização inteligente por IA:")
        print("(Pressione Ctrl+Z e depois Enter no Windows ou Ctrl+D no Linux/macOS em uma linha vazia para salvar, ou apenas dê Enter para pular):")
        
        roteiro_lines = []
        while True:
            try:
                line = input()
                roteiro_lines.append(line)
            except EOFError:
                break
                
        roteiro_text = "\n".join(roteiro_lines).strip()

    # Obter duração do áudio
    try:
        audio = AudioFileClip(audio_path)
        audio_duration = audio.duration
        audio.close()
    except Exception as e:
        print(f"[ERRO] Falha ao ler arquivo de áudio: {str(e)}")
        sys.exit(1)

    # Tenta obter a chave do DeepSeek e analisar o roteiro
    deepseek_key = load_deepseek_api_key()
    timeline = None
    if roteiro_text:
        timeline = analyze_script_timeline(deepseek_key, roteiro_text, audio_duration, audio_path, json_path=args.json)

    # Definir diretórios
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    temp_dir = os.path.join(base_dir, "media", "videos", "temp")
    output_dir = os.path.join(base_dir, "media", "videos", "output")
    
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    output_filename = f"video_cinema_{int(time.time())}.mp4"
    output_path = os.path.join(output_dir, output_filename)

    video_temp_path = None
    try:
        # 1. Grava a tela do navegador
        video_temp_path, loading_duration = capture_video_recording(match_url, temp_dir, audio_duration, timeline)
        if not video_temp_path or not os.path.exists(video_temp_path):
            raise Exception("Não foi possível gerar a gravação de tela temporária do Playwright.")

        # 2. Mescla gravação + áudio narração + Capa e Outro
        merge_video_audio(video_temp_path, audio_path, output_path, loading_duration, thumb_path=args.thumb, outro_path=args.outro)

        print("\n" + "=" * 60)
        print("🎉 VÍDEO CINEMATOGRÁFICO GERADO COM SUCESSO!")
        print(f"Caminho do arquivo final: {output_path}")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERRO] Ocorreu uma falha durante o processo: {str(e)}")
    
    finally:
        if video_temp_path and os.path.exists(video_temp_path):
            print("\nLimpando gravação de tela temporária...")
            try:
                os.remove(video_temp_path)
                print("Limpeza concluída.")
            except Exception as e:
                print(f"[AVISO] Não foi possível apagar o vídeo temporário: {str(e)}")

    if not (args.url and args.audio):
        print("\nPressione Enter para fechar...")
        input()

if __name__ == "__main__":
    main()
