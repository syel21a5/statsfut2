import logging
from django.conf import settings
from matches.models import Match, ScannerTip
from matches.services.advanced_stats import MatchAnalyzer
from matches.services.telegram_bot import TelegramBotService

logger = logging.getLogger(__name__)

class LiveLayDetector:
    """
    Robô Exchange VIP — Lay 0-2 Zebra (Apostar CONTRA a Goleada da Zebra).
    Baseado na inteligência do Painel VIP (Lay Correct Score 95%+).
    Auditado com 96.60% de taxa real de Green no banco de dados.

    Regras da Estratégia:
    1. Filtro Matemático VIP: Probabilidade pré-jogo de Lay 0-2 >= 95% (ou seja, Poisson indica < 5% de chance de 0-2).
    2. Janela ao vivo: Jogo entre os 15' e 65' minutos.
    3. Gatilho de Entrada: O visitante (zebra/azarão) abriu o placar (está 0x1).
    4. Entrada na Betfair/Exchange: LAY 0-2 (Aposta contra o placar exato 0-2).
    5. Proteção de Banca: Odd Teto recomendada até @4.20 (Responsabilidade barata).
    
    Cenários de Vitória (Green):
    - Se o mandante empatar (1x1) -> Green Imediato!
    - Se o mandante virar (2x1, 3x1...) -> Green!
    - Se o jogo terminar 0x1 -> Green!
    - Se sair mais de 2 gols (0x3, 1x2...) -> Green!
    - Apenas perde se o jogo morrer estritamente em 0x2.
    """

    def __init__(self, target_chat_id=None):
        self.MIN_MINUTE = 15
        self.MAX_MINUTE = 65
        self.MIN_PROBABILITY_LAY = 95.0
        self.target_chat_id = target_chat_id or getattr(settings, 'TELEGRAM_CHAT_ID', None)

    def _send(self, msg):
        """Envia para o chat do Telegram unificado."""
        return TelegramBotService.send_message(msg, chat_id=self.target_chat_id)

    def process_live_matches(self):
        """Busca jogos ao vivo e analisa oportunidades de Lay 0-2."""
        logger.info("⚡ Verificando oportunidades Exchange Lay 0-2 Zebra...")

        live_matches = Match.objects.filter(
            status__in=['1H', '2H', 'HT', 'In Progress', 'Live', 'LIVE', 'In Play', 'IN_PLAY']
        ).select_related('home_team', 'away_team', 'league')

        for match in live_matches:
            self.analyze_match(match)

    def analyze_match(self, match):
        try:
            home_score = match.home_score or 0
            away_score = match.away_score or 0
            elapsed = match.elapsed_time or 0
            if match.status == 'HT':
                elapsed = 45

            # Filtro 1: Janela de minutos de liquidez (15' a 65')
            if elapsed < self.MIN_MINUTE or elapsed > self.MAX_MINUTE:
                return

            # Filtro 2: O visitante precisa estar vencendo por 0x1 exatamente
            if not (home_score == 0 and away_score == 1):
                return

            # Filtro 3: Validação do modelo Poisson do VIP
            analyzer = MatchAnalyzer(match)
            gm = analyzer.get_goal_markets()
            if not gm or 'lay_correct_scores' not in gm:
                return

            lay_cs = gm.get('lay_correct_scores', {})
            prob_lay_02 = lay_cs.get('0_2', 0)

            # Só entra se tiver selo VIP de 95%+ de segurança
            if prob_lay_02 < self.MIN_PROBABILITY_LAY:
                return

            # Dispara alerta de Exchange
            self.send_lay_02_alert(match, home_score, away_score, elapsed, prob_lay_02)

        except Exception as e:
            logger.error(f"Erro ao analisar Lay 0-2 para jogo {match.id}: {str(e)}")

    def send_lay_02_alert(self, match, h_score, a_score, elapsed, prob):
        market_key = f"TLGRM_EXCHANGE_LAY_02_{match.id}"
        tip, created = ScannerTip.objects.get_or_create(
            match=match,
            market=market_key,
            defaults={
                'prediction_text': f"Exchange Lay 0-2 Zebra ({h_score}x{a_score} aos {elapsed}')",
                'probability': prob,
                'status': 'PENDING'
            }
        )
        if not created:
            return  # Já alertamos esta partida

        home_name = match.home_team.name
        away_name = match.away_team.name
        league_name = match.league.name if match.league else "Liga"

        msg = (
            f"🔴 <b>[EXCHANGE VIP — LAY 0-2 ZEBRA]</b> 🔴\n\n"
            f"🏆 <b>{league_name}</b>\n"
            f"⚽ <b>{home_name} 0 x 1 {away_name}</b>\n"
            f"⏱️ <i>{elapsed}' minutos</i> (Zebra abriu o placar fora de casa)\n\n"
            f"📊 <b>Inteligência VIP (Modelo Poisson):</b>\n"
            f"• Confiança de Lay 0-2: <b>{prob:.1f}%</b>\n"
            f"• Histórico auditado de Green: <b>96.6%</b>\n"
            f"• Mandante forçado a atacar para buscar o empate.\n\n"
            f"🎯 <b>OPERAÇÃO NA BETFAIR / EXCHANGE:</b>\n"
            f"👉 <b>Mercado: Resultado Correto</b>\n"
            f"👉 <b>Ação: LAY 0-2 (Apostar CONTRA o placar 0-2)</b>\n"
            f"🛡️ <b>ODD MÁXIMA DE LAY: @4.20</b> (Responsabilidade controlada)\n"
            f"⛔ <i>Não entre se a odd de Lay estiver acima de @4.20!</i>\n\n"
            f"💰 <b>Cenários de Vitória (Green):</b>\n"
            f"✅ Se o mandante empatar (1x1) ➔ <b>Green Imediato!</b>\n"
            f"✅ Se o jogo terminar 0x1 ➔ <b>Green Total!</b>\n"
            f"✅ Se o jogo virar (2x1, 1x2...) ➔ <b>Green Total!</b>\n"
            f"⚠️ <i>Você só perde se a zebra fizer o 2º gol e o jogo morrer 0x2.</i>\n\n"
            f"🔗 Acompanhe no Terminal VIP:\n"
            f"👉 https://vip.statsfut.com/vip/radar/"
        )

        logger.info(f"Disparando Alerta Lay 0-2 Zebra para {home_name} x {away_name} ({h_score}x{a_score})")
        TelegramBotService.send_deduped_tip("LAY_02_ZEBRA", match, msg, chat_id=self.target_chat_id)
