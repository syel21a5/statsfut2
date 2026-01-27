import os
import time
import subprocess
import django
from django.utils import timezone
from datetime import datetime, timedelta

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from matches.models import Match

# ==========================================
# CONFIGURAÇÃO DE INTERVALOS INTELIGENTES
# ==========================================

# Quando NÃO há jogos ao vivo ou próximos (modo econômico)
IDLE_CHECK_INTERVAL = 300  # 5 minutos (economiza ~80% de chamadas)

# Quando HÁ jogos ao vivo ou começando em breve (modo ativo)
ACTIVE_UPDATE_INTERVAL = 60  # 1 minuto (atualização rápida)

# Sincronização completa (resultados + próximos 14 dias)
FULL_SYNC_INTERVAL = 3600  # 1 hora

# Buffer de tempo para considerar jogo "próximo"
UPCOMING_BUFFER_MINUTES = 30

last_full_sync = None
last_mode = "IDLE"  # Rastreia modo atual para logging

def check_active_matches():
    """
    Verifica se há jogos ao vivo ou próximos no banco de dados.
    Retorna True se houver atividade, False caso contrário.
    """
    now = timezone.now()
    buffer_time = now + timedelta(minutes=UPCOMING_BUFFER_MINUTES)
    
    # Busca jogos que estão ao vivo ou começam em breve
    active_matches = Match.objects.filter(
        date__lte=buffer_time,
        status__in=['Scheduled', 'Live', '1H', 'HT', '2H', 'ET', 'PEN', 'IN_PLAY']
    ).exclude(status__in=['Finished', 'Postponed', 'Cancelled'])
    
    return active_matches.exists()

def run_live_update():
    """
    Atualiza apenas jogos que estão acontecendo AGORA ou começando em breve.
    Só chama a API se realmente houver jogos ativos.
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔴 Verificando jogos ao vivo...")
    try:
        has_active = check_active_matches()
        
        if has_active:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚽ Jogos ativos detectados! Atualizando via API...")
            subprocess.run(["python3", "manage.py", "update_live_matches", "--mode", "live"], check=True)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 💤 Nenhum jogo ao vivo no momento (economizando API).")
            
    except Exception as e:
        print(f"❌ Erro na atualização ao vivo: {e}")

def run_full_sync():
    """
    Atualiza TUDO: Resultados de hoje, jogos de ontem (se tiver), e calendário dos próximos 14 dias.
    Garante que o banco tenha dados frescos para a checagem inteligente funcionar.
    """
    global last_full_sync
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Iniciando Sincronização Completa (Resultados + Calendário)...")
    try:
        subprocess.run(["python3", "manage.py", "update_live_matches", "--mode", "upcoming"], check=True)
        last_full_sync = datetime.now()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Sincronização Completa finalizada.")
    except Exception as e:
        print(f"❌ Erro na sincronização completa: {e}")

def get_smart_interval():
    """
    Retorna o intervalo apropriado baseado na atividade de jogos.
    IDLE (5min) quando não há jogos, ACTIVE (1min) quando há.
    """
    global last_mode
    
    has_active = check_active_matches()
    
    if has_active:
        if last_mode != "ACTIVE":
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🟢 Modo ATIVO: Atualizações a cada {ACTIVE_UPDATE_INTERVAL}s")
            last_mode = "ACTIVE"
        return ACTIVE_UPDATE_INTERVAL
    else:
        if last_mode != "IDLE":
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🟡 Modo ECONÔMICO: Checagens a cada {IDLE_CHECK_INTERVAL}s")
            last_mode = "IDLE"
        return IDLE_CHECK_INTERVAL

if __name__ == "__main__":
    print("="*60)
    print("🚀 StatsFut Smart Auto-Updater v2.0")
    print("="*60)
    print("📊 Configurações:")
    print(f"   • Modo ECONÔMICO: {IDLE_CHECK_INTERVAL}s (sem jogos)")
    print(f"   • Modo ATIVO: {ACTIVE_UPDATE_INTERVAL}s (com jogos)")
    print(f"   • Sync Completo: {FULL_SYNC_INTERVAL}s (1 hora)")
    print("="*60)
    print("💡 Sistema inteligente: economiza ~80% de chamadas API!")
    print("="*60)

    # Força um sync completo ao iniciar para garantir dados frescos
    run_full_sync()

    while True:
        try:
            # Verifica se está na hora do Full Sync
            if not last_full_sync or (datetime.now() - last_full_sync).total_seconds() > FULL_SYNC_INTERVAL:
                run_full_sync()
            
            # Roda atualização Live (só chama API se houver jogos)
            run_live_update()
            
            # Aguarda próximo ciclo com intervalo inteligente
            smart_interval = get_smart_interval()
            time.sleep(smart_interval)
            
        except KeyboardInterrupt:
            print("\n🛑 Monitoramento paralisado pelo usuário.")
            break
        except Exception as e:
            print(f"❌ Erro fatal no loop principal: {e}")
            time.sleep(60)
