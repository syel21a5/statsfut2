import json
from datetime import timedelta
from zoneinfo import ZoneInfo
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from matches.models import Match, League
from matches.utils import get_flag_code

def cornerpro_home_view(request):
    """
    Página independente de testes no estilo CornerPro Analysis
    Não interfere com nenhuma view ou template existente do StatsFut
    """
    br_tz = ZoneInfo('America/Sao_Paulo')
    now_br = timezone.now().astimezone(br_tz)
    start_of_day = now_br.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Filtro de data / status
    status_filter = request.GET.get('status', 'all')
    date_filter = request.GET.get('date', 'today')
    
    if date_filter == 'yesterday':
        query_start = start_of_day - timedelta(days=1)
        query_end = start_of_day
        display_date = (now_br - timedelta(days=1)).strftime('%d/%m')
        day_label = (now_br - timedelta(days=1)).strftime('%a %d').upper()
    elif date_filter == 'tomorrow':
        query_start = start_of_day + timedelta(days=1)
        query_end = query_start + timedelta(days=1)
        display_date = (now_br + timedelta(days=1)).strftime('%d/%m')
        day_label = (now_br + timedelta(days=1)).strftime('%a %d').upper()
    else: # today
        query_start = start_of_day
        query_end = start_of_day + timedelta(days=1)
        display_date = now_br.strftime('%d/%m')
        day_label = now_br.strftime('%a %d').upper()
        
    live_statuses = ['Live', 'LIVE', '1H', '2H', 'HT', 'IN_PLAY', 'In Play']
    finished_statuses = ['Finished', 'FT', 'AET', 'PEN', 'FINISHED', 'Postponed', 'PST', 'AWD', 'CANC']
    
    day_matches = Match.objects.filter(date__range=(query_start, query_end)).select_related('league', 'home_team', 'away_team')
    
    # Contagens
    total_count = day_matches.count()
    live_count = day_matches.filter(status__in=live_statuses).count()
    scheduled_count = day_matches.filter(status='Scheduled').count()
    finished_count = day_matches.filter(status__in=finished_statuses).count()
    
    if status_filter == 'live':
        filtered_matches = day_matches.filter(status__in=live_statuses)
    elif status_filter == 'scheduled':
        filtered_matches = day_matches.filter(status='Scheduled')
    elif status_filter == 'finished':
        filtered_matches = day_matches.filter(status__in=finished_statuses)
    else:
        filtered_matches = day_matches
        
    # Agrupamento por País e Liga
    grouped = {}
    for m in filtered_matches.order_by('league__country', 'league__name', 'date'):
        # Cálculo de estatísticas rápidas
        def get_quick_stat(team):
            last = Match.objects.filter(Q(home_team=team)|Q(away_team=team), status__in=['Finished', 'FT']).order_by('-date')[:10]
            t = len(last)
            if t == 0:
                return {'btts': 0, 'over15': 0, 'over25': 0, 'under35': 0}
            btts = sum(1 for match in last if (match.home_score or 0) > 0 and (match.away_score or 0) > 0)
            o15 = sum(1 for match in last if (match.home_score or 0) + (match.away_score or 0) > 1)
            o25 = sum(1 for match in last if (match.home_score or 0) + (match.away_score or 0) > 2)
            u35 = sum(1 for match in last if (match.home_score or 0) + (match.away_score or 0) < 4)
            return {
                'btts': int((btts / t) * 100),
                'over15': int((o15 / t) * 100),
                'over25': int((o25 / t) * 100),
                'under35': int((u35 / t) * 100),
            }
            
        m.home_stats = get_quick_stat(m.home_team)
        m.away_stats = get_quick_stat(m.away_team)
        
        country = m.league.country
        league_name = m.league.name
        if country not in grouped:
            grouped[country] = {}
        if league_name not in grouped[country]:
            grouped[country][league_name] = []
        grouped[country][league_name].append(m)
        
    grouped_list = []
    sorted_countries = sorted(grouped.keys(), key=lambda x: (x != 'Brasil', x))
    for c in sorted_countries:
        leagues = []
        for l_name, l_matches in grouped[c].items():
            leagues.append({
                'name': l_name,
                'matches': l_matches,
                'league_obj': l_matches[0].league
            })
        leagues.sort(key=lambda x: x['name'])
        grouped_list.append({
            'country': c,
            'flag_code': get_flag_code(c),
            'leagues': leagues
        })
        
    context = {
        'grouped_matches': grouped_list,
        'status_counts': {
            'total': total_count,
            'live': live_count,
            'scheduled': scheduled_count,
            'finished': finished_count,
        },
        'status_filter': status_filter,
        'date_filter': date_filter,
        'day_label': day_label,
        'display_date': display_date,
    }
    return render(request, 'cornerpro_home.html', context)
