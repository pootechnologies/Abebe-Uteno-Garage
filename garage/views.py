from sys import exception
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from django.db import transaction
import calendar
import traceback

from .models import (
    Customer, Vehicle, Service, ServicePackage,
    JobCard, JobCardAssignment, AssignedService, Invoice,
    VehicleAcceptance, VehicleOldPartDelivery, VehicleOldPartDeliveryItems, 
    VehicleOrderVoucher, VehicleOrderVoucherItems, VehiclePartRequest,
    VehiclePartRequestItems, PerformaCustomer, PerformaPerforma, PerformaProduct,
    Category, Supplier, Product, Order, OrderItem, CompanyInfo,
    PurchaseSupplier, PurchaseExpense, PurchaseProduct, SupplierPaymentLog,
    ExpensePaymentLog, OrderPaymentLog, OrderLog, Report, JobCardLog, JobCardAssignmentLog, AssignedServiceLog,
    VehiclePartRequestLog, VehiclePartRequestItemLog, VehicleOldPartDeliveryLog, VehicleOldPartDeliveryItemLog,
    VehicleOrderVoucherLog, VehicleOrderVoucherItemLog, CreditCustomer, CreditCredit, CreditProduct
)

from .serializers import (
    CustomerSerializer, CustomerLightSerializer, VehicleSerializer, ServiceSerializer,
    ServicePackageSerializer, JobCardSerializer, JobCardLightSerializer, ProductLightSerializer,
    JobCardGetEveryThingSerializer, InvoiceSerializer, InvoiceGetSerializer,
    VehicleAcceptanceSerializer, VehicleAcceptanceLightSerializer, VehicleOldPartDeliverySerializer, VehicleOldPartDeliveryLightSerializer,
    VehicleOldPartDeliveryItemsSerializer, AssignedServiceSerializer,
    VehicleOrderVoucherSerializer, VehicleOrderVoucherItemsSerializer, VehicleOrderVoucherLightSerializer,
    VehiclePartRequestSerializer, VehiclePartRequestItemsSerializer, VehiclePartRequestLightSerializer,
    JobCardAssignmentSerializer, JobCardAssignmentLightSerializer,
    PerformaCustomerSerializer, PerformaCustomerLightSerializer, PerformaPerformaSerializer,
    PerformaPerformaLightSerializer, PerformaProductSerializer, CompanyInfoSerializer, CategorySerializer,
    SupplierSerializer, ProductGetSerializer, ProductPostSerializer,
    OrderItemSerializer, OrderSerializer, OrderLightSerializer, PurchaseSupplierSerializer,
    PurchaseExpenseSerializer, PurchaseProductSerializer, PurchaseSupplierLightSerializer,
    PurchaseExpenseLightSerializer, SupplierPaymentLogSerializer, ExpensePaymentLogSerializer,
    OrderPaymentLogSerializer, OrderLogSerializer, OrderReportSerializer, JobCardLogSerializer,
    VehiclePartRequestLogSerializer, VehiclePartRequestItemLogSerializer, VehicleOldPartDeliveryLogSerializer,
    VehicleOldPartDeliveryItemLogSerializer, VehicleOrderVoucherLogSerializer, VehicleOrderVoucherItemLogSerializer,
    CreditCustomerSerializer, CreditCustomerLightSerializer, CreditCreditSerializer, CreditCreditLightSerializer, CreditProductSerializer

)

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework import filters
from django.db.models import Sum, Count, Q


# ------------------ Pagination ------------------
class Pagination(PageNumberPagination):
    page_size = 10  # default items per page
    page_size_query_param = 'page_size'  # allow client to override
    max_page_size = 100


# ------------------ Customer ------------------
class CustomerListCreateAPIView(APIView):
    def get(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Receptionist' or user.role == 'Customer Officer' or user.role == 'Store Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Customer."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )

        
        search_query = request.query_params.get('search', None)
        include_all = request.query_params.get('include_all', '').lower() in ('1', 'true', 'yes')

        customers = Customer.objects.all()
        all_customers = Customer.objects.only('name', 'organization').all()
        
        # Apply search
        if search_query:
            customers = customers.filter(
                Q(name__icontains=search_query) |
                Q(organization__icontains=search_query)
            )

        # Ensure consistent ordering for pagination
        customers = customers.order_by('-id')  # or '-id'

         # Paginate
        paginator = Pagination()
        page = paginator.paginate_queryset(customers, request)
        if page is not None:
            page_data = CustomerSerializer(page, many=True).data
            if include_all:
                all_data = CustomerLightSerializer(all_customers, many=True).data
                return Response({
                    'count': paginator.page.paginator.count,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link(),
                    'results': page_data,
                    'all_results': all_data,
                })
            return paginator.get_paginated_response(page_data)

        # Fallback - no pagination applied
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)


    def post(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Receptionist'):            
        #     return Response(
        #         {"error": "You are not authorized to Create the Customer."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        serializer = CustomerSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomerDetailAPIView(APIView):
    def get(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Receptionist' or user.role == 'Customer Officer' or user.role == 'Store Manager' or user.role == 'Field Operator'):           
        #     return Response(
        #         {"error": "You are not authorized to retrive the Customer."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        customer = get_object_or_404(Customer, pk=pk)
        serializer = CustomerSerializer(customer)
        return Response(serializer.data)

    def put(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Receptionist'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Customer."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        customer = get_object_or_404(Customer, pk=pk)
        serializer = CustomerSerializer(customer, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Receptionist'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Customer."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        customer = get_object_or_404(Customer, pk=pk)
        serializer = CustomerSerializer(customer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Receptionist'):
        #     return Response(
        #         {"error": "You are not authorized to Delete the Customer."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        customer = get_object_or_404(Customer, pk=pk)
        customer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ------------------ Vehicle ------------------
class VehicleListCreateAPIView(APIView):
    def get(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Receptionist' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Vehicle."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        

        search_query = request.query_params.get('search', None)
        include_all = request.query_params.get('include_all', '').lower() in ('1', 'true', 'yes')

        vehicles = Vehicle.objects.all()
        
        # Apply search
        if search_query:
            vehicles = vehicles.filter(
                Q(shanci_kutir__icontains=search_query) |
                Q(license_plate__icontains=search_query) |
                Q(customer__name__icontains=search_query) |
                Q(customer__organization__icontains=search_query) |
                Q(motor_kutir__icontains=search_query)
            )

        # Ensure consistent ordering for pagination
        vehicles = vehicles.order_by('-id')  # or '-id'

         # Paginate
        paginator = Pagination()
        page = paginator.paginate_queryset(vehicles, request)
        if page is not None:
            page_data = VehicleSerializer(page, many=True).data
            if include_all:
                all_data = VehicleSerializer(vehicles, many=True).data
                return Response({
                    'count': paginator.page.paginator.count,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link(),
                    'results': page_data,
                    'all_results': all_data,
                })
            return paginator.get_paginated_response(page_data)

        # Fallback - no pagination applied
        serializer = VehicleSerializer(vehicles, many=True)
        return Response(serializer.data)


    def post(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Receptionist'):
        #     return Response(
        #         {"error": "You are not authorized to Create the Vehicle."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        serializer = VehicleSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VehicleDetailAPIView(APIView):
    def get(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Receptionist' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Vehicle."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        vehicle = get_object_or_404(Vehicle, pk=pk)
        serializer = VehicleSerializer(vehicle)
        return Response(serializer.data)

    def put(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Receptionist'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Vehicle."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        vehicle = get_object_or_404(Vehicle, pk=pk)
        serializer = VehicleSerializer(vehicle, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Receptionist'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Vehicle."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        vehicle = get_object_or_404(Vehicle, pk=pk)
        serializer = VehicleSerializer(vehicle, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Receptionist'):
        #     return Response(
        #         {"error": "You are not authorized to Delete the Vehicle."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        vehicle = get_object_or_404(Vehicle, pk=pk)
        vehicle.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ------------------ Service ------------------
class ServiceListCreateAPIView(APIView):
    def get(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner' or user.role == 'Mechanic' or user.role == 'Electrician' or user.role == 'Paint Worker' or user.role == 'Bat Lamera'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Service."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        


        search_query = request.query_params.get('search', None)
        include_all = request.query_params.get('include_all', '').lower() in ('1', 'true', 'yes')

        services = Service.objects.all()
        
        # Apply search
        if search_query:
            services = services.filter(
                Q(name__icontains=search_query)
            )

        # Ensure consistent ordering for pagination
        services = services.order_by('-id')  # or '-id'

         # Paginate
        paginator = Pagination()
        page = paginator.paginate_queryset(services, request)
        if page is not None:
            page_data = ServiceSerializer(page, many=True).data
            if include_all:
                all_data = ServiceSerializer(services, many=True).data
                return Response({
                    'count': paginator.page.paginator.count,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link(),
                    'results': page_data,
                    'all_results': all_data,
                })
            return paginator.get_paginated_response(page_data)

        # Fallback - no pagination applied
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)


    def post(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager'):
        #     return Response(
        #         {"error": "You are not authorized to Create the Service."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        serializer = ServiceSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ServiceDetailAPIView(APIView):
    def get(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner' or user.role == 'Mechanic' or user.role == 'Electrician' or user.role == 'Paint Worker' or user.role == 'Bat Lamera'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Service."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        service = get_object_or_404(Service, pk=pk)
        serializer = ServiceSerializer(service)
        return Response(serializer.data)

    def put(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Mechanic' or user.role == 'Electrician' or user.role == 'Paint Worker' or user.role == 'Bat Lamera'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Service."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        service = get_object_or_404(Service, pk=pk)
        serializer = ServiceSerializer(service, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Mechanic' or user.role == 'Electrician' or user.role == 'Paint Worker' or user.role == 'Bat Lamera'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Service."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        service = get_object_or_404(Service, pk=pk)
        serializer = ServiceSerializer(service, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager'):
        #     return Response(
        #         {"error": "You are not authorized to Delete the Service."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        service = get_object_or_404(Service, pk=pk)
        service.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ------------------ Service Package ------------------
class ServicePackageListCreateAPIView(APIView):
    def get(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner' or user.role == 'Mechanic' or user.role == 'Electrician' or user.role == 'Paint Worker' or user.role == 'Bat Lamera'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Service Package."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        packages = ServicePackage.objects.all()
        serializer = ServicePackageSerializer(packages, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager'):
        #     return Response(
        #         {"error": "You are not authorized to Create the Service Package."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        serializer = ServicePackageSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ServicePackageDetailAPIView(APIView):
    def get(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner' or user.role == 'Mechanic' or user.role == 'Electrician' or user.role == 'Paint Worker' or user.role == 'Bat Lamera'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Service Package."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        package = get_object_or_404(ServicePackage, pk=pk)
        serializer = ServicePackageSerializer(package)
        return Response(serializer.data)

    def put(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner' or user.role == 'Mechanic' or user.role == 'Electrician' or user.role == 'Paint Worker' or user.role == 'Bat Lamera'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Service Package."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        package = get_object_or_404(ServicePackage, pk=pk)
        serializer = ServicePackageSerializer(package, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner' or user.role == 'Mechanic' or user.role == 'Electrician' or user.role == 'Paint Worker' or user.role == 'Bat Lamera'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Service Package."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        package = get_object_or_404(ServicePackage, pk=pk)
        serializer = ServicePackageSerializer(package, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager'):
        #     return Response(
        #         {"error": "You are not authorized to Delete the Service Package."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        package = get_object_or_404(ServicePackage, pk=pk)
        package.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ------------------ JobCard ------------------
class JobCardListCreateAPIView(APIView):
      
    def get(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Cashier' or user.role == 'Technical Examiner' or user.role == 'Mechanic' or user.role == 'Electrician' or user.role == 'Paint Worker' or user.role == 'Bat Lamera' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Jobcard."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        search_query = request.query_params.get('search', None)
        include_all = request.query_params.get('include_all', '').lower() in ('1', 'true', 'yes')

        # Use select_related to avoid N+1 when accessing customer fields
        jobcards = JobCard.objects.only('id', 'customer__name', 'vehicle__model', 'vehicle__license_plate', 'status', 'service_date', 'odometer_reading', 'total_cost', 'user').select_related('customer').all()
        # jobcards = JobCard.objects.only('id', 'customer__name', 'vehicle__model', 'vehicle__license_plate', 'status', 'service_date', 'odometer_reading', 'total_cost', 'user').select_related('customer').exclude(status__in=['Completed'])
        # Apply search
        if search_query:
            jobcards = jobcards.filter(
                Q(customer__name__icontains=search_query) |
                Q(status__icontains=search_query)
            )

        # Ensure consistent ordering for pagination
        jobcards = jobcards.order_by('-service_date')  # or '-id'

         # Paginate
        paginator = Pagination()
        page = paginator.paginate_queryset(jobcards, request)
        if page is not None:
            page_data = JobCardLightSerializer(page, many=True).data
            if include_all:
                all_data = JobCardLightSerializer(jobcards, many=True).data
                return Response({
                    'count': paginator.page.paginator.count,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link(),
                    'results': page_data,
                    'all_results': all_data,
                })
            return paginator.get_paginated_response(page_data)

        # Fallback - no pagination applied
        serializer = JobCardLightSerializer(jobcards, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager'):
        #     return Response(
        #         {"error": "You are not authorized to Create the Jobcard."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        serializer = JobCardSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class JobCardDetailAPIView(APIView):
    def get(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Cashier' or user.role == 'Technical Examiner' or user.role == 'Mechanic' or user.role == 'Electrician' or user.role == 'Paint Worker' or user.role == 'Bat Lamera' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Jobcard."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        jobcard = get_object_or_404(JobCard, pk=pk)
        serializer = JobCardGetEveryThingSerializer(jobcard)
        return Response(serializer.data)

    def put(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner' or user.role == 'Mechanic' or user.role == 'Electrician' or user.role == 'Paint Worker' or user.role == 'Bat Lamera'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Jobcard."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        jobcard = get_object_or_404(JobCard, pk=pk)
        serializer = JobCardSerializer(jobcard, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def patch(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner' or user.role == 'Mechanic' or user.role == 'Electrician' or user.role == 'Paint Worker' or user.role == 'Bat Lamera'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Jobcard."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        jobcard = get_object_or_404(JobCard, pk=pk)
        serializer = JobCardSerializer(jobcard, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager'):
        #     return Response(
        #         {"error": "You are not authorized to Delete the Jobcard."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        jobcard = get_object_or_404(JobCard, pk=pk)
        jobcard.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



# ------------------ JobCard Assignment ------------------\
class JobCardAssignmentListCreateAPIView(APIView):
    def get(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Jobcard Assignment."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        assignments = JobCardAssignment.objects.all()
        serializer = JobCardAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager'):
        #     return Response(
        #         {"error": "You are not authorized to Create the Jobcard Assignment."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        serializer = JobCardAssignmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class JobCardAssignmentDetailAPIView(APIView):
    def get(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner' or user.role == 'Mechanic' or user.role == 'Electrician' or user.role == 'Paint Worker' or user.role == 'Bat Lamera'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Jobcard Assignment."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        assignment = get_object_or_404(JobCardAssignment, pk=pk)
        serializer = JobCardAssignmentSerializer(assignment)
        return Response(serializer.data)

    def put(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner' or user.role == 'Mechanic' or user.role == 'Electrician' or user.role == 'Paint Worker' or user.role == 'Bat Lamera'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Jobcard Assignment."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        assignment = get_object_or_404(JobCardAssignment, pk=pk)
        serializer = JobCardAssignmentSerializer(assignment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner' or user.role == 'Mechanic' or user.role == 'Electrician' or user.role == 'Paint Worker' or user.role == 'Bat Lamera'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Jobcard Assignment."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        assignment = get_object_or_404(JobCardAssignment, pk=pk)
        serializer = JobCardAssignmentSerializer(assignment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager'):
        #     return Response(
        #         {"error": "You are not authorized to Delete the Jobcard Assignment."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        assignment = get_object_or_404(JobCardAssignment, pk=pk)
        assignment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ------------------------Each Workers Tasks---------------------------------
class MyAssignedTasksAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        assignments = JobCardAssignment.objects.filter(worker=request.user)
        serializer = JobCardAssignmentLightSerializer(assignments, many=True)
        return Response(serializer.data)

class MyAssignedTasksDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, assignment_id):
        assignment = JobCardAssignment.objects.get(id=assignment_id)
        serializer = JobCardAssignmentLightSerializer(assignment)
        return Response(serializer.data)



class UpdateAssignedServiceStatusAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, assignment_id, service_id):
        try:
            # Convert IDs to integers to ensure type matching
            assignment_id = int(assignment_id)
            service_id = int(service_id)
            
            # First check if assignment exists and is assigned to user
            from django.core.exceptions import ObjectDoesNotExist
            try:
                assignment = JobCardAssignment.objects.get(
                    id=assignment_id,
                    worker=request.user
                )
            except ObjectDoesNotExist:
                return Response(
                    {"detail": "Assignment not found or not assigned to this user."}, 
                    status=404
                )
                
            # Then check if service exists for this assignment
            try:
                assigned_service = AssignedService.objects.get(
                    assignment_id=assignment_id,
                    service__id=service_id
                )
                serializer = AssignedServiceSerializer(assigned_service)
                return Response(serializer.data)
            except AssignedService.DoesNotExist:
                return Response(
                    {"detail": "Service not found for this assignment."}, 
                    status=404
                )
                
        except ValueError:
            return Response(
                {"detail": "Invalid ID format. Assignment and Service IDs must be numbers."},
                status=400
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=500
            )

    def patch(self, request, assignment_id, service_id):
        try:
            assigned_service = AssignedService.objects.get(
                assignment__id=assignment_id,
                service__id=service_id,
                assignment__worker=request.user
            )
        except AssignedService.DoesNotExist:
            return Response({"detail": "Not found or unauthorized."}, status=404)

        new_status = request.data.get('status')
        if new_status not in ['in_progress', 'completed']:
            return Response({"detail": "Invalid status value."}, status=400)

        assigned_service.status = new_status
        if new_status == 'in_progress':
            assigned_service.started_at = timezone.now()
        if new_status == 'completed':
            assigned_service.completed_at = timezone.now()
        assigned_service.save()
        

        return Response({
            "detail": "Status updated.",
            "status": assigned_service.status,
            "started_at": assigned_service.started_at,
            "completed_at": assigned_service.completed_at
        }, status=200)



class UpdateAssignmentPackageStatusAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, assignment_id):
        try:
            # Convert IDs to integers to ensure type matching
            assignment_id = int(assignment_id)
            
            # First check if assignment exists and is assigned to user
            from django.core.exceptions import ObjectDoesNotExist
            try:
                assignment = JobCardAssignment.objects.get(
                    id=assignment_id,
                    worker=request.user
                )
                serializer = JobCardAssignmentSerializer(assignment)
                return Response(serializer.data)
            except ObjectDoesNotExist:
                return Response(
                    {"detail": "Assignment not found or not assigned to this user."}, 
                    status=404
                )
                
        except ValueError:
            return Response(
                {"detail": "Invalid ID format. Assignment and Service IDs must be numbers."},
                status=400
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=500
            )

    def patch(self, request, assignment_id):
        try:
            assignment = JobCardAssignment.objects.get(
                id=assignment_id,
                worker=request.user
            )
        except JobCardAssignment.DoesNotExist:
            return Response({"detail": "Not found or unauthorized."}, status=404)

        new_status = request.data.get('package_status')
        if new_status not in ['in_progress', 'completed']:
            return Response({"detail": "Invalid status value."}, status=400)

        assignment.package_status = new_status
        if new_status == 'in_progress':
            assignment.started_at = timezone.now()
        if new_status == 'completed':
            assignment.completed_at = timezone.now()
        assignment.save()

        if assignment.package_status == 'in_progress':
            assignment.status = 'in_progress'
            assignment.save()

            if assignment.job_card:
                assignment.job_card.status = 'in_progress'
                assignment.job_card.save()
        

        return Response({
            "detail": "Status updated.",
            "status": assignment.package_status,
            "started_at": assignment.started_at,
            "completed_at": assignment.completed_at
        }, status=200)



class ExaminerUpdateAssignedServiceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, assigned_service_id):
        # Examiner permission check
        if request.user.role not in ['Technical Examiner', 'Manager', 'Field Operator'] and not request.user.is_superuser:
            return Response(
                {"detail": "You are not authorized to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )

        assigned_service = get_object_or_404(AssignedService, id=assigned_service_id)

        new_status = request.data.get('status')

        if new_status not in ['in_progress', 'completed']:
            return Response(
                {"detail": "Invalid status."},
                status=status.HTTP_400_BAD_REQUEST
            )

        assigned_service.status = new_status

        if new_status == 'in_progress':
            assigned_service.started_at = timezone.now()
        if new_status == 'completed':
            assigned_service.completed_at = timezone.now()
        else:
            assigned_service.completed_at = None

        assigned_service.save()

        return Response({
            "detail": "Service status updated by examiner.",
            "status": assigned_service.status,
            "started_at": assigned_service.started_at,
            "completed_at": assigned_service.completed_at
        })


class ExaminerUpdateServicePackageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assignment_id):
        try:
            # Convert IDs to integers to ensure type matching
            assignment_id = int(assignment_id)
            
            # First check if assignment exists and is assigned to user
            from django.core.exceptions import ObjectDoesNotExist
            try:
                assignment = JobCardAssignment.objects.get(
                    id=assignment_id,
                )
                serializer = JobCardAssignmentSerializer(assignment)
                return Response(serializer.data)
            except ObjectDoesNotExist:
                return Response(
                    {"detail": "Assignment not found or not assigned to this user."}, 
                    status=404
                )
                
        except ValueError:
            return Response(
                {"detail": "Invalid ID format. Assignment and Service IDs must be numbers."},
                status=400
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=500
            )

    def patch(self, request, assignment_id):
        if request.user.role not in ['Technical Examiner', 'Manager', 'Field Operator'] and not request.user.is_superuser:
            return Response(
                {"detail": "You are not authorized to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )

        assignment = get_object_or_404(JobCardAssignment, id=assignment_id)

        new_status = request.data.get('package_status')
        if new_status not in ['in_progress', 'completed']:
            return Response({"detail": "Invalid status value."}, status=400)

        assignment.package_status = new_status
        if new_status == 'in_progress':
            assignment.started_at = timezone.now()
        if new_status == 'completed':
            assignment.completed_at = timezone.now()
        assignment.save()

        if assignment.package_status == 'in_progress':
            assignment.status = 'in_progress'
            assignment.save()

            if assignment.job_card:
                assignment.job_card.status = 'in_progress'
                assignment.job_card.save()
        

        return Response({
            "detail": "Status updated.",
            "status": assignment.package_status,
            "started_at": assignment.started_at,
            "completed_at": assignment.completed_at
        }, status=200)



class AssignmentVerificationAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, assignment_id):
        assignment = get_object_or_404(JobCardAssignment, id=assignment_id)
        if request.user.role not in ['Technical Examiner', 'Manager'] and not request.user.is_superuser:
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = JobCardAssignmentSerializer(assignment)
        return Response(serializer.data)

    def patch(self, request, assignment_id):
        assignment = get_object_or_404(JobCardAssignment, id=assignment_id)

        # Optional: check user has examiner role
        if request.user.role not in ['Technical Examiner', 'Manager'] and not request.user.is_superuser:
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        try:
            if assignment.service_package is not None:
                print("service_package")
                # Check if services packages in this assignment are completed
                incomplete_services_package = assignment.package_status !='completed'
                if incomplete_services_package:
                    return Response({"detail": "service packages is not completed."}, status=400)

                # Mark the assignment as completed/verified
                new_status = request.data.get('status')
                comment = request.data.get('examiner_comment', '')  

                if new_status not in ['completed', 'verified']:
                    return Response({"detail": "Invalid status."}, status=400)

                assignment.status = new_status
                assignment.examiner_comment = comment
                assignment.save()
                

                return Response({
                    "detail": "Assignment package status updated.",
                    "status": assignment.status,
                    "examiner_comment": assignment.examiner_comment
                }, status=200)

            else:
                print("assigned_services")
                # Check if all services in this assignment are completed
                incomplete_services = assignment.assigned_services.filter(status__in=['in_progress', 'scheduled'])
                if incomplete_services.exists():
                    return Response({"detail": "Not all assigned services are completed."}, status=400)

                # Mark the assignment as completed/verified
                new_status = request.data.get('status')
                comment = request.data.get('examiner_comment', '')

                if new_status not in ['completed', 'verified']:
                    return Response({"detail": "Invalid status."}, status=400)

                assignment.status = new_status
                assignment.examiner_comment = comment
                assignment.save()

                return Response({
                    "detail": "Assignment status updated.",
                    "status": assignment.status,
                    "examiner_comment": assignment.examiner_comment
                }, status=200)
        except Exception as e:
            print(e)
            return Response({"detail": str(e)}, status=500)


# ------------------ Invoice ------------------
class InvoiceListCreateAPIView(APIView):
    def get(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Cashier'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Invoice."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        


        search_query = request.query_params.get('search', None)
        include_all = request.query_params.get('include_all', '').lower() in ('1', 'true', 'yes')

        invoices = Invoice.objects.all()
        
        # Apply search
        if search_query:
            invoices = invoices.filter(
                Q(job_card__id__icontains=search_query) |
                Q(job_card__customer__name__icontains=search_query)
            )

        # Ensure consistent ordering for pagination
        invoices = invoices.order_by('-id')  # or '-id'

         # Paginate
        paginator = Pagination()
        page = paginator.paginate_queryset(invoices, request)
        if page is not None:
            page_data = InvoiceSerializer(page, many=True).data
            if include_all:
                all_data = InvoiceSerializer(invoices, many=True).data
                return Response({
                    'count': paginator.page.paginator.count,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link(),
                    'results': page_data,
                    'all_results': all_data,
                })
            return paginator.get_paginated_response(page_data)

        # Fallback - no pagination applied
        serializer = InvoiceSerializer(invoices, many=True)
        return Response(serializer.data)


    def post(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Cashier'):
        #     return Response(
        #         {"error": "You are not authorized to Create the Invoice."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        serializer = InvoiceSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InvoiceDetailAPIView(APIView):
    def get(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Cashier'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Invoice."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        invoice = get_object_or_404(Invoice, pk=pk)
        serializer = InvoiceGetSerializer(invoice)
        return Response(serializer.data)

    def put(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Cashier'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Invoice."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        invoice = get_object_or_404(Invoice, pk=pk)
        serializer = InvoiceSerializer(invoice, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Cashier'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Invoice."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        invoice = get_object_or_404(Invoice, pk=pk)
        serializer = InvoiceSerializer(invoice, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Cashier'):
        #     return Response(
        #         {"error": "You are not authorized to Delete the Invoice."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        invoice = get_object_or_404(Invoice, pk=pk)
        invoice.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvoiceReceiptAPIView(APIView):
    def get(self, request, pk):
        try:
            # 1. Single database fetch for Invoice with pre-fetched job_card and all nested relations
            invoice = get_object_or_404(
                Invoice.objects.select_related(
                    'job_card__customer',
                    'job_card__vehicle'
                ).prefetch_related(
                    'job_card__assignments__services',
                    'job_card__assignments__worker',
                    'job_card__assignments__assigned_services'
                ),
                id=pk
            )

            # 2. Retrieve Company Information
            company = CompanyInfo.objects.first()

            # 3. Serialize the invoice with all nested data using InvoiceGetSerializer
            serializer = InvoiceGetSerializer(invoice)
            invoice_data = serializer.data

            # 4. Add company info to the response
            receipt_data = {
                "company": {
                    "en_name": company.en_name if company and company.en_name else "Company",
                    "am_name": company.am_name if company and company.am_name else "Company",
                    "email": company.email if company and company.email else "",
                    "phone": company.phone1 if company and company.phone1 else "",
                    "tin_number": company.tin_number if company and company.tin_number else "",
                    "vat_number": company.vat_number if company and company.vat_number else "",
                    "bank_accounts": company.bank_accounts if company and company.bank_accounts else {},
                    "country": company.country if company and company.country else "",
                    "region": company.region if company and company.region else "",
                    "zone": company.zone if company and company.zone else "",
                    "city": company.city if company and company.city else "",
                    "sub_city": company.sub_city if company and company.sub_city else "",
                    "logo": company.logo.url if company and company.logo else None
                },
                **invoice_data
            }

            return Response(receipt_data, status=status.HTTP_200_OK)

        except Invoice.DoesNotExist:
            return Response(
                {"error": "Invoice record does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred while retrieving the Invoice Receipt: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
# New Perfoma Views
class PerformaPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user and (getattr(user, "role", None) == "Manager" or user.is_superuser or user.role == 'Assistant Manager' or user.role == 'Customer Officer')


class PerformaCustomerListCreateView(generics.ListCreateAPIView):
    queryset = PerformaCustomer.objects.all().order_by('-id')
    permission_classes = [PerformaPermission]
    serializer_class = PerformaCustomerSerializer
    pagination_class = Pagination
    filter_backends = [filters.SearchFilter]  # enable search
    search_fields = ['customer__organization']  # fields to search in

    def get_queryset(self):
        # only fetch id, name, email from the DB
        return PerformaCustomer.objects.only('id', 'customer__organization', 'user').select_related('customer').order_by('-id')


    def get_serializer_class(self):
        # Use light serializer for list, full serializer for create
        if self.request.method == 'GET':
            return PerformaCustomerLightSerializer
        return PerformaCustomerSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        id = response.data.get('performas')[0]['id']
        id = str(id).zfill(4)
        return Response({
            "message": "Performa Customer created successfully.",
            "data": response.data,
            "id": id
        }, status=status.HTTP_201_CREATED)

class PerformaCustomerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PerformaCustomer.objects.all()
    permission_classes = [PerformaPermission]
    serializer_class = PerformaCustomerSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Lightweight customer (avoid heavy nested performas)
        customer_data = PerformaCustomerLightSerializer(instance).data

        # Query and paginate related performas (light fields)
        performas_qs = (
            instance.performas.only(
                'id', 'issued_date', 'customer', 'receipt', 'shanci_kutir', 'targa_kutir', 'service_charge', 'products_service_charge', 'sub_total', 'vat', 'total', 'user'
            )
            .order_by('-id')
        )

        # Optional search
        search_query = request.query_params.get('search')
        if search_query:
            performas_qs = performas_qs.filter(
                Q(customer__icontains=search_query) |
                Q(shanci_kutir__icontains=search_query) |
                Q(targa_kutir__icontains=search_query)
            )

        paginator = Pagination()
        page = paginator.paginate_queryset(performas_qs, request)
        results = PerformaPerformaLightSerializer(page or performas_qs, many=True).data

        # zero-padded latest performa id (most recent by desc)
        padded_id = None
        if results:
            latest_id = results[0]['id']
            padded_id = str(latest_id).zfill(4)

        if page is not None:
            return Response({
                "message": "Performa Customer retrived successfully.",
                "data": customer_data,
                "performas": {
                    "count": paginator.page.paginator.count,
                    "next": paginator.get_next_link(),
                    "previous": paginator.get_previous_link(),
                    "results": results,
                },
                "id": padded_id
            }, status=status.HTTP_200_OK)

        # Fallback without pagination
        return Response({
            "message": "Performa Customer retrived successfully.",
            "data": customer_data,
            "performas": {
                "count": len(results),
                "next": None,
                "previous": None,
                "results": results,
            },
            "id": padded_id
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        id = response.data.get('performas')[-1]['id']
        id = str(id).zfill(4)
        return Response({
            "message": "Performa Customer updated successfully.",
            "data": response.data,
            "id": id
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({"message": "Performa Customer Deleted successfully."}, status=status.HTTP_200_OK)


class PerformaPerformaListCreateView(generics.ListCreateAPIView):
    queryset = PerformaPerforma.objects.all().order_by('-id')
    permission_classes = [PerformaPermission]
    serializer_class = PerformaPerformaSerializer
    pagination_class = Pagination
    filter_backends = [filters.SearchFilter]  # enable search
    search_fields = ['customer', 'shanci_kutir', 'targa_kutir']  # fields to search in
    

    def get_queryset(self):
        # only fetch id, name, email from the DB
        return PerformaPerforma.objects.only('id', 'issued_date', 'customer', 'receipt', 'shanci_kutir', 'targa_kutir', 'service_charge', 'products_service_charge', 'sub_total', 'vat', 'total', 'user').order_by('-id')


    def get_serializer_class(self):
        # Use light serializer for list, full serializer for create
        if self.request.method == 'GET':
            return PerformaPerformaLightSerializer
        return PerformaPerformaSerializer


    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "message": "Performa Performa created successfully.",
            "data": response.data
        }, status=status.HTTP_201_CREATED)

class PerformaPerformaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PerformaPerforma.objects.all()
    permission_classes = [PerformaPermission]
    serializer_class = PerformaPerformaSerializer

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        id = response.data.get('id')
        id = str(id).zfill(4)
        return Response({
            "message": "Performa Performa retrived successfully.",
            "data": response.data,
            "id": id
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response({
            "message": "Performa Performa updated successfully.",
            "data": response.data
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({"message": "Performa Performa Deleted successfully."}, status=status.HTTP_200_OK)


class PerformaProductListCreateView(generics.ListCreateAPIView):
    queryset = PerformaProduct.objects.all()
    permission_classes = [PerformaPermission]
    serializer_class = PerformaProductSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "message": "Performa Product created successfully.",
            "data": response.data
        }, status=status.HTTP_201_CREATED)

class PerformaProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PerformaProduct.objects.all()
    permission_classes = [PerformaPermission]
    serializer_class = PerformaProductSerializer

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response({
            "message": "Performa Products updated successfully.",
            "data": response.data
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({"message": "Performa Products Deleted successfully."}, status=status.HTTP_200_OK)

# ------------------ Performa to Order Conversion API ------------------

class ConvertPerformaToOrderAPIView(APIView):
    """
    Converts a PerformaPerforma into an Order by resolving Customer via customer_level_id,
    copies line items from performa.products, and deducts product stock.
    """
    def post(self, request, performa_id):
        # Prefetch customer_level_id -> customer in 1 database query
        performa = get_object_or_404(
            PerformaPerforma.objects.select_related('customer_level__customer'), 
            id=performa_id
        )

        try:
            with transaction.atomic():
                # Step 1: Traverse PerformaPerforma -> customer_level_id (PerformaCustomer) -> customer (Customer)
                performa_customer_instance = performa.customer_level
                
                if not performa_customer_instance or not performa_customer_instance.customer:
                    return Response(
                        {"error": "Cannot create Order: No valid Customer found on this Performa's customer_level_id."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                actual_customer = performa_customer_instance.customer

                # Step 2: Create the Order instance
                new_order = Order.objects.create(
                    customer=actual_customer,
                    receipt=performa.receipt or 'Receipt',
                    sub_total=performa.sub_total,
                    vat=performa.vat,
                    total_amount=performa.total,
                    credit=False,
                    performa=True,
                    status='Done',
                    payment_status='Paid',
                    paid_amount=performa.total,
                    unpaid_amount=0,
                    number_of_items=performa.number_of_items,
                    user=getattr(request.user, 'username', performa.user or 'User'),
                    user_email=getattr(request.user, 'email', 'User@gmail.com'),
                    user_role=getattr(request.user, 'role', 'Salesman'),
                )

                # Step 3: Fetch linked products using related_name='products'
                performa_products = performa.products.all()
                if not performa_products.exists():
                    return Response(
                        {"error": "This Performa contains no products to convert."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                order_items = []
                for perf_item in performa_products:
                    product_obj = perf_item.product
                    product_stock = product_obj.stock if product_obj.stock is not None else 0

                    # Stock validation & deduction
                    if perf_item.quantity > product_stock:
                        raise ValueError(
                            f"Insufficient stock for product '{getattr(product_obj, 'name', product_obj.id)}'. "
                            f"Available: {product_stock}, Required: {perf_item.quantity}"
                        )
                    product_obj.stock -= perf_item.quantity
                    product_obj.save(update_fields=['stock'])

                    # Prepare OrderItem
                    order_items.append(
                        OrderItem(
                            order=new_order,
                            product=product_obj,
                            product_price=perf_item.unit_price,
                            unit_price=perf_item.unit_price,
                            quantity=perf_item.quantity,
                            price=perf_item.quantity * perf_item.unit_price,
                            unit=perf_item.unit,
                            item_receipt=performa.receipt,
                            status='Done'
                        )
                    )

                # Bulk insert items into database
                OrderItem.objects.bulk_create(order_items)

                # Step 4: Return response
                serializer = OrderSerializer(new_order)
                return Response(
                    {
                        "message": "Order successfully created from Performa.",
                        "data": serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )

        except ValueError as val_err:
            return Response(
                {"error": str(val_err)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"error": f"An unexpected error occurred during conversion: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ------------------ Performa to Credit Conversion API ------------------

# class ConvertPerformaToCreditAPIView(APIView):
#     """
#     Converts a PerformaPerforma into Credit by resolving Customer via customer_level_id,
#     copies line items from performa.products, and deducts product stock.
#     """
#     def post(self, request, performa_id):
#         # Prefetch customer_level_id -> customer in 1 database query
#         performa = get_object_or_404(
#             PerformaPerforma.objects.select_related('customer_level__customer'), 
#             id=performa_id
#         )

#         try:
#             with transaction.atomic():
#                 # Step 1: Traverse PerformaPerforma -> customer_level_id (PerformaCustomer) -> customer (Customer)
#                 performa_customer_instance = performa.customer_level
                
#                 if not performa_customer_instance or not performa_customer_instance.customer:
#                     return Response(
#                         {"error": "Cannot create Credit: No valid Customer found on this Performa's customer_level_id."},
#                         status=status.HTTP_400_BAD_REQUEST
#                     )

#                 actual_customer = performa_customer_instance.customer

#                 # Step 2: Create the Order instance
#                 new_order = Order.objects.create(
#                     customer=actual_customer,
#                     receipt=performa.receipt or 'Receipt',
#                     sub_total=performa.sub_total,
#                     vat=performa.vat,
#                     total_amount=performa.total,
#                     credit=True,
#                     status='Pending',
#                     payment_status='Unpaid',
#                     paid_amount=0,
#                     unpaid_amount=performa.total,
#                     user=getattr(request.user, 'username', performa.user or 'User'),
#                     user_email=getattr(request.user, 'email', 'User@gmail.com'),
#                     user_role=getattr(request.user, 'role', 'Salesman'),
#                 )

#                 # Step 3: Fetch linked products using related_name='products'
#                 performa_products = performa.products.all()
#                 if not performa_products.exists():
#                     return Response(
#                         {"error": "This Performa contains no products to convert."},
#                         status=status.HTTP_400_BAD_REQUEST
#                     )

#                 order_items = []
#                 for perf_item in performa_products:
#                     product_obj = perf_item.product

#                     # Stock validation & deduction
#                     if hasattr(product_obj, 'quantity'):
#                         if product_obj.quantity < perf_item.quantity:
#                             raise ValueError(
#                                 f"Insufficient stock for product '{getattr(product_obj, 'name', product_obj.id)}'. "
#                                 f"Available: {product_obj.quantity}, Required: {perf_item.quantity}"
#                             )
#                         product_obj.quantity -= perf_item.quantity
#                         product_obj.save(update_fields=['quantity'])

#                     # Prepare OrderItem
#                     order_items.append(
#                         OrderItem(
#                             order=new_order,
#                             product=product_obj,
#                             product_price=perf_item.unit_price,
#                             unit_price=perf_item.unit_price,
#                             quantity=perf_item.quantity,
#                             price=perf_item.quantity * perf_item.unit_price,
#                             unit=perf_item.unit,
#                             item_receipt=performa.receipt,
#                             status='Pending'
#                         )
#                     )

#                 # Bulk insert items into database
#                 OrderItem.objects.bulk_create(order_items)

#                 # Step 4: Return response
#                 serializer = OrderSerializer(new_order)
#                 return Response(
#                     {
#                         "message": "Credit successfully created from Performa.",
#                         "data": serializer.data
#                     },
#                     status=status.HTTP_201_CREATED
#                 )

#         except ValueError as val_err:
#             return Response(
#                 {"error": str(val_err)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         except Exception as e:
#             traceback.print_exc()
#             return Response(
#                 {"error": f"An unexpected error occurred during conversion: {str(e)}"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

class ConvertPerformaToCreditAPIView(APIView):
    """
    Converts a PerformaPerforma instance to a Credit record, handles or creates 
    the parent CreditCustomer, deducts product stock, and updates credit balances.
    """
    def post(self, request, performa_id):
        # Prefetch customer_level_id -> customer in 1 DB query
        performa = get_object_or_404(
            PerformaPerforma.objects.select_related('customer_level__customer'), 
            id=performa_id
        )

        try:
            with transaction.atomic():
                # 1. Resolve target Customer instance
                performa_customer_instance = performa.customer_level
                if not performa_customer_instance or not performa_customer_instance.customer:
                    return Response(
                        {"error": "Cannot convert to Credit: No valid Customer assigned to this Performa."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                customer_obj = performa_customer_instance.customer

                # 2. Get or Create parent CreditCustomer for this Customer
                credit_customer, created = CreditCustomer.objects.get_or_create(
                    customer=customer_obj,
                    defaults={
                        'total_amount': Decimal('0.00'),
                        'paid_amount': Decimal('0.00'),
                        'unpaid_amount': Decimal('0.00'),
                        'payment_status': 'Pending',
                        'user': getattr(request.user, 'username', performa.user or 'Admin')
                    }
                )

                # 3. Create the Credit entry (Header level)
                new_credit = CreditCredit.objects.create(
                    customer_level=credit_customer,  # FK pointing to CreditCustomer
                    customer=performa.customer,
                    receipt=performa.receipt or 'Receipt',
                    performa=True,
                    sub_total=performa.sub_total,
                    vat=performa.vat,
                    total=performa.total,
                    payment_status='Pending',
                    paid_amount=Decimal('0.00'),
                    unpaid_amount=performa.total,
                    user=getattr(request.user, 'username', performa.user or 'User'),
                    number_of_items=performa.number_of_items
                )

                # 4. Fetch line items and deduct stock
                performa_products = performa.products.all()
                if not performa_products.exists():
                    return Response(
                        {"error": "This Performa contains no products to convert."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                credit_products = []
                for perf_item in performa_products:
                    product_obj = perf_item.product
                    product_stock = product_obj.stock if product_obj.stock is not None else 0

                    # Stock validation & deduction
                    if perf_item.quantity > product_stock:
                        raise ValueError(
                            f"Insufficient stock for product '{getattr(product_obj, 'name', product_obj.id)}'. "
                            f"Available: {product_stock}, Required: {perf_item.quantity}"
                        )
                    product_obj.stock -= perf_item.quantity
                    product_obj.save(update_fields=['stock'])

                    # # Stock Check & Deduction
                    # if hasattr(product_obj, 'quantity'):
                    #     if product_obj.quantity < perf_item.quantity:
                    #         raise ValueError(
                    #             f"Insufficient stock for product '{getattr(product_obj, 'name', product_obj.id)}'. "
                    #             f"Available: {product_obj.quantity}, Required: {perf_item.quantity}"
                    #         )
                    #     product_obj.quantity -= perf_item.quantity
                    #     product_obj.save(update_fields=['quantity'])

                    # Prepare CreditProduct record
                    credit_products.append(
                        CreditProduct(
                            credit=new_credit,
                            product=product_obj,
                            part_number=perf_item.part_number,
                            unit=perf_item.unit,
                            description=perf_item.description or '',
                            quantity=perf_item.quantity,
                            unit_price=perf_item.unit_price,
                            total_price=perf_item.quantity * perf_item.unit_price
                        )
                    )

                # Bulk insert credit items
                CreditProduct.objects.bulk_create(credit_products)

                # 5. Update CreditCustomer aggregated running balance
                credit_customer.total_amount += performa.total
                credit_customer.unpaid_amount += performa.total
                credit_customer.save(update_fields=['total_amount', 'unpaid_amount'])

                # 6. Return response
                serializer = CreditCreditSerializer(new_credit)
                return Response(
                    {
                        "message": "Credit generated successfully from Performa.",
                        "data": serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )

        except ValueError as val_err:
            return Response(
                {"error": str(val_err)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"error": f"An unexpected error occurred during credit conversion: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ------------------ Vehicle Acceptance ------------------
class VehicleAcceptanceListCreateAPIView(APIView):
    def get(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Receptionist' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Vehicle Acceptance."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        search_query = request.query_params.get('search', None)

        # Use select_related to avoid N+1 when accessing customer fields
        acceptance = VehicleAcceptance.objects.only('id', 'customer__name', 'vehicle__model', 'vehicle__shanci_kutir', 'vehicle__motor_kutir', 'ken', 'user').select_related('customer').all()

        # Apply search
        if search_query:
            acceptance = acceptance.filter(
                Q(customer__name__icontains=search_query) |
                Q(vehicle__model__icontains=search_query) |
                Q(vehicle__shanci_kutir__icontains=search_query) |
                Q(vehicle__motor_kutir__icontains=search_query)
            )

        # Ensure consistent ordering for pagination
        acceptance = acceptance.order_by('-ken')  # or '-id'

        # Paginate
        paginator = Pagination()
        page = paginator.paginate_queryset(acceptance, request)
        if page is not None:
            serializer = VehicleAcceptanceLightSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # Fallback - no pagination applied
        serializer = VehicleAcceptanceLightSerializer(acceptance, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Receptionist' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to Create the Vehicle Acceptance."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        serializer = VehicleAcceptanceSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VehicleAcceptanceDetailAPIView(APIView):
    def get(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Receptionist' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Vehicle Acceptance."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        vehicle_acceptance = get_object_or_404(VehicleAcceptance, pk=pk)
        serializer = VehicleAcceptanceSerializer(vehicle_acceptance)
        return Response(serializer.data)

    def put(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Receptionist' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Vehicle Acceptance."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        vehicle_acceptance = get_object_or_404(VehicleAcceptance, pk=pk)
        serializer = VehicleAcceptanceSerializer(vehicle_acceptance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Receptionist' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Vehicle Acceptance."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        vehicle_acceptance = get_object_or_404(VehicleAcceptance, pk=pk)
        serializer = VehicleAcceptanceSerializer(vehicle_acceptance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Receptionist' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to Delete the Vehicle Acceptance."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        vehicle_acceptance = get_object_or_404(VehicleAcceptance, pk=pk)
        vehicle_acceptance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ------------------ Vehicle Old Part Delivery ------------------
class VehicleOldPartDeliveryListCreateAPIView(APIView):
    def get(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Vehicle Old Part Delivery."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        search_query = request.query_params.get('search', None) 

        # Use select_related to avoid N+1 when accessing terekabi fields
        old_part = VehicleOldPartDelivery.objects.only('id', 'tegagn_mechanic__name', 'vehicle__model', 'vehicle__license_plate', 'ken', 'asrekabi_sim__name', 'terekabi_sim__name', 'terekabi_sim__phone', 'user', 'job_card').select_related('terekabi_sim').all()


        # Apply search
        if search_query:
            old_part = old_part.filter(
                Q(terekabi_sim__name__icontains=search_query) |
                Q(vehicle__shanci_kutir__icontains=search_query) |
                Q(vehicle__license_plate__icontains=search_query)
            )
 
        # Ensure consistent ordering for pagination
        old_part = old_part.order_by('-ken')  # or '-id'

        # Paginate
        paginator = Pagination()
        page = paginator.paginate_queryset(old_part, request)
        if page is not None:
            serializer = VehicleOldPartDeliveryLightSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # Fallback - no pagination applied
        serializer = VehicleOldPartDeliveryLightSerializer(old_part, many=True)
        return Response(serializer.data)


    def post(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to Create the Vehicle Old Part Delivery."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        serializer = VehicleOldPartDeliverySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VehicleOldPartDeliveryDetailAPIView(APIView):
    def get(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Vehicle Old Part Delivery."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        delivery = get_object_or_404(VehicleOldPartDelivery, pk=pk)
        serializer = VehicleOldPartDeliverySerializer(delivery)
        return Response(serializer.data)

    def put(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Vehicle Old Part Delivery."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        delivery = get_object_or_404(VehicleOldPartDelivery, pk=pk)
        serializer = VehicleOldPartDeliverySerializer(delivery, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Vehicle Old Part Delivery."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        delivery = get_object_or_404(VehicleOldPartDelivery, pk=pk)
        serializer = VehicleOldPartDeliverySerializer(delivery, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Vehicle Old Part Delivery."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        delivery = get_object_or_404(VehicleOldPartDelivery, pk=pk)
        delivery.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    


# ------------------ Vehicle Old Part Item Delivery ------------------
class VehicleOldPartDeliveryItemsListCreateAPIView(APIView):
    def get(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Vehicle Old Part Delivery Item."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        items = VehicleOldPartDeliveryItems.objects.all()
        serializer = VehicleOldPartDeliveryItemsSerializer(items, many=True)
        return Response(serializer.data)

class VehicleOldPartDeliveryItemsDetailAPIView(APIView):
    def get(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Vehicle Old Part Delivery Item."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        item = get_object_or_404(VehicleOldPartDeliveryItems, pk=pk)
        serializer = VehicleOldPartDeliveryItemsSerializer(item)
        return Response(serializer.data)

    def put(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Vehicle Old Part Delivery Item."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        item = get_object_or_404(VehicleOldPartDeliveryItems, pk=pk)
        serializer = VehicleOldPartDeliveryItemsSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Vehicle Old Part Delivery Item."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        item = get_object_or_404(VehicleOldPartDeliveryItems, pk=pk)
        serializer = VehicleOldPartDeliveryItemsSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to Delete the Vehicle Old Part Delivery Item."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        item = get_object_or_404(VehicleOldPartDeliveryItems, pk=pk)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



# ------------------ Vehicle Order Voucher ------------------
class VehicleOrderVoucherListCreateAPIView(APIView):
    def get(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Vehicle Order Voucher."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        search_query = request.query_params.get('search', None)

        # Use select_related to avoid N+1 when accessing customer fields
        order_voucher = VehicleOrderVoucher.objects.only('id', 'customer', 'vehicle', 'customer__name', 'customer__phone', 'vehicle__model', 'vehicle__license_plate', 'ken', 'asrekabi_sim__name', 'terekabi_sim__name', 'user', 'job_card').select_related('customer').all()

        # Apply search
        if search_query:
            order_voucher = order_voucher.filter(
                Q(customer__name__icontains=search_query) |
                Q(vehicle__shanci_kutir__icontains=search_query) |
                Q(vehicle__motor_kutir__icontains=search_query)
            )

        # Ensure consistent ordering for pagination
        order_voucher = order_voucher.order_by('-ken')  # or '-id'

        # Paginate
        paginator = Pagination()
        page = paginator.paginate_queryset(order_voucher, request)
        if page is not None:
            serializer = VehicleOrderVoucherLightSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # Fallback - no pagination applied
        serializer = VehicleOrderVoucherLightSerializer(order_voucher, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to Create the Vehicle Order Voucher."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        serializer = VehicleOrderVoucherSerializer(data=request.data, context={'request': request})
        print(serializer)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VehicleOrderVoucherDetailAPIView(APIView):
    def get(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Vehicle Order Voucher."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        voucher = get_object_or_404(VehicleOrderVoucher, pk=pk)
        serializer = VehicleOrderVoucherSerializer(voucher)
        return Response(serializer.data)

    def put(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Vehicle Order Voucher."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        voucher = get_object_or_404(VehicleOrderVoucher, pk=pk)
        serializer = VehicleOrderVoucherSerializer(voucher, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Vehicle Order Voucher."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        voucher = get_object_or_404(VehicleOrderVoucher, pk=pk)
        serializer = VehicleOrderVoucherSerializer(voucher, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to Delete the Vehicle Order Voucher."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        voucher = get_object_or_404(VehicleOrderVoucher, pk=pk)
        voucher.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    


# ------------------ Vehicle Order Voucher Items ------------------
class VehicleOrderVoucherItemsListCreateAPIView(APIView):
    def get(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Vehicle Order Voucher Item."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        items = VehicleOrderVoucherItems.objects.all()
        serializer = VehicleOrderVoucherItemsSerializer(items, many=True)
        return Response(serializer.data)

class VehicleOrderVoucherItemsDetailAPIView(APIView):
    def get(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Vehicle Order Voucher Item."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        item = get_object_or_404(VehicleOrderVoucherItems, pk=pk)
        serializer = VehicleOrderVoucherItemsSerializer(item)
        return Response(serializer.data)

    def put(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Vehicle Order Voucher Item."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        item = get_object_or_404(VehicleOrderVoucherItems, pk=pk)
        serializer = VehicleOrderVoucherItemsSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Vehicle Order Voucher Item."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        item = get_object_or_404(VehicleOrderVoucherItems, pk=pk)
        serializer = VehicleOrderVoucherItemsSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator'):
        #     return Response(
        #         {"error": "You are not authorized to Delete the Vehicle Order Voucher Item."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        item = get_object_or_404(VehicleOrderVoucherItems, pk=pk)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    


# ------------------ Vehicle part request ------------------

class VehiclePartRequestListCreateAPIView(APIView):
    def get(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Store Manager'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Vehicle Part Request."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        search_query = request.query_params.get('search', None)

        # Use select_related to avoid N+1 when accessing customer fields
        part_requests = VehiclePartRequest.objects.only('id', 'customer__name', 'customer__phone', 'vehicle__model', 'vehicle__license_plate', 'ken', 'asrekabi_sim__name', 'terekabi_sim__name', 'total_amount', 'user', 'job_card').select_related('customer').all()

        # Apply search
        if search_query:
            part_requests = part_requests.filter(
                Q(customer__name__icontains=search_query) |
                Q(vehicle__shanci_kutir__icontains=search_query) |
                Q(vehicle__motor_kutir__icontains=search_query)
            )

        # Ensure consistent ordering for pagination
        part_requests = part_requests.order_by('-ken')  # or '-id'

        # Paginate
        paginator = Pagination()
        page = paginator.paginate_queryset(part_requests, request)
        if page is not None:
            serializer = VehiclePartRequestLightSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # Fallback - no pagination applied
        serializer = VehiclePartRequestLightSerializer(part_requests, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Store Manager'):
        #     return Response(
        #         {"error": "You are not authorized to Create the Vehicle Part Request."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        serializer = VehiclePartRequestSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class VehiclePartRequestDetailAPIView(APIView):
    def get(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Store Manager'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Vehicle Part Request."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        part_request = get_object_or_404(VehiclePartRequest, pk=pk)
        serializer = VehiclePartRequestSerializer(part_request)
        return Response(serializer.data)

    def put(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Store Manager'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Vehicle Part Request."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        part_request = get_object_or_404(VehiclePartRequest, pk=pk)
        serializer = VehiclePartRequestSerializer(part_request, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Store Manager'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Vehicle Part Request."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        part_request = get_object_or_404(VehiclePartRequest, pk=pk)
        serializer = VehiclePartRequestSerializer(part_request, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Store Manager'):
        #     return Response(
        #         {"error": "You are not authorized to Delete the Vehicle Part Request."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        part_request = get_object_or_404(VehiclePartRequest, pk=pk)
        part_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    


# ------------------ Vehicle part request items ------------------
class VehiclePartRequestItemsListCreateAPIView(APIView):
    def get(self, request):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Store Manager'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Vehicle Part Request Items."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        part_request_items = VehiclePartRequestItems.objects.all()
        serializer = VehiclePartRequestItemsSerializer(part_request_items, many=True)
        return Response(serializer.data)

class VehiclePartRequestItemsDetailAPIView(APIView):
    def get(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Store Manager'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Vehicle Part Request Items."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        part_request_item = get_object_or_404(VehiclePartRequestItems, pk=pk)
        serializer = VehiclePartRequestItemsSerializer(part_request_item)
        return Response(serializer.data)

    def put(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Store Manager'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Vehicle Part Request Items."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        part_request_item = get_object_or_404(VehiclePartRequestItems, pk=pk)
        serializer = VehiclePartRequestItemsSerializer(part_request_item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Store Manager'):
        #     return Response(
        #         {"error": "You are not authorized to Update the Vehicle Part Request Items."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        part_request_item = get_object_or_404(VehiclePartRequestItems, pk=pk)
        serializer = VehiclePartRequestItemsSerializer(part_request_item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Store Manager'):
        #     return Response(
        #         {"error": "You are not authorized to Delete the Vehicle Part Request Items."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        part_request_item = get_object_or_404(VehiclePartRequestItems, pk=pk)
        part_request_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    




# ------------------ From Tokiyo Category, Supplier, Product, CompanyInfo, Order and OrderItem ------------------
class ProductListCreateAPIView(APIView):
    def get(self, request, format=None):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Store Manager' or user.role == 'Field Operator'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Product."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            
            search_query = request.query_params.get('search', None)
            include_all = request.query_params.get('include_all', '').lower() in ('1', 'true', 'yes')

            products = Product.objects.all()
            all_products = Product.objects.only('name', 'part_number', 'selling_price', 'stock').all()
            
            # Apply search
            if search_query:
                products = products.filter(
                    Q(name__icontains=search_query)
                )

            # Ensure consistent ordering for pagination
            products = products.order_by('-id')  # or '-id'

            # Paginate
            paginator = Pagination()
            page = paginator.paginate_queryset(products, request)
            if page is not None:
                page_data = ProductGetSerializer(page, many=True).data
                if include_all:
                    all_data = ProductLightSerializer(all_products, many=True).data
                    return Response({
                        'count': paginator.page.paginator.count,
                        'next': paginator.get_next_link(),
                        'previous': paginator.get_previous_link(),
                        'results': page_data,
                        'all_results': all_data,
                    })
                return paginator.get_paginated_response(page_data)

            # Fallback - no pagination applied
            serializer = ProductGetSerializer(products, many=True)
            return Response(serializer.data)
            
                      
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Product.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, format=None):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Store Manager'):
            #     return Response(
            #         {"error": "You are not authorized to create the Product."},
            #         status=status.HTTP_403_FORBIDDEN
            #      )   
            serializer = ProductPostSerializer(data=request.data)
            if not serializer.is_valid():
                print(serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            validated_data = serializer.validated_data
            serializer.create(validated_data, user=request.user)
            return Response({"message": f"Product Created successfully."}, status=status.HTTP_201_CREATED)

        except IntegrityError:
            return Response(
                {"error": "A product with this name and category already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except KeyError as e:
            print(e)
            return Response(
                {"error": f"An error occurred while creating the Product. Missing field: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print(e)
            return Response(
                {"error": f"An unexpected error occurred while creating the Product. {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ProductRetrieveUpdateDeleteAPIView(APIView):
    def get(self, request, pk):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Store Manager' or user.role == 'Field Operator'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Product."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )               
            if not Product.objects.filter(id=pk).exists():
                return Response(
                    {"error": "Product Does not Exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            product = Product.objects.get(id=pk)
            serializer = ProductGetSerializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK)      
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Product.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    def put(self, request, pk):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Store Manager'):
            #     return Response(
            #         {"error": "You are not authorized to update the Product."},
            #         status=status.HTTP_403_FORBIDDEN
            #     ) 
            if not Product.objects.filter(id=pk).exists():
                return Response(
                    {"error": "Product Does not Exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            product = Product.objects.get(id=pk)
            serializer = ProductPostSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            validated_data = serializer.validated_data
            validated_data['user'] = user
            serializer.update(product, validated_data)
            return Response({"message": f"Product Updated successfully."}, status=status.HTTP_200_OK)        
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while updating the Product.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request, pk):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Store Manager'):
            #     return Response(
            #         {"error": "You are not authorized to update the Product."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )          
            if not Product.objects.filter(id=pk).exists():
                return Response(
                    {"error": "Product Does not Exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            product = Product.objects.get(id=pk)    
            serializer = ProductPostSerializer(product, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response({"message": f"Product Updated successfully."}, status=status.HTTP_200_OK)      
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while updating the Product.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    def delete(self, request, pk):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Store Manager'):
            #     return Response(
            #         {"error": "You are not authorized to delete the Product."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )                
            if not Product.objects.filter(id=pk).exists():
                return Response(
                    {"error": "Product Does not Exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            Product.objects.get(id=pk).delete()
            if not Product.objects.filter(id=pk).exists():
                return Response({"message": f"Product Deleted successfully."},
                    status=status.HTTP_204_NO_CONTENT
                )
            else:
                return Response(
                    {"error": "Failed to delete an Product."},
                    status=status.HTTP_400_BAD_REQUEST
                )      
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Deleting the Product.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SupplierListCreateAPIView(APIView):
    def get(self, request, format=None):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Customer Officer' or user.role == 'Store Manager'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Supplier."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            supplier = Supplier.objects.all()
            serializer = SupplierSerializer(supplier, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)                            
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Supplier.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, format=None):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Customer Officer'):
            #     return Response(
            #         {"error": "You are not authorized to create the Supplier."},
            #         status=status.HTTP_403_FORBIDDEN
            #     ) 
            print(user.role)
            serializer = SupplierSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            validated_data = serializer.validated_data
            # validated_data['user'] = user
            serializer.create(validated_data, user=request.user)
            return Response({"message": "Supplier created successfully."}, status=status.HTTP_201_CREATED) 
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while creating the Supplier.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class SupplierRetrieveUpdateDeleteAPIView(APIView):
    def get(self, request, pk):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Customer Officer' or user.role == 'Store Manager'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Supplier."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )            
            if not Supplier.objects.filter(id=pk).exists():
                return Response(
                    {"error": "Supplier Does not Exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            supplier = Supplier.objects.get(id=pk)
            serializer = SupplierSerializer(supplier)
            return Response(serializer.data, status=status.HTTP_200_OK)      
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Supplier.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, pk):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Customer Officer'):
            #     return Response(
            #         {"error": "You are not authorized to update the Supplier."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )              
            if not Supplier.objects.filter(id=pk).exists():
                return Response(
                    {"error": "Supplier Does not Exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            supplier = Supplier.objects.get(id=pk)
            serializer = SupplierSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            validated_data = serializer.validated_data
            serializer.update(supplier, validated_data)
            return Response({"message": f"Supplier Updated successfully."}, status=status.HTTP_200_OK)      
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while updating the Supplier.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request, pk):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Customer Officer'):
            #     return Response(
            #         {"error": "You are not authorized to update the Supplier."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )  
            if not Supplier.objects.filter(id=pk).exists():
                return Response(
                    {"error": "Supplier Does not Exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            supplier = Supplier.objects.get(id=pk)    
            serializer = SupplierSerializer(supplier, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response({"message": f"Supplier Updated successfully."}, status=status.HTTP_200_OK)                    
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while updating the Supplier.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Customer Officer'):
            #     return Response(
            #         {"error": "You are not authorized to delete the Supplier."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )  

            if not Supplier.objects.filter(id=pk).exists():
                return Response(
                    {"error": "Supplier Does not Exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            Supplier.objects.get(id=pk).delete()
            if not Supplier.objects.filter(id=pk).exists():
                return Response({"message": f"Supplier Deleted successfully."},
                    status=status.HTTP_204_NO_CONTENT
                )
            else:
                return Response(
                    {"error": "Failed to delete an Supplier."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                    
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Deleting the Supplier.{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CompanyListCreateAPIView(APIView):
    def get(self, request, format=None):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator' or user.role == 'Store Manager' or user.role == 'Customer Officer' or user.role == 'Cashier'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Company."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            company = CompanyInfo.objects.all()
            serializer = CompanyInfoSerializer(company, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
                      
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Company.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, format=None):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager'):
            #     return Response(
            #         {"error": "You are not authorized to create the Company."},
            #         status=status.HTTP_403_FORBIDDEN
            #      )   
            serializer = CompanyInfoSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            validated_data = serializer.validated_data
            validated_data['user'] = user
            serializer.create(validated_data, user=request.user)
            return Response({"message": f"Company Created successfully."}, status=status.HTTP_201_CREATED)

        except KeyError as e:
            print(e)
            return Response(
                {"error": f"An error occurred while Creating the Company.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CompanyRetrieveUpdateDeleteAPIView(APIView):
    def get(self, request, pk):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Field Operator' or user.role == 'Store Manager' or user.role == 'Customer Officer' or user.role == 'Cashier'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Company."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )               
            if not CompanyInfo.objects.filter(id=pk).exists():
                return Response(
                    {"error": "Company Does not Exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            company = CompanyInfo.objects.get(id=pk)
            serializer = CompanyInfoSerializer(company)
            return Response(serializer.data, status=status.HTTP_200_OK)      
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Company.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, pk):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager'):
            #     return Response(
            #         {"error": "You are not authorized to update the Company."},
            #         status=status.HTTP_403_FORBIDDEN
            #     ) 
            if not CompanyInfo.objects.filter(id=pk).exists():
                return Response(
                    {"error": "Company Does not Exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            company = CompanyInfo.objects.get(id=pk)
            serializer = CompanyInfoSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            validated_data = serializer.validated_data
            serializer.update(company, validated_data)
            return Response({"message": f"Company Updated successfully."}, status=status.HTTP_200_OK)        
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while updating the Company.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request, pk):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager'):
            #     return Response(
            #         {"error": "You are not authorized to update the Company."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )          
            if not CompanyInfo.objects.filter(id=pk).exists():
                return Response(
                    {"error": "Company Does not Exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            company = CompanyInfo.objects.get(id=pk)    
            serializer = CompanyInfoSerializer(company, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response({"message": f"Company Updated successfully."}, status=status.HTTP_200_OK)      
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while updating the Company.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, pk):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager'):
            #     return Response(
            #         {"error": "You are not authorized to delete the Company."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )                
            if not CompanyInfo.objects.filter(id=pk).exists():
                return Response(
                    {"error": "Company Does not Exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            CompanyInfo.objects.get(id=pk).delete()
            if not CompanyInfo.objects.filter(id=pk).exists():
                return Response({"message": f"Company Deleted successfully."},
                    status=status.HTTP_204_NO_CONTENT
                )
            else:
                return Response(
                    {"error": "Failed to delete an Company."},
                    status=status.HTTP_400_BAD_REQUEST
                )      
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Deleting the Company.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# --------------------------------Order--------------------------------
# class OrderPermission(BasePermission):
#     def has_permission(self, request, view):
#         user = request.user
#         return user and (getattr(user, "role", None) == "Manager" or user.is_superuser or user.role == 'Cashier' or user.role == 'Store Manager' or user.role == 'Assistant Manager')


class OrderListCreatView(generics.ListCreateAPIView):
    # queryset = Order.objects.order_by('-id')
    queryset = Order.objects.filter(credit=False).order_by('-id')
    # permission_classes = [OrderPermission]
    serializer_class = OrderSerializer
    pagination_class = Pagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['=customer__organization', '=payment_status']  # 🔍 allow searching by customer's name and payment status

    def get_queryset(self):
        # only fetch id, name, email from the DB
        return Order.objects.only('id', 'customer', 'customer__organization', 'status', 'receipt', 'receipt_id', 'order_date', 'sub_total', 'vat',  'total_amount', 'payment_status', 'paid_amount', 'unpaid_amount', 'credit', 'user').select_related('customer').filter(credit=False).order_by('-id')


    def get_serializer_class(self):
        # Use light serializer for list, full serializer for create
        if self.request.method == 'GET':
            return OrderLightSerializer
        return OrderSerializer

    def list(self, request, *args, **kwargs):
        # Get the queryset
        queryset = self.filter_queryset(self.get_queryset())
        
        # Get paginated data
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = self.get_paginated_response(serializer.data).data
        else:
            data = self.get_serializer(queryset, many=True).data
            data = {
                'count': len(data),
                'results': data
            }
        
        # Add all results
        all_serializer = self.get_serializer(queryset, many=True)
        data['all_results'] = all_serializer.data
        
        return Response(data)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        id = response.data.get('receipt_id')
        return Response({
            "message": "Order created successfully.",
            "data": response.data,
            "id": id
        }, status=status.HTTP_201_CREATED)

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    # permission_classes = [OrderPermission]
    serializer_class = OrderSerializer

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        id = response.data.get('receipt_id')
        return Response({
            "message": "Order retrived successfully.",
            "data": response.data,
            "id": id
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response({
            "message": "Order updated successfully.",
            "data": response.data
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({"message": "Order Deleted successfully."}, status=status.HTTP_200_OK)

class OrderItemListCreateView(generics.ListCreateAPIView):
    # queryset = OrderItem.objects.order_by('id')
    queryset = OrderItem.objects.filter(order__credit=False).order_by('id')
    # permission_classes = [OrderPermission]
    serializer_class = OrderItemSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "message": "Order Item created successfully.",
            "data": response.data
        }, status=status.HTTP_201_CREATED)

class OrderItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = OrderItem.objects.all()
    # permission_classes = [OrderPermission]
    serializer_class = OrderItemSerializer

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response({
            "message": "Order Item updated successfully.",
            "data": response.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        order = instance.order  # Get the order before deletion
        self.perform_destroy(instance)  # Delete the OrderItem

        # Check if the order still exists
        if Order.objects.filter(pk=order.pk).exists():
            items_count = OrderItem.objects.filter(order=order).count()
            return Response({
                "message": "Order Item Deleted successfully.",
                "order_id": order.id,
                "number_of_items": items_count
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "message": "Order Item Deleted successfully. The order was also deleted because it had no items left.",
                "order_id": None,
                "number_of_items": 0
            }, status=status.HTTP_200_OK)


class OrderCreditListAPIView(generics.ListAPIView):
    queryset = Order.objects.filter(credit=True).order_by('-id')
    # permission_classes = [OrderPermission]
    serializer_class = OrderLightSerializer
    pagination_class = Pagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['=customer__organization', '=payment_status']  # 🔍 allow searching by customer's name and payment status

    def get_queryset(self):
        # only fetch id, name, email from the DB
        return Order.objects.only('id', 'customer', 'customer__organization', 'status', 'receipt', 'receipt_id', 'order_date', 'sub_total', 'vat',  'total_amount', 'payment_status', 'paid_amount', 'unpaid_amount', 'credit', 'user').select_related('customer').filter(credit=True).order_by('-id')
    
    def list(self, request, *args, **kwargs):
        # Get the queryset
        queryset = self.filter_queryset(self.get_queryset())
        
        # Get paginated data
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = self.get_paginated_response(serializer.data).data
        else:
            data = self.get_serializer(queryset, many=True).data
            data = {
                'count': len(data),
                'results': data
            }
        
        # Add all results
        all_serializer = self.get_serializer(queryset, many=True)
        data['all_results'] = all_serializer.data
        
        return Response(data)


class OrderItemCreditListView(generics.ListAPIView):
    queryset = OrderItem.objects.filter(order__credit=True).order_by('id')
    serializer_class = OrderItemSerializer

    # def get_queryset(self):
    #     # only fetch id, name, email from the DB
    #     return OrderItem.objects.only('id', 'order', 'product', 'product_price', 'product__name', 'item_receipt', 'package', 'unit', 'quantity', 'unit_price', 'price', 'status').select_related('order', 'product').filter(order__credit=True).order_by('id')



class RecentOrderLimitedAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Salesman'):
            #     return Response(
            #         {"error": "You are not authorized to access Recent Orders."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            recent_orders = Order.objects.all().order_by('-order_date')[:10]
            serializer = OrderSerializer(recent_orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while accessing Recent Orders.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class RecentJobCardLimitedAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Salesman'):
            #     return Response(
            #         {"error": "You are not authorized to access Recent Orders."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            recent_jobcard = JobCard.objects.all().order_by('-service_date')[:10]
            serializer = JobCardLightSerializer(recent_jobcard, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while accessing Recent Job cards.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




class RecentAcceptanceLimitedAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Salesman'):
            #     return Response(
            #         {"error": "You are not authorized to access Recent Orders."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            recent_acceptance = VehicleAcceptance.objects.all().order_by('-ken')[:10]
            serializer = VehicleAcceptanceLightSerializer(recent_acceptance, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while accessing Recent Acceptances.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




# --------------------------------Category--------------------------------
class CategoryListCreateAPIView(APIView):
    def get(self, request, format=None):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Store Manager' or user.role == 'Assistant Manager'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Category."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )

            category = Category.objects.all().order_by('id')
            serializer = CategorySerializer(category, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK) 
       
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Category.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, format=None):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Store Manager' or user.role == 'Assistant Manager'):
            #     return Response(
            #         {"error": "You are not authorized to create the Category."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )

            serializer = CategorySerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            validated_data = serializer.validated_data
            validated_data['user'] = user
            serializer.create(validated_data, user=request.user)
            return Response({"message": f"Category created successfully."}, status=status.HTTP_201_CREATED)
                      
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while creating the Category.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
   
class CategoryRetrieveUpdateDeleteAPIView(APIView):
    def get(self, request, pk):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Store Manager' or user.role == 'Assistant Manager'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Category."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            if not Category.objects.filter(id=pk).exists():
                return Response(
                    {"error": "Category Does not Exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            category = Category.objects.get(id=pk)
            serializer = CategorySerializer(category)
            return Response(serializer.data, status=status.HTTP_200_OK)     
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Category.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, pk):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Store Manager' or user.role == 'Assistant Manager'):
            #     return Response(
            #         {"error": "You are not authorized to update the Category."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )                
            if not Category.objects.filter(id=pk).exists():
                return Response(
                    {"error": "Category Does not Exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            category = Category.objects.get(id=pk)
            serializer = CategorySerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            validated_data = serializer.validated_data
            serializer.update(category, validated_data)
            return Response({"message": f"Category Updated successfully."}, status=status.HTTP_200_OK)      
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while updating the Category.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def patch(self, request, pk):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Store Manager' or user.role == 'Assistant Manager'):
            #     return Response(
            #         {"error": "You are not authorized to update the Category."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )                
            if not Category.objects.filter(id=pk).exists():
                return Response(
                    {"error": "Category Does not Exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            category = Category.objects.get(id=pk)    
            serializer = CategorySerializer(category, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response({"message": f"Category Updated successfully."}, status=status.HTTP_200_OK)      
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while updating the Category.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Store Manager' or user.role == 'Assistant Manager'):
            #     return Response(
            #         {"error": "You are not authorized to delete the Category."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )                
            if not Category.objects.filter(id=pk).exists():
                return Response(
                    {"error": "Category Does not Exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            Category.objects.get(id=pk).delete()
            if not Category.objects.filter(id=pk).exists():
                return Response({"message": f"Category Deleted successfully."},
                    status=status.HTTP_204_NO_CONTENT   
                )
            else:
                return Response(
                    {"error": "Failed to delete an Category."},
                    status=status.HTTP_400_BAD_REQUEST
                )      
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Delete the Category.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




# ------------------------------------- Purchase Views --------------------------------------------------

# class PurchasePermission(BasePermission):
#     def has_permission(self, request, view):
#         user = request.user
#         return user and (getattr(user, "role", None) == "Manager" or user.is_superuser or user.role == 'Store Manager' or user.role == 'Assistant Manager')


class PurchaseSupplierListCreateView(generics.ListCreateAPIView):
    queryset = PurchaseSupplier.objects.all().order_by('-id')
    # permission_classes = [PurchasePermission]
    serializer_class = PurchaseSupplierSerializer
    pagination_class = Pagination
    filter_backends = [filters.SearchFilter]  # enable search
    search_fields = ['supplier__name']  # fields to search in

    def get_queryset(self):
        # only fetch id, name, email from the DB
        return PurchaseSupplier.objects.only('id', 'supplier__name', 'total_amount', 'payment_status', 'paid_amount', 'unpaid_amount', 'user').select_related('supplier').order_by('-id')

    def get_serializer_class(self):
        # Use light serializer for list, full serializer for create
        if self.request.method == 'GET':
            return PurchaseSupplierLightSerializer
        return PurchaseSupplierSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "message": "Purchase Supplier created successfully.",
            "data": response.data
        }, status=status.HTTP_201_CREATED)

class PurchaseSupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PurchaseSupplier.objects.all()
    # permission_classes = [PurchasePermission]
    serializer_class = PurchaseSupplierSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Lightweight customer (avoid heavy nested performas)
        supplier_data = PurchaseSupplierLightSerializer(instance).data

        # Query and paginate related performas (light fields)
        expenses_qs = (
            instance.expenses.only(
                'id', 'purchase_date', 'supplier', 'total', 'payment_status', 'paid_amount', 'unpaid_amount', 'user'
            )
            .order_by('-id')
        )

        # Optional search
        search_query = request.query_params.get('search')
        if search_query:
            expenses_qs = expenses_qs.filter(Q(supplier__icontains=search_query))

        paginator = Pagination()
        page = paginator.paginate_queryset(expenses_qs, request)
        results = PurchaseExpenseLightSerializer(page or expenses_qs, many=True).data

        # zero-padded latest performa id (most recent by desc)
        padded_id = None
        if results:
            latest_id = results[0]['id']
            padded_id = str(latest_id).zfill(4)

        if page is not None:
            return Response({
                "message": "Purchase Supplier retrived successfully.",
                "data": supplier_data,
                "expenses": {
                    "count": paginator.page.paginator.count,
                    "next": paginator.get_next_link(),
                    "previous": paginator.get_previous_link(),
                    "results": results,
                },
                "id": padded_id
            }, status=status.HTTP_200_OK)

        # Fallback without pagination
        return Response({
            "message": "Purchase Supplier retrived successfully.",
            "data": supplier_data,
            "expenses": {
                "count": len(results),
                "next": None,
                "previous": None,
                "results": results,
            },
            "id": padded_id
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response({
            "message": "Purchase Supplier updated successfully.",
            "data": response.data
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({"message": "Purchase Supplier Deleted successfully."}, status=status.HTTP_200_OK)


class PurchaseExpenseListCreateView(generics.ListCreateAPIView):
    queryset = PurchaseExpense.objects.all().order_by('-id')
    # permission_classes = [PurchasePermission]
    serializer_class = PurchaseExpenseSerializer
    pagination_class = Pagination
    filter_backends = [filters.SearchFilter]  # enable search
    search_fields = ['supplier']  # fields to search in


    def get_queryset(self):
        # only fetch id, name, email from the DB
        return PurchaseExpense.objects.only('id', 'purchase_date', 'supplier', 'total', 'payment_status', 'paid_amount', 'unpaid_amount', 'user').order_by('-id')


    def get_serializer_class(self):
        # Use light serializer for list, full serializer for create
        if self.request.method == 'GET':
            return PurchaseExpenseLightSerializer
        return PurchaseExpenseSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "message": "Purchase Expense created successfully.",
            "data": response.data
        }, status=status.HTTP_201_CREATED)

class PurchaseExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PurchaseExpense.objects.all()
    # permission_classes = [PurchasePermission]
    serializer_class = PurchaseExpenseSerializer

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response({
            "message": "Purchase Expenses updated successfully.",
            "data": response.data
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({"message": "Purchase Expenses Deleted successfully."}, status=status.HTTP_200_OK)


class PurchaseProductListCreateView(generics.ListCreateAPIView):
    queryset = PurchaseProduct.objects.all()
    # permission_classes = [PurchasePermission]
    serializer_class = PurchaseProductSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "message": "Purchase Product created successfully.",
            "data": response.data
        }, status=status.HTTP_201_CREATED)

class PurchaseProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PurchaseProduct.objects.all()
    # permission_classes = [PurchasePermission]
    serializer_class = PurchaseProductSerializer

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response({
            "message": "Purchase Products updated successfully.",
            "data": response.data
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({"message": "Purchase Products Deleted successfully."}, status=status.HTTP_200_OK)






# ------------------------------------- New Credit Views --------------------------------------------------

# class CreditPermission(BasePermission):
#     def has_permission(self, request, view):
#         user = request.user
#         return user and (getattr(user, "role", None) == "Manager" or user.is_superuser or user.role == 'Store Manager' or user.role == 'Assistant Manager')


class CreditCustomerListCreateView(generics.ListCreateAPIView):
    queryset = CreditCustomer.objects.all().order_by('-id')
    # permission_classes = [CreditPermission]
    serializer_class = CreditCustomerSerializer
    pagination_class = Pagination
    filter_backends = [filters.SearchFilter]  # enable search
    # search_fields = ['customer__name']  # fields to search in
    search_fields = ['customer__organization']  # fields to search in

    def get_queryset(self):
        # only fetch id, name, email from the DB
        return CreditCustomer.objects.only('id', 'customer__organization', 'total_amount', 'payment_status', 'paid_amount', 'unpaid_amount', 'user').select_related('customer').order_by('-id')

    def get_serializer_class(self):
        # Use light serializer for list, full serializer for create
        if self.request.method == 'GET':
            return CreditCustomerLightSerializer
        return CreditCustomerSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "message": "Credit Customer created successfully.",
            "data": response.data
        }, status=status.HTTP_201_CREATED)

class CreditCustomerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CreditCustomer.objects.all()
    # permission_classes = [CreditPermission]
    serializer_class = CreditCustomerSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Lightweight customer (avoid heavy nested performas)
        customer_data = CreditCustomerLightSerializer(instance).data

        # Query and paginate related credits (light fields)
        credits_qs = (
            instance.credits.only(
                'id', 'credit_date', 'customer', 'performa', 'number_of_items', 'receipt', 'total', 'payment_status', 'paid_amount', 'unpaid_amount', 'user'
            )
            .order_by('-id')
        )

        # Optional search
        search_query = request.query_params.get('search')
        if search_query:
            credits_qs = credits_qs.filter(
                Q(customer__icontains=search_query)
            )

        paginator = Pagination()
        page = paginator.paginate_queryset(credits_qs, request)
        results = CreditCreditLightSerializer(page or credits_qs, many=True).data

        # zero-padded latest performa id (most recent by desc)
        padded_id = None
        if results:
            latest_id = results[0]['id']
            padded_id = str(latest_id).zfill(4)

        if page is not None:
            return Response({
                "message": "Credits Customer retrived successfully.",
                "data": customer_data,
                "credits": {
                    "count": paginator.page.paginator.count,
                    "next": paginator.get_next_link(),
                    "previous": paginator.get_previous_link(),
                    "results": results,
                },
                "id": padded_id
            }, status=status.HTTP_200_OK)

        # Fallback without pagination
        return Response({
            "message": "Credits Customer retrived successfully.",
            "data": customer_data,
            "credits": {
                "count": len(results),
                "next": None,
                "previous": None,
                "results": results,
            },
            "id": padded_id
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response({
            "message": "Credits Customer updated successfully.",
            "data": response.data
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({"message": "Credits Customer Deleted successfully."}, status=status.HTTP_200_OK)


class CreditCreditListCreateView(generics.ListCreateAPIView):
    queryset = CreditCredit.objects.all().order_by('-id')
    # permission_classes = [CreditPermission]
    serializer_class = CreditCreditSerializer
    pagination_class = Pagination
    filter_backends = [filters.SearchFilter]  # enable search
    search_fields = ['customer']  # fields to search in


    def get_queryset(self):
        # only fetch id, name, email from the DB
        return CreditCredit.objects.only('id', 'credit_date', 'customer', 'performa', 'total', 'payment_status', 'paid_amount', 'unpaid_amount', 'user').order_by('-id')


    def get_serializer_class(self):
        # Use light serializer for list, full serializer for create
        if self.request.method == 'GET':
            return CreditCreditLightSerializer
        return CreditCreditSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "message": "Credit created successfully.",
            "data": response.data
        }, status=status.HTTP_201_CREATED)

class CreditCreditDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CreditCredit.objects.all()
    # permission_classes = [CreditPermission]
    serializer_class = CreditCreditSerializer

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response({
            "message": "Credit updated successfully.",
            "data": response.data
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({"message": "Credit Deleted successfully."}, status=status.HTTP_200_OK)


class CreditProductListCreateView(generics.ListCreateAPIView):
    queryset = CreditProduct.objects.all()
    # permission_classes = [CreditPermission]
    serializer_class = CreditProductSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "message": "Credit Product created successfully.",
            "data": response.data
        }, status=status.HTTP_201_CREATED)

class CreditProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CreditProduct.objects.all()
    # permission_classes = [CreditPermission]
    serializer_class = CreditProductSerializer

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response({
            "message": "Credit Products updated successfully.",
            "data": response.data
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({"message": "Credit Products Deleted successfully."}, status=status.HTTP_200_OK)






# Receipt Related

class OrderReceiptAPIView(APIView):
    def get(self, request, pk):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Order Receipt."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )

            # Retrieve the order along with related data
            order = get_object_or_404(Order.objects.prefetch_related('items__product').select_related('customer'), id=pk)
            
            # Get the first (or default) company info (assuming there's only one)
            company = CompanyInfo.objects.first()

            # Prepare receipt data
            receipt_data = {
                "company": {
                    "en_name": company.en_name if company else "Company",
                    "am_name": company.am_name if company else "Company",
                    "email": company.email if company else "",
                    "phone": company.phone1 if company else "",
                    "tin_number": company.tin_number if company else "",
                    "vat_number": company.vat_number if company else "",
                    "bank_accounts": company.bank_accounts if company else {},
                    "country": company.country if company else "",
                    "region": company.region if company else "",
                    "zone": company.zone if company else "",
                    "city": company.city if company else "",
                    "sub_city": company.sub_city if company else "",
                    "logo": company.logo.url if company and company.logo else None
                },
                "customer": {
                    "name": order.customer.name if order.customer else "Customer",
                    "phone": order.customer.phone if order.customer else "",
                    "tin_number": order.customer.tin_number if order.customer else "",
                    "organization": order.customer.organization if order.customer else "",
                    "address": order.customer.address if order.customer else "",
                },
                "order_details": {
                    "order_id": order.id,
                    "date": order.order_date,
                    "status": order.status,
                    "receipt": order.receipt,
                    "sub_total": order.sub_total,
                    "vat": order.vat,
                    "total_amount": order.total_amount,
                    "user": order.user if order.user else "User",
                },
                "items": [
                    {
                        "product_name": item.product.name if item.product else "Unknown",
                        "part_number": item.product.part_number  if item.product else "Unknown",
                        "quantity": item.quantity,
                        "product_price": item.unit_price if item.unit_price else item.product.selling_price if item.product else 0,
                        "unit": item.unit,
                        "unit_price": item.unit_price,
                        "price": item.price,
                        "status": item.status,
                    }
                    for item in order.items.all()
                ]
            }

            return Response(receipt_data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Order Receipt.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreditReceiptAPIView(APIView):
    def get(self, request, pk):
        try:
            # 1. Single database fetch for CreditCredit with pre-fetched customer and product details
            credit = get_object_or_404(
                CreditCredit.objects.select_related(
                    'customer_level__customer'
                ).prefetch_related(
                    'products__product'
                ), 
                id=pk
            )

            # 2. Extract Customer details through customer_level relation
            credit_customer_instance = credit.customer_level
            if not credit_customer_instance or not credit_customer_instance.customer:
                return Response(
                    {"error": "Cannot create Credit Receipt: No valid Customer found on this Credit's customer level."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            actual_customer = credit_customer_instance.customer

            # 3. Retrieve Company Information
            company = CompanyInfo.objects.first()

            # 4. Construct response dictionary
            receipt_data = {
                "company": {
                    "en_name": company.en_name if company and company.en_name else "Company",
                    "am_name": company.am_name if company and company.am_name else "Company",
                    "email": company.email if company and company.email else "",
                    "phone": company.phone1 if company and company.phone1 else "",
                    "tin_number": company.tin_number if company and company.tin_number else "",
                    "vat_number": company.vat_number if company and company.vat_number else "",
                    "bank_accounts": company.bank_accounts if company and company.bank_accounts else {},
                    "country": company.country if company and company.country else "",
                    "region": company.region if company and company.region else "",
                    "zone": company.zone if company and company.zone else "",
                    "city": company.city if company and company.city else "",
                    "sub_city": company.sub_city if company and company.sub_city else "",
                    "logo": company.logo.url if company and company.logo else None
                },
                "customer": {
                    "name": getattr(actual_customer, 'name', 'Customer'),
                    "phone": getattr(actual_customer, 'phone', ''),
                    "tin_number": getattr(actual_customer, 'tin_number', ''),
                    "organization": getattr(actual_customer, 'organization', ''),
                    "address": getattr(actual_customer, 'address', ''),
                },
                "credit_details": {
                    "credit_id": credit.id,
                    "date": credit.credit_date,
                    "payment_status": credit.payment_status,
                    "receipt": credit.receipt,
                    "sub_total": credit.sub_total,
                    "vat": credit.vat,
                    "total_amount": credit.total,  # Model field name is 'total'
                    "paid_amount": credit.paid_amount,
                    "unpaid_amount": credit.unpaid_amount,
                    "user": credit.user if credit.user else "User",
                },
                "items": [
                    {
                        "product_name": item.product.name if item.product else "Unknown",
                        "part_number": item.part_number or (item.product.part_number if item.product and hasattr(item.product, 'part_number') else ""),
                        "description": item.description or "",
                        "quantity": item.quantity,
                        "unit": item.unit,
                        "unit_price": item.unit_price,
                        "price": item.total_price,  # Model field name is 'total_price'
                    }
                    for item in credit.products.all()
                ]
            }

            return Response(receipt_data, status=status.HTTP_200_OK)

        except CreditCredit.DoesNotExist:
            return Response(
                {"error": "Credit record does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred while retrieving the Credit Receipt: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PerformaReceiptAPIView(APIView):
    def get(self, request, pk):
        try:
            # 1. Single database fetch for performaperforma with pre-fetched customer and product details
            performa = get_object_or_404(
                PerformaPerforma.objects.select_related(
                    'customer_level__customer'
                ).prefetch_related(
                    'products__product'
                ), 
                id=pk
            )

            # 2. Extract Customer details through customer_level relation
            performa_customer_instance = performa.customer_level
            if not performa_customer_instance or not performa_customer_instance.customer:
                return Response(
                    {"error": "Cannot create Performa Receipt: No valid Customer found on this Performa's customer level."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            actual_customer = performa_customer_instance.customer

            # 3. Retrieve Company Information
            company = CompanyInfo.objects.first()

            # 4. Construct response dictionary
            receipt_data = {
                "company": {
                    "en_name": company.en_name if company and company.en_name else "Company",
                    "am_name": company.am_name if company and company.am_name else "Company",
                    "email": company.email if company and company.email else "",
                    "phone": company.phone1 if company and company.phone1 else "",
                    "tin_number": company.tin_number if company and company.tin_number else "",
                    "vat_number": company.vat_number if company and company.vat_number else "",
                    "bank_accounts": company.bank_accounts if company and company.bank_accounts else {},
                    "country": company.country if company and company.country else "",
                    "region": company.region if company and company.region else "",
                    "zone": company.zone if company and company.zone else "",
                    "city": company.city if company and company.city else "",
                    "sub_city": company.sub_city if company and company.sub_city else "",
                    "logo": company.logo.url if company and company.logo else None
                },
                "customer": {
                    "name": getattr(actual_customer, 'name', 'Customer'),
                    "phone": getattr(actual_customer, 'phone', ''),
                    "tin_number": getattr(actual_customer, 'tin_number', ''),
                    "organization": getattr(actual_customer, 'organization', ''),
                    "address": getattr(actual_customer, 'address', ''),
                },
                "performa_details": {
                    "performa_id": performa.id,
                    "date": performa.issued_date,
                    "receipt": performa.receipt,
                    "service_charge": performa.service_charge,
                    "sub_total": performa.sub_total,
                    "vat": performa.vat,
                    "total_amount": performa.total,  # Model field name is 'total'
                    "user": performa.user if performa.user else "User",
                },
                "items": [
                    {
                        "product_name": item.product.name if item.product else "Unknown",
                        "part_number": item.part_number or (item.product.part_number if item.product and hasattr(item.product, 'part_number') else ""),
                        "description": item.description or "",
                        "quantity": item.quantity,
                        "unit": item.unit,
                        "unit_price": item.unit_price,
                        "product_service_charge": item.product_service_charge,
                        "price": item.total_price,  # Model field name is 'total_price'
                    }
                    for item in performa.products.all()
                ]
            }

            return Response(receipt_data, status=status.HTTP_200_OK)

        except PerformaPerforma.DoesNotExist:
            return Response(
                {"error": "performa record does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred while retrieving the performa Receipt: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Log Related

class OrderLogAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Order Log."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            logs = OrderLog.objects.all()
            serializer = OrderLogSerializer(logs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Order Log.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ExcelReportAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Order Report."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            report = Report.objects.all()
            serializer = OrderReportSerializer(report, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Order Report.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SupplierLogListView(generics.ListAPIView):
    serializer_class = SupplierPaymentLogSerializer

    def get_queryset(self):
        user = self.request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Supplier Log."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        supplier_id = self.kwargs['supplier_id']
        return SupplierPaymentLog.objects.filter(supplier_id=supplier_id).order_by('-timestamp')


class ExpenseLogListView(generics.ListAPIView):
    serializer_class = ExpensePaymentLogSerializer

    def get_queryset(self):
        user = self.request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Expense Log."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        expense_id = self.kwargs['expense_id']
        return ExpensePaymentLog.objects.filter(expense_id=expense_id).order_by('-timestamp')


class OrderLogListView(generics.ListAPIView):
    serializer_class = OrderPaymentLogSerializer

    def get_queryset(self):
        user = self.request.user
        # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager'):
        #     return Response(
        #         {"error": "You are not authorized to retrive the Order Log List."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        order_id = self.kwargs['order_id']
        return OrderPaymentLog.objects.filter(order_id=order_id).order_by('-timestamp')


class JobCardStatusScheduledAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            # user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the JobCard Status Schedules."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            total_number_scheduled = JobCard.objects.filter(status='scheduled').count()       
            return Response(total_number_scheduled, status=status.HTTP_200_OK)         
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the JobCard Status Schedules.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DailyJobCardStatusScheduledAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser or user.role == 'Salesman'):
            #     return Response(
            #         {"error": "You are not authorized to retrieve daily sales."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            today = timezone.now().date()
            daily_total_number_scheduled = JobCard.objects.filter(service_date__date=today, status='scheduled').count() 
            jobcard = JobCard.objects.filter(service_date__date=today, status="scheduled")
            serializer = JobCardSerializer(jobcard, many=True)
            return Response({
                "date": str(today),
                "daily_total_number_scheduled": daily_total_number_scheduled,
                "jobcard": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred while retrieving daily total number of scheduled. {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class JobCardStatusInProgressAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            # user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the JobCard Status In Progress."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            total_number_in_progress = JobCard.objects.filter(status='in_progress').count()       
            return Response(total_number_in_progress, status=status.HTTP_200_OK)         
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the JobCard Status In Progress.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DailyJobCardStatusInProgressAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser or user.role == 'Salesman'):
            #     return Response(
            #         {"error": "You are not authorized to retrieve daily sales."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            today = timezone.now().date()
            daily_total_number_in_progress = JobCard.objects.filter(service_date__date=today, status='in_progress').count() 
            jobcard = JobCard.objects.filter(service_date__date=today, status="in_progress")
            serializer = JobCardSerializer(jobcard, many=True)
            return Response({
                "date": str(today),
                "daily_total_number_in_progress": daily_total_number_in_progress,
                "jobcard": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred while retrieving daily total number of in_progress. {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class JobCardStatusCompletedAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            # user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the JobCard Status Completed."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            total_number_completed = JobCard.objects.filter(status='completed').count()       
            return Response(total_number_completed, status=status.HTTP_200_OK)         
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the JobCard Status Completed.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class DailyJobCardStatusCompletedAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser or user.role == 'Salesman'):
            #     return Response(
            #         {"error": "You are not authorized to retrieve daily sales."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            today = timezone.now().date()
            daily_total_number_completed = JobCard.objects.filter(service_date__date=today, status='completed').count() 
            jobcard = JobCard.objects.filter(service_date__date=today, status="completed")
            serializer = JobCardSerializer(jobcard, many=True)
            return Response({
                "date": str(today),
                "daily_total_number_completed": daily_total_number_completed,
                "jobcard": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred while retrieving daily total number of completed. {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




            
class JobCardStatusAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            # user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the JobCard Status."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            total_number = JobCard.objects.all().count()       
            return Response(total_number, status=status.HTTP_200_OK)         
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the JobCard Status.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ------------------------------------- Totals Counts for Dashboard -----------------------------------------

class TotalOrderAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:
            # user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Cashier'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Total Order."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            total_number_order = Order.objects.all().count()       
            return Response(total_number_order, status=status.HTTP_200_OK)

        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Total Order.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TotalProductAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            # user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Product."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            total_number = Product.objects.all().count()       
            return Response(total_number, status=status.HTTP_200_OK)         
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Product.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TotalCategoryAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            # user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Product."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            total_number = Category.objects.all().count()       
            return Response(total_number, status=status.HTTP_200_OK)         
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Product.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TotalSupplierAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            # user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Product."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            total_number = Supplier.objects.all().count()       
            return Response(total_number, status=status.HTTP_200_OK)         
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Product.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TotalServiceAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            # user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Product."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            total_number = Service.objects.all().count()       
            return Response(total_number, status=status.HTTP_200_OK)         
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Product.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TotalServicePackageAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            # user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Product."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            total_number = ServicePackage.objects.all().count()       
            return Response(total_number, status=status.HTTP_200_OK)         
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Product.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TotalVehicleAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            # user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Product."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            total_number = Vehicle.objects.all().count()       
            return Response(total_number, status=status.HTTP_200_OK)         
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Product.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TotalCustomerAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            # user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Product."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            total_number = Customer.objects.all().count()       
            return Response(total_number, status=status.HTTP_200_OK)         
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Product.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TotalAcceptanceAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            # user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Product."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            total_number = VehicleAcceptance.objects.all().count()       
            return Response(total_number, status=status.HTTP_200_OK)         
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Product.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TotalPerformaAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            # user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Product."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            total_number = PerformaPerforma.objects.all().count()       
            return Response(total_number, status=status.HTTP_200_OK)         
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Product.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TotalExpensesAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            # user = request.user
            # if not (user.role == 'Manager' or user.is_superuser == True or user.role == 'Assistant Manager' or user.role == 'Technical Examiner'):
            #     return Response(
            #         {"error": "You are not authorized to retrive the Product."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            total_number = PurchaseExpense.objects.all().count()       
            return Response(total_number, status=status.HTTP_200_OK)         
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Product.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



# ------------------------------------- Available JobCards for VOV, VOPD, VPR and Invoice -----------------------------------------

class AvailableJobCardPartRequestAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            avaiilable_jobcard_part_request = JobCard.objects.filter(vehicle_part_requests__isnull=True).exclude(status='completed')

            serializer = JobCardLightSerializer(avaiilable_jobcard_part_request, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)       
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Available JobCards | Part Request.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AvailableJobCardOrderVoucherAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            avaiilable_jobcard_order_voucher = JobCard.objects.filter(vehicle_order_vouchers__isnull=True).exclude(status='completed')

            serializer = JobCardLightSerializer(avaiilable_jobcard_order_voucher, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)       
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Available JobCards | Order Voucher.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AvailableJobCardOldPartAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            avaiilable_jobcard_old_part = JobCard.objects.filter(vehicle_old_parts__isnull=True).exclude(status='completed')

            serializer = JobCardLightSerializer(avaiilable_jobcard_old_part, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)       
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Available JobCards | Old Part.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AvailableJobCardInvoiceAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            avaiilable_jobcard_invoice = JobCard.objects.filter(invoice__isnull=True, status='completed') 

            serializer = JobCardLightSerializer(avaiilable_jobcard_invoice, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)       
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Available JobCards | Invoice.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



# ------------------------------------- Jobcard Log -----------------------------------------

class JobCardLogAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            jobcard_log = JobCardLog.objects.all()

            serializer = JobCardLogSerializer(jobcard_log, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)       
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the JobCards Logs.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class JobCardAssignmentLogAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            jobcard_assignment_log = JobCardAssignmentLog.objects.all()

            serializer = JobCardLogSerializer(jobcard_assignment_log, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)       
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the JobCard Assignment Logs.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AssignedServiceLogAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            assigned_services_log = AssignedServiceLog.objects.all()

            serializer = JobCardLogSerializer(assigned_services_log, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)       
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Assigned Services Logs.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ---------------- JobCard Receipt ----------------
class JobCardReceiptAPIView(APIView):
    def get(self, request, pk):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser is True or user.role == 'Assistant Manager'):
            #     return Response(
            #         {"error": "You are not authorized to retrieve the JobCard Receipt."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )

            jobcard = get_object_or_404(
                JobCard.objects
                    .select_related('customer', 'vehicle')
                    .prefetch_related(
                        'assignments__assigned_services__service',
                        'assignments__worker',
                        'assignments__service_package',
                        'vehicle_part_requests__items__product'  # NEW
                    ),
                id=pk
            )

            company = CompanyInfo.objects.first()

            # Calculate totals from assignments and assigned services
            services_total = 0
            service_packages_total = 0

            assignments_payload = []
            for assignment in jobcard.assignments.all():
                if assignment.service_package and assignment.service_package.cost:
                    service_packages_total += assignment.service_package.cost

                assigned_services_payload = []
                for asg in assignment.assigned_services.all():
                    cost = asg.service.cost if (asg.service and asg.service.cost is not None) else 0
                    services_total += cost or 0
                    assigned_services_payload.append({
                        "service": asg.service.name if asg.service else None,
                        "status": asg.status,
                        "started_at": asg.started_at,
                        "completed_at": asg.completed_at,
                        "cost": cost,
                    })

                assignments_payload.append({
                    "id": assignment.id,
                    "worker": assignment.worker.name if assignment.worker else None,
                    "service_package": assignment.service_package.name if assignment.service_package else None,
                    "service_package_cost": assignment.service_package.cost if assignment.service_package else None,
                    "status": assignment.status,
                    "package_status": assignment.package_status,
                    "task_description": assignment.task_description,
                    "started_at": assignment.started_at,
                    "completed_at": assignment.completed_at,
                    "assigned_services": assigned_services_payload,
                })

            # Part request (one-to-one by model, related_name='vehicle_part_requests')
            part_request_payload = None
            parts_total = 0
            pr = getattr(jobcard, 'vehicle_part_requests', None)
            if pr:
                items_payload = []
                for item in pr.items.all():
                    # Prefer stored price; fall back to unit_price * quantity if price is null
                    line_price = item.price if item.price is not None else (
                        (item.unit_price or 0) * (item.quantity or 0)
                    )
                    parts_total += line_price or 0
                    items_payload.append({
                        "product_name": item.product.name if item.product else None,
                        "part_number": item.product.part_number if item.product else None,
                        "unit_price": item.unit_price,
                        "quantity": item.quantity,
                        "price": line_price,
                    })

                part_request_payload = {
                    "id": pr.id,
                    "ken": pr.ken,
                    "asrekabi_name": pr.asrekabi_sim.name if pr.asrekabi_sim else None,
                    "terekabi_name": pr.terekabi_sim.name if pr.terekabi_sim else None,
                    "total_amount": pr.total_amount,
                    "items": items_payload,
                }

                # If you prefer to trust the stored total on the model:
                # parts_total = pr.total_amount or parts_total

            receipt_data = {
                "company": {
                    "en_name": company.en_name if company else "Company",
                    "am_name": company.am_name if company else "Company",
                    "email": company.email if company else "",
                    "phone": company.phone1 if company else "",
                    "tin_number": company.tin_number if company else "",
                    "vat_number": company.vat_number if company else "",
                    "bank_accounts": company.bank_accounts if company else {},
                    "country": company.country if company else "",
                    "region": company.region if company else "",
                    "zone": company.zone if company else "",
                    "city": company.city if company else "",
                    "sub_city": company.sub_city if company else "",
                    "logo": company.logo.url if company and company.logo else None,
                },
                "customer": {
                    "name": jobcard.customer.name if jobcard.customer else "Customer",
                    "phone": jobcard.customer.phone if jobcard.customer else "",
                    "tin_number": jobcard.customer.tin_number if jobcard.customer else "",
                    "organization": jobcard.customer.organization if jobcard.customer else "",
                },
                "vehicle": {
                    "model": jobcard.vehicle.model if jobcard.vehicle else None,
                    "license_plate": jobcard.vehicle.license_plate if jobcard.vehicle else None,
                    "motor_kutir": jobcard.vehicle.motor_kutir if jobcard.vehicle else None,
                    "shanci_kutir": jobcard.vehicle.shanci_kutir if jobcard.vehicle else None,
                    "color": jobcard.vehicle.color if jobcard.vehicle else None,
                    "year": jobcard.vehicle.year if jobcard.vehicle else None,
                },
                "jobcard_details": {
                    "jobcard_id": jobcard.id,
                    "service_date": jobcard.service_date,
                    "status": jobcard.status,
                    "notes": jobcard.notes,
                    "odometer_reading": jobcard.odometer_reading,
                    "total_cost": jobcard.total_cost,
                    "user": jobcard.user if jobcard.user else "User",
                },
                "assignments": assignments_payload,
                "part_request": part_request_payload,  # NEW section
                "totals": {
                    "services_total": services_total,
                    "service_packages_total": service_packages_total,
                    "parts_total": parts_total,  # NEW
                    "combined_subtotal": (services_total or 0) + (service_packages_total or 0) + (parts_total or 0),
                    "vat": Decimal((services_total or 0) + (service_packages_total or 0) + (parts_total or 0)) * Decimal(0.15),
                    "total_amount": (Decimal((services_total or 0) + (service_packages_total or 0) + (parts_total or 0)) * Decimal(0.15)) + (services_total or 0) + (service_packages_total or 0) + (parts_total or 0)
                }
            }

            return Response(receipt_data, status=status.HTTP_200_OK)
        except JobCard.DoesNotExist:
            return Response(
                {"error": "JobCard does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred while Retrieving the JobCard Receipt. {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ------------------------------------- Total Sales relative to Time --------------------------------------------------

class DailySalesAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser or user.role == 'Salesman'):
            #     return Response(
            #         {"error": "You are not authorized to retrieve daily sales."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            today = timezone.now().date()
            orders = Order.objects.filter(order_date__date=today, status="Done", payment_status='Paid')
            total_sales = orders.aggregate(total_sales=Sum('total_amount'))['total_sales'] or 0
            serializer = OrderSerializer(orders, many=True)
            return Response({
                "date": str(today),
                "total_sales": total_sales,
                "orders": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred while retrieving daily sales. {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
       
class WeeklySalesAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser or user.role == 'Salesman'):
            #     return Response(
            #         {"error": "You are not authorized to retrieve sales."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            today = timezone.now().date()
            sales_data = []

            for i in range(6, -1, -1):  # Start from 6 days ago to today
                day = today - timedelta(days=i)
                orders = Order.objects.filter(
                    order_date__date=day,
                    status="Done", 
                    payment_status='Paid'
                )
                total_sales = orders.aggregate(total_sales=Sum('total_amount'))['total_sales'] or 0
                sales_data.append({
                    "period": day.strftime("%A"),  # Day name, e.g., "Monday"
                    "sales": float(total_sales)
                })

            return Response(sales_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred while retrieving last seven days sales. {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class MonthlySalesAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser or user.role == 'Salesman'):
            #     return Response(
            #         {"error": "You are not authorized to retrieve sales."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            today = timezone.now().date()
            year = today.year
            sales_data = []

            for month in range(1, 13):
                orders = Order.objects.filter(
                    order_date__year=year,
                    order_date__month=month,
                    status="Done", 
                    payment_status='Paid'
                )
                total_sales = orders.aggregate(total_sales=Sum('total_amount'))['total_sales'] or 0
                sales_data.append({
                    "period": calendar.month_name[month],
                    "sales": float(total_sales)
                })

            return Response(sales_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred while retrieving monthly sales. {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class YearlySalesAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser or user.role == 'Salesman'):
            #     return Response(
            #         {"error": "You are not authorized to retrieve sales."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            today = timezone.now().date()
            year = today.year

            orders = Order.objects.filter(
                order_date__year=year,
                status="Done", 
                payment_status='Paid'
            )
            total_sales = orders.aggregate(total_sales=Sum('total_amount'))['total_sales'] or 0

            data = [{
                "period": str(year),
                "sales": float(total_sales)
            }]

            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred while retrieving yearly sales. {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
# ------------------------------------- Total Sales relative to Time for Each User --------------------------------------------------

class DailySalesEachUserAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser or user.role == 'Salesman' or user.role == 'Sales Manager'):
            #     return Response(
            #         {"error": "You are not authorized to retrieve daily sales."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            today = timezone.now().date()
            orders = Order.objects.filter(order_date__date=today, user_email=user.email, status="Done", payment_status='Paid')
            total_sales = orders.aggregate(total_sales=Sum('total_amount'))['total_sales'] or 0
            serializer = OrderSerializer(orders, many=True)
            return Response({
                "date": str(today),
                "total_sales": total_sales,
                "orders": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred while retrieving daily sales. {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
       
class WeeklySalesEachUserAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser or user.role == 'Salesman' or user.role == 'Sales Manager'):
            #     return Response(
            #         {"error": "You are not authorized to retrieve sales."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            today = timezone.now().date()
            sales_data = []

            for i in range(6, -1, -1):  # Start from 6 days ago to today
                day = today - timedelta(days=i)
                orders = Order.objects.filter(
                    order_date__date=day,
                    user_email=user.email,
                    status="Done", 
                    payment_status='Paid'
                )
                total_sales = orders.aggregate(total_sales=Sum('total_amount'))['total_sales'] or 0
                sales_data.append({
                    "period": day.strftime("%A"),  # Day name, e.g., "Monday"
                    "sales": float(total_sales)
                })

            return Response(sales_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred while retrieving last seven days sales. {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class MonthlySalesEachUserAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser or user.role == 'Salesman' or user.role == 'Sales Manager'):
            #     return Response(
            #         {"error": "You are not authorized to retrieve sales."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            today = timezone.now().date()
            year = today.year
            sales_data = []

            for month in range(1, 13):
                orders = Order.objects.filter(
                    order_date__year=year,
                    order_date__month=month,
                    user_email=user.email,
                    status="Done", 
                    payment_status='Paid'
                )
                total_sales = orders.aggregate(total_sales=Sum('total_amount'))['total_sales'] or 0
                sales_data.append({
                    "period": calendar.month_name[month],
                    "sales": float(total_sales)
                })

            return Response(sales_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred while retrieving monthly sales. {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class YearlySalesEachUserAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            # if not (user.role == 'Manager' or user.is_superuser or user.role == 'Salesman' or user.role == 'Sales Manager'):
            #     return Response(
            #         {"error": "You are not authorized to retrieve sales."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            today = timezone.now().date()
            year = today.year

            orders = Order.objects.filter(
                order_date__year=year,
                user_email=user.email,
                status="Done", 
                payment_status='Paid'
            )
            total_sales = orders.aggregate(total_sales=Sum('total_amount'))['total_sales'] or 0

            data = [{
                "period": str(year),
                "sales": float(total_sales)
            }]

            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred while retrieving yearly sales. {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ------------------------------------- All V Logs --------------------------------------------------

class VehiclePartRequestLogAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            vehicle_part_request_log = VehiclePartRequestLog.objects.all()

            serializer = VehiclePartRequestLogSerializer(vehicle_part_request_log, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)       
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Vehicle Part Request Logs.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VehiclePartRequestItemLogAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            vehicle_part_request_item_log = VehiclePartRequestItemLog.objects.all()

            serializer = VehiclePartRequestItemLogSerializer(vehicle_part_request_item_log, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)       
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Vehicle Part Request Item Logs.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class VehicleOldPartDeliveryLogAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            vehicle_old_part_delivery_log = VehicleOldPartDeliveryLog.objects.all()

            serializer = VehicleOldPartDeliveryLogSerializer(vehicle_old_part_delivery_log, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)       
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Vehicle Old Part Delivery Logs.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VehicleOldPartDeliveryItemLogAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            vehicle_old_part_delivery_item_log = VehicleOldPartDeliveryItemLog.objects.all()

            serializer = VehicleOldPartDeliveryItemLogSerializer(vehicle_old_part_delivery_item_log, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)       
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Vehicle Old Part Delivery Item Logs.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VehicleOrderVoucherLogAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            vehicle_order_voucher_log = VehicleOrderVoucherLog.objects.all()

            serializer = VehicleOrderVoucherLogSerializer(vehicle_order_voucher_log, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)       
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Vehicle Order Voucher Logs.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VehicleOrderVoucherItemLogAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): 
        try:     
            vehicle_order_voucher_item_log = VehicleOrderVoucherItemLog.objects.all()

            serializer = VehicleOrderVoucherItemLogSerializer(vehicle_order_voucher_item_log, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)       
        except KeyError as e:
            return Response(
                {"error": f"An error occurred while Retriving the Vehicle Order Voucher Item Logs.  {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )





class RetriveTotalRevenueAPIView(APIView):
    def get(self, request): 
        try:
            
            # Get all paid and done orders
            non_cancelled_orders = Order.objects.exclude(status="Cancelled")
            paid_invoice = Invoice.objects.all()

            orders_revenue = non_cancelled_orders.aggregate(total_orders_revenue=Sum('paid_amount'))['total_orders_revenue']
            invoices_revenue = paid_invoice.aggregate(total_invoice_revenue=Sum('paid_amount'))['total_invoice_revenue']

            # Handle potential None values from aggregation
            total_revenue = (orders_revenue or 0) + (invoices_revenue or 0)

            return Response({"total_revenue": total_revenue}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred while retrieving the revenue. {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
