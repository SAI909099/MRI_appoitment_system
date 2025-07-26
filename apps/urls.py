# urls.py
from django.urls import path
from .views import (
    ControlPanelView, RegisterPatientView, PatientListView,
    FinancialReportView, TVDisplayView, PrintReceiptView, edit_body_part, delete_body_part
)

urlpatterns = [
    path('', ControlPanelView.as_view(), name='control_panel'),
    path('control_panel/', ControlPanelView.as_view(), name='control_panel'),
    path('control_panel/edit/', edit_body_part, name='edit_body_part'),                 # <-- NEW
    path('control_panel/delete/<int:pk>/', delete_body_part, name='delete_body_part'),  # <-- NEW
    path('register_patient/', RegisterPatientView.as_view(), name='register_patient'),
    path('patient_list/', PatientListView.as_view(), name='patient_list'),
    path('financial_report/', FinancialReportView.as_view(), name='financial_report'),
    path('tv_display/', TVDisplayView.as_view(), name='tv_display'),
    path('print-receipt/<int:patient_id>/', PrintReceiptView.as_view(), name='print_receipt'),
]
