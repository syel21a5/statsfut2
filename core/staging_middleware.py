import hashlib
from django.shortcuts import render
from django.http import HttpResponseRedirect

AUTH_USER = 'statsfut'
AUTH_PASS = 'importe*$2010MT218exVaN$'
COOKIE_NAME = 'statsfut2_staging_access'
SECRET_SALT = 'statsfut2_salt_staging_2026'

def get_auth_token():
    raw = f"{AUTH_USER}:{AUTH_PASS}:{SECRET_SALT}"
    return hashlib.sha256(raw.encode()).hexdigest()

class StagingAuthModalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]
        if 'statsfut2' not in host:
            return self.get_response(request)

        user_token = request.COOKIES.get(COOKIE_NAME)
        valid_token = get_auth_token()

        if user_token == valid_token:
            return self.get_response(request)

        error_msg = None
        if request.method == 'POST':
            u = request.POST.get('username', '').strip()
            p = request.POST.get('password', '').strip()
            if (u.lower() in [AUTH_USER.lower(), 'admin']) and p == AUTH_PASS:
                target_url = request.get_full_path()
                response = HttpResponseRedirect(target_url)
                response.set_cookie(
                    COOKIE_NAME,
                    valid_token,
                    max_age=30 * 86400,
                    path='/',
                    domain=None,
                    httponly=True,
                    samesite='Lax'
                )
                return response
            else:
                error_msg = "Usuário ou senha incorretos. Verifique suas credenciais de homologação."

        response = render(request, 'staging_lock.html', {
            'error_msg': error_msg,
            'current_path': request.get_full_path()
        }, status=401)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response
