from django.core.management.base import BaseCommand
from matches.services.live_lay_detector import LiveLayDetector
from matches.services.live_under_detector import LiveUnderDetector
from matches.services.live_over_detector import LiveOverDetector

class Command(BaseCommand):
    help = 'Executa o Hub Unificado de Robôs de Telegram ao vivo (Lay + Under Pro + Over 1.5 VIP).'

    def handle(self, *args, **options):
        # Robô 1: Lay Correct Score (Apostar contra placares improváveis)
        self.stdout.write(self.style.NOTICE("🎯 Robô 1: Live Lay Detector..."))
        try:
            lay_detector = LiveLayDetector()
            lay_detector.process_live_matches()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro no Lay Detector: {e}"))

        # Robô 2: Under 4.5 Sniper Pro (Surfar no jogo que esfria após 2 gols rápidos)
        self.stdout.write(self.style.NOTICE("🛡️ Robô 2: Under 4.5 Sniper Pro..."))
        try:
            under_detector = LiveUnderDetector()
            under_detector.process_live_matches()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro no Under Detector: {e}"))

        # Robô 3: Over 1.5 FT VIP (Drip Staking 2 Frações: 20' @1.45+ e 32' @1.80+)
        self.stdout.write(self.style.NOTICE("⚡ Robô 3: Over 1.5 FT VIP (Drip Staking)..."))
        try:
            over_detector = LiveOverDetector()
            over_detector.process_live_matches()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro no Over 1.5 VIP Detector: {e}"))

        self.stdout.write(self.style.SUCCESS("✅ Todos os robôs do Hub concluídos."))
