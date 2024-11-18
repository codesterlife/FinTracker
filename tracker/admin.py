from django.contrib import admin
from .models import Transaction, Category
from django.utils.formats import date_format

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'category', 'amount', 'transaction_type', 'user')
    list_filter = ('user', 'transaction_type', 'category__category_type')
    search_fields = ('user__username', 'category__name')

    def formatted_date(self, obj):
        return date_format(obj.date, format='d-m-Y')
    
    formatted_date.short_description = 'Date'

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'user', 'is_global')
    list_filter = ('user', 'category_type', 'is_global')
    search_fields = ('name',)

    def save_model(self, request, obj, form, change):
        if obj.is_global:
            obj.user = None
        else:
            obj.user = request.user
        super().save_model(request, obj, form, change)

admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Category, CategoryAdmin)