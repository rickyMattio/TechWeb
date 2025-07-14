from rest_framework import serializers

class WishlistActionSerializer(serializers.Serializer):
    """
    Serializer per validare l'ID dell'asta per l'azione sulla wishlist.
    """
    asta_id = serializers.IntegerField()