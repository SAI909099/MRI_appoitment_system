from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db.models import Sum, DecimalField
from decimal import Decimal



class BodyPart(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tana qismi")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Narx")

    def __str__(self):
        return self.name

class Patient(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Ism")
    last_name = models.CharField(max_length=100, verbose_name="Familiya")
    birth_year = models.IntegerField(verbose_name="Tug'ilgan yil")
    notes = models.TextField(verbose_name="Eslatmalar", blank=True)
    body_parts = models.ManyToManyField(BodyPart, verbose_name="Skani qilinadigan joylar")
    finished = models.BooleanField(default=False, verbose_name="Tugallangan (TVda ko‘rinmasin)")


    appointment_number = models.CharField(
        max_length=10,
        verbose_name="Navbat raqami"
    )

    registered = models.BooleanField(default=False, verbose_name="Ro'yxatdan o'tgan")
    paid = models.BooleanField(default=False, verbose_name="To'langan")
    partial_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Qisman to'lov"
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Telefon raqami"
    )

    registration_date = models.DateTimeField(auto_now_add=True, verbose_name="Ro'yxatdan o'tkazilgan sana")
    missed = models.BooleanField(default=False, verbose_name="Navbatini o'tkazib yuborgan")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['appointment_number', 'registration_date'],
                name='unique_appointment_per_day'
            )
        ]

    @property
    def total_price(self):
        return self.body_parts.aggregate(
            total=Coalesce(Sum('price'), Decimal('0.00'), output_field=DecimalField())
        )['total']

    def __str__(self):
        return f"{self.appointment_number} - {self.first_name} {self.last_name}"

class Expense(models.Model):
    title = models.CharField(max_length=100, verbose_name="Chiqim nomi")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Miqdor")
    note = models.TextField(verbose_name="Eslatma", blank=True)
    date = models.DateTimeField(auto_now_add=True, verbose_name="Sana")