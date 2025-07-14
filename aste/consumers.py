import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio

class AstaConsumer(AsyncWebsocketConsumer):
    # Questo metodo viene chiamato quando un client WebSocket si connette.
    async def connect(self):
        # 1. Otteniamo l'ID dell'asta dall'URL.
        #    La chiave 'pk' deve corrispondere al nome catturato nella regex in routing.py.
        self.asta_pk = self.scope['url_route']['kwargs']['pk']
        
        # 2. Creiamo un nome univoco per il gruppo (la "stanza" di questa asta).
        self.asta_group_name = f'asta_{self.asta_pk}'
        print(f"[DEBUG] CONNECT: channel_layer id: {id(self.channel_layer)} | channel_name: {self.channel_name}")
        # 3. Aggiungiamo questo canale (la connessione del singolo client) al gruppo.
        #    Tutti i canali in questo gruppo riceveranno i messaggi inviati al gruppo.
        await self.channel_layer.group_add(
            self.asta_group_name,
            self.channel_name
        )

        # 4. Accettiamo la connessione WebSocket. Se non lo facciamo, verrà rifiutata.
        await self.accept()

    # Questo metodo viene chiamato quando il client si disconnette.
    async def disconnect(self, close_code):
        # Rimuoviamo il canale dal gruppo per non inviargli più messaggi.
        await self.channel_layer.group_discard(
            self.asta_group_name,
            self.channel_name
        )
        
    async def receive(self, text_data):
        print("[DEBUG] receive chiamato con:", text_data)
        
    async def websocket_receive(self, event):
        print("[DEBUG] websocket_receive", event)



    # Questo è un metodo "ricevitore di eventi". Viene chiamato automaticamente da Channels
    # quando la nostra vista Django invia un messaggio al gruppo con 'type': 'offerta.aggiornata'.
    async def offerta_aggiornata(self, event):
        await asyncio.sleep(0.05)
        # Spiegazione: Per essere robusti, controlliamo se i dati sono direttamente
        # nell'evento o in una sotto-chiave.
        # Il backend InMemory a volte passa i dati direttamente.
        dati = event.get('dati_offerta') or {
            "nuovo_prezzo": event.get("nuovo_prezzo"),
            "acquirente": event.get("acquirente")
        }

        # Invia i dati al client JavaScript
        await self.send(text_data=json.dumps(dati))