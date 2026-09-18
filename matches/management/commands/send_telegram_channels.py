import logging
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from matches.models import BetTicket, ScannerTip

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Dispara tips e bilhetes diários nos canais do Telegram (Free e VIP)"

    def add_arguments(self, parser):
        parser.add_argument('--target', type=str, default='all', choices=['all', 'free', 'vip'], help="Canal alvo")

    def handle(self, *args, **options):
        target = options['target']
        bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        free_chat_id = getattr(settings, 'TELEGRAM_CHANNEL_FREE_ID', None)
        vip_chat_id = getattr(settings, 'TELEGRAM_CHANNEL_VIP_ID', None)

        if not bot_token:
            self.stderr.write("TELEGRAM_BOT_TOKEN não configurado.")
            return

        now = timezone.now()
        today_str = now.strftime('%d/%m/%Y')

        def send_tg(chat_id, text):
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            try:
                r = requests.post(url, json=payload, timeout=12)
                return r.status_code == 200
            except Exception as e:
                logger.error(f"Erro ao enviar Telegram: {e}")
                return False

        # ==========================================
        # 1. DISPARO PARA O CANAL VIP
        # ==========================================
        if target in ['all', 'vip'] and vip_chat_id:
            self.stdout.write("Disparando bateria de elite para o CANAL VIP...")

            # Buscar Bilhetes Ativos do Dia
            active_tickets = BetTicket.objects.filter(
                status='Pending',
                ticket_type__in=['Double', 'Treble']
            ).order_by('-average_probability')

            if active_tickets.exists():
                msg_vip_header = f"👑 <b>STATSFUT VIP • ESTRATÉGIAS DO DIA</b> 🚀\n"
                msg_vip_header += f"📅 <i>{today_str} • Taxa de Assertividade: 86% Green</i>\n\n"
                msg_vip_header += f"Confira os bilhetes gerados pela nossa inteligência de dados para hoje:\n"

                for t in active_tickets[:4]:
                    msg_vip_header += f"\n━━━━━━━━━━━━━━━━━━━━\n"
                    msg_vip_header += f"🎟️ <b>{t.title.upper()}</b>\n"
                    msg_vip_header += f"📊 <b>Odd Total:</b> <code>{t.total_odd}</code> | <b>Tipo:</b> {t.get_ticket_type_display()}\n\n"
                    
                    for s in t.selections.all():
                        m = s.match
                        msg_vip_header += f"⚽ <b>{m.home_team.name} vs {m.away_team.name}</b>\n"
                        msg_vip_header += f"   📌 <b>Entrada:</b> {s.prediction_label}\n"
                        msg_vip_header += f"   📈 <b>Odd:</b> {s.odd} | <b>Confiança:</b> {s.probability}%\n"

                msg_vip_header += f"\n━━━━━━━━━━━━━━━━━━━━\n"
                msg_vip_header += f"🔗 <b>Acesse o painel VIP:</b> https://statsfut.com/members/premium/\n"
                msg_vip_header += f"<i>Gestão de banca recomendada: 1 a 2 unidades por bilhete.</i>"

                send_tg(vip_chat_id, msg_vip_header)
                self.stdout.write("Bilhetes enviados com sucesso no VIP!")

            # Buscar Top 3 Picks do Sniper VIP
            sniper_tips = ScannerTip.objects.filter(
                status='Pending',
                probability__gte=90,
                match__date__gte=now
            ).order_by('-probability', 'match__date')[:5]

            if sniper_tips.exists():
                msg_sniper = f"🎯 <b>SNIPER VIP • TOP PICKS DE OURO (90%+)</b>\n"
                msg_sniper += f"📅 <i>Seleções com a maior certeza matemática do dia</i>\n\n"
                for st in sniper_tips:
                    m = st.match
                    time_str = m.date.strftime('%H:%M')
                    msg_sniper += f"⏰ <b>{time_str}</b> | 🏆 {m.league.name}\n"
                    msg_sniper += f"⚽ <b>{m.home_team.name} vs {m.away_team.name}</b>\n"
                    msg_sniper += f"👉 <b>Entrada:</b> <code>{st.prediction_text}</code>\n"
                    msg_sniper += f"🛡️ <b>Probabilidade:</b> <b>{st.probability}% de Green</b>\n\n"

                msg_sniper += f"📊 <i>Todas as odds calculadas via Poisson & xG no StatsFut VIP.</i>"
                send_tg(vip_chat_id, msg_sniper)
                self.stdout.write("Sniper enviado com sucesso no VIP!")

        # ==========================================
        # 2. DISPARO PARA O CANAL FREE (FREEMIUM)
        # ==========================================
        if target in ['all', 'free'] and free_chat_id:
            self.stdout.write("Disparando degustação para o CANAL FREE...")

            # Pegar a melhor Dupla de Ouro para demonstração
            best_ticket = BetTicket.objects.filter(
                status='Pending',
                ticket_type='Double'
            ).order_by('-average_probability').first()

            # Pegar 1 Sniper de Ouro
            best_sniper = ScannerTip.objects.filter(
                status='Pending',
                probability__gte=90,
                match__date__gte=now
            ).order_by('-probability').first()

            # Pegar 1 Lay Placar 96%+
            best_lay = ScannerTip.objects.filter(
                status='Pending',
                market__startswith='LAY_',
                probability__gte=96,
                match__date__gte=now
            ).order_by('-probability').first()

            msg_free = f"🔥 <b>STATSFUT • DEGUSTAÇÃO GRATUITA DO DIA</b> ⚽\n"
            msg_free += f"📅 <i>{today_str} • Projeções Matemáticas Avançadas</i>\n\n"
            msg_free += f"Aqui está a sua dose diária de dados de alta precisão:\n"

            if best_ticket:
                msg_free += f"\n━━━━━━━━━━━━━━━━━━━━\n"
                msg_free += f"🎟️ <b>BILHETE DUPLA DO DIA (86% Green)</b>\n"
                msg_free += f"📊 <b>Odd Combinada:</b> <code>{best_ticket.total_odd}</code>\n\n"
                for s in best_ticket.selections.all():
                    m = s.match
                    msg_free += f"⚽ <b>{m.home_team.name} vs {m.away_team.name}</b>\n"
                    msg_free += f"   👉 {s.prediction_label} (Odd {s.odd})\n"

            if best_sniper:
                m = best_sniper.match
                msg_free += f"\n━━━━━━━━━━━━━━━━━━━━\n"
                msg_free += f"🎯 <b>ENTRADA SNIPER (90%+ Confiança)</b>\n"
                msg_free += f"⚽ <b>{m.home_team.name} vs {m.away_team.name}</b>\n"
                msg_free += f"👉 <b>Mercado:</b> <code>{best_sniper.prediction_text}</code>\n"
                msg_free += f"🛡️ <b>Probabilidade:</b> {best_sniper.probability}% de Acerto\n"

            if best_lay:
                m = best_lay.match
                msg_free += f"\n━━━━━━━━━━━━━━━━━━━━\n"
                msg_free += f"⚡ <b>SMART LAY PLACAR (96%+ Green)</b>\n"
                msg_free += f"⚽ <b>{m.home_team.name} vs {m.away_team.name}</b>\n"
                msg_free += f"👉 <b>Contra Placar:</b> <code>{best_lay.prediction_text}</code>\n"
                msg_free += f"🛡️ <b>Assertividade:</b> {best_lay.probability}% Green\n"

            msg_free += f"\n━━━━━━━━━━━━━━━━━━━━\n"
            msg_free += f"🔒 <b>Quer receber TODOS os bilhetes prontos e ter o Scanner ao vivo completo?</b>\n\n"
            msg_free += f"👑 <i>Faça o upgrade agora para o Plano VIP por apenas R$ 18/mês:</i>\n"
            msg_free += f"👉 <a href='https://pay.kiwify.com.br/qiGV4Pk'><b>CLIQUE AQUI PARA ASSINAR O VIP (KIWIFY)</b></a>\n"
            msg_free += f"🌍 <i>Cartão Internacional (Stripe):</i> <a href='https://buy.stripe.com/28E3cw4MK0TvaQddyu7EQ02'>Assinar via Stripe</a>"

            send_tg(free_chat_id, msg_free)
            self.stdout.write("Degustação enviada com sucesso no canal Free!")
