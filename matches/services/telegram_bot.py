import requests
import logging
import re
import unicodedata
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

def _normalize_team_token(name: str) -> str:
    """Normaliza o nome do time para chave única (ex: 'Inter Miami CF' -> 'intermiami')."""
    if not name:
        return ""
    n = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').lower()
    # Remove sufixos comuns de clubes que causam duplicidade em feeds diferentes
    n = re.sub(r'\b(fc|cf|ec|sc|ac|cr|jk|fk|sk|cd|ca|de|da|do|sportif|faaliyetler)\b', '', n)
    return "".join(c for c in n if c.isalnum())

class TelegramBotService:
    @staticmethod
    def send_message(text: str, chat_id: str = None) -> bool:
        """
        Envia uma mensagem de texto para um chat específico via Telegram Bot API.
        Se chat_id não for fornecido, tenta usar o TELEGRAM_CHAT_ID do settings.
        """
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        target_chat_id = chat_id or getattr(settings, 'TELEGRAM_CHAT_ID', None)
        
        if not token or not target_chat_id:
            logger.warning("TelegramBotService: Token ou Chat ID ausente. Mensagem não enviada.")
            return False
            
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": target_chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Erro ao enviar Telegram: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Exceção ao enviar Telegram: {str(e)}")
            return False

    @staticmethod
    def send_deduped_tip(strategy_key: str, match, msg_text: str, chat_id: str = None, timeout_hours: int = 4) -> bool:
        """
        Blindagem Definitiva Anti-Duplicidade para Alertas de Telegram:
        Evita envio duplicado causado por:
        1. Jogos duplicados no banco com IDs diferentes (ex: Inter Miami vs Inter Miami CF).
        2. Execuções paralelas ou consecutivas de rotinas de cron.
        3. Registros de ScannerTip com keys distintas para o mesmo jogo.
        """
        h_norm = _normalize_team_token(match.home_team.name if match.home_team else "")
        a_norm = _normalize_team_token(match.away_team.name if match.away_team else "")
        
        # Chave canônica unificada de times normalizados
        cache_key = f"tg_tip_sent_{strategy_key}_{h_norm}_{a_norm}"
        
        # Se já enviamos nos últimos N horas para esse mesmo confronto e estratégia, bloqueia!
        if cache.get(cache_key):
            logger.info(f"[Anti-Duplicação] Alerta '{strategy_key}' já enviado para {match.home_team.name} x {match.away_team.name}. Bloqueando disparo repetido.")
            return False
            
        # Grava a trava no cache antes do envio (TTL padrão 4 horas = duração de um jogo)
        cache.set(cache_key, True, timeout_hours * 3600)
        
        return TelegramBotService.send_message(msg_text, chat_id=chat_id)

    @staticmethod
    def get_updates() -> list:
        """
        Puxa as últimas mensagens recebidas pelo Bot (usado para descobrir o Chat ID).
        """
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not token:
            return []
            
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json().get('result', [])
            return []
        except Exception:
            return []
