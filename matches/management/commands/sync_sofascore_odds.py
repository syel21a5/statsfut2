import time
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from matches.models import Match
from matches.services.sofascore_tor import SofaScoreTorService


class Command(BaseCommand):
    help = 'Sincroniza odds reais diretamente do SofaScore via Tor para jogos futuros/hoje'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=2,
            help='Quantos dias à frente buscar odds (padrão: 2 dias = hoje e amanhã)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=80,
            help='Limite de partidas para consultar odds nesta execução'
        )

    def handle(self, *args, **options):
        days = options['days']
        limit = options['limit']

        now = timezone.now()
        max_date = now + timedelta(days=days)

        self.stdout.write(self.style.SUCCESS(f"=== INICIANDO SYNC DE ODDS VIA SOFASCORE TOR ==="))
        self.stdout.write(f"Buscando jogos entre {now.strftime('%d/%m %H:%M')} e {max_date.strftime('%d/%m %H:%M')}...")

        # Filtra jogos do SofaScore que tenham api_id (que é exatamente o ID do evento no SofaScore)
        # Prioriza jogos mais próximos e sem odds ou com odds mais antigas
        matches = Match.objects.filter(
            date__gte=now - timedelta(hours=2),
            date__lte=max_date,
            api_id__isnull=False
        ).exclude(
            status__in=['FT', 'AET', 'PEN', 'Finished', 'Postponed', 'Cancelled']
        ).order_by('date')[:limit]

        total = len(matches)
        if total == 0:
            self.stdout.write(self.style.WARNING("Nenhuma partida encontrada no período."))
            return

        self.stdout.write(f"Processando {total} partidas no SofaScore via Tor...")

        svc = SofaScoreTorService()
        updated_count = 0

        for idx, match in enumerate(matches, 1):
            event_id = str(match.api_id).strip()
            if not event_id.isdigit():
                continue

            try:
                odds = svc.get_event_odds(event_id)
                if odds:
                    changed = False
                    if odds.get('home_win'):
                        match.home_team_win_odds = odds['home_win']
                        changed = True
                    if odds.get('draw'):
                        match.draw_odds = odds['draw']
                        changed = True
                    if odds.get('away_win'):
                        match.away_team_win_odds = odds['away_win']
                        changed = True
                    if odds.get('over_15'):
                        match.over_15_odds = odds['over_15']
                        changed = True
                    if odds.get('over_25'):
                        match.over_25_odds = odds['over_25']
                        changed = True
                    if odds.get('under_25'):
                        match.under_25_odds = odds['under_25']
                        changed = True
                    if odds.get('over_35'):
                        match.over_35_odds = odds['over_35']
                        changed = True
                    if odds.get('under_35'):
                        match.under_35_odds = odds['under_35']
                        changed = True
                    if odds.get('over_45'):
                        match.over_45_odds = odds['over_45']
                        changed = True
                    if odds.get('under_45'):
                        match.under_45_odds = odds['under_45']
                        changed = True
                    if odds.get('corners_over_75'):
                        match.corners_over_75_odds = odds['corners_over_75']
                        changed = True
                    if odds.get('corners_over_85'):
                        match.corners_over_85_odds = odds['corners_over_85']
                        changed = True
                    if odds.get('corners_over_95'):
                        match.corners_over_95_odds = odds['corners_over_95']
                        changed = True
                    if odds.get('corners_over_105'):
                        match.corners_over_105_odds = odds['corners_over_105']
                        changed = True
                    if odds.get('btts_yes'):
                        match.btts_yes_odds = odds['btts_yes']
                        changed = True
                    if odds.get('btts_no'):
                        match.btts_no_odds = odds['btts_no']
                        changed = True
                    if odds.get('dc_1x'):
                        match.dc_1x_odds = odds['dc_1x']
                        changed = True
                    if odds.get('dc_x2'):
                        match.dc_x2_odds = odds['dc_x2']
                        changed = True
                    if odds.get('dnb_home'):
                        match.dnb_home_odds = odds['dnb_home']
                        changed = True
                    if odds.get('dnb_away'):
                        match.dnb_away_odds = odds['dnb_away']
                        changed = True

                    if changed:
                        match.save()
                        updated_count += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"[{idx}/{total}] ✅ {match.home_team.name} vs {match.away_team.name} | Odds 1X2: {match.home_team_win_odds} / {match.draw_odds} / {match.away_team_win_odds} | O2.5: {match.over_25_odds} | BTTS: {match.btts_yes_odds}"
                        ))
                    else:
                        self.stdout.write(f"[{idx}/{total}] ⚠️ Sem mercado relevante aberto para {match.home_team.name} vs {match.away_team.name}")
                else:
                    self.stdout.write(f"[{idx}/{total}] ⚪ Sem odds ainda no SofaScore para {match.home_team.name} vs {match.away_team.name}")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[{idx}/{total}] ❌ Erro ao buscar ID {event_id}: {e}"))

            # Pequeno intervalo para não afogar o Tor
            time.sleep(0.3)

        self.stdout.write(self.style.SUCCESS(f"\nConcluído! {updated_count}/{total} partidas atualizadas com odds 100% SofaScore."))
