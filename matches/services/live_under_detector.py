import logging
from matches.models import Match
from matches.services.advanced_stats import MatchAnalyzer
from matches.services.telegram_bot import TelegramBotService

logger = logging.getLogger(__name__)

class LiveUnderDetector:
    """
    Robô Under Dinâmico — Radar Completo de Oportunidades no 1º Tempo.
    Foco: Encontrar jogos com forte matemática Under (<= 15% Over 4.5).
    Fases:
    1. Radar Inicial (0x0 nos primeiros 10min)
    2. Surfar o Pânico do mercado se saírem gols (1, 2, 3...) no 1º tempo.
    """

    def __init__(self):
        # Janela de Ouro Blindada: 2º gol saindo entre 25' e 35' (74.2% de Win Rate auditado)
        self.MIN_MINUTE = 25
        self.MAX_MINUTE = 35

        # A Regra de Ouro: Over 4.5 pré-jogo deve ser <= 18%
        self.MAX_OVER_45_PROB = 18.0

        # Lista Negra de Ligas Suicidas (historicamente > 50% de RED em jogos malucos com 2 gols cedo)
        self.BLACKLISTED_LEAGUES = [
            'super league', 'besta deild', 'ykkosliiga', 'ykkösliiga', 
            '1st division', 'u20', 'u21', 'u19', 'sub-20', 'sub-21', 'sub-19',
            'amateur', 'regional', 'oberliga'
        ]

    def process_live_matches(self):
        """Busca jogos ao vivo e analisa oportunidades de Under."""
        logger.info("🛡️ Verificando oportunidades Under Dinâmico (Radar HT)...")

        live_matches = Match.objects.filter(
            status__in=['1H', 'HT', 'In Progress', 'Live']
        ).select_related('home_team', 'away_team', 'league')

        for match in live_matches:
            self.analyze_match(match)

    def analyze_match(self, match):
        try:
            # 1. Garante que só olha para o Primeiro Tempo
            if match.status in ['2H', 'FT', 'Finished', 'Match Finished']:
                return

            home_score = match.home_score or 0
            away_score = match.away_score or 0
            total_goals = home_score + away_score

            # 2. REGRA DE OURO INEGOCIÁVEL: EXATAMENTE 2 GOLS NO PLACAR!
            # (Se tiver 3 gols ou mais, a auditoria provou que o risco de RED passa de 58%!)
            if total_goals != 2:
                return

            # 3. FILTRO DE MINUTAGEM: Entre o 18' e 32'
            elapsed = match.elapsed_time or 0
            if not (self.MIN_MINUTE <= elapsed <= self.MAX_MINUTE):
                return

            # 4. FILTRO DE LIGA: Bloquear ligas doidas / de alta variância
            league_name = (match.league.name if match.league else '').lower()
            league_country = (match.league.country if match.league and match.league.country else '').lower()
            full_league_str = f"{league_country} {league_name}"
            for blacklisted in self.BLACKLISTED_LEAGUES:
                if blacklisted in full_league_str:
                    logger.info(f"🛡️ Under Detector: Jogo {match.id} ignorado por estar em liga de alto risco ({match.league.name}).")
                    return

            # 5. FILTRO DE TELEMETRIA AO VIVO: Ritmo não pode ser tiroteio desenfreado
            tot_shots = (match.home_shots or 0) + (match.away_shots or 0)
            if tot_shots > 9:  # Mais de 9 chutes aos 30' indica partida aberta
                logger.info(f"🛡️ Under Detector: Jogo {match.id} ignorado por excesso de chutes ({tot_shots} chutes aos {elapsed}').")
                return

            # 6. Analisa as estatísticas pré-jogo
            analyzer = MatchAnalyzer(match)
            stats = analyzer.generate_full_report()

            if not stats or 'goals' not in stats:
                return

            over_45_prob = stats['goals'].get('over_45', 100)

            # Filtro Mestre: Validação Matemática pré-jogo
            if over_45_prob <= self.MAX_OVER_45_PROB:
                self.send_telegram_alert(
                    match, home_score, away_score, elapsed, over_45_prob, total_goals
                )

        except Exception as e:
            logger.error(f"Erro ao analisar Under para jogo {match.id}: {str(e)}")

    def send_telegram_alert(self, match, h_score, a_score, elapsed, over_45_prob, total_goals):
        from matches.models import ScannerTip

        # Anti-spam definitivo via Banco de Dados
        market_key = "TLGRM_UNDER_45_SNIPER"
        tip, created = ScannerTip.objects.get_or_create(
            match=match,
            market=market_key,
            defaults={
                'prediction_text': f"Telegram Under 4.5 Sniper Alert ({h_score}x{a_score} aos {elapsed}')",
                'probability': over_45_prob,
                'status': 'PENDING'
            }
        )
        
        # Se já alertou esta partida, não envia de novo
        if not created:
            return

        home_name = match.home_team.name
        away_name = match.away_team.name
        league = match.league.name if match.league else 'Liga'
        under_45_prob = round(100 - over_45_prob, 1)

        msg = (
            f"🛡️ <b>SNIPER UNDER 4.5 (Pós-Gols Rápidos)</b> 🛡️\n\n"
            f"🏆 <b>{league}</b>\n"
            f"⚽ <b>{home_name} {h_score} x {a_score} {away_name}</b>\n"
            f"⏱️ <i>{elapsed}' minutos (1º Tempo)</i>\n\n"
            f"📊 <b>Leitura de Valor & Telemetria:</b>\n"
            f"• Placar controlado: Exatamente 2 gols no 1T\n"
            f"• Confiança matemática prévia: <b>{under_45_prob}%</b> de Under\n"
            f"• O mercado inflacionou a linha para <b>Under 4.5</b> pagando odds altas!\n\n"
            f"🎯 <b>Recomendação de Entrada:</b>\n"
            f"👉 <b>Mercado: Menos de 4.5 Gols (Under 4.5 FT)</b>\n"
            f"💰 <b>ODD MÍNIMA DE VALOR: @1.45</b> (Ideal entre @1.50 e @1.75)\n"
            f"⛔ <i>NUNCA entre se a odd estiver abaixo de @1.45 ou se já tiver saído o 3º gol!</i>\n\n"
            f"⚠️ <b>GESTÃO DE BANCA BLINDADA:</b>\n"
            f"• Stake Fixa: <b>1% a 1.5% da banca</b> (NUNCA aumente a mão)\n"
            f"• Stop Loss: Máximo de 2 reds no dia nesta tática\n\n"
            f"🔗 Acompanhe o Live Radar no Terminal VIP:\n"
            f"👉 https://vip.statsfut.com/vip/radar/"
        )

        logger.info(f"Disparando Under 4.5 Sniper Alert para {home_name} x {away_name} ({h_score}x{a_score} aos {elapsed}')")
        TelegramBotService.send_message(msg)
