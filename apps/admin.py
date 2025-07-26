# from django.contrib import admin
# from .models import Patient, Appointment, Expense
#
# @admin.register(Patient)
# class PatientAdmin(admin.ModelAdmin):
#     list_display = ('first_name', 'last_name', 'phone', 'created_at')
#     search_fields = ('first_name', 'last_name', 'phone')
#
# @admin.register(Appointment)
# class AppointmentAdmin(admin.ModelAdmin):
#     list_display = ('patient', 'appointment_date', 'appointment_time', 'service_type', 'price', 'paid')
#     list_filter = ('appointment_date', 'paid')
#     search_fields = ('patient__first_name', 'patient__last_name')
#
# @admin.register(Expense)
# class ExpenseAdmin(admin.ModelAdmin):
#     list_display = ('purpose', 'amount', 'date')
#     list_filter = ('date',)
#     search_fields = ('purpose',)
