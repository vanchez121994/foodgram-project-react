from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.fields import (
    CharField, IntegerField, SerializerMethodField,
    CurrentUserDefault, HiddenField)
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueTogetherValidator

from users.models import Subscription
from recipes.models import (
    Ingredient, Recipe, RecipeIngredients, Tag,
    ShopCart, FavoriteRecipes)

from .fields import Base64ImageField

User = get_user_model()


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = ('__all__',)


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('__all__',)


class RecipeIngredientsSerializer(ModelSerializer):
    id = IntegerField(source='ingredient.id')
    name = CharField(source='ingredient.name')
    measurement_unit = CharField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientsCreateSerializer(ModelSerializer):
    id = IntegerField(source='ingredient.id')

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if value < 0:
            raise ValidationError('Количество должно быть больше 0.')
        return value


class RecipeShortSerializer(ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('__all__',)


class CustomUserCreateSerializer(UserCreateSerializer):
    password = CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'password'
        )

    def validate_username(self, value):
        if value == 'me':
            raise ValidationError('Это имя использовать запрещено.')
        if User.objects.filter(username=value).exists():
            raise ValidationError('Это имя пользователя уже занято.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise ValidationError('Эта почта уже используется.')
        return value


class CustomUserSerializer(UserSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return user.subscriptions.filter(author=obj).exists()


class SubscriptionCreateSerializer(ModelSerializer):
    subscriber = HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Subscription
        fields = (
            'subscriber', 'author'
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['subscriber', 'author']
            )
        ]

    def validate(self, attrs):
        subscriber = attrs.get('subscriber')
        author = attrs.get('author')
        if not author:
            raise ValidationError('Укажите подписчика')
        if subscriber == author:
            raise ValidationError('Запрещено подписываться на самого себя')
        if not User.objects.filter(id=author.id).exists():
            raise ValidationError('Такого пользователя не существует')
        return attrs


class SubscriptionSerializer(CustomUserSerializer):
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed',
            'recipes', 'recipes_count'
        )
        read_only_fields = ('__all__',)

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        try:
            limit = self.context.get(
                'request'
            ).query_params.get('recipes_limit')
            if limit:
                recipes = recipes[:int(limit)]
        except ValueError:
            raise ValidationError(
                'recipes_limit должен быть числом'
            )
        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class ShopCartSerializer(ModelSerializer):
    user = HiddenField(default=CurrentUserDefault())

    class Meta:
        model = ShopCart
        fields = (
            'recipe', 'user'
        )
        validators = [
            UniqueTogetherValidator(
                queryset=ShopCart.objects.all(),
                fields=['recipe', 'user']
            )
        ]

    def validate_recipe(self, value):
        if not Recipe.objects.filter(id=value.id).exists():
            raise ValidationError('Такого рецепта не существует')
        return value


class FavoriteRecipeSerializer(ModelSerializer):
    user = HiddenField(default=CurrentUserDefault())

    class Meta:
        model = FavoriteRecipes
        fields = (
            'recipe', 'user'
        )
        validators = [
            UniqueTogetherValidator(
                queryset=FavoriteRecipes.objects.all(),
                fields=['recipe', 'user']
            )
        ]

    def validate_recipe(self, value):
        if not Recipe.objects.filter(id=value.id).exists():
            raise ValidationError('Такого рецепта не существует')
        return value


class RecipeSerializer(ModelSerializer):
    tags = TagSerializer(many=True)
    author = CustomUserSerializer(default=CurrentUserDefault())
    ingredients = RecipeIngredientsSerializer(
        many=True,
        source='recipeingredients_set'
    )
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField()
    text = CharField(source='description')

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = ('__all__',)

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return obj.in_favorite.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return obj.in_shopping_cart.filter(user=user).exists()


class RecipeCreateSerializer(ModelSerializer):
    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    author = HiddenField(default=CurrentUserDefault())
    ingredients = RecipeIngredientsCreateSerializer(
        many=True
    )
    image = Base64ImageField()
    text = CharField(source='description')

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = ('__all__',)

    def validate(self, attrs):
        tags = attrs.get('tags')
        ingredients = attrs.get('ingredients')
        if not tags:
            raise ValidationError('Укажите теги')
        if not ingredients:
            raise ValidationError('Укажите ингридиенты')
        return attrs

    def validate_cooking_time(self, value):
        if value < 1:
            raise ValidationError('Время приготовления должно быть больше 1')
        return value

    def validate_tags(self, value):
        if not value:
            raise ValidationError('Добавьте теги')
        len_value = len(value)
        if len_value > len(set(value)):
            raise ValidationError('Добавлен повторяющийся тег')
        if len_value != Tag.objects.filter(
                id__in=[val.id for val in value]
        ).count():
            raise ValidationError('Добавлен несуществующий тег')
        return value

    def validate_ingredients(self, value):
        ingredients_ids = []
        for ingredient in value:
            id = ingredient.get('ingredient', {}).get('id')
            if id not in ingredients_ids:
                ingredients_ids.append(id)
            else:
                raise ValidationError('Добавлен повторяющийся ингредиент')

        if len(value) != Ingredient.objects.filter(
            id__in=ingredients_ids
        ).count():
            raise ValidationError('Добавлен несуществующий ингредиент')

        if not ingredients_ids:
            raise ValidationError('Добавьте ингредиенты')

        return value

    def create_ingredients(self, recipe, ingredients):
        RecipeIngredients.objects.bulk_create([
            RecipeIngredients(
                recipe=recipe,
                ingredient_id=ingredient['ingredient'].get('id'),
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ])

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)

        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        if tags:
            instance.tags.clear()
            instance.tags.set(tags)

        if ingredients:
            RecipeIngredients.objects.filter(recipe=instance).delete()
            self.create_ingredients(instance, ingredients)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeSerializer(
            instance, context=context).data
