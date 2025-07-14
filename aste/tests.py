from django.test import TestCase

from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta

# Ci serve per creare un file finto in memoria
from django.core.files.uploadedfile import SimpleUploadedFile

# Importiamo i modelli necessari per creare dati di test
from .models import Asta, Categoria, Profile

# --- Test per la Logica dei Modelli ---

class AstaModelTests(TestCase):

    def setUp(self):
        """
        Il metodo setUp viene eseguito prima di ogni test.
        Lo usiamo per creare oggetti comuni che serviranno in più test.
        """
        # Creiamo un utente venditore e una categoria di test
        self.venditore = User.objects.create_user(username='venditore_test', password='password123')
        Profile.objects.create(user=self.venditore, ruolo='venditore') # Assumendo che il Profile venga creato
        self.categoria = Categoria.objects.create(nome='Elettronica')

    def test_aggiorna_stato_se_scaduta(self):
        """
        Verifica che lo stato di un'asta cambi correttamente in 'conclusa' quando scade.
        Questo è il test della "funzione di codice applicativo".
        """
        # 1. Creiamo un'asta la cui data di fine è nel passato (ieri)
        asta_scaduta = Asta.objects.create(
            venditore=self.venditore,
            titolo="Asta Scaduta",
            descrizione="Test per asta scaduta",
            prezzo_base=10.00,
            rilancio_minimo=1.00,
            categoria=self.categoria,
            data_fine=timezone.now() - timedelta(days=1)
        )

        # Chiamiamo il metodo che vogliamo testare
        asta_scaduta.aggiorna_stato_se_scaduta()

        # Verifichiamo che lo stato sia stato aggiornato a 'conclusa'
        self.assertEqual(asta_scaduta.stato, 'conclusa')

    def test_non_aggiorna_stato_se_non_scaduta(self):
        """
        Verifica che lo stato di un'asta attiva non cambi se non è ancora scaduta.
        """
        # 1. Creiamo un'asta la cui data di fine è nel futuro (domani)
        asta_attiva = Asta.objects.create(
            venditore=self.venditore,
            titolo="Asta Attiva",
            descrizione="Test per asta attiva",
            prezzo_base=10.00,
            rilancio_minimo=1.00,
            categoria=self.categoria,
            data_fine=timezone.now() + timedelta(days=1)
        )

        # Chiamiamo il metodo
        asta_attiva.aggiorna_stato_se_scaduta()

        # Verifichiamo che lo stato sia rimasto 'attiva'
        self.assertEqual(asta_attiva.stato, 'attiva')


# --- Test per le Viste (Pagine Utente) ---

class HomeViewTests(TestCase):

    def setUp(self):
        # Oltre al venditore, creiamo anche un'asta per i test
        self.venditore = User.objects.create_user(username='venditore_test_2', password='password123')
        Profile.objects.create(user=self.venditore, ruolo='venditore')
        self.categoria = Categoria.objects.create(nome='Libri')
        # Creiamo un'immagine GIF 1x1 pixel in memoria. È il modo standard
        # per fornire un file valido a un ImageField durante i test.
        dummy_image = SimpleUploadedFile(
            name='test_image.gif',
            content=b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;',
            content_type='image/gif'
        )
        self.asta = Asta.objects.create(
            venditore=self.venditore,
            titolo="Un Titolo di Prova",
            descrizione="Descrizione di prova",
            immagine=dummy_image,  # <-- MODIFICA: Assegniamo l'immagine finta
            prezzo_base=50.00,
            rilancio_minimo=5.00,
            categoria=self.categoria,
            data_fine=timezone.now() + timedelta(days=5)
        )

    def test_home_view_status_code(self):
        """
        Verifica che la homepage risponda con un codice di stato 200 (OK).
        Questo è il test della "vista".
        """
        # Usiamo il client di test per fare una richiesta GET alla homepage
        response = self.client.get(reverse('aste:home'))
        self.assertEqual(response.status_code, 200)

    def test_home_view_uses_correct_template(self):
        """
        Verifica che la homepage usi il template corretto.
        """
        response = self.client.get(reverse('aste:home'))
        self.assertTemplateUsed(response, 'aste/home.html')
        self.assertTemplateUsed(response, 'aste/_asta_card.html')

    def test_home_view_displays_asta(self):
        """
        Verifica che la homepage mostri il titolo dell'asta che abbiamo creato.
        """
        response = self.client.get(reverse('aste:home'))
        # Controlliamo che il titolo della nostra asta sia presente nel contenuto HTML della pagina
        self.assertContains(response, "Un Titolo di Prova")

    def test_home_view_no_aste_message(self):
        """
        Verifica che, se non ci sono aste, venga mostrato il messaggio corretto.
        """
        # Cancelliamo l'asta creata nel setUp per simulare un DB vuoto
        self.asta.delete()
        response = self.client.get(reverse('aste:home'))
        self.assertContains(response, "Al momento non ci sono aste attive.")

