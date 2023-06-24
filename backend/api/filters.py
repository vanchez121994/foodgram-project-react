from django.contrib.auth import get_user_model
from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag

User = get_user_model()
CHOICES_LIST = (
    (0, 0),
    (1, 1)
)


class CustomRecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.ChoiceFilter(
        label='is_favorited',
        choices=CHOICES_LIST,
        method='filter_favorites'
    )
    is_in_shopping_cart = filters.ChoiceFilter(
        label='is_in_shopping_cart',
        choices=CHOICES_LIST,
        method='filter_shopping_cart'
    )
    author = filters.NumberFilter(field_name='author', lookup_expr='exact')

    class Meta:
        model = Recipe
        fields = ('tags', 'author')

    def filter_authenticated(self, queryset, name, value):
        if not value:
            return queryset
        if not self.request.user.is_authenticated:
            return queryset.none()
        return queryset.filter(**{name: self.request.user})

    def filter_favorites(self, queryset, name, value):
        return self.filter_authenticated(queryset, 'in_favorite__user', value)

    def filter_shopping_cart(self, queryset, name, value):
        return self.filter_authenticated(
            queryset, 'in_shopping_cart__user', value
        )


class CustomIngredientFilter(FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
