from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Transaction, Category
from .forms import TransactionForm
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
import plotly.express as px
import plotly.graph_objs as go

def index(request):
    if request.user.is_authenticated:
        return redirect('spending')
    return render(request, 'index.html')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        
        if password != password2:
            messages.error(request, "Passwords do not match!")
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect('register')
        
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, "Registration successful! Please log in.")
        return redirect('login')
    
    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('spending')
        else:
            messages.error(request, "Invalid credentials!")
            return redirect('login')
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def spending(request):
    total_income = Transaction.objects.filter(user=request.user, transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Transaction.objects.filter(user=request.user, transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expense

    categories = Category.objects.filter(user=request.user)
    
    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,

    }

    return render(request, 'spending.html', context)

@login_required
def dashboard(request):
    transactions = Transaction.objects.filter(user=request.user)
    total_income = sum(t.amount for t in transactions if t.transaction_type == 'income')
    total_expense = sum(t.amount for t in transactions if t.transaction_type == 'expense')
    balance = total_income - total_expense

    bar_chart = go.Figure(
        data=[
            go.Bar(name='Income', x=['Total'], y=[total_income], marker_color='green'),
            go.Bar(name='Expense', x=['Total'], y=[total_expense], marker_color='red')
        ]
    )
    bar_chart.update_layout(title='Income vs. Expense', barmode='group')

    expense_categories = {}
    for t in transactions.filter(transaction_type='expense'):
        expense_categories[t.category.name] = expense_categories.get(t.category.name, 0) + t.amount
    pie_chart = go.Figure(
        data=[
            go.Pie(labels=list(expense_categories.keys()), values=list(expense_categories.values()))
        ]
    )
    pie_chart.update_layout(title='Expenses by Category')

    transactions_by_date = sorted(transactions, key=lambda x: x.date)
    dates = [t.date.strftime("%d-%m-%Y") for t in transactions_by_date]
    balances = []
    current_balance = 0
    for t in transactions_by_date:
        if t.transaction_type == 'income':
            current_balance += t.amount
        else:
            current_balance -= t.amount
        balances.append(current_balance)
    line_chart = go.Figure(
        data=[go.Scatter(x=dates, y=balances, mode='lines', name='Balance')]
    )
    line_chart.update_layout(title='Balance Over Time', xaxis_title='Date', yaxis_title='Balance')

    context = {
        'bar_chart': bar_chart.to_html(full_html=False),
        'pie_chart': pie_chart.to_html(full_html=False),
        'line_chart': line_chart.to_html(full_html=False),
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
    }
    return render(request, 'dashboard.html', context)


@login_required
def add_expense(request):
    if request.method == 'POST':
        date_str = request.POST.get('date')
        try:
            date_obj = datetime.strptime(date_str, '%d-%m-%Y').date()
        except ValueError:
            messages.error(request, 'Invalid date format. Please select a valid date.')
            return render(request, 'add_expense.html', {'form': TransactionForm()})

        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.date = date_obj
            transaction.transaction_type = 'expense'
            transaction.user = request.user
            transaction.save()
            messages.success(request, 'expense added successfully!')
            return redirect('spending')
        else:
            messages.error(request, 'Failed to add expense. Please check your input.')
    else:
        form = TransactionForm(transaction_type='expense')

    return render(request, 'add_expense.html', {'form': form})

def add_income(request):
    if request.method == 'POST':
        date_str = request.POST.get('date')
        try:
            date_obj = datetime.strptime(date_str, '%d-%m-%Y').date()
        except ValueError:
            messages.error(request, 'Invalid date format. Please select a valid date.')
            return render(request, 'add_income.html', {'form': TransactionForm()})

        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.date = date_obj
            transaction.transaction_type = 'income'
            transaction.user = request.user
            transaction.save()
            messages.success(request, 'Income added successfully!')
            return redirect('spending')
        else:
            messages.error(request, 'Failed to add income. Please check your input.')
    else:
        form = TransactionForm(transaction_type='income')

    return render(request, 'add_income.html', {'form': form})


@login_required
def transactions(request):
    user = request.user

    today = timezone.now().date()

    filter_type = request.GET.get('filter', 'daily')

    if filter_type == 'daily':
        transactions = Transaction.objects.filter(user=user, date=today).order_by('-date')
    elif filter_type == 'weekly':
        start_of_week = today - timezone.timedelta(days=today.weekday())
        end_of_week = start_of_week + timezone.timedelta(days=6)
        transactions = Transaction.objects.filter(user=user, date__range=[start_of_week, end_of_week]).order_by('-date')
    elif filter_type == 'monthly':
        transactions = Transaction.objects.filter(user=user, date__month=today.month, date__year=today.year).order_by('-date')
    elif filter_type == 'yearly':
        transactions = Transaction.objects.filter(user=user, date__year=today.year).order_by('-date')
    else:
        transactions = Transaction.objects.filter(user=user).order_by('-date')

    return render(request, 'transactions.html', {
        'transactions': transactions,
        'filter_type': filter_type,
    })

@login_required
def edit_transaction(request, transaction_id):
    # Get the transaction object to edit
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            # Save the updated transaction
            form.save()
            # Redirect to the transactions page after saving
            return redirect('transactions')
        else:
            # If form is invalid, print errors for debugging (optional)
            print(form.errors)
            return render(request, 'edit_transaction.html', {'form': form, 'transaction': transaction})
    else:
        form = TransactionForm(instance=transaction)
    
    return render(request, 'edit_transaction.html', {'form': form, 'transaction': transaction})

@login_required
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction deleted successfully!')
        return redirect('transactions')
    return render(request, 'confirm_delete.html', {'transaction': transaction})

@login_required
def categories(request):
    if request.method == 'POST':
        new_income_category = request.POST.get('new_income_category')
        if new_income_category:
            Category.objects.create(
                name=new_income_category,
                category_type='income',
                user=request.user
            )
            return redirect('categories')

        new_expense_category = request.POST.get('new_expense_category')
        if new_expense_category:
            Category.objects.create(
                name=new_expense_category,
                category_type='expense',
                user=request.user
            )
            return redirect('categories')

    income_categories = Category.objects.filter(category_type='income', is_global=True) | Category.objects.filter(user=request.user, category_type='income')
    expense_categories = Category.objects.filter(category_type='expense', is_global=True) | Category.objects.filter(user=request.user, category_type='expense')
    
    return render(request, 'categories.html', {
        'income_categories': income_categories,
        'expense_categories': expense_categories
    })

@login_required
def account(request):
    total_income = Transaction.objects.filter(user=request.user, transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Transaction.objects.filter(user=request.user, transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'user': request.user,
        'total_income': total_income,
        'total_expense': total_expense,
    }
    return render(request, 'account.html', context)


