from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from zoneinfo import ZoneInfo
from matches.models import Match, BetTicket, BetTicketSelection
from matches.services.advanced_stats import MatchAnalyzer

class Command(BaseCommand):
    help = 'Gera estratégias e bilhetes especializados baseados em IA para o dia'

    def handle(self, *args, **kwargs):
        self.stdout.write("Analisando jogos com algoritmos avançados para gerar bilhetes...")
        
        br_tz = ZoneInfo('America/Sao_Paulo')
        now_br = timezone.now().astimezone(br_tz)
        start_of_day = now_br.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_of_day + timedelta(days=8)
        
        matches = Match.objects.filter(
            date__range=(start_of_day, end_date),
            status__in=['NS', 'Not Started', 'Scheduled', 'TBD', 'POSTPONED', 'Postponed']
        ).select_related('home_team', 'away_team', 'league')

        if not matches.exists():
            self.stdout.write("Nenhum jogo encontrado para gerar bilhetes.")
            return

        # Dicionário para coletar opções agrupadas por data local (America/Sao_Paulo)
        # { date_obj: { 'ht_goal': [], 'over_15': [], ... } }
        by_date_pools = {}
        skipped_count = 0

        for m in matches:
            # Otimização: Pular jogos futuros (>= 2 dias) que já possuem bilhetes gerados
            m_date = m.date.astimezone(br_tz).date()
            diff_days = (m_date - now_br.date()).days
            if diff_days >= 2:
                if BetTicketSelection.objects.filter(match=m).exists():
                    skipped_count += 1
                    continue

            if m_date not in by_date_pools:
                by_date_pools[m_date] = {
                    'over_15': [],
                    'over_05': [],
                    'under_35': [],
                    'double_chance': [],
                    'sniper_elite': []
                }
            
            pool = by_date_pools[m_date]

            try:
                analyzer = MatchAnalyzer(m)
                goals = analyzer.get_goal_markets()
                odds = analyzer.get_match_odds_probs()
                
                # 1. Over 1.5 Gols FT (Filtro Blindado: Poisson >= 88% + Histórico Forte)
                over_15 = goals.get('over_15', 0)
                if over_15 >= 88:
                    pool['over_15'].append({'match': m, 'market': 'over_15', 'label': 'Mais de 1.5 Gols FT', 'prob': over_15})
                    pool['sniper_elite'].append({'match': m, 'market': 'over_15', 'label': 'Mais de 1.5 Gols FT', 'prob': over_15})

                # 2. Over 0.5 Gols FT (Alavancagem Máxima: Prob >= 92%)
                over_05 = goals.get('over_05', 0)
                if over_05 >= 92:
                    pool['over_05'].append({'match': m, 'market': 'over_05', 'label': 'Mais de 0.5 Gols FT', 'prob': over_05})
                    pool['sniper_elite'].append({'match': m, 'market': 'over_05', 'label': 'Mais de 0.5 Gols FT', 'prob': over_05})

                # 3. Menos de 3.5 Gols FT (Under 3.5 Gols Blindado: Prob >= 88%)
                over_35 = goals.get('over_35', 0)
                under_35 = 100 - over_35
                if under_35 >= 88:
                    pool['under_35'].append({'match': m, 'market': 'under_35', 'label': 'Menos de 3.5 Gols FT', 'prob': under_35})
                    pool['sniper_elite'].append({'match': m, 'market': 'under_35', 'label': 'Menos de 3.5 Gols FT', 'prob': under_35})

                # 4. Dupla Chance Casa (1X Super Segura: Prob >= 88%)
                double_home = odds.get('double_home', 0)
                if double_home >= 88:
                    pool['double_chance'].append({'match': m, 'market': 'double_chance_1x', 'label': f'1X - {m.home_team.name} ou Empate', 'prob': double_home})
                    pool['sniper_elite'].append({'match': m, 'market': 'double_chance_1x', 'label': f'1X - {m.home_team.name} ou Empate', 'prob': double_home})

                # 5. Dupla Chance Fora (X2 Super Segura: Prob >= 90%)
                double_away = odds.get('double_away', 0)
                if double_away >= 90:
                    pool['double_chance'].append({'match': m, 'market': 'double_chance_x2', 'label': f'X2 - {m.away_team.name} ou Empate', 'prob': double_away})
                    pool['sniper_elite'].append({'match': m, 'market': 'double_chance_x2', 'label': f'X2 - {m.away_team.name} ou Empate', 'prob': double_away})

                # 10. Hedge ao Favorito
                if m.home_team_win_odds and m.away_team_win_odds:
                    if m.home_team_win_odds < m.away_team_win_odds and m.home_team_win_odds >= 2.00:
                        if goals.get('over_15', 0) >= 75:
                            pool['hedge_favorito'].append({'match': m, 'market': 'home_win', 'label': f'Hedge - Vitória do {m.home_team.name}', 'prob': int(100/m.home_team_win_odds)})
                    elif m.away_team_win_odds < m.home_team_win_odds and m.away_team_win_odds >= 2.00:
                        if goals.get('over_15', 0) >= 75:
                            pool['hedge_favorito'].append({'match': m, 'market': 'away_win', 'label': f'Hedge - Vitória do {m.away_team.name}', 'prob': int(100/m.away_team_win_odds)})

                # 11. Trixie Combo Bets (As Mais Seguras Possíveis)
                # Novas Trixies de Ouro

                # Novas Trixies de Ouro
                if dnb_home >= 80:
                    pool['trixie_dnb'].append({'match': m, 'market': 'dnb_home', 'label': f'Empate Anula - {m.home_team.name}', 'prob': dnb_home, 'odd': 1.60})
                elif dnb_away >= 80:
                    pool['trixie_dnb'].append({'match': m, 'market': 'dnb_away', 'label': f'Empate Anula - {m.away_team.name}', 'prob': dnb_away, 'odd': 1.60})

                over_15_trixie = goals.get('over_15', 0)
                if over_15_trixie >= 85:
                    pool['trixie_over_15'].append({'match': m, 'market': 'over_15', 'label': 'Mais de 1.5 Gols FT', 'prob': over_15_trixie, 'odd': 1.35})

                if double_home >= 90:
                    pool['trixie_dc_safe'].append({'match': m, 'market': 'double_chance_1x', 'label': f'1X - {m.home_team.name} ou Empate', 'prob': double_home, 'odd': 1.30})
                elif double_away >= 90:
                    pool['trixie_dc_safe'].append({'match': m, 'market': 'double_chance_x2', 'label': f'X2 - {m.away_team.name} ou Empate', 'prob': double_away, 'odd': 1.30})

            except Exception:
                continue

        # Limpar bilhetes pendentes anteriores para evitar duplicar
        BetTicket.objects.filter(status='Pending', date_target__gte=start_of_day.date()).delete()

        created_count = 0

        # Iterar sobre cada data e gerar os bilhetes de forma isolada
        for target_date, pool in by_date_pools.items():
            # Ordenar tudo pelas maiores probabilidades
            for k in pool:
                pool[k].sort(key=lambda x: x['prob'], reverse=True)

            # ==========================================
            # 1. GERAR DUPLAS DE ELITE (Doubles 90%+)
            # ==========================================
            doubles_created = 0
            
            doubles_pool_sources = [
                {'opts': pool['double_chance'], 'title': 'Dupla Dupla Chance (Segurança Extra 90%+)'},
                {'opts': pool['under_35'], 'title': 'Dupla Sob Controle (Menos de 3.5 Gols)'},
                {'opts': pool['over_05'], 'title': 'Dupla Alavancagem (Mais de 0.5 Gols FT)'},
                {'opts': pool['over_15'], 'title': 'Dupla de Gols FT (Mais de 1.5 Gols Blindada)'},
            ]
            
            for source in doubles_pool_sources:
                if doubles_created >= 6:
                    break
                    
                opts = source['opts']
                title = source['title']
                
                i = 0
                group_idx = 65 # Char 'A'
                while i + 1 < len(opts) and doubles_created < 6:
                    chunk = opts[i:i+2]
                    avg_prob = sum(x['prob'] for x in chunk) // 2
                    
                    ticket_title = f"{title} - Grupo {chr(group_idx)}" if len(opts) > 2 else title
                    ticket = BetTicket.objects.create(
                        title=ticket_title,
                        ticket_type="Double",
                        average_probability=avg_prob,
                        date_target=target_date
                    )
                    
                    for sel in chunk:
                        BetTicketSelection.objects.create(
                            ticket=ticket,
                            match=sel['match'],
                            prediction_market=sel['market'],
                            prediction_label=sel['label'],
                            probability=sel['prob']
                        )
                    
                    doubles_created += 1
                    created_count += 1
                    group_idx += 1
                    i += 2

            # ==========================================
            # 2. GERAR TRIPLAS DE SEGURANÇA MÁXIMA (Trebles)
            # ==========================================
            triples_created = 0
            
            triples_pool_sources = [
                {'opts': pool['double_chance'], 'title': 'Tripla Dupla Chance (Segurança Máxima 90%+)'},
                {'opts': pool['over_05'], 'title': 'Tripla Alavancagem (Mais de 0.5 Gols FT)'},
                {'opts': pool['under_35'], 'title': 'Tripla Sob Controle (Menos de 3.5 Gols)'},
            ]
            
            for source in triples_pool_sources:
                if triples_created >= 4:
                    break
                    
                opts = source['opts']
                title = source['title']
                
                i = 0
                group_idx = 65 # 'A'
                while i + 2 < len(opts) and triples_created < 4:
                    chunk = opts[i:i+3]
                    avg_prob = sum(x['prob'] for x in chunk) // 3
                    
                    ticket_title = f"{title} - Grupo {chr(group_idx)}" if len(opts) > 3 else title
                    ticket = BetTicket.objects.create(
                        title=ticket_title,
                        ticket_type="Treble",
                        average_probability=avg_prob,
                        date_target=target_date
                    )
                    
                    for sel in chunk:
                        BetTicketSelection.objects.create(
                            ticket=ticket,
                            match=sel['match'],
                            prediction_market=sel['market'],
                            prediction_label=sel['label'],
                            probability=sel['prob']
                        )
                        
                    triples_created += 1
                    created_count += 1
                    group_idx += 1
                    i += 3

            # ==========================================
            # 3. GERAR BILHETE SNIPER ELITE DO DIA (Top 3 Picks)
            # ==========================================
            if len(pool['sniper_elite']) >= 3:
                # Ordena por maior probabilidade e seleciona os 3 melhores jogos únicos
                seen_sniper_m = set()
                top_3_sniper = []
                for x in sorted(pool['sniper_elite'], key=lambda val: val['prob'], reverse=True):
                    if x['match'].id not in seen_sniper_m:
                        seen_sniper_m.add(x['match'].id)
                        top_3_sniper.append(x)
                    if len(top_3_sniper) == 3:
                        break
                
                if len(top_3_sniper) == 3:
                    avg_prob = sum(x['prob'] for x in top_3_sniper) // 3
                    ticket = BetTicket.objects.create(
                        title="Bilhete Sniper de Ouro (Top 3 Picks 90%+)",
                        ticket_type="Treble",
                        average_probability=avg_prob,
                        date_target=target_date
                    )
                    for sel in top_3_sniper:
                        BetTicketSelection.objects.create(
                            ticket=ticket,
                            match=sel['match'],
                            prediction_market=sel['market'],
                            prediction_label=sel['label'],
                            probability=sel['prob']
                        )
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Sucesso! Foram gerados {created_count} bilhetes com super estratégias diversas agrupados por datas isoladas."))

        # Limpa o cache automaticamente para a página Premium atualizar
        try:
            from django.core.cache import cache
            from django.core.cache.utils import make_template_fragment_key
            for lang in ['pt-br', 'en']:
                for fragment in ['premium_dashboard_html_v8', 'premium_tickets_pane']:
                    key = make_template_fragment_key(fragment, [lang])
                    cache.delete(key)
            self.stdout.write(self.style.SUCCESS("Cache do dashboard premium invalidado com sucesso!"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Aviso ao limpar cache: {e}"))
