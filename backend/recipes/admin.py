from django.contrib import admin

from .models import (
    Ingredient, FavoriteRecipes, Recipe, RecipeIngredients, ShopCart, Tag
)


class RecipeIngredientsInline(admin.TabularInline):
    model = RecipeIngredients
    extra = 0


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name', )
    empty_value_display = '-пусто-'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    fields = (
        'author', 'name', 'image', 'description',
        'tags', 'cooking_time', 'pub_date', 'get_in_favorites'
    )
    readonly_fields = ('pub_date', 'get_in_favorites')
    inlines = [RecipeIngredientsInline]
    list_display = ('pk', 'name', 'author')
    search_fields = ('author', 'name', 'tags')
    empty_value_display = '-пусто-'
    date_hierarchy = 'pub_date'
    ordering = ('-pub_date', )

    def get_in_favorites(self, obj):
        return obj.in_favorite.count()

    get_in_favorites.short_description = 'Добавлен в избранное'


@admin.register(RecipeIngredients)
class RecipeIngredientsAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe', 'ingredient')
    empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color')
    search_fields = ('name',)
    empty_value_display = '-пусто-'


@admin.register(FavoriteRecipes)
class FavoriteRecipesAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'user')
    search_fields = ('recipe', 'user')
    empty_value_display = '-пусто-'


@admin.register(ShopCart)
class ShopCartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'user')
    search_fields = ('recipe', 'user')
    empty_value_display = '-пусто-'
