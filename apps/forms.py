from django import forms
from .models import Patient, Appointment, Expense
from django.db.models import Max

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'phone', 'queue_number']

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Get max queue_number and increment
        last_number = Patient.objects.aggregate(Max("queue_number"))["queue_number__max"] or 0
        instance.queue_number = last_number + 1
        if commit:
            instance.save()
        return instance


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient', 'appointment_date', 'appointment_time', 'service_type', 'price', 'paid']

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['purpose', 'amount']
