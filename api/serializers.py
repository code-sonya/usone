from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers

from approval.models import Document
from hr.models import Employee
from .models import AppToken


# 유저 조회
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


# 유저 등록
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
        )
        return user


# 로그인
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Incorrect Credentials")


# 앱 토큰
class AppTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppToken
        fields = ('id', 'token',)
