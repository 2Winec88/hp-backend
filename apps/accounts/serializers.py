from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

from .models import Role


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "name", "code", "description")


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    roles = RoleSerializer(many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "avatar",
            "bio",
            "roles",
        )
        read_only_fields = ("id", "full_name", "roles", "date_joined")

        def get_organization(self, obj):
            return obj.organization.name

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            'first_name', 'last_name', 'avatar', 'bio'
        )


class UserChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        validators=[validate_password],
    )
    new_password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "New passwords do not match."}
            )
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user    
    
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = get_user_model()
        fields = ("username", "email", "password", "password_confirm","first_name","last_name")

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password")
        user = self.Meta.model(**validated_data)
        user.set_password(password)
        user.is_active = False
        user.is_email_verified = False
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    """Сериализатор для входа пользователя"""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user_model = get_user_model()

        try:
            user = user_model.objects.get(email=email)
        except user_model.DoesNotExist:
            user = None

        if not user or not user.check_password(password):
            raise serializers.ValidationError(
                "Invalid email or password."
            )

        if not user.is_email_verified:
            raise serializers.ValidationError(
                "Email address is not verified."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "User account is disabled."
            )

        authenticated_user = authenticate(username=email, password=password)
        if not authenticated_user:
            raise serializers.ValidationError(
                "Invalid email or password."
            )

        attrs["user"] = authenticated_user
        return attrs
