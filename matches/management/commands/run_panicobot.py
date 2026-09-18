from django.core.management.base import BaseCommand
from matches.services.panicobot_detector import PanicoBotDetector

class Command(BaseCommand):
    help = 'Executa o PanicoBot (alerta de pânico no mercado para Under 6.5 no 1º tempo).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--chat-id',
            type=str,
            default=None,
            help='Chat ID ou @canal de destino para envio dos alertas no Telegram.'
        )

    def handle(self, *args, **options):
        chat_id = options.get('chat_id')
        self.stdout.write(self.style.NOTICE(f"🚨 Iniciando varredura do PanicoBot (Chat ID: {chat_id or 'Padrão'})..."))
        
        try:
            detector = PanicoBotDetector(target_chat_id=chat_id)
            detector.process_live_matches()
            self.stdout.write(self.style.SUCCESS("✅ Varredura do PanicoBot concluída com sucesso."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro ao executar PanicoBot: {e}"))
