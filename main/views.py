from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Account, Transaction, Goals
from .forms import AccountForm, TransactionForm, TransferForm, GoalForm


def apply_goal_progress(account, signed_amount):
    """Bump current_amount on any goal for this account that the transaction counts toward."""
    for goal in account.goals.all():
        if goal.goal_type == Goals.GoalType.at_least and signed_amount > 0:
            goal.current_amount += signed_amount
            goal.save(update_fields=['current_amount'])
        elif goal.goal_type == Goals.GoalType.at_most and signed_amount < 0:
            goal.current_amount += -signed_amount
            goal.save(update_fields=['current_amount'])


@login_required
def dashboard(request):
    accounts = Account.objects.filter(user=request.user)
    if not accounts.exists():
        return render(request, 'main/dashboard.html', {'accounts': accounts, 'selected_account': None})
    #always render the first account on start
    return redirect('account_detail', account_id=accounts.first().id)


@login_required
def account_detail(request, account_id):
    accounts = Account.objects.filter(user=request.user)
    selected_account = get_object_or_404(Account, pk=account_id, user=request.user)

    # lay form roi in ra trong HTML
    context = {
        'accounts': accounts,
        'selected_account': selected_account,
        'transactions': selected_account.transactions.all(),
        'goals': selected_account.goals.all(),
        'account_form': AccountForm(),
        'transaction_form': TransactionForm(),
        'transfer_form': TransferForm(user=request.user, exclude_account=selected_account),
        'goal_form': GoalForm(),
    }
    return render(request, 'main/dashboard.html', context)


@login_required
def create_account(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            account.save()
            messages.success(request, f'Account "{account.title}" created.')
            return redirect('account_detail', account_id=account.id)
        messages.error(request, 'Could not create account: ' + str(form.errors))
    return redirect('dashboard')


@login_required
def make_transaction(request, account_id):
    account = get_object_or_404(Account, pk=account_id, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.user = request.user
            tx.account = account
            if form.cleaned_data['action'] == 'withdraw':
                tx.amount = -tx.amount
                tx.kind = Transaction.Kind.withdraw
            else:
                tx.kind = Transaction.Kind.deposit
            tx.save()

            account.amount += tx.amount
            account.save(update_fields=['amount'])
            apply_goal_progress(account, tx.amount)
            messages.success(request, 'Transaction recorded.')
        else:
            messages.error(request, 'Could not record transaction: ' + str(form.errors))
    return redirect('account_detail', account_id=account.id)


@login_required
def make_transfer(request, account_id):
    account = get_object_or_404(Account, pk=account_id, user=request.user)
    if request.method == 'POST':
        form = TransferForm(request.POST, user=request.user, exclude_account=account)
        if form.is_valid():
            to_account = form.cleaned_data['to_account']

            out_tx = form.save(commit=False)
            out_tx.pk = None  # make sure we're creating, not touching an existing row
            out_tx.user = request.user
            out_tx.account = account
            out_tx.amount = -abs(out_tx.amount)
            out_tx.kind = Transaction.Kind.transfer_out
            out_tx.save()

            in_tx = Transaction.objects.create(
                user=request.user,
                account=to_account,
                title=out_tx.title,
                amount=-out_tx.amount,
                kind=Transaction.Kind.transfer_in,
                description=out_tx.description,
                linked_transaction=out_tx,
            )
            out_tx.linked_transaction = in_tx
            out_tx.save(update_fields=['linked_transaction'])

            account.amount += out_tx.amount
            account.save(update_fields=['amount'])
            to_account.amount += in_tx.amount
            to_account.save(update_fields=['amount'])

            apply_goal_progress(account, out_tx.amount)
            apply_goal_progress(to_account, in_tx.amount)

            messages.success(request, f'Transferred {in_tx.amount} to {to_account.title}.')
        else:
            messages.error(request, 'Could not transfer: ' + str(form.errors))
    return redirect('account_detail', account_id=account.id)


@login_required
def create_goal(request, account_id):
    account = get_object_or_404(Account, pk=account_id, user=request.user)
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.account = account
            goal.save()
            messages.success(request, f'Goal "{goal.title}" created.')
        else:
            messages.error(request, 'Could not create goal: ' + str(form.errors))
    return redirect('account_detail', account_id=account.id)
