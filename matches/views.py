
from django.shortcuts import render

# View para a página do CornerPro
def cornerpro_league_stats(request, country_name, league_name):
    # Lógica para obter os dados da liga
    league_data = {
        'league': {
            'name': league_name,
            'country': country_name,
        },
        'standings': [
            {'team': {'name': 'Ind. Rivadavia', 'logo_url': 'https://example.com/rivadavia.png'}, 'points': 48},
            # Adicione mais dados conforme necessário
        ],
        'season_best_attack': {
            'team': {'name': 'Ind. Rivadavia', 'logo_url': 'https://example.com/rivadavia.png'}, 'goals_for': 42,
        },
        'season_best_defense': {
            'team': {'name': 'Estudiantes L.P.', 'logo_url': 'https://example.com/estudiantes.png'}, 'goals_against': 16,
        },
        'common_scores': [
            {'score': '1-0', 'pct': 15.5},
        ],
        'league_stats': {
            'avg_goals_match': 1.98,
            'over15_pct': 59.4,
            'over25_pct': 31.9,
            'btts_pct': 40.6,
        },
        'avg_cs': 59.2,
        'avg_ppg': 1.35,
    }
    return render(request, 'matches/cornerpro_league.html', league_data)

# View para a página inicial do CornerPro
def cornerpro_home(request):
    return render(request, 'matches/cornerpro_home.html')
