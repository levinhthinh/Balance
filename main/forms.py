from django import forms
from .models import Account, Transaction, Goals


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        exclude = ['user', 'amount']  # user is set in the view; amount starts at 0


class TransactionForm(forms.ModelForm):
    ACTION_CHOICES = [('deposit', 'Add money'), ('withdraw', 'Take away money')]
    # Not a model field — just tells the view whether to flip amount negative.
    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = Transaction
        fields = ['action', 'title', 'amount', 'description']
        # amount is entered as a positive number here; the view flips the sign for withdrawals


class TransferForm(forms.ModelForm):
    to_account = forms.ModelChoiceField(queryset=Account.objects.none(), label='Transfer to')

    class Meta:
        model = Transaction
        fields = ['to_account', 'title', 'amount', 'description']

    def __init__(self, *args, user=None, exclude_account=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Account.objects.filter(user=user)
        if exclude_account:
            queryset = queryset.exclude(pk=exclude_account.pk)
        self.fields['to_account'].queryset = queryset


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goals
        exclude = ['user', 'account', 'current_amount']
