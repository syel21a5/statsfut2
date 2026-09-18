import logging
import json
import urllib.request
from django.conf import settings
from matches.models import Match, ScannerTip
from matches.services.advanced_stats import MatchAnalyzer

logger = logging.getLogger(__name__)

class PanicoBotDetector:
    """
    Robô PanicoBot — Detector de Pânico no Mercado de Gols (Under 6.5).
    
    Regra Central:
    - Jogo com vocação Under pré-jogo: probabilidade Over 5.5 < 15% (ou seja, Under 5.5 > 85%).
    - No 1º Tempo (1' até 40'): ocorrem 3 gols (total_goals >= 3).
    - O mercado entra em pânico e estica a linha para Under 6.5 com odds de valor.
    - Zero apostas ou alertas no 2º tempo!
    """

    def __init__(self, target_chat_id=None):
        self.MAX_MINUTE = 40
        self.MAX_OVER_55_PROB = 15.0  # Limite máximo de Over 5.5 pré-jogo
        self.target_chat_id = target_chat_id or getattr(settings, 'PANICOBOT_TELEGRAM_CHAT_ID', '@panicobot61')

    def process_live_matches(self):
        """Busca jogos ao vivo no 1º tempo e analisa o pânico."""
        logger.info("🚨 [PanicoBot] Verificando jogos ao vivo para pânico de gols no 1º tempo...")

        live_matches = Match.objects.filter(
            status__in=['1H', 'In Progress', 'Live']
        ).select_related('home_team', 'away_team', 'league')

        count_analyzed = 0
        for match in live_matches:
            self.analyze_match(match)
            count_analyzed += 1

        logger.info(f"🚨 [PanicoBot] {count_analyzed} partidas ao vivo analisadas.")

    def analyze_match(self, match):
        try:
            # Proteção: Se já virou pro 2º tempo ou finalizou, aborta na hora
            if match.status in ['2H', 'FT', 'Finished', 'Match Finished']:
                return

            elapsed = match.elapsed_time or 0
            if elapsed > self.MAX_MINUTE or match.status == 'HT':
                return

            home_score = match.home_score or 0
            away_score = match.away_score or 0
            total_goals = home_score + away_score

            # Gatilho: 3 ou mais gols antes dos 40 minutos
            if total_goals < 3:
                return

            # Análise matemática pré-jogo
            analyzer = MatchAnalyzer(match)
            stats = analyzer.generate_full_report()

            if not stats:
                return

            under_55_prob = stats.get('under_55')
            if under_55_prob is not None:
                over_55_prob = 100 - under_55_prob
            else:
                over_45_prob = stats.get('goals', {}).get('over_45', 100)
                over_55_prob = over_45_prob * 0.55

            if over_55_prob > self.MAX_OVER_55_PROB:
                return

            self.send_telegram_alert(match, home_score, away_score, elapsed, over_55_prob, total_goals)

        except Exception as e:
            logger.error(f"❌ [PanicoBot] Erro ao analisar partida {match.id}: {e}")

    def send_telegram_alert(self, match, h_score, a_score, elapsed, over_55_prob, total_goals):
        market_key = f"TLGRM_PANICOBOT_UNDER65_{match.id}"
        tip, created = ScannerTip.objects.get_or_create(
            match=match,
            market=market_key,
            defaults={
                'prediction_text': f"PanicoBot Under 6.5 ({h_score}x{a_score} aos {elapsed}')",
                'probability': round(100 - over_55_prob, 1),
                'status': 'PENDING'
            }
        )

        if not created:
            return

        home_name = match.home_team.name
        away_name = match.away_team.name
        league_name = match.league.name if match.league else "Geral"
        under_55_prob = round(100 - over_55_prob, 1)

        mensagem = (
            f"🚨 <b>PANICOBOT — ALERTA DE PÂNICO NO MERCADO</b> 🚨\n\n"
            f"⚽ <b>{home_name} {h_score} x {a_score} {away_name}</b>\n"
            f"🏆 <b>Liga:</b> {league_name}\n"
            f"⏱ <b>Tempo:</b> {elapsed}' (1º Tempo)\n"
            f"🔥 <b>Placar:</b> {total_goals} gols antes dos 40 min!\n\n"
            f"📊 <b>Histórico Pré-Jogo:</b>\n"
            f"• Chance Under 5.5: <b>{under_55_prob}%</b> (Over 5.5: {over_55_prob:.1f}%)\n"
            f"• Mercado inflacionado: linha esticada com valor matemático.\n\n"
            f"🎯 <b>ENTRADA RECOMENDADA:</b>\n"
            f"👉 <b>UNDER 6.5 GOLS</b>\n\n"
            f"💡 <i>Orientação Técnica:</i> O mercado precifica goleada histórica pelo início atípico. "
            f"Ainda restam 4 gols de margem (só perde se sair o 7º gol)!\n\n"
            f"⛔ <b>REGRA DE OURO:</b> Entrada válida apenas agora no 1º tempo. <b>NÃO aposte nada no 2º tempo!</b>"
        )

        chat_id = self.target_chat_id or '@panicobot61'
        
        # Puxa o token do Bot do .env / settings
        import os
        bot_token = os.environ.get('PANICOBOT_TELEGRAM_TOKEN') or getattr(settings, 'PANICOBOT_TELEGRAM_TOKEN', None) or getattr(settings, 'TELEGRAM_BOT_TOKEN', None)

        if not bot_token:
            logger.error("[PanicoBot] Token do Telegram não encontrado.")
            return

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": mensagem,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    logger.info(f"✅ [PanicoBot] Alerta enviado para {home_name} x {away_name} ({chat_id})")
                else:
                    logger.error(f"❌ [PanicoBot] Erro Telegram status {resp.status}")
        except Exception as e:
            logger.error(f"❌ [PanicoBot] Exceção Telegram: {e}")
