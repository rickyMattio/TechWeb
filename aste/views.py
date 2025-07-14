from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import *
from .models import * 
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .forms import * # Importa il nostro nuovo form
from django.contrib.auth.mixins import *
from django.http import JsonResponse # Per inviare risposte in formato JSON
import json # Per decodificare i dati in arrivo
from django.db.models import * # Per trovare facilmente l'offerta massima
from django.contrib.auth.decorators import login_required # Importa il decoratore
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import Coalesce



class HomeAsteView(ListView):
    # Spiegazione: Stiamo creando una vista basata sulla generica ListView.

    # 1. Specifichiamo quale modello deve essere interrogato.
    #    Django eseguirà `Asta.objects.all()` per noi.
    model = Asta

    # 2. Specifichiamo quale template usare per mostrare i dati.
    template_name = 'aste/home.html'

    # 3. Di default, ListView passa la lista di oggetti al template
    #    in una variabile chiamata `object_list`. Le diamo un nome più chiaro.
    context_object_name = 'aste_list'

    def get_queryset(self):
        # Spiegazione: Stiamo sovrascrivendo il metodo `get_queryset`.
        # Invece di prendere TUTTE le aste (`Asta.objects.all()`),
        # prendiamo solo quelle 'attive' e le ordiniamo per data di fine.
        # Ora anche la homepage calcola il prezzo_attuale per ogni asta,
        # usando il prezzo base come default se non ci sono offerte.
        # Usiamo Coalesce per gestire il caso in cui non ci siano offerte, usando il prezzo_base.
        
        aste_con_prezzo = Asta.objects.filter(stato='attiva').annotate(
            prezzo_attuale=Coalesce(Max('offerte__importo'), F('prezzo_base'))
        )
        # Usiamo Prefetch per caricare in modo efficiente l'offerta più alta per ogni asta.
        #    Questo farà una sola query aggiuntiva per tutte le offerte, invece di una per asta.
        offerte_prefetch = Prefetch(
            'offerte', # Nome del related_name nel modello Asta
            queryset=Offerta.objects.select_related('acquirente').order_by('-importo'),
            to_attr='offerte_ordinate' # Salviamo il risultato in un nuovo attributo sull'oggetto asta
        )
        
        return aste_con_prezzo.prefetch_related(offerte_prefetch).order_by('data_fine').distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            aste_vincenti_utente = set()
            for asta in context['aste_list']:
                # `asta.offerte_ordinate` esiste grazie al to_attr nel Prefetch.
                # Questa operazione NON fa una nuova query al database.
                if hasattr(asta, 'offerte_ordinate') and asta.offerte_ordinate:
                    offerta_top = asta.offerte_ordinate[0]
                    if offerta_top.acquirente == self.request.user:
                        aste_vincenti_utente.add(asta.pk)
            context['aste_vincenti_utente'] = aste_vincenti_utente
        return context
    

class DettaglioAstaView(DetailView):
    # Spiegazione: Questa vista è basata sulla generica DetailView.
    
    # 1. Specifichiamo il modello da cui pescare il singolo oggetto.
    model = Asta
    
    # 2. Specifichiamo il template da usare per mostrare i dettagli.
    template_name = 'aste/dettaglio_asta.html'
    
    # 3. Di default, DetailView passa l'oggetto al template in una variabile
    #    chiamata `object`. Le diamo un nome più chiaro e intuitivo.
    context_object_name = 'asta'
    
    def get_object(self, queryset=None):
        # Spiegazione: Sovrascriviamo get_object, il metodo che recupera
        # il singolo oggetto Asta dal database.
        asta = super().get_object(queryset)
        asta.aggiorna_stato_se_scaduta() # Chiamiamo il nostro metodo di aggiornamento!
        return asta

    def get_context_data(self, **kwargs):
        # Spiegazione: Stiamo sovrascrivendo questo metodo per aggiungere
        # più informazioni (il "contesto") da passare al template.
        # Oltre ai dettagli dell'asta, vogliamo anche mostrare la sua offerta più alta.

        # Chiamiamo prima l'implementazione base per ottenere il contesto di default
        context = super().get_context_data(**kwargs)
        asta = self.get_object()
        # Recuperiamo l'offerta più alta per l'asta corrente.
        # `self.get_object()` ci dà l'istanza dell'asta che la vista sta mostrando.
        # Usiamo `first()` perché abbiamo ordinato le offerte in modo decrescente nel modello.
        offerta_piu_alta = self.get_object().offerte.first()
        
        # Aggiungiamo l'offerta al contesto che passeremo al template.
        context['offerta_piu_alta'] = offerta_piu_alta
        if self.request.user.is_authenticated and offerta_piu_alta and offerta_piu_alta.acquirente == self.request.user:
            context['utente_sta_vincendo'] = True
        return context
    
class RegistrazioneView(CreateView):
    # Spiegazione: Usiamo una CreateView generica, ma la personalizziamo
    # per usare il nostro form invece di farne generare uno a Django.
    
    # 1. Invece di 'model', specifichiamo 'form_class'.
    #    Questo dice alla CreateView di usare il nostro CustomUserCreationForm.
    form_class = CustomUserCreationForm
    
    # 2. Specifichiamo il template che mostrerà il form.
    template_name = 'registration/registrazione.html'
    
    # 3. Specifichiamo l'URL a cui reindirizzare l'utente dopo una registrazione
    #    riuscita. `reverse_lazy` cerca un URL con il nome 'login'.
    success_url = reverse_lazy('aste:registrazione_completata')
    
class RegistrazioneConfermaView(TemplateView):
    template_name = 'registration/registrazione_completata.html'
    
class ProfiloView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/profilo.html'

    def get_context_data(self, **kwargs):
        # Spiegazione: Sovrascriviamo get_context_data per popolare il contesto
        # con tutte le informazioni necessarie per il pannello personale.
        context = super().get_context_data(**kwargs)
        
        # Recuperiamo l'utente corrente, non c'è bisogno di passarlo, è già nel contesto.
        user = self.request.user
        
        # Aggiungiamo un titolo dinamico
        context['title'] = f"Pannello di {user.username}"

        # Logica specifica per il ruolo VENDITORE
        if user.profile.ruolo == 'venditore':
            context['aste_create'] = Asta.objects.filter(venditore=user).order_by('-data_inizio')

        # Logica specifica per il ruolo ACQUIRENTE
        if user.profile.ruolo == 'acquirente':
            desideri = user.lista_desideri.all()
            desideri_ids = list(desideri.values_list('id', flat=True))
            context['offerte_fatte'] = Offerta.objects.filter(acquirente=user).order_by('-data_offerta')
            context['lista_desideri'] = user.lista_desideri.all()
            context['aste_vinte'] = Asta.objects.get_aste_vinte(user)
            # Raccomandazioni semplificate: per ogni asta nei desideri, suggeriamo 3 aste concluse
            # della stessa categoria, vinte da altri utenti
            aste_vinte_ids = context['aste_vinte'].values_list('id', flat=True)
            raccomandazioni = {}
            for asta in desideri:
                altre = Asta.objects.filter(
                    categoria=asta.categoria,
                    stato='conclusa',
                    offerte__isnull=False
                ).exclude(
                    pk=asta.pk
                ).exclude(
                    pk__in=aste_vinte_ids
                ).exclude(
                    pk__in=desideri_ids
                ).distinct()[:3]
                raccomandazioni[asta.pk] = altre
            context['lista_desideri_con_raccomandazioni'] = [
                (asta, raccomandazioni[asta.pk]) for asta in desideri
            ]

        return context
    
class VenditoreRequiredMixin(AccessMixin):
    
    # Spiegazione: Questo Mixin personalizzato verifica che l'utente sia loggato
    # E che il suo profilo abbia il ruolo 'venditore'.
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        try:
            if request.user.profile.ruolo != 'venditore':
                # Se l'utente è loggato ma non è un venditore, solleviamo un'eccezione
                # che può essere gestita mostrando un errore 403 (Forbidden).
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("Non hai i permessi per accedere a questa pagina.")
        except Profile.DoesNotExist:
             # Se l'utente non ha un profilo (caso anomalo), neghiamo l'accesso.
             return self.handle_no_permission()
        
        return super().dispatch(request, *args, **kwargs)



class CreaAstaView(VenditoreRequiredMixin, CreateView):
    model = Asta
    
    # SOSTITUISCI la riga 'fields' con questa:
    form_class = AstaForm # Usa il nostro form personalizzato
    
    template_name = 'aste/crea_asta.html'
    
    # MODIFICHIAMO il success_url per reindirizzare alla pagina di dettaglio dell'asta appena creata
    # Non possiamo usare reverse_lazy qui perché abbiamo bisogno dell'ID dell'oggetto.
    # Quindi sovrascriviamo il metodo get_success_url.
    def get_success_url(self):
        # `self.object` è l'istanza dell'asta appena salvata, resa disponibile dalla CreateView.
        return reverse_lazy('aste:dettaglio_asta', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        # ... Questo metodo rimane uguale ...
        form.instance.venditore = self.request.user
        
        # MA AGGIUNGIAMO IL MESSAGGIO DI CONFERMA QUI!
        messages.success(self.request, "La tua asta è stata creata con successo!")
        
        return super().form_valid(form)
    



@login_required # 1. Proteggiamo la vista: solo utenti loggati
def fai_offerta(request, pk):
    # Spiegazione: Questa vista gestisce la logica per piazzare una nuova offerta.
    
    # 2. Controlliamo che la richiesta sia di tipo POST
    if request.method == 'POST':
        
            
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Metodo non consentito.'}, status=405)
        
        asta = Asta.objects.get(pk=pk)
        
        # 3. Controlliamo che solo gli acquirenti possano fare offerte
        if request.user.profile.ruolo != 'acquirente':
            return JsonResponse({'success': False, 'error': 'Solo gli acquirenti possono fare offerte.'}, status=403)

        if asta.stato != 'attiva':
            return JsonResponse({'success': False, 'error': 'Questa asta è conclusa.'}, status=400)
            
        try:    
            # 4. Validazione logica
            # Prendiamo l'offerta più alta esistente o il prezzo base se non ci sono offerte
            offerta_corrente = asta.offerte.aggregate(Max('importo'))['importo__max'] or asta.prezzo_base
            
            # Leggiamo l'importo inviato dal client via AJAX
            data = json.loads(request.body)
            importo_offerta = float(data.get('importo'))

            if importo_offerta < (offerta_corrente + asta.rilancio_minimo):
                return JsonResponse({'success': False, 'error': 'La tua offerta non rispetta il rilancio minimo.'}, status=400)

            # 5. Se tutto è valido, creiamo e salviamo la nuova offerta
            nuova_offerta = Offerta.objects.create(
                asta=asta,
                acquirente=request.user,
                importo=importo_offerta
            )

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'asta_{asta.id}',
                {
                    'type': 'offerta_aggiornata',
                    'dati_offerta': {
                        'nuovo_prezzo': f"{nuova_offerta.importo:.2f}",
                        'acquirente': nuova_offerta.acquirente.username,
                    }
                }
            )

            print("[DEBUG] VIEW sending to group:", f"asta_{asta.id}")

            
            # 6. Restituiamo una risposta JSON di successo con i nuovi dati
            return JsonResponse({
                'success': True,
                'nuovo_prezzo': f"{nuova_offerta.importo:.2f}",
                'acquirente': nuova_offerta.acquirente.username
            })

        except Asta.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Asta non trovata.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    # Se la richiesta non è POST, restituiamo un errore
    return JsonResponse({'success': False, 'error': 'Metodo non consentito.'}, status=405)

@login_required
def gestisci_lista_desideri(request, pk):
    # Spiegazione: Questa vista gestisce l'aggiunta/rimozione di un'asta
    # dalla lista dei desideri dell'utente corrente.
    
    # Ci aspettiamo solo richieste POST per questa azione.
    if request.method == 'POST':
        try:
            asta = Asta.objects.get(pk=pk)
            user = request.user
            
            # Controlliamo se l'asta è già nella lista dei desideri dell'utente.
            if asta in user.lista_desideri.all():
                # Se c'è, la rimuoviamo.
                user.lista_desideri.remove(asta)
                added = False # Flag per comunicare al client che abbiamo rimosso l'asta.
            else:
                # Se non c'è, la aggiungiamo.
                user.lista_desideri.add(asta)
                added = True # Flag per comunicare al client che abbiamo aggiunto l'asta.

            # Restituiamo una risposta JSON di successo.
            return JsonResponse({'success': True, 'added': added})

        except Asta.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Asta non trovata.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Metodo non consentito.'}, status=405)



@login_required
def aggiungi_feedback(request, pk):
    # Recuperiamo l'asta per cui si vuole lasciare il feedback.
    asta = get_object_or_404(Asta, pk=pk)
    vincitore = asta.offerte.first().acquirente if asta.offerte.exists() else None

    # --- Logica dei Permessi ---
    # Solo il vincitore può lasciare un feedback, e solo se l'asta è conclusa.
    if asta.stato != 'conclusa' or request.user != vincitore:
        messages.error(request, "Non puoi lasciare un feedback per questa asta.")
        return redirect('aste:dettaglio_asta', pk=asta.pk)
    
    # Controlliamo se l'utente ha già lasciato un feedback per questa asta
    if Feedback.objects.filter(asta=asta, autore=request.user).exists():
        messages.warning(request, "Hai già lasciato un feedback per questa asta.")
        return redirect('aste:dettaglio_asta', pk=asta.pk)

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.asta = asta
            feedback.autore = request.user
            feedback.destinatario = asta.venditore # Il feedback è per il venditore
            feedback.save()
            messages.success(request, "Il tuo feedback è stato salvato con successo.")
            return redirect('aste:dettaglio_asta', pk=asta.pk)
    else:
        form = FeedbackForm()

    context = {
        'form': form,
        'asta': asta
    }
    return render(request, 'aste/aggiungi_feedback.html', context)


class RisultatiRicercaView(ListView):
    model = Asta
    template_name = 'aste/risultati_ricerca.html'
    context_object_name = 'aste_list'
    paginate_by = 10 # Mostriamo 10 risultati per pagina

    def get_queryset(self):
       
        offerte_prefetch = Prefetch(
            'offerte',
            queryset=Offerta.objects.select_related('acquirente').order_by('-importo')
        )
        # Spiegazione: Questo è il cuore della ricerca.
        # Iniziamo con un queryset di tutte le aste.
        queryset = Asta.objects.annotate(
            prezzo_attuale=Coalesce(
                Max('offerte__importo'), 
                F('prezzo_base'), 
                0.0, 
                output_field=DecimalField()
            ),
            reputazione_venditore=Avg('venditore__feedback_ricevuti__voto')
        ).prefetch_related(offerte_prefetch)
        # Recuperiamo i dati dal form passato come parametri GET.
        form = SearchForm(self.request.GET)
        
        # Controlliamo che i dati siano validi (anche se non sono "required")
        if form.is_valid():
            keyword = form.cleaned_data.get('keyword')
            categoria = form.cleaned_data.get('categoria')
            prezzo_min = form.cleaned_data.get('prezzo_min')
            prezzo_max = form.cleaned_data.get('prezzo_max')
            durata = form.cleaned_data.get('durata')
            includi_concluse = form.cleaned_data.get('includi_concluse')
            ordina_per = form.cleaned_data.get('ordina_per')

            if not includi_concluse:
                # Filtro di base: mostra solo le aste attive.
                queryset = queryset.filter(stato='attiva')
            if keyword:
                # Filtro per parola chiave su titolo.
                queryset = queryset.filter(titolo__icontains=keyword)
            if categoria:
                queryset = queryset.filter(categoria=categoria)
                
            # Applichiamo il filtro del prezzo minimo se è stato fornito.
            # Rimuoviamo il controllo "> 0" per permettere filtri che iniziano da zero.
            if prezzo_min is not None:
                queryset = queryset.filter(prezzo_attuale__gte=prezzo_min)

            # Il filtro del prezzo massimo è già corretto, ma lo manteniamo per coerenza.
            if prezzo_max is not None:
                queryset = queryset.filter(prezzo_attuale__lte=prezzo_max)

            if durata:
                # Calcola la data futura e filtra le aste che scadono prima di quella data
                data_limite = timezone.now() + timedelta(days=int(durata))
                queryset = queryset.filter(data_fine__lte=data_limite)
            
            if ordina_per:
                if ordina_per == 'reputazione':
                    queryset = queryset.order_by('-reputazione_venditore', 'data_fine')
                else:
                    queryset = queryset.order_by(ordina_per)
            else:
                queryset = queryset.order_by('data_fine')
        return queryset.distinct()   
    
    
    def get_context_data(self, **kwargs):
        # Passiamo il form al contesto per poter mostrare i filtri applicati.
        context = super().get_context_data(**kwargs)
        context['form'] = SearchForm(self.request.GET or None)
        
        # Calcoliamo il prezzo massimo tra tutte le aste
        max_price_agg = Asta.objects.annotate(
            prezzo_attuale=Case(
                When(offerte__importo__isnull=False, then=Max('offerte__importo')),
                default=F('prezzo_base'),
                output_field=DecimalField()
            )
        ).aggregate(max_val=Max('prezzo_attuale'))
        
        max_price = 1000  # Valore di default se non ci sono aste
        if max_price_agg['max_val'] is not None:
            max_price = int(max_price_agg['max_val'])
            
        context['max_prezzo_asta'] = max_price
        
        if self.request.user.is_authenticated:
            # Creiamo un 'set' (un tipo di lista molto veloce per le ricerche) 
            # contenente gli ID di tutte le aste nella pagina corrente che l'utente sta vincendo.
            aste_vincenti = set(
                asta.pk for asta in context['aste_list'] 
                if asta.offerte.first() and asta.offerte.first().acquirente == self.request.user
            )
            context['aste_vincenti_utente'] = aste_vincenti
        else:
            # Se l'utente non è loggato, passiamo una lista vuota per sicurezza
            context['aste_vincenti_utente'] = set()
        return context
    

class ProfiloVenditoreView(View):
    def get(self, request, user_id):
        venditore = get_object_or_404(User, id=user_id)
        feedback_list = Feedback.objects.filter(destinatario=venditore).order_by('-data_creazione')
        media_voto = feedback_list.aggregate(Avg('voto'))['voto__avg']
        return render(request, 'aste/profilo_venditore.html', {
            'venditore': venditore,
            'feedback_list': feedback_list,
            'media_voto': media_voto,
        })
        
        
        
class VenditoreAstaOwnerMixin(UserPassesTestMixin):
    """
    Questo Mixin verifica che l'utente loggato sia il venditore dell'asta
    e che l'asta non abbia ancora ricevuto offerte.
    """
    def test_func(self):
        # self.get_object() è un metodo delle viste di dettaglio (Detail, Update, Delete)
        # che recupera l'oggetto Asta corrente.
        asta = self.get_object()
        return self.request.user == asta.venditore and asta.offerte.count() == 0

    def handle_no_permission(self):
        # Se test_func ritorna False, l'utente viene reindirizzato con un messaggio di errore.
        messages.error(self.request, "Azione non consentita: puoi modificare solo le tue aste che non hanno ancora ricevuto offerte.")
        return redirect('aste:home')
    
class ModificaAstaView(VenditoreAstaOwnerMixin, UpdateView):
    model = Asta
    form_class = AstaForm
    template_name = 'aste/crea_asta.html' # Riusiamo il template di creazione!
    context_object_name = 'asta'

    def get_success_url(self):
        messages.success(self.request, "La tua asta è stata modificata con successo.")
        # Reindirizza alla pagina di dettaglio dell'asta appena modificata.
        return reverse_lazy('aste:dettaglio_asta', kwargs={'pk': self.object.pk})

class EliminaAstaView(VenditoreAstaOwnerMixin, DeleteView):
    model = Asta
    template_name = 'aste/asta_confirm_delete.html'
    
    # Dopo l'eliminazione, reindirizza al profilo del venditore.
    success_url = reverse_lazy('aste:profilo')

    def form_valid(self, form):
        messages.success(self.request, f"L'asta '{self.object.titolo}' è stata eliminata.")
        return super().form_valid(form)
    
    
class NotificheView(LoginRequiredMixin, ListView):
    """
    Mostra l'elenco delle notifiche per l'utente loggato
    e le segna come lette.
    """
    model = Notifica
    template_name = 'aste/notifiche.html'
    context_object_name = 'notifiche_list'
    paginate_by = 15 # Mostriamo 15 notifiche per pagina

    def get_queryset(self):
        # Filtriamo le notifiche per ottenere solo quelle dell'utente corrente
        queryset = Notifica.objects.filter(utente_destinatario=self.request.user)

        # --- AZIONE CHIAVE: Segniamo le notifiche come lette ---
        # Prendiamo solo quelle non lette e le aggiorniamo nel database
        # con un'unica, efficiente query.
        queryset.filter(letta=False).update(letta=True)

        # Restituiamo l'intero queryset (lette e non) da mostrare
        return queryset