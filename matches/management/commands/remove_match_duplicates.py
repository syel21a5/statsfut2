from django.core.management.base import BaseCommand
from django.db.models import Count
from matches.models import Match

class Command(BaseCommand):
    help = "Remove jogos duplicados (mesma data, mandante e visitante)"

    def handle(self, *args, **options):
        # Encontra duplicatas
        duplicates = (
            Match.objects.values('home_team', 'away_team', 'date')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )

        total_deleted = 0
        
        self.stdout.write(f"Encontrados {duplicates.count()} grupos de jogos duplicados.")

        for item in duplicates:
            matches = Match.objects.filter(
                home_team=item['home_team'],
                away_team=item['away_team'],
                date=item['date']
            ).order_by('-id') # Mantém o mais recente (maior ID) ou o mais antigo? 
            # Geralmente o mais recente tem dados mais novos, mas se for importação duplicada tanto faz.
            # Se um tiver api_id e o outro não, prefira o que tem.
            
            matches_to_keep = []
            matches_to_delete = []

            # Separa o melhor candidato para manter
            # Critério: tem api_id > tem placar > mais recente
            
            sorted_matches = sorted(matches, key=lambda m: (
                1 if m.api_id else 0,
                1 if m.status == 'Finished' else 0,
                m.id
            ), reverse=True)
            
            keep = sorted_matches[0]
            delete_list = sorted_matches[1:]
            
            for m in delete_list:
                m.delete()
                total_deleted += 1
                
        self.stdout.write(self.style.SUCCESS(f"Removidos {total_deleted} jogos duplicados."))
