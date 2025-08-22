from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        print("\n--- Serializer.validate called ---")
        print("Incoming attrs:", attrs)

        username = attrs.get("username")
        password = attrs.get("password")
        print("Using -> username:", username, "| password:", password)

        user = authenticate(username=username, password=password)
        print("authenticate() result:", user)

        if not user:
            print("❌ Authentication failed inside serializer")
        else:
            print("✅ Authentication success inside serializer:", user)

        data = super().validate(attrs)
        print("super().validate returned:", data)
        print("--- Serializer.validate END ---\n")
        return data
