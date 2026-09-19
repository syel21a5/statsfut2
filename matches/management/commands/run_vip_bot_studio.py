from django.core.management.base import BaseCommand
from django.utils import timezone
from matches.models import Match, UserBotStrategy, UserBotAlertLog
from matches.services.live_radar import LiveRadarService
from matches.services.telegram_bot import TelegramBotService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Motor de execução do Bot Studio VIP: avalia jogos ao vivo contra as estratégias personalizadas dos clientes'

    def handle(self, *args, **options):
        active_strategies = UserBotStrategy.objects.filter(is_active=True)
        if not active_strategies.exists():
            self.stdout.write("Nenhuma estratégia de bot ativa no momento.")
            return

        live_statuses = ['1H', '2H', 'HT', 'LIVE', 'Live', 'In Play', 'IN_PLAY', 'ET', 'P', 'Halftime']
        active_matches = Match.objects.filter(status__in=live_statuses).select_related('home_team', 'away_team', 'league')
        
        if not active_matches.exists():
            self.stdout.write("Nenhum jogo ao vivo rolando no momento.")
            return

        self.stdout.write(f"Avaliando {active_matches.count()} jogos ao vivo contra {active_strategies.count()} estratégias VIP...")
        alerts_sent = 0

        for match in active_matches:
            elapsed = match.elapsed_time or 0
            h_score = match.home_score or 0
            a_score = match.away_score or 0
            tot_goals = h_score + a_score

            h_corners = match.home_corners or 0
            a_corners = match.away_corners or 0
            tot_corners = h_corners + a_corners

            h_shots = match.home_shots or 0
            a_shots = match.away_shots or 0
            tot_shots = h_shots + a_shots

            shots_per_min = round(tot_shots / max(elapsed, 1), 2)
            p5 = LiveRadarService.calculate_pressure(match, window_minutes=5)
            max_p5 = max(p5.get('home_pressure', 0), p5.get('away_pressure', 0))

            for strategy in active_strategies:
                # 1. Filtro de minuto
                if not (strategy.min_minute <= elapsed <= strategy.max_minute):
                    continue

                # 2. Filtro de gols máximos
                if strategy.max_total_goals is not None and tot_goals > strategy.max_total_goals:
                    continue

                # 3. Filtro de condição de placar
                cond = strategy.score_condition
                if cond == 'draw' and h_score != a_score:
                    continue
                elif cond == 'home_losing_1' and (a_score - h_score != 1):
                    continue
                elif cond == 'away_losing_1' and (h_score - a_score != 1):
                    continue
                elif cond == 'fav_losing':
                    # Checa odds pré-jogo
                    h_odd = match.home_team_win_odds or 3.0
                    a_odd = match.away_team_win_odds or 3.0
                    if h_odd < 1.70 and h_score <= a_score:
                        pass # Favorito de casa perdendo ou empatando
                    elif a_odd < 1.70 and a_score <= h_score:
                        pass # Favorito fora perdendo ou empatando
                    else:
                        continue

                # 4. Filtro de telemetria / pressão
                if p5.get('status') != 'dados_indisponiveis' and max_p5 < strategy.min_pressure_5m:
                    continue

                if tot_corners < strategy.min_total_corners:
                    continue

                if tot_shots < strategy.min_total_shots:
                    continue

                if shots_per_min < strategy.min_shots_per_minute:
                    continue

                # 5. Já alertou nesta partida?
                already_alerted = UserBotAlertLog.objects.filter(strategy=strategy, match=match).exists()
                if already_alerted:
                    continue

                # DISPARAR ALERTA VIP VIA TELEGRAM
                msg = (
                    f"🤖 <b>[STATSFUT VIP BOT]</b>\n"
                    f"🎯 <b>Estratégia:</b> {strategy.title}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚽ <b>{match.home_team.name} {h_score} x {a_score} {match.away_team.name}</b>\n"
                    f"🏆 Liga: {match.league.name}\n"
                    f"⏱️ <b>Minuto:</b> {elapsed}'\n"
                    f"🔥 <b>Pressão 5m:</b> {max_p5}% ({p5.get('status', 'Intensa')})\n"
                    f"🚩 <b>Cantos:</b> {tot_corners} | 🎯 <b>Chutes:</b> {tot_shots} (Pace: {shots_per_min} s/m)\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"💡 <b>Entrada Recomendada:</b> <code>{strategy.market_suggestion}</code>\n"
                    f"📊 <a href='https://vip.statsfut.com/vip/analise/{match.id}/'>Abrir Telemetria no VIP Terminal</a>"
                )

                sent = TelegramBotService.send_message(msg, chat_id=strategy.telegram_chat_id)
                if sent:
                    UserBotAlertLog.objects.create(strategy=strategy, match=match, minute_sent=elapsed)
                    strategy.total_alerts_sent += 1
                    strategy.save(update_fields=['total_alerts_sent'])
                    alerts_sent += 1
                    self.stdout.write(self.style.SUCCESS(f"Alerta enviado com sucesso para {strategy.telegram_chat_id}: {match.home_team.name} x {match.away_team.name}"))

        self.stdout.write(self.style.SUCCESS(f"Varredura do Bot Studio concluída! {alerts_sent} alertas disparados."))
