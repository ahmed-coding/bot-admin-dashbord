from rest_framework import serializers
from .. import models



class SettingsSerializers(serializers.ModelSerializer):
    # is_open = serializers.ReadOnlyField()
    class Meta:
        model= models.BotSettings
        fields= ('key','value','for_spot','for_futuer')


