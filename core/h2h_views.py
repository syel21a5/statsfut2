from django.shortcuts import render
from matches.views import HeadToHeadView

def h2h_novo_view(request, country_name, league_name, team1_name, team2_name):
    """
    View que herda 100% dos dados consolidados de HeadToHeadView
    e entrega para o template novo e moderno h2h_novo.html
    sem repetições, no estilo dark com blocos de monetização / VIP.
    """
    view_instance = HeadToHeadView()
    view_instance.setup(request, country_name=country_name, league_name=league_name, team1_name=team1_name, team2_name=team2_name)
    
    kwargs = {
        'country_name': country_name,
        'league_name': league_name,
        'team1_name': team1_name,
        'team2_name': team2_name,
    }
    context = view_instance.get_context_data(**kwargs)
    return render(request, 'h2h_novo.html', context)
