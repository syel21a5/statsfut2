import logging
from django.conf import settings
from matches.models import Match, ScannerTip
from matches.services.advanced_stats import MatchAnalyzer
from matches.services.telegram_bot import TelegramBotService

logger = logging.getLogger(__name__)

class LiveOverDetector:
    """
    Robô Over 1.5 FT VIP — Drip Staking 2 Entradas (50% / 50%).
    Conectado com os critérios de alta assertividade do Painel VIP (vip.statsfut.com).
    
    Critérios:
    1. Régua VIP: Probabilidade matemática pré-jogo de Over 1.5 >= 80% (Padrão Elite).
    2. Entrada 1 (50% da Stake): Aos 20' (tolerância 19'-23') se o jogo estiver 0x0.
       - Odd Mínima de Valor: @1.45 (Não entrar abaixo disso!).
    3. Entrada 2 (50% da Stake restante): Aos 32' (tolerância 31'-35') se continuar 0x0.
       - Odd Mínima de Valor: @1.80 (Ideal @1.85 a @2.10. Não entrar abaixo de @1.80!).
    4. Se sair gol entre 20' e 45': Avisa oportunidade de Lay / Cashout Free Bet.
    5. No intervalo (HT 0x0): Mensagem de gestão para manter a calma sem cashout precipitado.
    """

    def __init__(self, target_chat_id=None):
        # Régua de Elite do Painel VIP (80%+)
        self.MIN_OVER_15_PROB = 80.0
        self.ENTRY_WINDOW = 2  # tolerância de minutos
        
        # Envia para o chat principal configurado (ou customizado)
        self.target_chat_id = target_chat_id or getattr(settings, 'TELEGRAM_CHAT_ID', None)

    def _send(self, msg, strategy_key, match):
        """Envia mensagem para o Telegram usando dedup canônico."""
        return TelegramBotService.send_deduped_tip(strategy_key, match, msg, chat_id=self.target_chat_id)

    def process_live_matches(self):
        """Busca jogos ao vivo e analisa oportunidades de Over 1.5 VIP."""
        logger.info("⚡ Verificando oportunidades Over 1.5 VIP (Drip Staking 2 Frações)...")

        live_matches = Match.objects.filter(
            status__in=['1H', '2H', 'HT', 'In Progress', 'Live', 'LIVE', 'In Play', 'IN_PLAY']
        ).select_related('home_team', 'away_team', 'league')

        for match in live_matches:
            self.analyze_match(match)

    def analyze_match(self, match):
        try:
            elapsed = match.elapsed_time or 0
            home_score = match.home_score or 0
            away_score = match.away_score or 0
            total_goals = home_score + away_score

            # Se já tem 2+ gols, Over 1.5 já bateu — nada a fazer
            if total_goals >= 2:
                return

            # Calcula tendência e probabilidades matemáticas do modelo VIP
            analyzer = MatchAnalyzer(match)
            stats = analyzer.generate_full_report()

            if not stats or 'goals' not in stats:
                return

            over_15 = stats['goals'].get('over_15', 0)

            # Filtro Estrito: Apenas jogos com selo de Elite do VIP (>= 80%)
            if over_15 < self.MIN_OVER_15_PROB:
                return

            # Fase de entrada fracionada (1º Tempo 0x0)
            if total_goals == 0:
                self._entry_phase(match, elapsed, over_15)
            else:
                # Já tem 1 gol — verifica se precisa alertar Free Bet / Lay se tiver entrado
                self._check_free_bet_layer(match, home_score, away_score, elapsed)

            # Fase HT 0x0 (Intervalo)
            if match.status == 'HT' and total_goals == 0:
                self._ht_hold_phase(match, over_15)

        except Exception as e:
            logger.error(f"Erro ao analisar jogo para Over 1.5 VIP {match.id}: {str(e)}")

    def _entry_phase(self, match, elapsed, over_15):
        """Dispara as 2 entradas fracionadas (20' e 32')."""
        entries = {
            20: ("TLGRM_VIP_OVER_ENTRY_1", "1ª ENTRADA (50% DA STAKE)", "1.45", 1),
            32: ("TLGRM_VIP_OVER_ENTRY_2", "2ª ENTRADA (50% RESTANTE)", "1.80", 2),
        }

        entry_minute = None
        market_key = None
        entry_title = None
        min_odd = None
        entry_step = None

        for target_min, (key, title, odd_lim, step) in entries.items():
            if abs(elapsed - target_min) <= self.ENTRY_WINDOW:
                entry_minute = target_min
                market_key = key
                entry_title = title
                min_odd = odd_lim
                entry_step = step
                break

        if not market_key:
            return

        # Anti-spam: registra no ScannerTip
        tip, created = ScannerTip.objects.get_or_create(
            match=match,
            market=market_key,
            defaults={
                'prediction_text': f"Over 1.5 VIP Entry {entry_minute}' ({over_15}%)",
                'probability': over_15,
                'status': 'PENDING'
            }
        )
        if not created:
            return

        league_name = match.league.name if match.league else "Liga"
        home_name = match.home_team.name
        away_name = match.away_team.name

        if entry_step == 1:
            instrucoes = (
                f"💰 <b>Fração da Stake:</b> 50% da sua unidade\n"
                f"🛡️ <b>ODD MÍNIMA DE VALOR: @{min_odd}</b> (Não entre abaixo de @{min_odd}!)\n"
                f"📌 <i>Se o jogo continuar 0x0, a 2ª fração será enviada aos 32' (Odd @1.80+).</i>\n"
                f"⚠️ <i>Se sair gol antes dos 32', a 2ª entrada fica automaticamente cancelada.</i>"
            )
        else:
            instrucoes = (
                f"💰 <b>Fração da Stake:</b> 50% restante da sua unidade\n"
                f"🛡️ <b>ODD MÍNIMA DE VALOR: @{min_odd}</b> (Ideal entre @1.85 e @2.10!)\n"
                f"📈 <b>Odd Média da Operação:</b> ~@1.65 a @1.75\n"
                f"📌 <i>Operação 100% montada. Agora aguarde os gols do 2º tempo com alta margem matemática!</i>"
            )

        msg = (
            f"⚡ <b>[ESTRATÉGIA OVER 1.5 VIP — {entry_title}]</b> ⚡\n\n"
            f"🏆 <b>{league_name}</b>\n"
            f"⚽ <b>{home_name} 0 x 0 {away_name}</b>\n"
            f"⏱️ <i>{elapsed}' minutos (1º Tempo)</i>\n\n"
            f"📊 <b>Modelo Matemático VIP:</b>\n"
            f"• Probabilidade Over 1.5: <b>{over_15}%</b> (Régua de Elite)\n"
            f"• Placar favorável: Jogo empatado em 0x0 valorizando as odds\n\n"
            f"🎯 <b>Recomendação de Entrada:</b>\n"
            f"👉 <b>Mercado: Mais de 1.5 Gols FT (Over 1.5)</b>\n\n"
            f"{instrucoes}\n\n"
            f"🔗 Acompanhe no Terminal VIP:\n"
            f"👉 https://vip.statsfut.com/vip/radar/"
        )

        logger.info(f"⚡ Over 1.5 VIP Entry {entry_minute}' disparada para {home_name} x {away_name}")
        self._send(msg, f"OVER_15_ENTRY_{entry_step}", match)

    def _check_free_bet_layer(self, match, h_score, a_score, elapsed):
        """Verifica se saiu o 1º gol durante a fase de entradas e orienta proteção/Free Bet."""
        if elapsed < 20 or elapsed > 46:
            return

        total_goals = h_score + a_score
        if total_goals != 1:
            return

        lay_key = "TLGRM_VIP_OVER_LAY_GOAL"
        tip, created = ScannerTip.objects.get_or_create(
            match=match,
            market=lay_key,
            defaults={
                'prediction_text': f"Over 1.5 VIP Free Bet ({h_score}x{a_score})",
                'probability': 0,
                'status': 'PENDING'
            }
        )
        if not created:
            return

        # Checa se houve pelo menos a 1ª entrada
        entry_keys = ['TLGRM_VIP_OVER_ENTRY_1', 'TLGRM_VIP_OVER_ENTRY_2']
        entradas_feitas = ScannerTip.objects.filter(
            match=match,
            market__in=entry_keys
        ).count()

        if entradas_feitas == 0:
            tip.delete()
            return

        league_name = match.league.name if match.league else "Liga"
        home_name = match.home_team.name
        away_name = match.away_team.name

        msg = (
            f"⚽ <b>[GOL NO JOGO — OVER 1.5 VIP]</b> ⚽\n\n"
            f"🏆 <b>{league_name}</b>\n"
            f"⚽ <b>{home_name} {h_score} x {a_score} {away_name}</b>\n"
            f"⏱️ <i>{elapsed}' minutos</i>\n\n"
            f"📌 <b>Orientação de Posição:</b>\n"
            f"• O 1º gol saiu! Resta apenas <b>mais 1 gol</b> para o Green Total.\n"
            f"• <b>2ª Entrada CANCELADA</b> caso você ainda não tivesse feito.\n\n"
            f"💡 <b>Opções do Trader:</b>\n"
            f"1. <b>Segurar a posição:</b> Jogo aberto com alta tendência histórica de sair o 2º gol.\n"
            f"2. <b>Cashout / Free Bet:</b> Encerrar com lucro garantido ou tirar o valor investido na casa de apostas.\n"
        )

        logger.info(f"⚽ Alerta de 1º Gol Over 1.5 VIP: {home_name} x {away_name}")
        self._send(msg, "OVER_15_GOAL", match)

    def _ht_hold_phase(self, match, over_15):
        """Fase de intervalo: se seguiu 0x0, mensagem de controle emocional e gestão."""
        market_key = "TLGRM_VIP_OVER_HT_HOLD"
        tip, created = ScannerTip.objects.get_or_create(
            match=match,
            market=market_key,
            defaults={
                'prediction_text': f"Over 1.5 VIP HT Hold ({over_15}%)",
                'probability': over_15,
                'status': 'PENDING'
            }
        )
        if not created:
            return

        entry_keys = ['TLGRM_VIP_OVER_ENTRY_1', 'TLGRM_VIP_OVER_ENTRY_2']
        entradas_feitas = ScannerTip.objects.filter(
            match=match,
            market__in=entry_keys
        ).count()

        if entradas_feitas == 0:
            return

        league_name = match.league.name if match.league else "Liga"
        home_name = match.home_team.name
        away_name = match.away_team.name

        msg = (
            f"🧘 <b>[INTERVALO 0x0 — GESTÃO OVER 1.5 VIP]</b> 🧘\n\n"
            f"🏆 <b>{league_name}</b>\n"
            f"⚽ <b>{home_name} 0 x 0 {away_name}</b>\n"
            f"⏱️ <i>Intervalo (HT)</i>\n\n"
            f"📊 Probabilidade Over 1.5 VIP: <b>{over_15}%</b>\n\n"
            f"⚠️ <b>Gestão Emocional Profissional:</b>\n"
            f"• NUNCA faça cashout com prejuízo no intervalo!\n"
            f"• Estatisticamente, mais de <b>65% dos gols</b> em jogos Over acontecem no 2º tempo (linhas abertas e cansaço físico).\n"
            f"• Mantenha a posição e confie no método matemático.\n"
        )

        logger.info(f"🧘 HT Hold Over 1.5 VIP: {home_name} x {away_name}")
        self._send(msg, "OVER_15_HT_HOLD", match)
