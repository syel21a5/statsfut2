import sys
from datetime import timedelta
from zoneinfo import ZoneInfo
from django.core.management.base import BaseCommand
from django.utils import timezone
from matches.models import Match, ScannerTip
from matches.services.advanced_stats import MatchAnalyzer

class Command(BaseCommand):
    help = 'Gera e salva as dicas do Scanner Inteligente no banco de dados para os próximos 3 dias.'

    def handle(self, *args, **options):
        br_tz = ZoneInfo('America/Sao_Paulo')
        now_br = timezone.now().astimezone(br_tz)
        start_of_day = now_br.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_of_day + timedelta(days=8) # Próximos 8 dias
        
        matches = Match.objects.filter(
            date__range=(start_of_day, end_date),
            status__in=['NS', 'Not Started', 'Scheduled', 'TBD', 'POSTPONED', 'Postponed']
        ).select_related('home_team', 'away_team')

        self.stdout.write(f"Iniciando scan para {matches.count()} jogos não iniciados...")

        created_count = 0
        updated_count = 0
        skipped_count = 0

        def save_tip(match, market, probability, text):
            nonlocal created_count, updated_count
            _, created = ScannerTip.objects.update_or_create(
                match=match, market=market,
                defaults={'probability': probability, 'prediction_text': text}
            )
            if created: created_count += 1
            else: updated_count += 1

        for match in matches:
            diff_days = (match.date.astimezone(br_tz).date() - now_br.date()).days
            if diff_days >= 2:
                if ScannerTip.objects.filter(match=match).exists():
                    skipped_count += 1
                    continue

            try:
                analyzer = MatchAnalyzer(match)
                
                # Filtro de amostra mínima
                if len(analyzer.home_last_10) < 6 or len(analyzer.away_last_10) < 6:
                    continue

                goals: dict = analyzer.get_goal_markets() or {}
                corners: dict = analyzer.get_corner_markets() or {}
                odds: dict = analyzer.get_match_odds_probs() or {}
                
                home = match.home_team.name
                away = match.away_team.name
                
                # Probabilidades individuais para concordância
                home_len = len(analyzer.home_last_10)
                away_len = len(analyzer.away_last_10)
                
                home_over25_pct = int((sum(1 for m in analyzer.home_last_10 if m.home_score is not None and (m.home_score + m.away_score) > 2.5) / home_len) * 100) if home_len > 0 else 0
                away_over25_pct = int((sum(1 for m in analyzer.away_last_10 if m.home_score is not None and (m.home_score + m.away_score) > 2.5) / away_len) * 100) if away_len > 0 else 0

                home_over35_pct = int((sum(1 for m in analyzer.home_last_10 if m.home_score is not None and (m.home_score + m.away_score) > 3.5) / home_len) * 100) if home_len > 0 else 0
                away_over35_pct = int((sum(1 for m in analyzer.away_last_10 if m.home_score is not None and (m.home_score + m.away_score) > 3.5) / away_len) * 100) if away_len > 0 else 0

                home_btts_pct = int((sum(1 for m in analyzer.home_last_10 if m.home_score is not None and m.home_score > 0 and m.away_score > 0) / home_len) * 100) if home_len > 0 else 0
                away_btts_pct = int((sum(1 for m in analyzer.away_last_10 if m.home_score is not None and m.home_score > 0 and m.away_score > 0) / away_len) * 100) if away_len > 0 else 0

                # ========== MERCADO DE GOLS (Alta Assertividade) ==========
                # HT_GOAL removido devido a baixa assertividade historica (16.4%)
                # DC Combos (DC + Under, DC + BTTS) removidos devido a baixa assertividade historica (0% - 35%)

                if goals.get('over_15', 0) >= 85:
                    save_tip(match, 'OVER_15', goals['over_15'], 'Over 1.5 Goals')
                if goals.get('over_25', 0) >= 80 and home_over25_pct >= 70 and away_over25_pct >= 70:
                    save_tip(match, 'OVER_25', goals['over_25'], 'Over 2.5 Goals')
                # Over 3.5 removido por baixa frequencia e alta variancia
                if goals.get('under_35', 0) >= 85:
                    save_tip(match, 'UNDER_35', goals['under_35'], 'Under 3.5 Goals')
                if goals.get('under_45', 0) >= 90:
                    save_tip(match, 'UNDER_45', goals['under_45'], 'Under 4.5 Goals')

                if goals.get('btts', 0) >= 75 and home_btts_pct >= 65 and away_btts_pct >= 65:
                    save_tip(match, 'BTTS', goals['btts'], 'Both Teams to Score')
                
                # ========== VENCEDOR / RESULTADO ==========
                if odds.get('home_win', 0) >= 75:
                    save_tip(match, 'HOME_WIN', odds['home_win'], f'{home} to Win')
                elif odds.get('away_win', 0) >= 75:
                    save_tip(match, 'AWAY_WIN', odds['away_win'], f'{away} to Win')
                
                if odds.get('double_home', 0) >= 90:
                    save_tip(match, 'DC_1X', odds['double_home'], f'Double Chance 1X ({home} or Draw)')
                if odds.get('double_away', 0) >= 90:
                    save_tip(match, 'DC_X2', odds['double_away'], f'Double Chance X2 (Draw or {away})')
                
                dnb: dict = goals.get('dnb') or {}
                if dnb.get('home', 0) >= 75:
                    save_tip(match, 'DNB_HOME', dnb['home'], f'Draw No Bet - {home}')
                elif dnb.get('away', 0) >= 75:
                    save_tip(match, 'DNB_AWAY', dnb['away'], f'Draw No Bet - {away}')
                
                # ========== CLEAN SHEET / WIN TO NIL ==========
                # Removidos: HOME_CS, AWAY_CS, HOME_WTN, AWAY_WTN tinham taxas entre 17% e 38% (altissimo risco)
                
                # ========== HANDICAPS ==========
                handicaps: dict = goals.get('handicaps') or {}
                if handicaps.get('home_minus_0_5', 0) >= 70:
                    save_tip(match, 'HC_HOME_M05', handicaps['home_minus_0_5'], f'{home} -0.5 (AH)')
                
                # ========== CORNERS (Apenas Over 6.5 com alta probabilidade) ==========
                # Cantos desativados por baixa assertividade (59% com odds baixas)
                # if corners and corners.get('match_has_data'):
                #     m_overs: dict = corners.get('match_overs') or {}
                #     if m_overs.get(6, 0) >= 80: 
                #         save_tip(match, 'CORNERS_OVER_65', m_overs[6], 'Over 6.5 Corners')
                    
                # ========== LAY CORRECT SCORES (Alta Assertividade 96%+) ==========
                lay_scores: dict = goals.get('lay_correct_scores') or {}
                # Placares estratégicos para evitar poluição visual e manter taxa de acerto em ~97%
                target_lays = ['0_0', '0_1', '1_0', '1_1', '0_2', '2_0', '1_2', '2_1', '2_2', '3_0', '0_3']
                for score in target_lays:
                    if lay_scores.get(score, 0) >= 96:
                        readable_score = score.replace('_', '-')
                        save_tip(match, f'LAY_CS_{score}', lay_scores[score], f'Lay Score {readable_score}')

            except Exception as e:
                continue

        self.stdout.write(self.style.SUCCESS(f"Scanner finalizado! Criados: {created_count}, Atualizados: {updated_count}, Pulados (Futuros): {skipped_count}"))

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
