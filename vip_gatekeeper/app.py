import http.server
import socketserver
import urllib.request
import urllib.parse
import urllib.error
import os
import sys
import hmac
import hashlib
import time

# Configurar Django para autenticar diretamente com os usuários do banco de dados
sys.path.insert(0, '/www/wwwroot/statsfut.com')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
try:
    import django
    django.setup()
    from django.contrib.auth import authenticate
    from django.contrib.auth.models import User
    from members.models import UserProfile
    DJANGO_AVAILABLE = True
except Exception as e:
    print(f"Aviso: Não foi possível carregar o Django no Gatekeeper: {e}")
    DJANGO_AVAILABLE = False

PORT = 8094
COOKIE_NAME = "vip_session"
SECRET_KEY = os.environ.get("VIP_GATEKEEPER_SECRET", "statsfut_vip_sec_token_2026_q8w9e")
ADMIN_USER = os.environ.get("VIP_ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("VIP_ADMIN_PASS", "statsfut@2026")

def generate_session_token(username, plan_type="vip"):
    ts = int(time.time())
    data = f"{username}:{plan_type}:{ts}"
    sig = hmac.new(SECRET_KEY.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"{data}:{sig}"

def verify_session_token(token):
    if not token:
        return False, None, None
    # Token de desenvolvimento/legado
    if token == "vip_auth_ok_2026":
        return True, "admin", "vip"
    parts = token.split(":")
    if len(parts) != 4:
        return False, None, None
    username, plan_type, ts_str, sig = parts
    try:
        ts = int(ts_str)
        # Sessão expira em 30 dias (30 * 86400 segundos)
        if time.time() - ts > (30 * 86400):
            return False, None, None
        expected_data = f"{username}:{plan_type}:{ts}"
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), expected_data.encode('utf-8'), hashlib.sha256).hexdigest()
        if hmac.compare_digest(sig, expected_sig):
            return True, username, plan_type
    except Exception:
        pass
    return False, None, None

LOGIN_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StatsFut VIP · Acesso Exclusivo</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #0b0e14; color: #e2e8f0; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
        .terminal-border { border: 1px solid rgba(255, 255, 255, 0.08); }
        .glow-cyan { text-shadow: 0 0 10px rgba(0, 180, 216, 0.4); }
    </style>
</head>
<body class="flex items-center justify-center min-h-screen p-4 bg-[#0b0e14]">
    <div class="w-full max-w-md bg-[#10141d] terminal-border rounded-2xl p-8 shadow-2xl relative overflow-hidden">
        <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-500 via-cyan-500 to-indigo-500"></div>
        
        <div class="text-center mb-8">
            <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 mb-4 shadow-lg shadow-amber-500/5">
                <i class="fa-solid fa-crown text-2xl"></i>
            </div>
            <h1 class="text-xl font-bold text-white tracking-wider flex items-center justify-center gap-2">
                STATSFUT <span class="text-amber-400 font-extrabold">VIP TOTAL</span>
            </h1>
            <p class="text-gray-400 text-xs mt-2">Terminal Quantitativo de Elite & Alertas In-Play</p>
        </div>

        {error_box}

        <form method="POST" action="/vip-login" class="space-y-4">
            <div>
                <label class="block text-xs uppercase tracking-wider text-gray-400 mb-2 font-semibold">E-mail ou Usuário</label>
                <div class="relative">
                    <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500"><i class="fa-solid fa-user text-xs"></i></span>
                    <input type="text" name="username" required autofocus placeholder="seu@email.com" 
                           class="w-full pl-9 pr-3 py-2.5 bg-[#0a0d14] border border-gray-800 rounded-xl text-white text-sm focus:outline-none focus:border-amber-500 transition">
                </div>
            </div>

            <div>
                <label class="block text-xs uppercase tracking-wider text-gray-400 mb-2 font-semibold">Senha de Acesso</label>
                <div class="relative">
                    <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500"><i class="fa-solid fa-lock text-xs"></i></span>
                    <input type="password" name="password" required placeholder="••••••••" 
                           class="w-full pl-9 pr-3 py-2.5 bg-[#0a0d14] border border-gray-800 rounded-xl text-white text-sm focus:outline-none focus:border-amber-500 transition">
                </div>
            </div>

            <button type="submit" 
                    class="w-full py-3 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-black font-bold rounded-xl transition shadow-lg shadow-amber-500/20 text-sm tracking-wide flex items-center justify-center gap-2">
                <span>ACESSAR TERMINAL VIP</span>
                <i class="fa-solid fa-arrow-right text-xs"></i>
            </button>
        </form>

        <div class="mt-8 pt-6 border-t border-gray-800/80 text-center">
            <p class="text-gray-400 text-xs mb-3">Ainda não possui o Plano VIP Total?</p>
            <a href="https://statsfut.com/members/plans/" target="_blank" 
               class="inline-flex items-center gap-2 text-cyan-400 hover:text-cyan-300 text-xs font-semibold hover:underline">
                <span>Conhecer os Recursos & Fazer Assinatura</span>
                <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
            </a>
        </div>
    </div>
</body>
</html>
"""

PAYWALL_UPGRADE_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upgrade para VIP Total · StatsFut</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #0b0e14; color: #e2e8f0; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
        .terminal-border { border: 1px solid rgba(255, 255, 255, 0.08); }
    </style>
</head>
<body class="flex items-center justify-center min-h-screen p-4 bg-[#0b0e14]">
    <div class="w-full max-w-xl bg-[#10141d] terminal-border rounded-2xl p-8 shadow-2xl relative overflow-hidden text-center">
        <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-500 via-rose-500 to-amber-500"></div>

        <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-400 mb-5 shadow-lg shadow-amber-500/10">
            <i class="fa-solid fa-lock text-3xl"></i>
        </div>

        <span class="px-3 py-1 bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-bold rounded-full uppercase tracking-wider">
            Exclusivo para Assinantes VIP Total
        </span>

        <h1 class="text-2xl font-bold text-white mt-4 tracking-tight">
            Olá, <span class="text-amber-400">{username}</span>!
        </h1>
        
        <p class="text-gray-400 text-xs max-w-md mx-auto mt-3 leading-relaxed">
            Identificamos que você possui o <strong class="text-white">Plano Popular</strong>. O terminal quantitativo, robôs privados no Telegram e scanner +EV são armas restritas do <strong class="text-amber-400">Plano VIP Total</strong>.
        </p>

        <!-- Benefícios do Upgrade -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left my-6 bg-[#0a0d14] p-4 rounded-xl border border-gray-800 text-xs">
            <div class="flex items-center gap-2.5 text-gray-300">
                <i class="fa-solid fa-bolt text-amber-400"></i>
                <span>Radar In-Play com APM de Pressão</span>
            </div>
            <div class="flex items-center gap-2.5 text-gray-300">
                <i class="fa-solid fa-robot text-cyan-400"></i>
                <span>VIP Bot Studio & Alertas no Telegram</span>
            </div>
            <div class="flex items-center gap-2.5 text-gray-300">
                <i class="fa-solid fa-calculator text-emerald-400"></i>
                <span>Calculadora Hedge, Kelly & Scanner +EV</span>
            </div>
            <div class="flex items-center gap-2.5 text-gray-300">
                <i class="fa-solid fa-ticket text-rose-400"></i>
                <span>Bilhetes Prontos de Elite (90%+ Winrate)</span>
            </div>
        </div>

        <div class="flex flex-col sm:flex-row gap-3 justify-center">
            <a href="https://pay.kiwify.com.br/qiGV4Pk" target="_blank"
               class="px-6 py-3.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-black font-bold rounded-xl transition shadow-lg shadow-amber-500/20 text-xs tracking-wider flex items-center justify-center gap-2">
                <i class="fa-solid fa-crown"></i>
                <span>FAZER UPGRADE PARA VIP TOTAL</span>
            </a>
            
            <a href="https://statsfut.com/members/premium/" 
               class="px-5 py-3.5 bg-gray-800 hover:bg-gray-700 text-gray-300 font-semibold rounded-xl transition text-xs flex items-center justify-center gap-2">
                <i class="fa-solid fa-arrow-left"></i>
                <span>Voltar ao Painel Popular</span>
            </a>
        </div>

        <div class="mt-6 pt-4 border-t border-gray-800 text-center text-[11px] text-gray-500">
            Deseja sair desta conta? <a href="/vip-logout" class="text-rose-400 hover:underline">Fazer Logout</a>
        </div>
    </div>
</body>
</html>
"""

class VIPProxyHandler(http.server.BaseHTTPRequestHandler):

    def send_no_cache_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")

    def get_cookie(self, name):
        cookie_header = self.headers.get('Cookie')
        if not cookie_header:
            return None
        cookies = cookie_header.split(';')
        for c in cookies:
            c = c.strip()
            if c.startswith(name + '='):
                return c[len(name)+1:]
        return None

    def check_auth(self):
        cookie_val = self.get_cookie(COOKIE_NAME)
        valid, username, plan_type = verify_session_token(cookie_val)
        return valid, username, plan_type

    def do_GET(self):
        # 1. Rota de logout
        if self.path == "/vip-logout":
            self.send_response(302)
            self.send_header("Set-Cookie", f"{COOKIE_NAME}=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; SameSite=Lax")
            self.send_header("Location", "/vip-login")
            self.send_header("Content-Length", "0")
            self.send_no_cache_headers()
            self.end_headers()
            return

        # 2. Rota de login
        if self.path.startswith("/vip-login"):
            valid, username, plan_type = self.check_auth()
            if valid and plan_type == 'vip':
                self.send_response(302)
                self.send_header("Location", "/")
                self.send_header("Content-Length", "0")
                self.send_no_cache_headers()
                self.end_headers()
                return

            content = LOGIN_HTML.replace("{error_box}", "").encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_no_cache_headers()
            self.end_headers()
            self.wfile.write(content)
            return

        # 3. Rota de Paywall / Upgrade
        if self.path.startswith("/vip-upgrade"):
            valid, username, plan_type = self.check_auth()
            display_user = username if username else "Apostador"
            content = PAYWALL_UPGRADE_HTML.replace("{username}", display_user).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_no_cache_headers()
            self.end_headers()
            self.wfile.write(content)
            return

        # 4. Verificação de Acesso / Paywall
        valid, username, plan_type = self.check_auth()
        if not valid:
            self.send_response(302)
            self.send_header("Location", "/vip-login")
            self.send_header("Content-Length", "0")
            self.send_no_cache_headers()
            self.end_headers()
            return

        # Usuário autenticado, mas com Plano Popular -> Exibir tela de Upgrade Paywall!
        if plan_type != 'vip':
            self.send_response(302)
            self.send_header("Location", "/vip-upgrade")
            self.send_header("Content-Length", "0")
            self.send_no_cache_headers()
            self.end_headers()
            return

        # 5. Redirecionar raiz para /vip/jogos/
        if self.path == "/":
            self.send_response(302)
            self.send_header("Location", "/vip/jogos/")
            self.send_header("Content-Length", "0")
            self.send_no_cache_headers()
            self.end_headers()
            return

        # 6. Proxy transparente para o Django (Porta 8092)
        target_url = f"http://127.0.0.1:8092{self.path}"
        try:
            req = urllib.request.Request(target_url)
            req.add_header('Host', 'statsfut.com')
            req.add_header('Accept', self.headers.get('Accept', '*/*'))
            req.add_header('User-Agent', self.headers.get('User-Agent', 'StatsFutVIP-Gatekeeper/1.0'))
            if 'Cookie' in self.headers:
                req.add_header('Cookie', self.headers.get('Cookie'))

            class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, req, fp, code, msg, headers, newurl):
                    return None
            custom_opener = urllib.request.build_opener(NoRedirectHandler)

            try:
                resp = custom_opener.open(req, timeout=35)
                status_code = resp.status
                headers_list = resp.getheaders()
                content = resp.read()
            except urllib.error.HTTPError as e:
                status_code = e.code
                headers_list = e.headers.items()
                content = e.read()

            self.send_response(status_code)
            for h, v in headers_list:
                if h.lower() not in ['transfer-encoding', 'content-length', 'connection']:
                    self.send_header(h, v)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(502)
            msg = f"VIP Gateway Error: {str(e)}".encode('utf-8')
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(msg)))
            self.send_no_cache_headers()
            self.end_headers()
            self.wfile.write(msg)

    def do_POST(self):
        # 1. Processamento de Formulário de Login
        if self.path == "/vip-login":
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            params = urllib.parse.parse_qs(body)
            user_input = params.get('username', [''])[0].strip()
            pwd_input = params.get('password', [''])[0].strip()

            authenticated = False
            user_plan = 'popular'
            authenticated_user = user_input

            # A. Verificação Master de Administrador
            if user_input == ADMIN_USER and pwd_input == ADMIN_PASS:
                authenticated = True
                user_plan = 'vip'
                authenticated_user = 'admin'
            elif DJANGO_AVAILABLE:
                # B. Autenticação via Django (suporta username ou email)
                django_user = None
                # Se digitou email, buscar o username correspondente
                if '@' in user_input:
                    try:
                        u = User.objects.filter(email__iexact=user_input).first()
                        if u:
                            django_user = authenticate(username=u.username, password=pwd_input)
                    except Exception as e:
                        print("Erro ao buscar usuário por email:", e)
                
                if not django_user:
                    django_user = authenticate(username=user_input, password=pwd_input)

                if django_user and django_user.is_active:
                    authenticated = True
                    authenticated_user = django_user.username
                    if django_user.is_superuser or django_user.is_staff:
                        user_plan = 'vip'
                    else:
                        try:
                            profile = UserProfile.objects.filter(user=django_user).first()
                            if profile and profile.is_premium:
                                user_plan = profile.plan_type  # 'vip' ou 'popular'
                            else:
                                user_plan = 'free'
                        except Exception:
                            user_plan = 'popular'

            if authenticated:
                if user_plan == 'vip':
                    session_token = generate_session_token(authenticated_user, plan_type='vip')
                    self.send_response(302)
                    self.send_header("Set-Cookie", f"{COOKIE_NAME}={session_token}; Path=/; HttpOnly; SameSite=Lax")
                    self.send_header("Location", "/vip/jogos/")
                    self.send_header("Content-Length", "0")
                    self.send_no_cache_headers()
                    self.end_headers()
                elif user_plan == 'popular':
                    # Assinante Popular tentando entrar no VIP -> Gerar sessão com role popular para cair no Upgrade Paywall
                    session_token = generate_session_token(authenticated_user, plan_type='popular')
                    self.send_response(302)
                    self.send_header("Set-Cookie", f"{COOKIE_NAME}={session_token}; Path=/; HttpOnly; SameSite=Lax")
                    self.send_header("Location", "/vip-upgrade")
                    self.send_header("Content-Length", "0")
                    self.send_no_cache_headers()
                    self.end_headers()
                else:
                    # Assinatura vencida ou gratuita
                    err = """<div class="mb-5 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold text-center">Sua assinatura não está ativa ou expirou. Renove para acessar o VIP.</div>"""
                    content = LOGIN_HTML.replace("{error_box}", err).encode('utf-8')
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(content)))
                    self.send_no_cache_headers()
                    self.end_headers()
                    self.wfile.write(content)
            else:
                err = """<div class="mb-5 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold text-center">Credenciais inválidas. Verifique seu login/email e senha.</div>"""
                content = LOGIN_HTML.replace("{error_box}", err).encode('utf-8')
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_no_cache_headers()
                self.end_headers()
                self.wfile.write(content)
            return

        # 2. Proxy POST para Django para usuários autenticados
        valid, username, plan_type = self.check_auth()
        if valid and plan_type == 'vip':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length) if length > 0 else b""
            target_url = f"http://127.0.0.1:8092{self.path}"
            try:
                req = urllib.request.Request(target_url, data=body, method='POST')
                req.add_header('Host', 'statsfut.com')
                req.add_header('Content-Type', self.headers.get('Content-Type', 'application/x-www-form-urlencoded'))
                req.add_header('Accept', self.headers.get('Accept', '*/*'))
                req.add_header('User-Agent', self.headers.get('User-Agent', 'StatsFutVIP-Gatekeeper/1.0'))
                if 'Cookie' in self.headers:
                    req.add_header('Cookie', self.headers.get('Cookie'))

                class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
                    def redirect_request(self, req, fp, code, msg, headers, newurl):
                        return None
                custom_opener = urllib.request.build_opener(NoRedirectHandler)

                try:
                    resp = custom_opener.open(req, timeout=35)
                    status_code = resp.status
                    headers_list = resp.getheaders()
                    content = resp.read()
                except urllib.error.HTTPError as e:
                    status_code = e.code
                    headers_list = e.headers.items()
                    content = e.read()

                self.send_response(status_code)
                for h, v in headers_list:
                    if h.lower() not in ['transfer-encoding', 'content-length', 'connection']:
                        self.send_header(h, v)
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception as e:
                print("Erro proxy POST:", e)

        self.send_response(403)
        self.send_header("Content-Length", "0")
        self.send_no_cache_headers()
        self.end_headers()

def run():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), VIPProxyHandler) as httpd:
        print(f"StatsFut VIP Gatekeeper v2.0 rodando na porta {PORT} com suporte a Django Auth & Paywall...")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    run()
