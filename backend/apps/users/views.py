"""
views.py — Users Module
Future University LIMS
API endpoints for user management
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User, Group
from rest_framework import serializers


class IsAdminUser(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.is_staff or request.user.groups.filter(
            name='Admin'
        ).exists()


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Group
        fields = ['id', 'name']


class UserSerializer(serializers.ModelSerializer):
    groups     = GroupSerializer(many=True, read_only=True)
    full_name  = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = [
            'id', 'username', 'first_name', 'last_name',
            'email', 'is_active', 'groups', 'full_name',
            'date_joined', 'last_login',
        ]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class CreateUserSerializer(serializers.Serializer):
    username   = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=150)
    last_name  = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email      = serializers.EmailField()
    password   = serializers.CharField(min_length=8)
    role       = serializers.ChoiceField(choices=[
        'Student', 'Lecturer', 'Researcher', 'Lab Technician', 'Admin'
    ])

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already in use.")
        return value


class UserViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    def list(self, request):
        """List all users with their groups."""
        users = User.objects.prefetch_related('groups').order_by('date_joined')
        return Response(UserSerializer(users, many=True).data)

    def retrieve(self, request, pk=None):
        """Get a single user."""
        try:
            user = User.objects.prefetch_related('groups').get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(UserSerializer(user).data)

    @action(detail=False, methods=['post'], url_path='create')
    def create_user(self, request):
        """Create a new user with a role."""
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = User.objects.create_user(
            username   = data['username'],
            email      = data['email'],
            password   = data['password'],
            first_name = data['first_name'],
            last_name  = data.get('last_name', ''),
        )

        # Assign to group
        try:
            group = Group.objects.get(name=data['role'])
            user.groups.add(group)
        except Group.DoesNotExist:
            pass

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        """Deactivate a user account."""
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        if user == request.user:
            return Response(
                {"detail": "Cannot deactivate your own account."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.is_active = False
        user.save()
        return Response({"detail": f"User {user.username} deactivated."})

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        """Reactivate a user account."""
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        user.is_active = True
        user.save()
        return Response({"detail": f"User {user.username} activated."})

    @action(detail=True, methods=['post'], url_path='change-role')
    def change_role(self, request, pk=None):
        """Change a user's role."""
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        role = request.data.get('role')
        if not role:
            return Response(
                {"detail": "role field required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            group = Group.objects.get(name=role)
        except Group.DoesNotExist:
            return Response(
                {"detail": f"Role '{role}' not found."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.groups.clear()
        user.groups.add(group)
        return Response(UserSerializer(user).data)

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Get current logged in user profile."""
        return Response(UserSerializer(request.user).data)
