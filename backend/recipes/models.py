from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField('Название тега', max_length=256, unique=True)
    color = ColorField(
        verbose_name='HEX-код',
        format='hex',
        max_length=7,
        unique=True,
        validators=[
            RegexValidator(
                regex="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
                message='Проверьте вводимый формат',
            )
        ],
    )
    slug = models.SlugField(
        'Слаг для URL',
        max_length=50,
        unique=True,
        db_index=False
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        'Название ингредиента',
        max_length=256,
        db_index=True
    )
    measurement_unit = models.CharField('Единица измерения', max_length=50)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    name = models.CharField('Название рецепта', max_length=256, db_index=True)
    image = models.ImageField(upload_to='recipe/images')
    description = models.TextField('Описание рецепта', max_length=2500)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredients',
        related_name='recipes'
    )
    tags = models.ManyToManyField(Tag, related_name='recipes')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления в минутах',
        validators=[MinValueValidator(1, message='Минимальное значение 1!')]
    )
    pub_date = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField()

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]


class FavoriteRecipes(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_favorite'
    )
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='favorite_recipes'
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_favoriterecipe_user'
            )
        ]

    def __str__(self):
        return f'{self.user} likes {self.recipe}'


class ShopCart(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart'
    )
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )

    class Meta:
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_cartrecipe_user'
            )
        ]

    def __str__(self):
        return f'{self.user} byes {self.recipe}'
