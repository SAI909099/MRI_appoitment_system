# views.py

import base64
import logging
import os
from decimal import Decimal
from io import BytesIO

import qrcode
from django.db import transaction
from django.db.models import Max, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.db.models.functions import Coalesce
from django.conf import settings
from django.views.decorators.http import require_POST   # <-- NEW

from .models import BodyPart, Expense, Patient

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OS-specific import
if os.name == 'nt':
    import win32print

# -----------------------
# Control Panel
# -----------------------
class ControlPanelView(View):
    def get(self, request):
        body_parts = BodyPart.objects.all()
        return render(request, 'control_panel.html', {'body_parts': body_parts})

    def post(self, request):
        # Create new body part
        name = request.POST.get('body_part')
        price = request.POST.get('price')
        if name and price:
            BodyPart.objects.create(name=name, price=price)
        return redirect('control_panel')


# -----------------------
# BodyPart edit/delete (NEW)
# -----------------------
@require_POST
def edit_body_part(request):
    bp_id = request.POST.get('body_part_id')
    name = request.POST.get('name')
    price = request.POST.get('price')

    bp = get_object_or_404(BodyPart, pk=bp_id)
    if name:
        bp.name = name
    if price:
        bp.price = Decimal(price)
    bp.save()
    return redirect('control_panel')


@require_POST
def delete_body_part(request, pk):
    bp = get_object_or_404(BodyPart, pk=pk)
    bp.delete()
    return redirect('control_panel')


# -----------------------
# Register Patient
# -----------------------
class RegisterPatientView(View):
    def get(self, request):
        body_parts = BodyPart.objects.all()
        return render(request, 'register_patient.html', {'body_parts': body_parts})

    def post(self, request):
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        birth_year = request.POST.get('birth_year')
        phone_number = request.POST.get('phone_number', '')
        notes = request.POST.get('notes', '')
        body_parts_ids = request.POST.getlist('body_parts')
        payment_method = request.POST.get('payment_method')
        partial_paid_raw = request.POST.get('partial_paid', '0')

        if not body_parts_ids:
            return redirect('register_patient')

        try:
            partial_paid = Decimal(str(partial_paid_raw or 0))
        except Exception:
            partial_paid = Decimal('0')

        today = timezone.localdate()

        with transaction.atomic():
            max_number = (
                Patient.objects
                .filter(registration_date__date=today)
                .aggregate(max_num=Max('appointment_number'))
                .get('max_num')
            )
            try:
                next_number = int(max_number) + 1 if max_number else 1
            except (TypeError, ValueError):
                next_number = 1

            appointment_number = f"{next_number:03d}"

            patient = Patient.objects.create(
                first_name=first_name,
                last_name=last_name,
                birth_year=birth_year,
                phone_number=phone_number,
                notes=notes,
                appointment_number=appointment_number,
                registered=True,
                finished=False,
                missed=False,
            )

        patient.body_parts.set(body_parts_ids)

        total_price = patient.total_price

        if partial_paid >= total_price and total_price > 0:
            patient.paid = True
            patient.partial_paid = total_price
        elif partial_paid > 0:
            patient.paid = False
            patient.partial_paid = min(partial_paid, total_price)
        else:
            patient.paid = False
            patient.partial_paid = Decimal('0.00')

        patient.save()

        request.session['last_payment_method'] = payment_method

        return redirect('print_receipt', patient_id=patient.id)


# -----------------------
# Print Receipt
# -----------------------
class PrintReceiptView(View):
    def get(self, request, patient_id):
        patient = get_object_or_404(Patient, id=patient_id)
        total_price = patient.total_price
        payment_method = request.session.pop('last_payment_method', None)

        qr_text = (
            f"Navbat: {patient.appointment_number}\n"
            f"Ism: {patient.first_name}\n"
            f"Familiya: {patient.last_name}\n"
            f"Jami: {total_price}\n"
            f"To'langan: {patient.partial_paid}\n"
            f"To'lov turi: {payment_method}\n"
            f"Sana: {timezone.localtime(patient.registration_date)}"
        )

        qr_img = qrcode.make(qr_text)
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return render(request, 'print_receipt.html', {
            'patient': patient,
            'total_price': total_price,
            'payment_method': payment_method,
            'qr_base64': qr_base64
        })


# -----------------------
# Patient List
# -----------------------
class PatientListView(View):
    def get(self, request):
        current_date = request.GET.get('date') or timezone.localdate().isoformat()

        patients = (
            Patient.objects
            .filter(registration_date__date=current_date)
            .order_by('appointment_number')
        )
        body_parts = BodyPart.objects.all()

        search = request.GET.get('search')
        if search:
            patients = patients.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(appointment_number__icontains=search)
            )

        return render(request, 'patient_list.html', {
            'patients': patients,
            'current_date': current_date,
            'body_parts': body_parts
        })

    def post(self, request):
        action = request.POST.get('action')
        patient_id = request.POST.get('patient_id')
        patient = get_object_or_404(Patient, id=patient_id)

        if action == 'edit':
            patient.first_name = request.POST.get('first_name', patient.first_name)
            patient.last_name = request.POST.get('last_name', patient.last_name)
            patient.birth_year = request.POST.get('birth_year', patient.birth_year)
            patient.phone_number = request.POST.get('phone_number', patient.phone_number)

            body_parts_ids = request.POST.getlist('body_parts')
            if body_parts_ids:
                patient.body_parts.set(body_parts_ids)

            total_price = patient.total_price
            try:
                partial_paid_raw = request.POST.get('partial_paid', patient.partial_paid)
                partial_paid = Decimal(str(partial_paid_raw))
            except Exception:
                partial_paid = Decimal('0.00')

            if partial_paid > total_price:
                partial_paid = total_price

            patient.partial_paid = partial_paid
            patient.paid = ('paid' in request.POST) or (partial_paid >= total_price)

            patient.save()

        elif action == 'call':
            patient.registered = False
            patient.missed = False
            patient.finished = False
            patient.save()

        elif action == 'done':
            patient.finished = True
            patient.save()

        elif action == 'not_here':
            patient.missed = True
            patient.finished = False
            patient.save()

        elif action == 'delete':
            patient.delete()

        return redirect('patient_list')


# -----------------------
# Financial Report
# -----------------------
class FinancialReportView(View):
    def get(self, request):
        current_date = request.GET.get('date') or timezone.localdate().isoformat()
        search = request.GET.get('search')

        expenses = Expense.objects.filter(date__date=current_date)
        if search:
            expenses = expenses.filter(Q(title__icontains=search) | Q(note__icontains=search))

        patients = Patient.objects.filter(registration_date__date=current_date)
        income = sum(p.partial_paid for p in patients)
        outcome = sum(e.amount for e in expenses)
        balance = income - outcome

        return render(request, 'financial_report.html', {
            'expenses': expenses,
            'income': income,
            'outcome': outcome,
            'balance': balance,
            'current_date': current_date,
        })

    def post(self, request):
        title = request.POST.get('title')
        amount_raw = request.POST.get('amount')
        note = request.POST.get('note', '')

        try:
            amount = Decimal(str(amount_raw))
        except:
            amount = Decimal('0.00')

        Expense.objects.create(title=title, amount=amount, note=note)
        return redirect('financial_report')


# -----------------------
# TV Display
# -----------------------
class TVDisplayView(View):
    def get(self, request):
        current_date = request.GET.get('date') or timezone.localdate().isoformat()
        patients = (
            Patient.objects
            .filter(registration_date__date=current_date, finished=False)
            .order_by('appointment_number')
        )
        body_parts = BodyPart.objects.all()

        emergency_phone = getattr(settings, 'TV_EMERGENCY_PHONE', '+998 (90) 304 - 04 - 44')

        return render(request, 'tv_display.html', {
            'patients': patients,
            'current_date': current_date,
            'body_parts': body_parts,
            'emergency_phone': emergency_phone,
        })
