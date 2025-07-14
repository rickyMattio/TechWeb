from .models import Notifica

def notifiche_non_lette(request):
    if request.user.is_authenticated:
        # Conta le notifiche dell'utente loggato che non sono state ancora lette
        count = Notifica.objects.filter(utente_destinatario=request.user, letta=False).count()
        return {'notifiche_non_lette_count': count}
    return {'notifiche_non_lette_count': 0}