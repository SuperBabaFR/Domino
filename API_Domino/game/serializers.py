from rest_framework.serializers import ModelSerializer

from authentification.models import Domino


class DominoSerializer(ModelSerializer):
    class Meta:
        model = Domino
        fields = '__all__'  # Expose tous les champs du modèle