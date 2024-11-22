from django import forms
from .models import Transaction, Category

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['date', 'category', 'amount', 'description']

    date = forms.DateField(
        input_formats=['%d-%m-%Y'],
        widget=forms.DateInput(attrs={'class': 'datepicker', 'placeholder': 'DD-MM-YYYY'})
    )

    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        widget=forms.NumberInput(attrs={'placeholder': 'Enter amount'})
    )

    def __init__(self, *args, **kwargs):
        transaction_type = kwargs.pop('transaction_type', None)
        super(TransactionForm, self).__init__(*args, **kwargs)
        
        if transaction_type:
            self.fields['category'].queryset = Category.objects.filter(category_type=transaction_type)