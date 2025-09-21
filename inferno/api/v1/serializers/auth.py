"""
Authentication serializers
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from userauths.models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer with additional user data
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add extra user data to the response
        data.update({
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'is_staff': self.user.is_staff,
            }
        })
        
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        
        return token


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    User registration serializer
    """
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number'
        )
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        """
        Validate password confirmation
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                _("Password and password confirmation do not match.")
            )
        return attrs

    def validate_email(self, value):
        """
        Validate email is unique
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                _("A user with this email already exists.")
            )
        return value

    def validate_username(self, value):
        """
        Validate username is unique
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                _("A user with this username already exists.")
            )
        return value

    def create(self, validated_data):
        """
        Create new user
        """
        # Remove password_confirm from validated_data
        validated_data.pop('password_confirm', None)
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    User profile serializer for viewing/updating profile
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 
            'full_name', 'phone_number', 'bio', 'date_joined'
        )
        read_only_fields = ('id', 'username', 'date_joined')

    def get_full_name(self, obj):
        """
        Get user's full name
        """
        return f"{obj.first_name} {obj.last_name}".strip()


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        """
        Validate password change
        """
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                _("New password and confirmation do not match.")
            )
        return attrs

    def validate_old_password(self, value):
        """
        Validate old password
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Old password is incorrect."))
        return value


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for password reset request
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """
        Validate email exists
        """
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                _("No user found with this email address.")
            )
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation
    """
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        """
        Validate password reset
        """
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                _("Password and confirmation do not match.")
            )
        return attrs