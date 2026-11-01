from django.contrib import admin
from .models import ( 
    Customer, Vehicle, Service, ServicePackage,  Invoice, JobCard, JobCardAssignment,
    VehicleAcceptance, VehicleOldPartDelivery, VehicleOldPartDeliveryItems, 
    VehicleOrderVoucher, VehicleOrderVoucherItems, VehiclePartRequest, VehiclePartRequestItems, )
# Register your models here.



# # Custom admin for Customer to show all fields as headers
# @admin.register(Customer)
# class CustomerAdmin(admin.ModelAdmin):
#     list_display = ('name', 'phone', 'email', 'address')  # Add every field you want as a column header
    


# def all_fields(model):
#     return [field.name for field in model._meta.fields]

def all_fields(model):
    return [field.name for field in model._meta.fields if field.name != 'id']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = all_fields(Customer)

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = all_fields(Vehicle)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = all_fields(Service)

@admin.register(ServicePackage)
class ServicePackageAdmin(admin.ModelAdmin):
    list_display = all_fields(ServicePackage)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = all_fields(Invoice)

@admin.register(JobCard)
class JobCardAdmin(admin.ModelAdmin):
    list_display = all_fields(JobCard)

@admin.register(JobCardAssignment)
class JobCardAssignmentAdmin(admin.ModelAdmin):
    list_display = all_fields(JobCardAssignment)


@admin.register(VehicleAcceptance)
class VehicleAcceptanceAdmin(admin.ModelAdmin):
    list_display = all_fields(VehicleAcceptance)

@admin.register(VehicleOldPartDelivery)
class VehicleOldPartDeliveryAdmin(admin.ModelAdmin):
    list_display = all_fields(VehicleOldPartDelivery)

@admin.register(VehicleOldPartDeliveryItems)
class VehicleOldPartDeliveryItemsAdmin(admin.ModelAdmin):
    list_display = all_fields(VehicleOldPartDeliveryItems)

@admin.register(VehicleOrderVoucher)
class VehicleOrderVoucherAdmin(admin.ModelAdmin):
    list_display = all_fields(VehicleOrderVoucher)

@admin.register(VehicleOrderVoucherItems)
class VehicleOrderVoucherItemsAdmin(admin.ModelAdmin):
    list_display = all_fields(VehicleOrderVoucherItems)

@admin.register(VehiclePartRequest)
class VehiclePartRequestAdmin(admin.ModelAdmin):
    list_display = all_fields(VehiclePartRequest)

@admin.register(VehiclePartRequestItems)
class VehiclePartRequestItemsAdmin(admin.ModelAdmin):
    list_display = all_fields(VehiclePartRequestItems)
# The above code registers the models with the Django admin site.
# This allows the models to be managed through the Django admin interface.