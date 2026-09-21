"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

from core.views import custom_set_language

# Rota de troca de idioma (sem prefixo, funciona de qualquer página)
urlpatterns = [
    path('i18n/setlang/', custom_set_language, name='set_language'),
    path('api/widgets/', include('widget_api.urls')),
]

from django.conf import settings

from core import vip_views
from core import cornerpro_views
from core import h2h_views

urlpatterns += [
    path('cornerpro/', cornerpro_views.cornerpro_home_view, name='cornerpro_home'),
    path('h2h-novo/<str:country_name>/<str:league_name>/<str:team1_name>/<str:team2_name>/', h2h_views.h2h_novo_view, name='h2h_novo'),
    path('vip/', vip_views.vip_games_list_view, name='vip_hub'),
    path('vip/jogos/', vip_views.vip_games_list_view, name='vip_games_list'),
    path('vip/analise/<int:match_id>/', vip_views.vip_match_analysis_view, name='vip_match_analysis'),
    path('vip/live-radar/', vip_views.vip_live_radar_view, name='vip_live_radar'),
    path('vip/radar/', vip_views.vip_live_radar_view, name='vip_radar'),
    path('vip/bots/', vip_views.vip_bot_studio_view, name='vip_bots'),
    path('vip/ferramentas/', vip_views.vip_tools_view, name='vip_tools'),
    path('vip/bilhetes/', vip_views.vip_tickets_view, name='vip_tickets'),
    path('vip/gestao/', vip_views.vip_management_view, name='vip_management'),
]

# Rotas com prefixo de idioma (/pt-br/, /es/, /de/) - inglês sem prefixo (/)
i18n_routes = [
    path('admin/', admin.site.urls),
    path('members/', include('members.urls')),
    path('vip/', vip_views.vip_games_list_view, name='vip_hub_i18n'),
    path('vip/jogos/', vip_views.vip_games_list_view, name='vip_games_list_i18n'),
    path('vip/analise/<int:match_id>/', vip_views.vip_match_analysis_view, name='vip_match_analysis_i18n'),
    path('vip/live-radar/', vip_views.vip_live_radar_view, name='vip_live_radar_i18n'),
    path('vip/radar/', vip_views.vip_live_radar_view, name='vip_radar_i18n'),
    path('vip/bots/', vip_views.vip_bot_studio_view, name='vip_bots_i18n'),
    path('vip/ferramentas/', vip_views.vip_tools_view, name='vip_tools_i18n'),
    path('vip/bilhetes/', vip_views.vip_tickets_view, name='vip_tickets_i18n'),
    path('vip/gestao/', vip_views.vip_management_view, name='vip_management_i18n'),
]

if 'video_maker' in settings.INSTALLED_APPS:
    i18n_routes.append(path('video-maker/', include('video_maker.urls')))

i18n_routes.append(path('', include('matches.urls')))

urlpatterns += i18n_patterns(
    *i18n_routes,
    prefix_default_language=False
)

from django.urls import re_path
from django.http import FileResponse, Http404
import os
from django.conf import settings

def serve_curated_image(request, filename_safe):
    # O Nginx intercepta qualquer URL com '.jpg'. Para evitar isso,
    # passamos a URL com '_dot_' no lugar do ponto.
    filename = filename_safe.replace("_dot_", ".")
    
    # Serve a imagem direto da pasta curated_images original na raiz do projeto
    path = os.path.join(settings.BASE_DIR, "curated_images", filename)
    if os.path.exists(path):
        return FileResponse(open(path, 'rb'))
    # Fallback para a pasta media ou static
    path2 = os.path.join(settings.BASE_DIR, "staticfiles", "curated_images", filename)
    if os.path.exists(path2):
        return FileResponse(open(path2, 'rb'))
    raise Http404("Imagem não encontrada")

# Forçar o Django a servir a pasta na web para o Blogger enxergar as imagens
urlpatterns += [
    path('imagens-blog/<str:filename_safe>', serve_curated_image),
]

# ── Servir áudios gerados via /api/dl-audio/ (bypass Nginx /media/) ──
def serve_audio_file(request, filename):
    """Serve arquivos de áudio da pasta media/audios_locucao/ em produção."""
    audio_dir = os.path.join(settings.MEDIA_ROOT, 'audios_locucao')
    full_path = os.path.join(audio_dir, filename)
    # Fallback: pasta audios_locucao na raiz do projeto (gerados antes do MEDIA_ROOT)
    if not os.path.exists(full_path):
        full_path = os.path.join(settings.BASE_DIR, 'audios_locucao', filename)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        return FileResponse(open(full_path, 'rb'))
    raise Http404("Arquivo de áudio não encontrado")

# ── Servir vídeos gerados via /api/dl-video/ ──
def serve_video_file(request, filename):
    """Serve arquivos de vídeo da pasta media/videos/output/ ou atemporal/output/ em produção."""
    video_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'output')
    full_path = os.path.join(video_dir, filename)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        return FileResponse(open(full_path, 'rb'), content_type='video/mp4')
        
    # Suporte para vídeos atemporais em video_maker/atemporal/output/
    atemporal_dir = "/www/wwwroot/statsfut.com/video_maker/atemporal/output"
    atemporal_path = os.path.join(atemporal_dir, filename)
    if os.path.exists(atemporal_path) and os.path.isfile(atemporal_path):
        return FileResponse(open(atemporal_path, 'rb'), content_type='video/mp4')
        
    raise Http404("Arquivo de vídeo não encontrado")

# ── Servir imagens de teste e preview de thumbnails ──
def serve_thumb_preview(request, filename):
    """Serve arquivos de preview de imagem da pasta media/videos/output/."""
    thumb_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'output')
    full_path = os.path.join(thumb_dir, filename)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        return FileResponse(open(full_path, 'rb'), content_type='image/png')
    raise Http404("Thumbnail não encontrada")

# ── Callback OAuth do YouTube ──
def serve_youtube_oauth_callback(request):
    """Recebe o código OAuth do Google e salva o token permanente do YouTube."""
    import os, json, requests
    code = request.GET.get('code')
    error = request.GET.get('error')
    if error:
        return HttpResponse(f"<h1>Erro na autorização do Google: {error}</h1>", status=400)
    if not code:
        return HttpResponse("<h1>Código de autorização não recebido.</h1>", status=400)
        
    cred_dir = "/www/wwwroot/statsfut.com/video_maker/credentials"
    secrets_file = os.path.join(cred_dir, "client_secrets_youtube.json")
    token_file = os.path.join(cred_dir, "youtube_token.json")
    
    try:
        # Troca direta do código pelo token via requisição REST padrão do Google
        with open(secrets_file, "r") as f:
            secret_data = json.load(f)
            
        client_config = secret_data.get("web") or secret_data.get("installed")
        client_id = client_config["client_id"]
        client_secret = client_config["client_secret"]
        token_uri = client_config.get("token_uri", "https://oauth2.googleapis.com/token")
        redirect_uri = "https://statsfut.com/api/youtube-callback"
        
        token_payload = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        
        r = requests.post(token_uri, data=token_payload, timeout=30)
        if r.status_code == 200:
            token_data = r.json()
            with open(token_file, "w") as tf:
                json.dump(token_data, tf, indent=2)
                
            return HttpResponse("""
                <div style='font-family: sans-serif; text-align: center; margin-top: 50px;'>
                    <h1 style='color: #10b981;'>🎉 Canal do YouTube Conectado com Sucesso!</h1>
                    <p style='font-size: 18px; color: #334155;'>As credenciais foram salvas no servidor do StatsFut. Você já pode fechar esta aba e voltar para o chat!</p>
                </div>
            """)
        else:
            return HttpResponse(f"<h1>Erro na troca do token ({r.status_code}):</h1><pre>{r.text}</pre>", status=400)
    except Exception as e:
        return HttpResponse(f"<h1>Erro ao processar credenciais: {str(e)}</h1>", status=500)

# ── Upload de Thumbnails para video_maker/thumbnails/ ──
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
import base64

def check_basic_auth(request):
    """Verifica autenticação HTTP Basic (usuário e senha do operador)."""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Basic '):
        try:
            auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
            username, password = auth_decoded.split(':', 1)
            if username == 'statsfut' and password == 'importe*$2010MT218exVaN$':
                return True
        except Exception:
            pass
    return False

@csrf_exempt
def upload_thumbnail_view(request):
    """Exibe a página de upload e processa o envio direto de thumbnails com proteção."""
    # Endpoint de checagem para o formulário de login integrado
    if request.GET.get('check_auth') == '1':
        if check_basic_auth(request):
            return JsonResponse({'authenticated': True})
        return JsonResponse({'authenticated': False, 'error': 'Credenciais inválidas'}, status=401)

    # Requisições POST (upload) exigem autenticação obrigatória
    if request.method == 'POST':
        if not check_basic_auth(request):
            return JsonResponse({'success': False, 'error': 'Não autorizado'}, status=401)
            
        match_id = request.POST.get('match_id', '').strip()
        thumb_file = request.FILES.get('thumbnail')
        
        if not match_id:
            return JsonResponse({'success': False, 'error': 'ID da partida não informado'}, status=400)
        if not thumb_file:
            return JsonResponse({'success': False, 'error': 'Nenhum arquivo enviado'}, status=400)
            
        dest_dir = "/www/wwwroot/statsfut.com/video_maker/thumbnails"
        os.makedirs(dest_dir, exist_ok=True)
        filename = f"match_{match_id}.jpg"
        dest_path = os.path.join(dest_dir, filename)
        
        try:
            with open(dest_path, 'wb+') as destination:
                for chunk in thumb_file.chunks():
                    destination.write(chunk)
            os.chmod(dest_path, 0o664)
            return JsonResponse({
                'success': True,
                'filename': filename,
                'path': dest_path,
                'url': f'/api/dl-thumb/{filename}'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # Requisição GET entrega o template com formulário integrado moderno
    html_path = "/www/wwwroot/statsfut.com/video_maker/upload_thumbnail.html"
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html; charset=utf-8')
    return HttpResponse("<h1>Página de upload não encontrada no servidor</h1>", status=404)

def serve_video_player(request):
    """Player HTML moderno para assistir vídeos atemporais em teste."""
    player_path = "/www/wwwroot/statsfut.com/video_maker/atemporal/templates/player.html"
    if os.path.exists(player_path):
        with open(player_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html; charset=utf-8')
    return HttpResponse("Player não encontrado", status=404)

urlpatterns += [
    path('api/dl-audio/<str:filename>', serve_audio_file),
    path('api/dl-video/<str:filename>', serve_video_file),
    path('api/preview-atemporal/', serve_video_player),
    path('api/dl-thumb/<str:filename>', serve_thumb_preview),
    path('api/youtube-callback', serve_youtube_oauth_callback),
    path('api/upload-thumbnail/', upload_thumbnail_view),
]


