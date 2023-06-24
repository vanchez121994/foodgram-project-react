from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import Q, F


class User(AbstractUser):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        'Ник пользователя',
        max_length=150,
        unique=True,
        help_text=(
            'Обязательное поле. Не более 150 символов. '
            'Допустимые символы: буквы, цифры и @/./+/-/_.'
        ),
        validators=[username_validator, ],
        error_messages={
            'unique': 'Имя пользователя уже используется',
        },
    )
    email = models.EmailField('Почта', max_length=254, unique=True)
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    is_active = models.BooleanField(
        'Активный/неактивный.',
        default=True,
        help_text='Аккаунт - активирован или нет.',
    )
    is_staff = models.BooleanField(
        default=False,
        help_text='Пользователь является суперюзером.',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='subscribers'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'author'],
                name='unique_subscriber_author'
            ),
            models.CheckConstraint(
                check=~Q(subscriber=F('author')),
                name='subscriber_not_author'
            )
        ]

    def __str__(self):
        return (
            f'{self.subscriber} '
            f'subscribed to '
            f'{self.author}'
        )
