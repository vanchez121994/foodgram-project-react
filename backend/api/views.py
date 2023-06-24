from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import (
    Ingredient, Recipe, Tag, RecipeIngredients
)
from users.models import Subscription
from .filters import CustomIngredientFilter, CustomRecipeFilter
from .paginators import CustomPageNumberPagination
from .permissions import OwnerOrReadOnly
from .serializers import (
    IngredientSerializer, RecipeSerializer, RecipeShortSerializer,
    TagSerializer, SubscriptionSerializer,
    SubscriptionCreateSerializer, FavoriteRecipeSerializer,
    ShopCartSerializer, RecipeCreateSerializer)


User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CustomIngredientFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = (OwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CustomRecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add_or_delete(self, serializer_cls, pk):
        if self.request.method == 'POST':
            serializer_obj = serializer_cls(
                data={'recipe': pk},
                context={'request': self.request}
            )
            serializer_obj.is_valid(raise_exception=True)
            cart = serializer_obj.save()

            serializer = RecipeShortSerializer(cart.recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if self.request.method == 'DELETE':
            serializer_cls.Meta.model.objects.filter(
                recipe=pk, user=self.request.user
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({
            'errors': 'Некорректный запрос'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=('post', 'delete'),
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk=None):
        return self.add_or_delete(FavoriteRecipeSerializer, pk)

    @action(detail=True, methods=('post', 'delete'),
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        return self.add_or_delete(ShopCartSerializer, pk)

    @action(detail=False, methods=('get',),
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        full_shopping_cart = RecipeIngredients.objects.filter(
            recipe__in_shopping_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            count=Count('ingredient__name')
        ).order_by(
            'ingredient'
        ).annotate(
            amount=Sum('amount')
        )

        result = 'Список покупок: \n' + '\n'.join([
            (f'{i["ingredient__name"]} '
             f'({i["ingredient__measurement_unit"]}) - '
             f'{i["amount"]}')
            for i in full_shopping_cart
        ])

        response = HttpResponse(result, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="ingredients_to_buy.txt"'
        )
        return response


class CustomUserViewSet(UserViewSet):
    pagination_class = CustomPageNumberPagination

    @action(detail=False, methods=('get',),
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        paginated_queryset = self.paginate_queryset(
            User.objects.filter(subscribers__subscriber=request.user)
        )
        serializer = SubscriptionSerializer(
            paginated_queryset,
            many=True, context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=('post', 'delete'),
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, pk=id)

        if self.request.method == 'POST':
            sub_serializer = SubscriptionCreateSerializer(
                data={'author': id},
                context={'request': request}
            )
            sub_serializer.is_valid(raise_exception=True)
            sub_serializer.save()

            serializer = SubscriptionSerializer(
                author,
                context={'request': request},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == 'DELETE':
            subscription = get_object_or_404(
                Subscription,
                author=author,
                subscriber=request.user
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({
            'errors': 'Некорректный запрос'
        }, status=status.HTTP_400_BAD_REQUEST)
