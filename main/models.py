from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Type(models.TextChoices):
    personal = 'prs', 'Personal'
    work = 'wk', 'Work'
    investment = 'inv', 'Investment'
    learning = 'learn', 'Learning'
    saving = 'save', 'Saving'


class Account(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='accounts')
    title = models.CharField(max_length=250)
    account_type = models.CharField(choices=Type.choices, max_length=250, default=Type.personal)
    amount = models.IntegerField(default=0, validators=[MinValueValidator(-100_000_000_000), MaxValueValidator(100_000_000_000)])

    class Meta:
        unique_together = ('user', 'title')

    def __str__(self):
        return f'{self.title}'


class Transaction(models.Model):
    class Kind(models.TextChoices):
        deposit = 'dep', 'Deposit'
        withdraw = 'wd', 'Withdraw'
        transfer_out = 'tout', 'Transfer out'
        transfer_in = 'tin', 'Transfer in'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    title = models.CharField(max_length=250)
    amount = models.IntegerField(validators=[MinValueValidator(-100_000_000_000) ,MaxValueValidator(100_000_000_000)])
    kind = models.CharField(choices=Kind.choices, max_length=10, default=Kind.deposit)
    description = models.TextField(blank=True)
    # Optional pointer to the "other half" of a transfer (not a hard requirement).
    linked_transaction = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title}: {self.amount}'


class Goals(models.Model):
    class GoalType(models.TextChoices):
        at_most = 'most', 'Spend at most'
        at_least = 'least', 'Save at least'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=250)
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1_000), MaxValueValidator(100_000_000_000)])
    goal_type = models.CharField(choices=GoalType.choices, max_length=250, default=GoalType.at_most)
    description = models.TextField(blank=True)
    months = models.PositiveIntegerField(default=1)
    # Stored directly and bumped whenever a matching transaction happens on this
    # account (see views.apply_goal_progress), instead of being recomputed from
    # a date range. Simpler for a small app, at the cost of being a second
    # source of truth alongside the transaction history.
    current_amount = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-months']

    @property
    def percent(self):
        #min (%, 100%) => 100% max
        return min(int(self.current_amount / self.amount * 100), 100) if self.amount else 0

    def __str__(self):
        return self.title
