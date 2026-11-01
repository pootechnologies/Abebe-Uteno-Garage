from django.db import models
from django.db.models import JSONField
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_save
from django.contrib.auth import get_user_model
from django.db.models import UniqueConstraint
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal
import json
import sys
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile

User = get_user_model()

class Customer(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    tin_number = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(blank=True, null=True)
    organization = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)

    def __str__(self):
        return self.name


class CompanyInfo(models.Model):
    en_name = models.CharField(max_length=255, default="Company", null=True, blank=True)
    am_name = models.CharField(max_length=255, default="Company", null=True, blank=True)
    owner_en_name = models.CharField(max_length=255, default="Mubarek", null=True, blank=True)
    owner_am_name = models.CharField(max_length=255, default="Company", null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    phone1 = models.CharField(max_length=255, null=True, blank=True)
    phone2 = models.CharField(max_length=255, null=True, blank=True)
    bank_accounts = models.JSONField(default=dict, null=True, blank=True)
    tin_number = models.CharField(max_length=255, null=True, blank=True)
    vat_number = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    region = models.CharField(max_length=255, null=True, blank=True)
    zone = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    sub_city = models.CharField(max_length=255, null=True, blank=True)
    logo = models.ImageField(upload_to='company/', null=True, blank=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['en_name', 'am_name', 'tin_number'], name='unique_company_fields')
        ]

    def __str__(self):
        return self.en_name
    
    def save(self, *args, **kwargs):
        if self.logo:
            # 1. Open the uploaded image using Pillow
            img = Image.open(self.logo)
            
            # 2. Convert to RGB (JPEG requires RGB; handles PNG/RGBA/P palettes)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # 3. Resize pixel dimensions (Crucial for getting WebP-like small file sizes)
            max_dimensions = (1200, 1200)
            img.thumbnail(max_dimensions, Image.Resampling.LANCZOS)
            
            # 4. Create in-memory buffer
            output_io = BytesIO()
            
            # 5. Save with advanced JPEG optimization settings
            img.save(
                output_io, 
                format='JPEG', 
                quality=70,          # Sweet spot for quality vs size
                optimize=True,       # Extra pass to compress Huffman tables (saves 5-10% space)
                progressive=True,    # Encodes progressively (smaller file + faster web rendering)
                subsampling=2        # 4:2:0 chroma subsampling for lower file footprint
            )
            output_io.seek(0)
            
            # 6. Re-assign compressed JPEG back to ImageField
            base_name = self.logo.name.rsplit('.', 1)[0]
            self.logo = InMemoryUploadedFile(
                output_io, 
                'ImageField', 
                f"{base_name}.jpg", 
                'image/jpeg', 
                sys.getsizeof(output_io), 
                None
            )
            
        super().save(*args, **kwargs)

class Category(models.Model):
    name = models.CharField(max_length=100, default='', unique=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)

    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    contact_info = models.CharField(max_length=50, null=True, blank=True)
    tin_number = models.CharField(max_length=50, null=True, blank=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200, blank=False, null=False)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    package = models.IntegerField(null=True, blank=True)
    piece = models.IntegerField(null=True, blank=True)
    buying_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=255, null=True, blank=True)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.IntegerField(null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    part_number = models.CharField(max_length=255, null=True, blank=True)
    receipt_no = models.IntegerField(null=True, blank=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.image:
            img = Image.open(self.image)
            
            # --- THIS IS THE MISSING PIECE ---
            # It downsizes the massive pixel grid to a web-friendly size
            max_dimensions = (1200, 1200)
            img.thumbnail(max_dimensions, Image.Resampling.LANCZOS)
            # ----------------------------------

            output_io = BytesIO()
            img.save(output_io, format='WEBP', quality=70) # Or 'JPEG'
            output_io.seek(0)
            
            base_name = self.image.name.split('.')[0]
            self.image = InMemoryUploadedFile(
                output_io, 'ImageField', f"{base_name}.webp", 'image/webp', sys.getsizeof(output_io), None
            )
            
        super().save(*args, **kwargs)

class Order(models.Model):
    ACTION_CHOICES = [
        ('Receipt', 'Receipt'),
        ('No Receipt', 'No Receipt')
    ]

    PAYMENT_STATUS=[
        ('Paid','Paid'),
        ('Unpaid','Unpaid'),
        ('Pending','Pending')
    ]

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=100, choices=(('Cancelled', 'Cancelled'), ('Pending', 'Pending'), ('Done', 'Done')), default="Done", null=True, blank=True)
    receipt = models.CharField(max_length=255, choices=ACTION_CHOICES, default="Receipt", null=True, blank=True)
    receipt_id = models.CharField(max_length=255, null=True, blank=True)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    vat = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS, default='Paid')
    paid_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00, null=True, blank=True)
    unpaid_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    number_of_items = models.IntegerField(null=True, blank=True)
    credit = models.BooleanField(default=False, null=True, blank=True)
    performa = models.BooleanField(default=False, null=True, blank=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)
    user_email = models.CharField(max_length=255, default="User@gmail.com", null=True, blank=True)
    user_role = models.CharField(max_length=255, default="Salesman", null=True, blank=True)
    item_pending = models.PositiveIntegerField(null=True, blank=True)

    def str(self):
        return self.customer
    
    # @property
    def is_empty(self):
        return not self.items.exists() 

    def get_sub_total_price(self):
        """Calculate the total price of the entire order."""
        return sum(item.get_price() for item in self.items.all())
    
    def check_and_delete_if_no_items(self):
        if not self.items.exists():
            self.delete()

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    package = models.PositiveIntegerField(null=True, blank=True)
    unit = models.CharField(max_length=255, default="Pcs", null=True, blank=True)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    item_receipt = models.CharField(max_length=255, default="No Receipt", null=True, blank=True)
    status = models.CharField(max_length=100, choices=(('Cancelled', 'Cancelled'), ('Pending', 'Pending'), ('Done', 'Done')), default="Done", null=True, blank=True)

    def str(self):
        return self.product
    
    def get_price(self):
        """Calculate the total price of this item."""
        return self.price  # Now it returns the stored price
    
    def get_cost(self):
        """Calculate the total price of this item."""
        if self.product.buying_price is not None:
            if self.package is not None and self.product.piece is not None:
                cost = self.product.buying_price * (self.package * self.product.piece)
            elif self.quantity is not None:
                cost = self.product.buying_price * self.quantity
            return cost
        else:
            # If buying_price is None, return 0 or handle as needed
            return Decimal('0.00')
        
    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        order.check_and_delete_if_no_items()




class CreditCustomer(models.Model):
    status = (
        ('Paid', 'Paid'),
        ('Unpaid', 'Unpaid'),
        ('Pending', 'Pending')
    )
    customer = models.OneToOneField(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=50, choices=status, default='Pending')
    paid_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00, null=True, blank=True)
    unpaid_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00, null=True, blank=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)

    def __str__(self):
        return f"{self.user}"

class CreditCredit(models.Model):
    status=(
        ('Paid','Paid'),
        ('Unpaid','Unpaid'),
        ('Pending','Pending')
    )
    ACTION_CHOICES = [
        ('Receipt', 'Receipt'),
        ('No Receipt', 'No Receipt')
    ]
    credit_date = models.DateTimeField(auto_now_add=True)
    customer = models.CharField(max_length=255, null=True, blank=True)
    performa = models.BooleanField(default=False, null=True, blank=True)
    number_of_items = models.IntegerField(null=True, blank=True)
    receipt = models.CharField(max_length=255, choices=ACTION_CHOICES, default="Receipt", null=True, blank=True)
    sub_total = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    vat = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=50, choices=status, default='Pending')
    paid_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00, null=True, blank=True)
    unpaid_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00, null=True, blank=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)
    customer_level = models.ForeignKey(CreditCustomer, related_name='credits', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.user}"

class CreditProduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    part_number = models.CharField(max_length=255, default="", null=True, blank=True)
    unit = models.CharField(max_length=255, default="Pcs", null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    credit = models.ForeignKey(CreditCredit, related_name='products', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.description} - {self.total_price}"




class Vehicle(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    license_plate = models.CharField(max_length=20, null=True, blank=True)
    motor_kutir = models.CharField(max_length=50, null=True, blank=True)
    shanci_kutir = models.CharField(max_length=50, null=True, blank=True)
    model = models.CharField(max_length=50, null=True, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    color = models.CharField(max_length=30, null=True, blank=True)
    image = models.ImageField(upload_to='vehicle/', null=True, blank=True)
    image2 = models.ImageField(upload_to='vehicle/', null=True, blank=True)
    image3 = models.ImageField(upload_to='vehicle/', null=True, blank=True)
    image4 = models.ImageField(upload_to='vehicle/', null=True, blank=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)

    def __str__(self):
        return f"{self.license_plate} - {self.model}"
    
    def save(self, *args, **kwargs):
        if self.image:
            img = Image.open(self.image)
            
            # --- THIS IS THE MISSING PIECE ---
            # It downsizes the massive pixel grid to a web-friendly size
            max_dimensions = (1200, 1200)
            img.thumbnail(max_dimensions, Image.Resampling.LANCZOS)
            # ----------------------------------

            output_io = BytesIO()
            img.save(output_io, format='WEBP', quality=70) # Or 'JPEG'
            output_io.seek(0)
            
            base_name = self.image.name.split('.')[0]
            self.image = InMemoryUploadedFile(
                output_io, 'ImageField', f"{base_name}.webp", 'image/webp', sys.getsizeof(output_io), None
            )
            
        super().save(*args, **kwargs)


class Service(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    part_number = models.CharField(max_length=255, default="", null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    duration = models.CharField(max_length=255, null=True, blank=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)

    def __str__(self):
        return self.name

class ServicePackage(models.Model):
    PACKAGE_CHOICES = (
        ('Service A', 'Service A'),
        ('Service B', 'Service B'),
        ('Service C', 'Service C'),
        ('Service D', 'Service D'),
    )
    name = models.CharField(max_length=10, choices=PACKAGE_CHOICES, unique=True, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    duration = models.CharField(max_length=255, null=True, blank=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)
    
    def __str__(self):
        return self.name



class JobCard(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('waiting_parts', 'Waiting for Parts'),
        ('completed', 'Completed'),
    )

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True) # this should be a dropdown from user list.
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    service_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True, null=True)
    receipt_id = models.CharField(max_length=255, null=True, blank=True)
    odometer_reading = models.PositiveIntegerField(null=True, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)

    def __str__(self):
        return f"JobCard {self.id} - {self.vehicle}"



class JobCardAssignment(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('waiting_parts', 'Waiting for Parts'),
        ('completed', 'Completed'),
    )
    job_card = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='assignments', null=True, blank=True)
    worker = models.ForeignKey(User, on_delete=models.SET_NULL, limit_choices_to={'groups__name__in': ['Mechanic', 'Electrician', 'Paint Worker']}, null=True, blank=True) # Technical Examiner should be removed
    services = models.ManyToManyField(Service, through='AssignedService')
    service_package = models.ForeignKey(ServicePackage, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    package_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    examiner_comment = models.TextField(blank=True, null=True)
    task_description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.id} - {self.worker} assigned to {self.services} for JobCard {self.job_card.id}"




class AssignedService(models.Model):

    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('waiting_parts', 'Waiting for Parts'),
        ('completed', 'Completed'),
    )
    assignment = models.ForeignKey('JobCardAssignment', on_delete=models.CASCADE, related_name='assigned_services')
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('assignment', 'service')

    def __str__(self):
        return f"{self.assignment.worker} - {self.service.name} ({self.status})"


class Invoice(models.Model):
    PAYMENT_STATUS = (
        ('Paid', 'Paid'),
        ('Unpaid', 'Unpaid'),
        ('Pending', 'Pending')
    )

    job_card = models.OneToOneField(JobCard, on_delete=models.SET_NULL, related_name='invoice', null=True, blank=True)
    invoice_date = models.DateTimeField(auto_now_add=True)
    sub_total = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    vat = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unpaid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='Unpaid')
    user = models.CharField(max_length=255, default="User", null=True, blank=True)

    def __str__(self):
        return f"Invoice {self.id} - {self.payment_status}"


# New Performa
class PerformaCustomer(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)

    def __str__(self):
        return f"{self.user}"

class PerformaPerforma(models.Model):
    ACTION_CHOICES = [
        ('Receipt', 'Receipt'),
        ('No Receipt', 'No Receipt')
    ]
    customer = models.CharField(max_length=255, null=True, blank=True)
    customer_id = models.CharField(max_length=255, null=True, blank=True)
    issued_date = models.DateTimeField(auto_now_add=True)
    receipt = models.CharField(max_length=255, choices=ACTION_CHOICES, default="Receipt", null=True, blank=True)
    sub_total = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    vat = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    service_charge = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    products_service_charge = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    products_only_total = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    number_of_items = models.IntegerField(null=True, blank=True)
    credit = models.BooleanField(default=False, null=True, blank=True)
    shanci_kutir = models.CharField(max_length=255, null=True, blank=True)
    targa_kutir = models.CharField(max_length=255, null=True, blank=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)
    customer_level = models.ForeignKey(PerformaCustomer, related_name='performas', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.user}"

class PerformaProduct(models.Model):
    # product = models.CharField(max_length=255, default="Product", null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    part_number = models.CharField(max_length=255, default="", null=True, blank=True)
    unit = models.CharField(max_length=255, default="Pcs", null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    product_service_charge = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    performa = models.ForeignKey(PerformaPerforma, related_name='products', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.description} - {self.total_price}"





class VehicleAcceptance(models.Model):
    
    # Header Section
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    ken = models.DateTimeField(auto_now_add=True)

    # 1. Motor Part
    ye_fren_zeyt = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_meri_zeyt = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_motor_zeyt = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_radiator = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    battery = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    zinab_metregya = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")

    # 2. Outer Part
    maskerya = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    antenna = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ferfango = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'left' and 'right' boolean values")
    ye_fit_mebrat = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    frecha_mebrat = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'left' and 'right' boolean values")
    makomiya_mebrat = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'left' and 'right' boolean values")
    ye_fit_targa = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'left' and 'right' boolean values")
    nifas_mekelakeya = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'left' and 'right' boolean values")
    spekiyo = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'left' and 'right' boolean values")
    ye_ber_ijeta = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ika_mekelakeya = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_sivat_kidan = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_huala_targa = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_huala_mebrat_birchiko = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_ber_gomini_mestawat_lstic_frame = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_fit_prawlit = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_zinab_metregiya_ye_bilon_kidan = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'left' and 'right' boolean values")
    birjineri_bilon = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_huala_prawlit_antsebaraki = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_fit_igir_fren_lock = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_huala_goma_libs = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    fortomegala = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    eskort_goma_mefcha = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")

    # 3. Inner Part
    tiras = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    meterkosha = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_welel_mintaf = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_wember_libs = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_wist_spekiyo = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_wist_mebrat = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    tep = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    isat_adega_mekelakeya = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    mebrat_mabriya = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    zinab_metregiya_mebrat = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    nedaj = models.CharField(max_length=255, null=True, blank=True, default="")
    ye_tsehay_mekelakeya = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_wist_ber_mekfecha = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_mestewat_mawcha_mawreja = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_fit_ye_kofen_amorzrater = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_huala_ye_kofen_amorzrater = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    klaks = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_wist_dashboard_kis_kulf = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_kofen_gomini = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    ye_wuha_mercha = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")

    # 4. Outer Condition
    ye_ginbar_mestewat = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    antsebaraki = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    # goma = models.CharField(
    #     max_length=10,
    #     choices=[('new', 'New'), ('mid', 'Mid'), ('old', 'Old')],
    #     blank=True,
    #     null=True
    # )
    goma = models.CharField(max_length=255, null=True, blank=True, default="")
    kirk = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    goma_mefcha = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    eskort_goma = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")
    kolenet = models.CharField(max_length=255, null=True, blank=True, default="")
    ye_cherke_get = models.JSONField(default=dict, blank=True, null=True, help_text="Dictionary with 'have' and 'don't_have' and 'broken' boolean values")

    # Footer Section
    asrekabi_sim = models.ForeignKey(Customer, on_delete=models.SET_NULL, related_name='customer_workers_acceptance', null=True, blank=True)
    firma = models.CharField(max_length=100, null=True, blank=True)
    ken_footer = models.DateTimeField(auto_now_add=True)
    terekabi_sim = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='asrekabi_workers_acceptance', null=True, blank=True)
    firma_2 = models.CharField(max_length=100, null=True, blank=True)
    ken_2 = models.DateTimeField(auto_now_add=True)
    ye_miwetabet_ken = models.DateField(null=True, blank=True)
    job_card = models.ForeignKey(JobCard, on_delete=models.SET_NULL, related_name='vehicle_acceptances', null=True, blank=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)

    def __str__(self):
        return f"VehicleAcceptance - {self.vehicle} - {self.ken}"



class VehicleOrderVoucher(models.Model):
    # Header Section
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    ken = models.DateTimeField(auto_now_add=True)

    # Footer Section
    asrekabi_sim = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='asrekabi_workers_order_voucher', null=True, blank=True)
    asrekabi_firma = models.CharField(max_length=100, null=True, blank=True)
    asrekabi_ken = models.DateTimeField(auto_now_add=True)
    terekabi_sim = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='terekabi_workers_order_voucher', null=True, blank=True)
    terekabi_firma = models.CharField(max_length=100, null=True, blank=True)
    terekabi_ken = models.DateTimeField(auto_now_add=True)
    ye_merekebiya_ken = models.DateField(null=True, blank=True)


    # Associated User
    job_card = models.OneToOneField(JobCard, on_delete=models.SET_NULL, related_name='vehicle_order_vouchers', null=True, blank=True)

    user = models.CharField(max_length=255, default="User", null=True, blank=True)
    

    def __str__(self):
        return f"VehicleAcceptance - {self.model} - {self.ken}"

class VehicleOrderVoucherItems(models.Model):
    voucher_order = models.ForeignKey(VehicleOrderVoucher, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=100, null=True, blank=True)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    fixed_parts = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.item_name
    


class VehicleOldPartDelivery(models.Model):
    # Header Section
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    tegagn_mechanic = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='terekabi_workers_old_part_delivery', null=True, blank=True)
    ken = models.DateTimeField(auto_now_add=True)

    # Footer Section
    asrekabi_sim = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='asrekabi_workers_old_part_delivery', null=True, blank=True)
    asrekabi_firma = models.CharField(max_length=100, null=True, blank=True)
    asrekabi_ken = models.DateTimeField(auto_now_add=True)
    terekabi_sim = models.ForeignKey(Customer, on_delete=models.SET_NULL,  null=True, blank=True)
    terekabi_firma = models.CharField(max_length=100, null=True, blank=True)
    terekabi_ken = models.DateTimeField(auto_now_add=True)

    # Associated User
    job_card = models.OneToOneField(JobCard, on_delete=models.SET_NULL, related_name='vehicle_old_parts', null=True, blank=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)

    def __str__(self):
        return f"Vehicle Old Part Return - {self.model} - {self.ken}"
    
class VehicleOldPartDeliveryItems(models.Model):
    old_part = models.ForeignKey(VehicleOldPartDelivery, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    fixed_parts = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.fixed_parts



class VehiclePartRequest(models.Model):
    # Header Section
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    ken = models.DateTimeField(auto_now_add=True)

    # Footer Section
    asrekabi_sim = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='asrekabi_workers_part_request', null=True, blank=True)
    asrekabi_firma = models.CharField(max_length=100, null=True, blank=True)
    asrekabi_ken = models.DateTimeField(auto_now_add=True)
    terekabi_sim = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='terekabi_workers_part_request', null=True, blank=True)
    terekabi_firma = models.CharField(max_length=100, null=True, blank=True)
    terekabi_ken = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Associated User
    job_card = models.OneToOneField(JobCard, on_delete=models.SET_NULL, related_name='vehicle_part_requests', null=True, blank=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)

    def __str__(self):
        return f"Vehicle Part Request - {self.vehicle} - {self.ken} - {self.total_amount}"
    
class VehiclePartRequestItems(models.Model):
    part_request = models.ForeignKey(VehiclePartRequest, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.item_name


class VehiclePartRequestReport(models.Model):
    user = models.CharField(max_length=50, default="user", blank=True, null=True)
    customer_name = models.CharField(max_length=255, default="Customer", null=True, blank=True)
    customer_phone = models.CharField(max_length=255, default="Customer", null=True, blank=True)
    customer_tin_number = models.CharField(max_length=255, default="Customer", null=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    product_name = models.CharField(max_length=255, default="Product", null=True, blank=True)
    product_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)

    def __str__(self):
        return self.user


class PurchaseSupplier(models.Model):
    status = (
        ('Paid', 'Paid'),
        ('Unpaid', 'Unpaid'),
        ('Pending', 'Pending')
    )
    supplier = models.OneToOneField(Supplier, on_delete=models.SET_NULL, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=50, choices=status, default='Pending')
    paid_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00, null=True, blank=True)
    unpaid_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00, null=True, blank=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)

    def __str__(self):
        return f"{self.user}"

class PurchaseExpense(models.Model):
    status=(
        ('Paid','Paid'),
        ('Unpaid','Unpaid'),
        ('Pending','Pending')
    )
    purchase_date = models.DateTimeField(auto_now_add=True)
    supplier = models.CharField(max_length=255, null=True, blank=True)
    number_of_items = models.IntegerField(null=True, blank=True)
    total = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=50, choices=status, default='Pending')
    paid_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00, null=True, blank=True)
    unpaid_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00, null=True, blank=True)
    user = models.CharField(max_length=255, default="User", null=True, blank=True)
    supplier_level = models.ForeignKey(PurchaseSupplier, related_name='expenses', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.user}"

class PurchaseProduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.CharField(max_length=255, default="Pcs", null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    expense = models.ForeignKey(PurchaseExpense, related_name='products', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.description} - {self.total_price}"


class Report(models.Model):
    user = models.CharField(max_length=50, default="user", blank=True, null=True)
    customer_name = models.CharField(max_length=255, default="Customer", null=True, blank=True)
    customer_phone = models.CharField(max_length=255, default="Customer", null=True, blank=True)
    customer_tin_number = models.CharField(max_length=255, default="Customer", null=True, blank=True)
    order_date = models.DateField(auto_now_add=True)
    order_id = models.IntegerField(null=True, blank=True)
    item_receipt = models.CharField(max_length=255, default="No Receipt", null=True, blank=True)
    product_name = models.CharField(max_length=255, default="", null=True, blank=True)
    unit = models.CharField(max_length=255, default="Pcs", null=True, blank=True)
    product_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.IntegerField()
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    vat = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=50, default='Paid', null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  

    def __str__(self):
        return self.user


class OrderLog(models.Model):
    ACTION_CHOICES = [
        ('Create', 'Create'),
        ('Update', 'Update'),
        ('Delete', 'Delete'),
    ]
    
    user = models.CharField(max_length=255, default="User", null=True, blank=True)
    action = models.CharField(max_length=100, choices=ACTION_CHOICES, null=True, blank=True)
    model_name = models.CharField(max_length=50, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)  # ID of the object affected
    timestamp = models.DateTimeField(auto_now_add=True)
    customer_info = models.CharField(max_length=255, default="Customer", null=True, blank=True)
    product_name = models.CharField(max_length=255, default="Product", null=True, blank=True)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    changes_on_update = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.action} - {self.model_name} ({self.object_id}) at {self.timestamp}"

class SupplierPaymentLog(models.Model):
    supplier = models.ForeignKey(PurchaseSupplier, on_delete=models.SET_NULL, related_name='logs', null=True, blank=True)
    change_type = models.CharField(max_length=255)
    field_name = models.CharField(max_length=100)
    old_value = models.CharField(max_length=255, null=True, blank=True)
    new_value = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.CharField(max_length=255, null=True, blank=True)

class ExpensePaymentLog(models.Model):
    expense = models.ForeignKey(PurchaseExpense, on_delete=models.SET_NULL, related_name='logs', null=True, blank=True)
    supplier = models.CharField(max_length=255, null=True, blank=True)
    change_type = models.CharField(max_length=255)
    field_name = models.CharField(max_length=100)
    old_value = models.CharField(max_length=255, null=True, blank=True)
    new_value = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.CharField(max_length=255, null=True, blank=True)

class OrderPaymentLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, related_name='logs', null=True, blank=True)
    customer = models.CharField(max_length=255, null=True, blank=True, default="Customer")
    change_type = models.CharField(max_length=255)
    field_name = models.CharField(max_length=100)
    old_value = models.CharField(max_length=255, null=True, blank=True)
    new_value = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.CharField(max_length=255, null=True, blank=True)


class JobCardLog(models.Model):
    ACTION_CHOICES = [
        ('Create', 'Create'),
        ('Update', 'Update'),
        ('Delete', 'Delete'),
    ]

    user = models.CharField(max_length=255, default="User", null=True, blank=True)
    action = models.CharField(max_length=100, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50, default='JobCard')
    object_id = models.PositiveIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # snapshot of important fields for convenience
    customer = models.CharField(max_length=255, null=True, blank=True)
    vehicle = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    odometer_reading = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    # JSON string of field diffs on update: {"field": {"old": ..., "new": ...}, ...}
    changes_on_update = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.action} - {self.model_name} ({self.object_id}) at {self.timestamp}"


# Add near the other log models
class JobCardAssignmentLog(models.Model):
    ACTION_CHOICES = [('Create','Create'), ('Update','Update'), ('Delete','Delete')]

    user = models.CharField(max_length=255, null=True, blank=True, default="User")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50, default='JobCardAssignment')
    object_id = models.PositiveIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # snapshot fields
    job_card_id = models.PositiveIntegerField(null=True, blank=True)
    worker = models.CharField(max_length=255, null=True, blank=True)
    service_package = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    package_status = models.CharField(max_length=50, null=True, blank=True)
    task_description = models.CharField(max_length=255, null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # on update: JSON diff string -> {"field": {"old":..., "new":...}}
    changes_on_update = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.action} - {self.model_name} ({self.object_id}) at {self.timestamp}"


class AssignedServiceLog(models.Model):
    ACTION_CHOICES = [('Create','Create'), ('Update','Update'), ('Delete','Delete')]

    user = models.CharField(max_length=255, null=True, blank=True, default="User")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50, default='AssignedService')
    object_id = models.PositiveIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # snapshot fields
    assignment_id = models.PositiveIntegerField(null=True, blank=True)
    worker = models.CharField(max_length=255, null=True, blank=True)   # from assignment.worker.name
    job_card_id = models.PositiveIntegerField(null=True, blank=True)    # from assignment.job_card_id
    service = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    changes_on_update = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.action} - {self.model_name} ({self.object_id}) at {self.timestamp}"


class VehiclePartRequestLog(models.Model):
    ACTION_CHOICES = [('Create','Create'), ('Update','Update'), ('Delete','Delete')]
    user = models.CharField(max_length=255, null=True, blank=True, default="User")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50, default='VehiclePartRequest')
    object_id = models.PositiveIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    job_card_id = models.PositiveIntegerField(null=True, blank=True)
    customer = models.CharField(max_length=255, null=True, blank=True)
    vehicle = models.CharField(max_length=255, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    asrekabi = models.CharField(max_length=255, null=True, blank=True)
    terekabi = models.CharField(max_length=255, null=True, blank=True)

    changes_on_update = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.action} - {self.model_name} ({self.object_id}) at {self.timestamp}"


class VehiclePartRequestItemLog(models.Model):
    ACTION_CHOICES = [('Create','Create'), ('Update','Update'), ('Delete','Delete')]
    user = models.CharField(max_length=255, null=True, blank=True, default="User")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50, default='VehiclePartRequestItems')
    object_id = models.PositiveIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    part_request_id = models.PositiveIntegerField(null=True, blank=True)
    product = models.CharField(max_length=255, null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    changes_on_update = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.action} - {self.model_name} ({self.object_id}) at {self.timestamp}"




class VehicleOldPartDeliveryLog(models.Model):
    ACTION_CHOICES = [('Create','Create'), ('Update','Update'), ('Delete','Delete')]
    user = models.CharField(max_length=255, null=True, blank=True, default="User")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50, default='VehicleOldPartDelivery')
    object_id = models.PositiveIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    job_card_id = models.PositiveIntegerField(null=True, blank=True)
    tegagn_mechanic = models.CharField(max_length=255, null=True, blank=True)
    vehicle = models.CharField(max_length=255, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    asrekabi = models.CharField(max_length=255, null=True, blank=True)
    terekabi = models.CharField(max_length=255, null=True, blank=True)

    changes_on_update = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.action} - {self.model_name} ({self.object_id}) at {self.timestamp}"


class VehicleOldPartDeliveryItemLog(models.Model):
    ACTION_CHOICES = [('Create','Create'), ('Update','Update'), ('Delete','Delete')]
    user = models.CharField(max_length=255, null=True, blank=True, default="User")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50, default='VehicleOldPartDeliveryItems')
    object_id = models.PositiveIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    old_part_id = models.PositiveIntegerField(null=True, blank=True)
    product = models.CharField(max_length=255, null=True, blank=True)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    fixed_parts = models.CharField(max_length=255, null=True, blank=True)

    changes_on_update = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.action} - {self.model_name} ({self.object_id}) at {self.timestamp}"





class VehicleOrderVoucherLog(models.Model):
    ACTION_CHOICES = [('Create','Create'), ('Update','Update'), ('Delete','Delete')]
    user = models.CharField(max_length=255, null=True, blank=True, default="User")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50, default='VehicleOrderVoucher')
    object_id = models.PositiveIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    job_card_id = models.PositiveIntegerField(null=True, blank=True)
    customer = models.CharField(max_length=255, null=True, blank=True)
    vehicle = models.CharField(max_length=255, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    asrekabi = models.CharField(max_length=255, null=True, blank=True)
    terekabi = models.CharField(max_length=255, null=True, blank=True)

    changes_on_update = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.action} - {self.model_name} ({self.object_id}) at {self.timestamp}"


class VehicleOrderVoucherItemLog(models.Model):
    ACTION_CHOICES = [('Create','Create'), ('Update','Update'), ('Delete','Delete')]
    user = models.CharField(max_length=255, null=True, blank=True, default="User")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50, default='VehicleOrderVoucherItems')
    object_id = models.PositiveIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    voucher_order_id = models.PositiveIntegerField(null=True, blank=True)
    item_name = models.CharField(max_length=255, null=True, blank=True)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    fixed_parts = models.CharField(max_length=255, null=True, blank=True)

    changes_on_update = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.action} - {self.model_name} ({self.object_id}) at {self.timestamp}"








# ========= Jobcard signals =========

@receiver(pre_save, sender=JobCard)
def jobcard_snapshot_before_update(sender, instance, **kwargs):
    # Store current DB state before update to diff in post_save
    if instance.pk:
        try:
            original = sender.objects.select_related('customer', 'vehicle').get(pk=instance.pk)
            instance._pre_save_snapshot = {
                'customer': original.customer.name if original.customer else None,
                'vehicle': str(original.vehicle) if original.vehicle else None,
                'status': original.status,
                'total_cost': str(original.total_cost) if original.total_cost is not None else None,
                'odometer_reading': original.odometer_reading,
                'notes': original.notes,
                'user': getattr(original, 'user', None),
            }
        except sender.DoesNotExist:
            instance._pre_save_snapshot = None
    else:
        instance._pre_save_snapshot = None


@receiver(post_save, sender=JobCard)
def jobcard_log_create_update(sender, instance, created, **kwargs):
    payload = {
        'user': getattr(instance, 'user', None),
        'object_id': instance.pk,
        'customer': instance.customer.name if instance.customer else None,
        'vehicle': str(instance.vehicle) if instance.vehicle else None,
        'status': instance.status,
        'total_cost': instance.total_cost,
        'odometer_reading': instance.odometer_reading,
        'notes': instance.notes,
    }

    if created:
        JobCardLog.objects.create(action='Create', **payload)
        return

    # Update: compute field diffs
    changes = {}
    snapshot = getattr(instance, '_pre_save_snapshot', None)
    current = {
        'customer': payload['customer'],
        'vehicle': payload['vehicle'],
        'status': payload['status'],
        'total_cost': str(payload['total_cost']) if payload['total_cost'] is not None else None,
        'odometer_reading': payload['odometer_reading'],
        'notes': payload['notes'],
        'user': payload['user'],
    }
    if snapshot is not None:
        for field, old_val in snapshot.items():
            new_val = current.get(field)
            if old_val != new_val:
                changes[field] = {'old': old_val, 'new': new_val}

    JobCardLog.objects.create(
        action='Update',
        changes_on_update=json.dumps(changes) if changes else None,
        **payload,
    )


@receiver(post_delete, sender=JobCard)
def jobcard_log_delete(sender, instance, **kwargs):
    JobCardLog.objects.create(
        action='Delete',
        user=getattr(instance, 'user', None),
        object_id=instance.pk,
        customer=instance.customer.name if instance.customer else None,
        vehicle=str(instance.vehicle) if instance.vehicle else None,
        status=instance.status,
        total_cost=instance.total_cost,
        odometer_reading=instance.odometer_reading,
        notes=instance.notes,
    )




# ========= JobCardAssignment signals =========

@receiver(pre_save, sender=JobCardAssignment)
def assignment_snapshot_before_update(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = sender.objects.select_related('worker', 'service_package', 'job_card').get(pk=instance.pk)
            instance._pre_save_snapshot = {
                'job_card_id': original.job_card_id,
                'worker': original.worker.name if original.worker else None,
                'service_package': original.service_package.name if original.service_package else None,
                'status': original.status,
                'package_status': original.package_status,
                'task_description': original.task_description,
                'started_at': original.started_at.isoformat() if original.started_at else None,
                'completed_at': original.completed_at.isoformat() if original.completed_at else None,
                'user': getattr(original, 'user', None),  # not present on model, but harmless
            }
        except sender.DoesNotExist:
            instance._pre_save_snapshot = None
    else:
        instance._pre_save_snapshot = None


@receiver(post_save, sender=JobCardAssignment)
def assignment_log_create_update(sender, instance, created, **kwargs):
    # actor attribution
    actor = getattr(instance, '_actor', None)
    if not actor and instance.job_card:
        actor = getattr(instance.job_card, 'user', None)

    payload = {
        'user': actor,
        'object_id': instance.pk,
        'job_card_id': instance.job_card_id,
        'worker': instance.worker.name if instance.worker else None,
        'service_package': instance.service_package.name if instance.service_package else None,
        'status': instance.status,
        'package_status': instance.package_status,
        'task_description': instance.task_description,
        'started_at': instance.started_at,
        'completed_at': instance.completed_at,
    }

    if created:
        JobCardAssignmentLog.objects.create(action='Create', **payload)
        return

    # update with diffs
    snapshot = getattr(instance, '_pre_save_snapshot', None)
    current = {
        'job_card_id': payload['job_card_id'],
        'worker': payload['worker'],
        'service_package': payload['service_package'],
        'status': payload['status'],
        'package_status': payload['package_status'],
        'task_description': payload['task_description'],
        'started_at': payload['started_at'].isoformat() if payload['started_at'] else None,
        'completed_at': payload['completed_at'].isoformat() if payload['completed_at'] else None,
        'user': payload['user'],
    }
    changes = {}
    if snapshot is not None:
        for k, old in snapshot.items():
            new = current.get(k)
            if old != new:
                changes[k] = {'old': old, 'new': new}

    JobCardAssignmentLog.objects.create(
        action='Update',
        changes_on_update=json.dumps(changes) if changes else None,
        **payload,
    )


@receiver(pre_delete, sender=JobCardAssignment) # <-- Changed to pre_delete
def assignment_log_delete(sender, instance, **kwargs):
    actor = getattr(instance, '_actor', None)
    if not actor and instance.job_card:  # <-- Safe now, JobCard still exists
        actor = getattr(instance.job_card, 'user', None)

    JobCardAssignmentLog.objects.create(
        action='Delete',
        user=actor,
        object_id=instance.pk,
        job_card_id=instance.job_card_id,
        worker=instance.worker.name if instance.worker else None,
        service_package=instance.service_package.name if instance.service_package else None,
        status=instance.status,
        package_status=instance.package_status,
        task_description=instance.task_description,
        started_at=instance.started_at,
        completed_at=instance.completed_at,
    )



# ========= AssignedService signals =========

@receiver(pre_save, sender=AssignedService)
def assigned_service_snapshot_before_update(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = sender.objects.select_related('assignment__worker', 'assignment__job_card', 'service').get(pk=instance.pk)
            instance._pre_save_snapshot = {
                'assignment_id': original.assignment_id,
                'worker': original.assignment.worker.name if (original.assignment and original.assignment.worker) else None,
                'job_card_id': original.assignment.job_card_id if original.assignment else None,
                'service': original.service.name if original.service else None,
                'status': original.status,
                'started_at': original.started_at.isoformat() if original.started_at else None,
                'completed_at': original.completed_at.isoformat() if original.completed_at else None,
            }
        except sender.DoesNotExist:
            instance._pre_save_snapshot = None
    else:
        instance._pre_save_snapshot = None


@receiver(post_save, sender=AssignedService)
def assigned_service_log_create_update(sender, instance, created, **kwargs):
    # actor attribution
    actor = getattr(instance, '_actor', None)
    if not actor and instance.assignment and instance.assignment.job_card:
        actor = getattr(instance.assignment.job_card, 'user', None)

    payload = {
        'user': actor,
        'object_id': instance.pk,
        'assignment_id': instance.assignment_id,
        'worker': instance.assignment.worker.name if (instance.assignment and instance.assignment.worker) else None,
        'job_card_id': instance.assignment.job_card_id if instance.assignment else None,
        'service': instance.service.name if instance.service else None,
        'status': instance.status,
        'started_at': instance.started_at,
        'completed_at': instance.completed_at,
    }

    if created:
        AssignedServiceLog.objects.create(action='Create', **payload)
        return

    snapshot = getattr(instance, '_pre_save_snapshot', None)
    current = {
        'assignment_id': payload['assignment_id'],
        'worker': payload['worker'],
        'job_card_id': payload['job_card_id'],
        'service': payload['service'],
        'status': payload['status'],
        'started_at': payload['started_at'].isoformat() if payload['started_at'] else None,
        'completed_at': payload['completed_at'].isoformat() if payload['completed_at'] else None,
        'user': payload['user'],
    }
    changes = {}
    if snapshot is not None:
        for k, old in snapshot.items():
            new = current.get(k)
            if old != new:
                changes[k] = {'old': old, 'new': new}

    AssignedServiceLog.objects.create(
        action='Update',
        changes_on_update=json.dumps(changes) if changes else None,
        **payload,
    )


@receiver(post_delete, sender=AssignedService)
def assigned_service_log_delete(sender, instance, **kwargs):
    actor = getattr(instance, '_actor', None)
    if not actor and instance.assignment and instance.assignment.job_card:
        actor = getattr(instance.assignment.job_card, 'user', None)

    AssignedServiceLog.objects.create(
        action='Delete',
        user=actor,
        object_id=instance.pk,
        assignment_id=instance.assignment_id,
        worker=instance.assignment.worker.name if (instance.assignment and instance.assignment.worker) else None,
        job_card_id=instance.assignment.job_card_id if instance.assignment else None,
        service=instance.service.name if instance.service else None,
        status=instance.status,
        started_at=instance.started_at,
        completed_at=instance.completed_at,
    )




# ========= VehiclePartRequest signals =========

@receiver(pre_save, sender=VehiclePartRequest)
def vpr_snapshot_before_update(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = sender.objects.select_related('customer', 'vehicle', 'job_card', 'asrekabi_sim', 'terekabi_sim').get(pk=instance.pk)
            instance._pre_save_snapshot = {
                'job_card_id': original.job_card_id,
                'customer': original.customer.name if original.customer else None,
                'vehicle': str(original.vehicle) if original.vehicle else None,
                'total_amount': str(original.total_amount) if original.total_amount is not None else None,
                'asrekabi': original.asrekabi_sim.name if original.asrekabi_sim else None,
                'terekabi': original.terekabi_sim.name if original.terekabi_sim else None,
                'user': getattr(original, 'user', None),
            }
        except sender.DoesNotExist:
            instance._pre_save_snapshot = None
    else:
        instance._pre_save_snapshot = None


@receiver(post_save, sender=VehiclePartRequest)
def vpr_log_create_update(sender, instance, created, **kwargs):
    payload = {
        'user': getattr(instance, 'user', None),
        'object_id': instance.pk,
        'job_card_id': instance.job_card_id,
        'customer': instance.customer.name if instance.customer else None,
        'vehicle': str(instance.vehicle) if instance.vehicle else None,
        'total_amount': instance.total_amount,
        'asrekabi': instance.asrekabi_sim.name if instance.asrekabi_sim else None,
        'terekabi': instance.terekabi_sim.name if instance.terekabi_sim else None,
    }
    if created:
        VehiclePartRequestLog.objects.create(action='Create', **payload)
        return

    snapshot = getattr(instance, '_pre_save_snapshot', None)
    current = {
        'job_card_id': payload['job_card_id'],
        'customer': payload['customer'],
        'vehicle': payload['vehicle'],
        'total_amount': str(payload['total_amount']) if payload['total_amount'] is not None else None,
        'asrekabi': payload['asrekabi'],
        'terekabi': payload['terekabi'],
        'user': payload['user'],
    }
    changes = {}
    if snapshot is not None:
        for k, old in snapshot.items():
            new = current.get(k)
            if old != new:
                changes[k] = {'old': old, 'new': new}

    VehiclePartRequestLog.objects.create(
        action='Update',
        changes_on_update=json.dumps(changes) if changes else None,
        **payload,
    )


# @receiver(post_save, sender=VehiclePartRequest)
# def update_invoice_on_vpr_change(sender, instance, **kwargs):
#     if instance.job_card and hasattr(instance.job_card, 'invoice'):
#         invoice = instance.job_card.invoice
#         job_card_cost = instance.job_card.total_cost or Decimal('0.00')
#         parts_cost = instance.total_amount or Decimal('0.00')
#         invoice.sub_total = job_card_cost + parts_cost
#         invoice.vat = invoice.sub_total * Decimal(0.15)
#         invoice.total_amount = invoice.sub_total + invoice.vat
#         invoice.unpaid_amount = invoice.total_amount - invoice.paid_amount
#         invoice.save()
#         print(f"Invoice total amount updated to after save: {invoice.total_amount}")
        
# @receiver(post_save, sender=VehiclePartRequest)
# def update_invoice_on_vpr_change(sender, instance, **kwargs):
#     if instance.job_card and hasattr(instance.job_card, 'invoice'):
#         invoice = instance.job_card.invoice
#         job_card_cost = instance.job_card.total_cost or Decimal('0.00')
#         parts_cost = instance.total_amount or Decimal('0.00')
#         invoice.sub_total = job_card_cost + parts_cost
#         invoice.vat = invoice.sub_total * Decimal(0.15)
#         invoice.total_amount = invoice.sub_total + invoice.vat
#         invoice.unpaid_amount = invoice.total_amount - invoice.paid_amount
#         invoice.save()
#         print(f"Invoice total amount updated to after save: {invoice.total_amount}")
        
# @receiver(post_delete, sender=VehiclePartRequest)
# def update_invoice_on_vpr_change_on_delete(sender, instance, **kwargs):
#     if instance.job_card and hasattr(instance.job_card, 'invoice'):
#         invoice = instance.job_card.invoice
#         job_card_cost = instance.job_card.total_cost or Decimal('0.00')
#         parts_cost = instance.total_amount or Decimal('0.00')
#         invoice.sub_total = job_card_cost
#         invoice.vat = invoice.sub_total * Decimal(0.15)
#         invoice.total_amount = invoice.sub_total + invoice.vat
#         invoice.unpaid_amount = invoice.total_amount - invoice.paid_amount
#         invoice.save()
#         print(f"Invoice total amount updated to after delete: {invoice.total_amount}")


@receiver(post_delete, sender=VehiclePartRequest)
def vpr_log_delete(sender, instance, **kwargs):
    VehiclePartRequestLog.objects.create(
        action='Delete',
        user=getattr(instance, 'user', None),
        object_id=instance.pk,
        job_card_id=instance.job_card_id,
        customer=instance.customer.name if instance.customer else None,
        vehicle=str(instance.vehicle) if instance.vehicle else None,
        total_amount=instance.total_amount,
        asrekabi=instance.asrekabi_sim.name if instance.asrekabi_sim else None,
        terekabi=instance.terekabi_sim.name if instance.terekabi_sim else None,
    )

# @receiver([post_save, post_delete], sender=VehiclePartRequest)
# def vpr_recalculate_invoice_on_change(sender, instance, **kwargs):
#     # i want to re calculate the invoice even after the invoice is already created
#     jobcard_id = instance.job_card.id
#     # instance.save()
#     print(jobcard_id)
#     invoice = Invoice.objects.filter(job_card_id=jobcard_id).first()
#     print(invoice.total_amount)
#     print(instance.total_amount)
#     if invoice:
#         # invoice.total_amount = instance.total_amount + invoice.job_card.total_cost
#         invoice.total_amount = instance.total_amount + invoice.total_amount
#         invoice.save()



@receiver([post_save, post_delete], sender=VehiclePartRequestItems)
def vpr_recalculate_total_amount(sender, instance, **kwargs):
    part_request = instance.part_request
    total_amount = part_request.items.aggregate(total=Sum('price'))['total'] or Decimal('0.00')
    if instance.part_request.job_card and hasattr(instance.part_request.job_card, 'invoice'):
        invoice = instance.part_request.job_card.invoice
        job_card_cost = instance.part_request.job_card.total_cost or Decimal('0.00')
        invoice.sub_total = job_card_cost + total_amount
        invoice.vat = invoice.sub_total * Decimal(0.15)
        invoice.total_amount = invoice.sub_total + invoice.vat
        invoice.unpaid_amount = invoice.total_amount - invoice.paid_amount
        invoice.save()


# ========= VehiclePartRequestItems signals =========

@receiver(pre_save, sender=VehiclePartRequestItems)
def vpri_snapshot_before_update(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = sender.objects.select_related('part_request__job_card', 'product').get(pk=instance.pk)
            instance._pre_save_snapshot = {
                'part_request_id': original.part_request_id,
                'product': original.product.name if original.product else None,
                'unit_price': str(original.unit_price) if original.unit_price is not None else None,
                'quantity': original.quantity,
                'price': str(original.price) if original.price is not None else None,
                'user': getattr(original.part_request, 'user', None),
            }
        except sender.DoesNotExist:
            instance._pre_save_snapshot = None
    else:
        instance._pre_save_snapshot = None


@receiver(post_save, sender=VehiclePartRequestItems)
def vpri_log_create_update(sender, instance, created, **kwargs):
    actor = getattr(instance.part_request, 'user', None) if instance.part_request else None
    payload = {
        'user': actor,
        'object_id': instance.pk,
        'part_request_id': instance.part_request_id,
        'product': instance.product.name if instance.product else None,
        'unit_price': instance.unit_price,
        'quantity': instance.quantity,
        'price': instance.price,
    }
    if created:
        VehiclePartRequestItemLog.objects.create(action='Create', **payload)
        return

    snapshot = getattr(instance, '_pre_save_snapshot', None)
    current = {
        'part_request_id': payload['part_request_id'],
        'product': payload['product'],
        'unit_price': str(payload['unit_price']) if payload['unit_price'] is not None else None,
        'quantity': payload['quantity'],
        'price': str(payload['price']) if payload['price'] is not None else None,
        'user': payload['user'],
    }
    changes = {}
    if snapshot is not None:
        for k, old in snapshot.items():
            new = current.get(k)
            if old != new:
                changes[k] = {'old': old, 'new': new}

    VehiclePartRequestItemLog.objects.create(
        action='Update',
        changes_on_update=json.dumps(changes) if changes else None,
        **payload,
    )


@receiver(post_delete, sender=VehiclePartRequestItems)
def vpri_log_delete(sender, instance, **kwargs):
    actor = getattr(instance.part_request, 'user', None) if instance.part_request else None
    VehiclePartRequestItemLog.objects.create(
        action='Delete',
        user=actor,
        object_id=instance.pk,
        part_request_id=instance.part_request_id,
        product=instance.product.name if instance.product else None,
        unit_price=instance.unit_price,
        quantity=instance.quantity,
        price=instance.price,
    )





# ========= VehicleOldPartDelivery Log signals =========

@receiver(pre_save, sender=VehicleOldPartDelivery)
def vopd_snapshot_before_update(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = sender.objects.select_related('tegagn_mechanic', 'vehicle', 'job_card', 'asrekabi_sim', 'terekabi_sim').get(pk=instance.pk)
            instance._pre_save_snapshot = {
                'job_card_id': original.job_card_id,
                'tegagn_mechanic': original.tegagn_mechanic.name if original.tegagn_mechanic else None,
                'vehicle': str(original.vehicle) if original.vehicle else None,
                'asrekabi': original.asrekabi_sim.name if original.asrekabi_sim else None,
                'terekabi': original.terekabi_sim.name if original.terekabi_sim else None,
                'user': getattr(original, 'user', None),
            }
        except sender.DoesNotExist:
            instance._pre_save_snapshot = None
    else:
        instance._pre_save_snapshot = None


@receiver(post_save, sender=VehicleOldPartDelivery)
def vopd_log_create_update(sender, instance, created, **kwargs):
    payload = {
        'user': getattr(instance, 'user', None),
        'object_id': instance.pk,
        'job_card_id': instance.job_card_id,
        'tegagn_mechanic': instance.tegagn_mechanic.name if instance.tegagn_mechanic else None,
        'vehicle': str(instance.vehicle) if instance.vehicle else None,
        'asrekabi': instance.asrekabi_sim.name if instance.asrekabi_sim else None,
        'terekabi': instance.terekabi_sim.name if instance.terekabi_sim else None,
    }
    if created:
        VehicleOldPartDeliveryLog.objects.create(action='Create', **payload)
        return

    snapshot = getattr(instance, '_pre_save_snapshot', None)
    current = {
        'job_card_id': payload['job_card_id'],
        'tegagn_mechanic': payload['tegagn_mechanic'],
        'vehicle': payload['vehicle'],
        'asrekabi': payload['asrekabi'],
        'terekabi': payload['terekabi'],
        'user': payload['user'],
    }
    changes = {}
    if snapshot is not None:
        for k, old in snapshot.items():
            new = current.get(k)
            if old != new:
                changes[k] = {'old': old, 'new': new}

    VehicleOldPartDeliveryLog.objects.create(
        action='Update',
        changes_on_update=json.dumps(changes) if changes else None,
        **payload,
    )


@receiver(post_delete, sender=VehicleOldPartDelivery)
def vopd_log_delete(sender, instance, **kwargs):
    VehicleOldPartDeliveryLog.objects.create(
        action='Delete',
        user=getattr(instance, 'user', None),
        object_id=instance.pk,
        job_card_id=instance.job_card_id,
        tegagn_mechanic=instance.tegagn_mechanic.name if instance.tegagn_mechanic else None,
        vehicle=str(instance.vehicle) if instance.vehicle else None,
        asrekabi=instance.asrekabi_sim.name if instance.asrekabi_sim else None,
        terekabi=instance.terekabi_sim.name if instance.terekabi_sim else None,
    )




# ========= VehicleOldPartDeliveryItems signals =========

@receiver(pre_save, sender=VehicleOldPartDeliveryItems)
def vopdi_snapshot_before_update(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = sender.objects.select_related('old_part__job_card', 'product').get(pk=instance.pk)
            instance._pre_save_snapshot = {
                'old_part_id': original.old_part_id,
                'product': original.product.name if original.product else None,
                'quantity': original.quantity,
                'fixed_parts': original.fixed_parts,
                'user': getattr(original.old_part, 'user', None),
            }
        except sender.DoesNotExist:
            instance._pre_save_snapshot = None
    else:
        instance._pre_save_snapshot = None


@receiver(post_save, sender=VehicleOldPartDeliveryItems)
def vopdi_log_create_update(sender, instance, created, **kwargs):
    actor = getattr(instance.old_part, 'user', None) if instance.old_part else None
    payload = {
        'user': actor,
        'object_id': instance.pk,
        'old_part_id': instance.old_part_id,
        'product': instance.product.name if instance.product else None,
        'quantity': instance.quantity,
        'fixed_parts': instance.fixed_parts
    }
    if created:
        VehicleOldPartDeliveryItemLog.objects.create(action='Create', **payload)
        return

    snapshot = getattr(instance, '_pre_save_snapshot', None)
    current = {
        'old_part_id': payload['old_part_id'],
        'product': payload['product'],
        'quantity': payload['quantity'],
        'fixed_parts': payload['fixed_parts'],
        'user': payload['user'],
    }
    changes = {}
    if snapshot is not None:
        for k, old in snapshot.items():
            new = current.get(k)
            if old != new:
                changes[k] = {'old': old, 'new': new}

    VehicleOldPartDeliveryItemLog.objects.create(
        action='Update',
        changes_on_update=json.dumps(changes) if changes else None,
        **payload,
    )


@receiver(post_delete, sender=VehicleOldPartDeliveryItems)
def vopdi_log_delete(sender, instance, **kwargs):
    actor = getattr(instance.old_part, 'user', None) if instance.old_part else None
    VehicleOldPartDeliveryItemLog.objects.create(
        action='Delete',
        user=actor,
        object_id=instance.pk,
        old_part_id=instance.old_part_id,
        product=instance.product.name if instance.product else None,
        quantity=instance.quantity,
        fixed_parts=instance.fixed_parts,
    )






# ========= VehicleOrderVoucher Log signals =========

@receiver(pre_save, sender=VehicleOrderVoucher)
def vov_snapshot_before_update(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = sender.objects.select_related('customer', 'vehicle', 'job_card', 'asrekabi_sim', 'terekabi_sim').get(pk=instance.pk)
            instance._pre_save_snapshot = {
                'job_card_id': original.job_card_id,
                'customer': original.customer.name if original.customer else None,
                'vehicle': str(original.vehicle) if original.vehicle else None,
                'asrekabi': original.asrekabi_sim.name if original.asrekabi_sim else None,
                'terekabi': original.terekabi_sim.name if original.terekabi_sim else None,
                'user': getattr(original, 'user', None),
            }
        except sender.DoesNotExist:
            instance._pre_save_snapshot = None
    else:
        instance._pre_save_snapshot = None


@receiver(post_save, sender=VehicleOrderVoucher)
def vov_log_create_update(sender, instance, created, **kwargs):
    payload = {
        'user': getattr(instance, 'user', None),
        'object_id': instance.pk,
        'job_card_id': instance.job_card_id,
        'customer': instance.customer.name if instance.customer else None,
        'vehicle': str(instance.vehicle) if instance.vehicle else None,
        'asrekabi': instance.asrekabi_sim.name if instance.asrekabi_sim else None,
        'terekabi': instance.terekabi_sim.name if instance.terekabi_sim else None,
    }
    if created:
        VehicleOrderVoucherLog.objects.create(action='Create', **payload)
        return

    snapshot = getattr(instance, '_pre_save_snapshot', None)
    current = {
        'job_card_id': payload['job_card_id'],
        'customer': payload['customer'],
        'vehicle': payload['vehicle'],
        'asrekabi': payload['asrekabi'],
        'terekabi': payload['terekabi'],
        'user': payload['user'],
    }
    changes = {}
    if snapshot is not None:
        for k, old in snapshot.items():
            new = current.get(k)
            if old != new:
                changes[k] = {'old': old, 'new': new}

    VehicleOrderVoucherLog.objects.create(
        action='Update',
        changes_on_update=json.dumps(changes) if changes else None,
        **payload,
    )


@receiver(post_delete, sender=VehicleOrderVoucher)
def vov_log_delete(sender, instance, **kwargs):
    VehicleOrderVoucherLog.objects.create(
        action='Delete',
        user=getattr(instance, 'user', None),
        object_id=instance.pk,
        job_card_id=instance.job_card_id,
        customer=instance.customer.name if instance.customer else None,
        vehicle=str(instance.vehicle) if instance.vehicle else None,
        asrekabi=instance.asrekabi_sim.name if instance.asrekabi_sim else None,
        terekabi=instance.terekabi_sim.name if instance.terekabi_sim else None,
    )




# ========= VehicleOrderVoucherItems signals =========

@receiver(pre_save, sender=VehicleOrderVoucherItems)
def vovi_snapshot_before_update(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = sender.objects.select_related('voucher_order__job_card').get(pk=instance.pk)
            instance._pre_save_snapshot = {
                'voucher_order_id': original.voucher_order_id,
                'item_name': original.item_name,
                'quantity': original.quantity,
                'fixed_parts': original.fixed_parts,
                'user': getattr(original.voucher_order, 'user', None),
            }
        except sender.DoesNotExist:
            instance._pre_save_snapshot = None
    else:
        instance._pre_save_snapshot = None


@receiver(post_save, sender=VehicleOrderVoucherItems)
def vovi_log_create_update(sender, instance, created, **kwargs):
    actor = getattr(instance.voucher_order, 'user', None) if instance.voucher_order else None
    payload = {
        'user': actor,
        'object_id': instance.pk,
        'voucher_order_id': instance.voucher_order_id,
        'item_name': instance.item_name,
        'quantity': instance.quantity,
        'fixed_parts': instance.fixed_parts
    }
    if created:
        VehicleOrderVoucherItemLog.objects.create(action='Create', **payload)
        return

    snapshot = getattr(instance, '_pre_save_snapshot', None)
    current = {
        'voucher_order_id': payload['voucher_order_id'],
        'item_name': payload['item_name'],
        'quantity': payload['quantity'],
        'fixed_parts': payload['fixed_parts'],
        'user': payload['user'],
    }
    changes = {}
    if snapshot is not None:
        for k, old in snapshot.items():
            new = current.get(k)
            if old != new:
                changes[k] = {'old': old, 'new': new}

    VehicleOrderVoucherItemLog.objects.create(
        action='Update',
        changes_on_update=json.dumps(changes) if changes else None,
        **payload,
    )


@receiver(post_delete, sender=VehicleOrderVoucherItems)
def vovi_log_delete(sender, instance, **kwargs):
    actor = getattr(instance.voucher_order, 'user', None) if instance.voucher_order else None
    VehicleOrderVoucherItemLog.objects.create(
        action='Delete',
        user=actor,
        object_id=instance.pk,
        voucher_order_id=instance.voucher_order_id,
        item_name=instance.item_name,
        quantity=instance.quantity,
        fixed_parts=instance.fixed_parts,
    )











@receiver(post_save, sender=PurchaseProduct)
def update_expense_total_on_delete(sender, instance, **kwargs):
    expense = instance.expense
    if not expense:
        return

    def update_expense_totals():
        total = expense.products.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
        expense.total = total
        expense.unpaid_amount = expense.total - expense.paid_amount
        expense.save(update_fields=['total', 'unpaid_amount'])

    transaction.on_commit(update_expense_totals)


@receiver(post_save, sender=AssignedService)
def set_jobcard_assignment_in_progress_if_all_assigned_service_in_progress(sender, instance, **kwargs):
    jobcardassignment = instance.assignment
    if jobcardassignment:  # First check if assignment exists
        jobcard = jobcardassignment.job_card
        # Check if all related assigned_services are in progress
        all_in_progress = not jobcardassignment.assigned_services.exclude(status='in_progress').exists()
        if all_in_progress and jobcardassignment.status != 'in_progress':
            jobcardassignment.status = 'in_progress'
            jobcardassignment.save(update_fields=['status'])
            
            # Update jobcard status if it's not already in progress
            if jobcard and jobcard.status != 'in_progress':
                jobcard.status = 'in_progress'
                jobcard.save(update_fields=['status'])        

@receiver(post_save, sender=JobCardAssignment)
def set_jobcard_complete_if_all_jobcard_assignment_completed(sender, instance, **kwargs):
    jobcard = instance.job_card
    if jobcard:
        # Check if all related jobcard_assignments are completed
        all_completed = not jobcard.assignments.exclude(status='completed').exists()
        # if all_completed and jobcard.status != 'completed' and jobcard.vehicle_old_parts == [] and jobcard.invoice: # this part is changed but it doesn't work yet
        if all_completed and jobcard.status != 'completed':
            jobcard.status = 'completed'
            jobcard.save(update_fields=['status'])


@receiver(post_save, sender=PurchaseExpense)
def update_purchase_supplier_total_amount(sender, instance, **kwargs):
    supplier = instance.supplier_level
    if not supplier:
        return

    def update_supplier_totals():
        supplier.total_amount = supplier.expenses.aggregate(Sum('total'))['total__sum'] or Decimal('0.00')
        supplier.paid_amount = supplier.expenses.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0.00')
        supplier.unpaid_amount = supplier.expenses.aggregate(Sum('unpaid_amount'))['unpaid_amount__sum'] or Decimal('0.00')
        supplier.save(update_fields=['total_amount', 'paid_amount', 'unpaid_amount'])

    transaction.on_commit(update_supplier_totals)


# @receiver([post_save, post_delete], sender=PurchaseProduct)
# def update_purchase_expense_total(sender, instance, **kwargs):
#     """Update total amount in Order when an OrderItem is added, updated, or deleted."""
#     expense = instance.expense

#     print(expense.paid_amount)

#     expense.total = expense.products.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
#     expense.total = Decimal(str(expense.total))
#     expense.unpaid_amount = expense.total - expense.paid_amount
#     expense.save()

@receiver([post_save, post_delete], sender=PurchaseProduct)
def update_purchase_expense_total(sender, instance, **kwargs):
    """Update total amount in Order when an OrderItem is added, updated, or deleted."""
    try:
        # Try to get the expense, but handle the case where it might be deleted
        expense = instance.expense
    except PurchaseExpense.DoesNotExist:
        # If the expense is already deleted, we can skip this update
        return

    try:
        expense.total = expense.products.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
        expense.total = Decimal(str(expense.total))
        expense.unpaid_amount = expense.total - expense.paid_amount
        expense.save()
    except (PurchaseExpense.DoesNotExist, AttributeError):
        # Handle case where expense is deleted during the operation
        pass

@receiver(post_save, sender=PurchaseExpense)
def set_supplier_paid_if_all_expenses_paid(sender, instance, **kwargs):
    supplier = instance.supplier_level
    if supplier:
        # Check if all related expenses are paid
        all_paid = not supplier.expenses.exclude(payment_status='Paid').exists()
        if all_paid and supplier.payment_status != 'Paid':
            supplier.payment_status = 'Paid'
            supplier.save(update_fields=['payment_status'])

@receiver(post_save, sender=PurchaseSupplier)
def set_expenses_paid_if_supplier_paid(sender, instance, **kwargs):
    if instance.payment_status == 'Paid':
        instance.expenses.update(
            payment_status='Paid',
            paid_amount=models.F('total'),
            unpaid_amount=0
    )




@receiver(pre_save, sender=OrderItem)
def set_order_item_price(sender, instance, **kwargs):
    """Calculate price before saving the OrderItem instance."""
    instance.price = instance.get_price()

@receiver(pre_save, sender=OrderItem)
def set_order_item_cost(sender, instance, **kwargs):
    """Calculate price before saving the OrderItem instance."""
    instance.cost = instance.get_cost()

@receiver([post_save, post_delete], sender=OrderItem)
def update_order_total(sender, instance, **kwargs):
    """Update total amount in Order when an OrderItem is added, updated, or deleted."""
    order = instance.order
    order.sub_total = order.get_sub_total_price()
    if order.receipt == 'Receipt':
        order.vat = order.sub_total * Decimal('0.15')
    else:
        order.vat = 0
    order.total_amount = order.sub_total + order.vat
    if order.payment_status == 'Paid':
        order.paid_amount = order.total_amount
    else:
        order.unpaid_amount = order.total_amount - order.paid_amount
    order.save()

@receiver([post_save, post_delete], sender=OrderItem)
def update_order_total(sender, instance, **kwargs):
    """Update total amount in Order when an OrderItem is added, updated, or deleted."""
    order = instance.order
    order.sub_total = order.get_sub_total_price()
    # Update VAT and total_amount here as well:
    if order.receipt == 'Receipt':
        order.vat = order.sub_total * Decimal('0.15')
    else:
        order.vat = 0
    order.total_amount = order.sub_total + order.vat
    if order.payment_status == 'Paid':
        order.paid_amount = order.total_amount
    elif order.payment_status == 'Pending':
        order.unpaid_amount = order.total_amount - order.paid_amount
    order.save()

@receiver(post_save, sender=Order)
def update_order_total_on_order_change(sender, instance, **kwargs):
    total = sum(item.price for item in instance.items.all())
    instance.sub_total = total
    if instance.receipt == 'Receipt':
        instance.vat = total * Decimal('0.15')  # Assuming a VAT rate of 15%
    else:
        instance.vat = 0
    instance.total_amount = total + instance.vat

@receiver(post_save, sender=OrderItem)
def update_order_status_if_all_items_status_cancelled(sender, instance, **kwargs):
    # Check if the associated order has no items with status 'Done'
    order = instance.order
    items = order.items.all()
    if items.exists() and items.filter(status='Cancelled').count() == items.count():
        order.status = 'Cancelled'
        order.save()

@receiver(post_save, sender=Order)
def update_order_items_status_on_order_update(sender, instance, **kwargs):
    """
    When an order is updated, update all related OrderItem statuses to 'Cancelled'
    if the order's status is set to 'Cancelled'.
    Also, restock products when an order item is cancelled.
    """

    if getattr(instance, '_updating', False):
        return  # Prevent recursion
    
    if instance.status == 'Cancelled':  # Check if the order is cancelled
        items_data = instance.items.all()  # Retrieve all related OrderItem instances
        instance.sub_total = 0  # Reset sub_total to 0 when cancelling
        instance.vat = 0  # Reset VAT to 0 when cancelling
        instance.total_amount = 0  # Reset total_amount to 0 when cancelling
        instance.paid_amount = 0  # Reset paid_amount to 0 when cancelling
        instance.unpaid_amount = 0  # Reset unpaid_amount to 0 when cancelling
        instance.payment_status = 'Unpaid'  # Reset payment_status to 'Unpaid' when cancelling
        # instance.save()  # Save the updated order
        
        instance._updating = True  # Set flag
        instance.save(update_fields=['sub_total', 'vat', 'total_amount', 'paid_amount', 'unpaid_amount', 'payment_status'])
        instance._updating = False  # Unset flag

        items_to_update = []  # List to collect OrderItems for bulk update

        for item_data in items_data:
            product = item_data.product  # Access related product
            receipt = item_data.item_receipt  # Access receipt type
            quantity = item_data.quantity  # Access quantity
            package = item_data.package  # Access package


            if item_data.status != 'Cancelled':  # Check if item is not already cancelled
                product.stock += item_data.quantity  # Restock the product
                item_data.quantity = 0 
                item_data.price = 0
                item_data.unit_price = 0 
                item_data.cost = 0
                item_data.status = 'Cancelled'  # Mark item as cancelled
                if product.package is not None and package is not None:
                    product.package += package
                    item_data.package = 0
                if receipt == "Receipt":
                    if product.receipt_no is not None:
                        product.receipt_no += quantity
                items_to_update.append(item_data)  # Collect for bulk update

                # Save the updated product and order item
                product.save()  # Save the updated product
                # item_data.save()  # Save the updated order item but it causes the multiple save issue

        # Bulk update all OrderItems at once
        OrderItem.objects.bulk_update(items_to_update, ['quantity', 'status', 'price', 'unit_price', 'cost', 'package'])

@receiver([post_save, post_delete], sender=OrderItem)
def update_order_item_pending_count(sender, instance, **kwargs):
    order = instance.order
    items = order.items.all()
    pending_count = items.filter(status='Pending').count()
    done_exists = items.filter(status='Done').exists()

    if items.count() == 1 and items.first().status == 'Pending':
        order.item_pending = 0
        order.status = "Pending"
    elif items.count() > 1:
        if done_exists:
            order.item_pending = pending_count
        elif not done_exists and items.exists() and items.filter(status='Pending').count() == items.count():
            order.item_pending = 0
            order.status = "Pending"
    else:
        order.item_pending = 0  # No items at all

    order.save(update_fields=['item_pending', 'status'])


@receiver([post_save, post_delete], sender=OrderItem)
def update_order_item_count(sender, instance, **kwargs):
    order = instance.order
    items = order.items.all()
    items_count = items.all().count()
    order.number_of_items = items_count
    order.save(update_fields=['number_of_items'])


@receiver([post_save, post_delete], sender=PerformaProduct)
def performa_performa_item_count(sender, instance, **kwargs):
    try:
        performa = instance.performa
        items = performa.products.all()
        items_count = items.count()
        performa.number_of_items = items_count
        performa.save(update_fields=['number_of_items'])
    except PerformaPerforma.DoesNotExist:
        # Performa was already deleted, nothing to update
        pass


# @receiver([post_save, post_delete], sender=PurchaseProduct)
# def purchase_expense_item_count(sender, instance, **kwargs):
#     expenses = instance.expense
#     items = expenses.products.all()
#     items_count = items.all().count()
#     expenses.number_of_items = items_count
#     expenses.save(update_fields=['number_of_items'])

@receiver([post_save, post_delete], sender=PurchaseProduct)
def purchase_expense_item_count(sender, instance, **kwargs):
    try:
        # Try to get the expense, but handle the case where it might be deleted
        expense = instance.expense
        if expense:
            items = expense.products.all()
            items_count = items.count()
            expense.number_of_items = items_count
            expense.save(update_fields=['number_of_items'])
    except (PurchaseExpense.DoesNotExist, AttributeError):
        # If expense is already deleted or doesn't exist, skip the update
        pass


@receiver([post_save, post_delete], sender=PerformaProduct)
def performa_performa_item_count(sender, instance, **kwargs):
    try:
        performa = instance.performa
        items = performa.products.all()
        items_count = items.count()
        performa.number_of_items = items_count
        performa.save(update_fields=['number_of_items'])
    except PerformaPerforma.DoesNotExist:
        # Performa was already deleted, nothing to update
        pass

@receiver([post_save, post_delete], sender=PerformaProduct)
def update_performa_performa_total(sender, instance, **kwargs):
    """Update total amount when a PerformaProduct is added, updated, or deleted."""
    try:
        performa = instance.performa
        # Calculate sub_total including both total_price and service_charge from products
        product_totals = performa.products.aggregate(
            total_price_sum=Sum('total_price'),
            service_charge_sum=Sum('product_service_charge')
        )
        sub_total = (product_totals['total_price_sum'] or Decimal('0.00')) + (product_totals['service_charge_sum'] or Decimal('0.00'))
        
        # Add performa-level service charge if any
        # sub_total += performa.service_charge or Decimal('0.00')
        # sub_total += sub_total
        
        performa.sub_total = sub_total
        if performa.receipt == "Receipt":
            performa.vat = performa.sub_total * Decimal('0.15')
        else:
            performa.vat = Decimal('0.00')
        performa.total = performa.sub_total + performa.vat + performa.service_charge or Decimal('0.00')
        performa.save()
    except PerformaPerforma.DoesNotExist:
        # Performa was already deleted, nothing to update
        pass


@receiver(pre_delete, sender=PerformaCustomer)
def performa_customer_pre_delete(sender, instance, **kwargs):
    # Disconnect the signals temporarily to prevent them from running during deletion
    post_save.disconnect(performa_performa_item_count, sender=PerformaProduct)
    post_delete.disconnect(performa_performa_item_count, sender=PerformaProduct)
    post_save.disconnect(update_performa_performa_total, sender=PerformaProduct)
    post_delete.disconnect(update_performa_performa_total, sender=PerformaProduct)
    
    try:
        # Delete all related PerformaPerforma objects
        instance.performas.all().delete()
    except Exception as e:
        # Log the error if needed
        print(f"Error deleting related performas: {e}")

# Reconnect the signals after the deletion is complete
@receiver(post_delete, sender=PerformaCustomer)
def performa_customer_post_delete(sender, **kwargs):
    post_save.connect(performa_performa_item_count, sender=PerformaProduct)
    post_delete.connect(performa_performa_item_count, sender=PerformaProduct)
    post_save.connect(update_performa_performa_total, sender=PerformaProduct)
    post_delete.connect(update_performa_performa_total, sender=PerformaProduct)


































@receiver(post_save, sender=CreditProduct)
def update_credit_total_on_delete(sender, instance, **kwargs):
    credit = instance.credit
    if not credit:
        return

    def update_credit_totals():
        total = credit.products.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
        credit.total = total
        credit.unpaid_amount = credit.total - credit.paid_amount
        credit.save(update_fields=['total', 'unpaid_amount'])

    transaction.on_commit(update_credit_totals)



@receiver(post_save, sender=CreditCredit)
def update_credit_customer_total_amount(sender, instance, **kwargs):
    customer = instance.customer_level
    if not customer:
        return

    def update_customer_totals():
        customer.total_amount = customer.credits.aggregate(Sum('total'))['total__sum'] or Decimal('0.00')
        customer.paid_amount = customer.credits.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0.00')
        customer.unpaid_amount = customer.credits.aggregate(Sum('unpaid_amount'))['unpaid_amount__sum'] or Decimal('0.00')
        customer.save(update_fields=['total_amount', 'paid_amount', 'unpaid_amount'])

    transaction.on_commit(update_customer_totals)


@receiver([post_save, post_delete], sender=CreditProduct)
def update_credit_credit_total(sender, instance, **kwargs):
    """Update total amount in Order when an OrderItem is added, updated, or deleted."""
    try:
        # Try to get the credit, but handle the case where it might be deleted
        credit = instance.credit
    except CreditCredit.DoesNotExist:
        # If the credit is already deleted, we can skip this update
        return

    try:
        credit.sub_total = credit.products.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
        if credit.receipt == "Receipt":
            credit.vat = credit.sub_total * Decimal('0.15')
        else:
            credit.vat = Decimal('0.00')
        credit.total = credit.sub_total + credit.vat
        credit.total = Decimal(str(credit.total))
        credit.unpaid_amount = credit.total - credit.paid_amount
        credit.save()
    except (CreditCredit.DoesNotExist, AttributeError):
        # Handle case where credit is deleted during the operation
        pass

@receiver(post_save, sender=CreditCredit)
def set_customer_paid_if_all_credits_paid(sender, instance, **kwargs):
    customer = instance.customer_level
    if customer:
        # Check if all related credits are paid
        all_paid = not customer.credits.exclude(payment_status='Paid').exists()
        if all_paid and customer.payment_status != 'Paid':
            customer.payment_status = 'Paid'
            customer.save(update_fields=['payment_status'])

@receiver(post_save, sender=CreditCustomer)
def set_credits_paid_if_customer_paid(sender, instance, **kwargs):
    if instance.payment_status == 'Paid':
        instance.credits.update(
            payment_status='Paid',
            paid_amount=models.F('total'),
            unpaid_amount=0
    )


@receiver([post_save, post_delete], sender=CreditProduct)
def credit_credit_item_count(sender, instance, **kwargs):
    try:
        # Try to get the credit, but handle the case where it might be deleted
        credit = instance.credit
        if credit:
            items = credit.products.all()
            items_count = items.count()
            credit.number_of_items = items_count
            credit.save(update_fields=['number_of_items'])
    except (CreditCredit.DoesNotExist, AttributeError):
        # If credit is already deleted or doesn't exist, skip the update
        pass


