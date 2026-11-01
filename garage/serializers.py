from rest_framework import serializers
from .models import ( 
    Customer, JobCardLog, Vehicle, Service, ServicePackage, JobCardAssignment, AssignedService,
     JobCard, Invoice, PerformaCustomer, 
    PerformaPerforma, PerformaProduct,
     VehicleAcceptance, VehicleOldPartDelivery, 
     VehicleOldPartDeliveryItems, VehicleOrderVoucher, 
     VehicleOrderVoucherItems, VehiclePartRequest, 
     VehiclePartRequestItems, Category, Supplier, Product, Order, OrderItem, CreditCustomer, CreditCredit, CreditProduct, CompanyInfo,
     PurchaseSupplier, PurchaseExpense, PurchaseProduct, SupplierPaymentLog,
    ExpensePaymentLog, OrderPaymentLog, OrderLog, Report, JobCardLog, JobCardAssignmentLog, AssignedServiceLog,
    VehiclePartRequestLog, VehiclePartRequestItemLog, VehicleOldPartDeliveryLog, VehicleOldPartDeliveryItemLog,
    VehicleOrderVoucherLog, VehicleOrderVoucherItemLog
    )
from django.db import transaction
from django.db.models import UniqueConstraint
from decimal import Decimal
from django.db.models import Q, Sum, Count
from .utils import update_payment_status_on_new_expense_or_product, create_order_log, create_order_report, update_payment_status_on_new_credit_or_product
from django.contrib.auth import get_user_model
import logging
logger = logging.getLogger(__name__)

User = get_user_model()

import logging
logger = logging.getLogger(__name__)



class CategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField(validators=[])  # Disable default unique validator

    class Meta:
        model = Category
        fields = '__all__'
    
    def validate_name(self, value):
        # Exclude the current instance when updating
        qs = Category.objects.filter(name=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return value
    

    def create(self, validated_data, user=None):
        if user:
            validated_data['user'] = user.name
        return super().create(validated_data)
        
class SupplierSerializer(serializers.ModelSerializer):

    class Meta:
        model = Supplier
        fields = '__all__'
    
    def create(self, validated_data, user=None):
        # Add the user to the validated_data if provided
        if user:
            validated_data['user'] = user.name
        return super().create(validated_data)

class ProductLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'part_number', 'selling_price', 'stock']

class ProductGetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'category_name', 'description', 'package', 'piece', 'unit', 'buying_price', 'selling_price', 'receipt_no', 'stock', 'supplier_name', 'part_number', 'image', 'user']
        constraints = [
            UniqueConstraint(fields=['name', 'part_number'], name='unique_product_part_number')
        ]

class ProductPostSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = '__all__'
        constraints = [
            UniqueConstraint(fields=['name', 'part_number'], name='unique_product_part_number')
        ]
    
    def validate(self, attrs):
        name = attrs.get('name')
        part_number = attrs.get('part_number')
        if Product.objects.filter(name=name, part_number=part_number).exists():
            raise serializers.ValidationError(
                {"error": "A product with this name and part number already exists."}
            )
        return super().validate(attrs)
    
    def create(self, validated_data, user=None):
        # Add the user to the validated_data if provided
        package = validated_data.get('package', None)
        piece = validated_data.get('piece', None)
        stock = validated_data.get('stock', None)

        if package is not None and piece is not None:
            stock = package * piece
            if stock < 0:
                  raise serializers.ValidationError({"error": "stock can't be negative"})
            validated_data['stock'] = stock
        if stock is not None:
            if stock < 0:
                  raise serializers.ValidationError({"error": "stock can't be negative"})
            validated_data['stock'] = stock


        if user:
            validated_data['user'] = user.name

        return super().create(validated_data)


    def update(self, instance, validated_data):
        update_package = validated_data.pop('package', None) # Get the number of boxes to add
        piece = validated_data.pop('piece', instance.piece) # Get the number of strips to add
        update_stocks = validated_data.pop('stock', None)  # Get the
        
        validated_data['piece'] = piece

        if update_package == instance.package:
            update_package = None

    
       # Calculate stock if boxes are provided
        if update_package is not None:
            # Calculate stock based on strips and boxes
            # piece = instance.piece  # Get the current strips per box
            if instance.package is not None:
                update_package = instance.package + update_package  # Update boxes per carton
                stock_quantity = piece * update_package
                module_stock = instance.stock % piece
                stock = stock_quantity + module_stock
                validated_data['package'] = stock // piece
                if stock < 0:
                  raise serializers.ValidationError({"error": "stock can't be negative"})
                validated_data['stock'] = stock  # Update the stock in validated_data
            else:
                stock_quantity = piece * update_package
                module_stock = instance.stock % piece
                stock = stock_quantity + module_stock
                validated_data['package'] = stock // piece
                if stock < 0:
                  raise serializers.ValidationError({"error": "stock can't be negative"})
                validated_data['stock'] = stock  # Update the stock in validated_data
           
        elif update_stocks is not None:
            # If update_stocks is provided, set stock to absolute value
            stock = update_stocks
            if instance.piece is not None and instance.package is not None:
                remaining_package = stock // instance.piece
                validated_data['package'] = remaining_package  # Update boxes per carton based on remaining stock
            if stock < 0:
                  raise serializers.ValidationError({"error": "stock can't be negative"})
            validated_data['stock'] = stock
            

        else:
            validated_data['stock'] = update_stocks if update_stocks is not None else instance.stock  # Use provided stock or keep existing        

        return super().update(instance, validated_data)




class CustomerLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'organization']


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
    
    def create(self, validated_data, user=None):
        # Get the current user from the request context
        current_user = self.context["request"].user
        
        # Set the user field in the validated data if user is authenticated
        if current_user and hasattr(current_user, 'name'):
            validated_data['user'] = current_user.name

        return super().create(validated_data)

class CompanyInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyInfo
        fields = '__all__'
        constraints = [
            UniqueConstraint(fields=['en_name', 'am_name', 'tin_number'], name='unique_company_fields')
        ]
    
    def create(self, validated_data, user=None):
        # Add the user to the validated_data if provided
        if user:
            validated_data['user'] = user.name
        return super().create(validated_data)



# The new implementation
class VehiclePartRequestLightSerializer(serializers.ModelSerializer):
    job_card = serializers.PrimaryKeyRelatedField(queryset=JobCard.objects.all())
    # Customer Info
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_organization = serializers.CharField(source='customer.organization', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    # Vehicle Info
    vehicle_model = serializers.CharField(source='vehicle.model', read_only=True)
    vehicle_targa_kutir = serializers.CharField(source='vehicle.license_plate', read_only=True)
    vehicle_shanci_kutir = serializers.CharField(source='vehicle.license_plate', read_only=True)
    # Asrekabi
    asrekabi_name = serializers.CharField(source='asrekabi_sim.name', read_only=True)
    terekabi_name = serializers.CharField(source='terekabi_sim.name', read_only=True)


    class Meta:
        model = VehiclePartRequest
        fields = [
            'id',
            'customer_name',
            'customer_organization',
            'customer_phone',
            'vehicle_model',
            'vehicle_targa_kutir',
            'vehicle_shanci_kutir',
            'ken',
            'asrekabi_name',
            'terekabi_name',
            'total_amount',
            'user',
            'job_card'
        ]


class VehiclePartRequestItemsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    product_name = serializers.CharField(source='product.name', read_only=True)
    part_number = serializers.CharField(source='product.part_number', read_only=True)

    class Meta:
        model = VehiclePartRequestItems
        fields = ['id', 'product', 'product_name', 'part_number', 'unit_price', 'quantity', 'price']
        read_only_fields = ['id']
        extra_kwargs = {
            'part_request': {'required': False, 'read_only': True},
        }

class VehiclePartRequestSerializer(serializers.ModelSerializer):
    items = VehiclePartRequestItemsSerializer(many=True)
    job_card = serializers.PrimaryKeyRelatedField(queryset=JobCard.objects.all())
    # Customer Info
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_organization = serializers.CharField(source='customer.organization', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    customer_tin_number = serializers.CharField(source='customer.tin_number', read_only=True)

    # Vehicle Info
    vehicle_model = serializers.CharField(source='vehicle.model', read_only=True)
    vehicle_shanci_kutir = serializers.CharField(source='vehicle.shanci_kutir', read_only=True)
    vehicle_motor_kutir = serializers.CharField(source='vehicle.motor_kutir', read_only=True)
    vehicle_targa_kutir = serializers.CharField(source='vehicle.license_plate', read_only=True)

    # Asrekabi
    asrekabi_name = serializers.CharField(source='asrekabi_sim.name', read_only=True)
    terekabi_name = serializers.CharField(source='terekabi_sim.name', read_only=True)


    class Meta:
        model = VehiclePartRequest
        fields = [
            'id',
            'customer',
            'vehicle',
            'customer_name',
            'customer_organization',
            'customer_phone',
            'customer_tin_number',
            'vehicle_model',
            'vehicle_shanci_kutir',
            'vehicle_motor_kutir',
            'vehicle_targa_kutir',
            'ken',
            'asrekabi_sim',
            'asrekabi_name',
            'asrekabi_firma',
            'asrekabi_ken',
            'terekabi_sim',
            'terekabi_name',
            'terekabi_firma',
            'terekabi_ken',
            'total_amount',
            'user',
            'job_card',
            'items'
        ]

    def create(self, validated_data, user=None):
        # Get the current user from the request context
        current_user = self.context["request"].user
        
        # Set the user field in the validated data if user is authenticated
        if current_user and hasattr(current_user, 'name'):
            validated_data['user'] = current_user.name
        
        # Extract items data from validated data
        items_to_create = validated_data.pop('items', [])

         # Reject creating a voucher with no items
        if not items_to_create:
            raise serializers.ValidationError({"error": "Order voucher must contain at least one item"})
        

        total = 0
        
        try:
            # All-or-nothing behavior: Everything inside the block is committed only if the whole block completes successfully. If any exception is raised (e.g., a serializers.ValidationError), Django rolls back all DB changes made inside the block.
            with transaction.atomic():
                # First validate all items before creating anything
                for item_data in items_to_create:
                    product = item_data['product']
                    if product.stock is None:
                        raise serializers.ValidationError({
                            "error": f"Product {product.name} stock is not available."
                        })

                # Create the main VehiclePartRequest instance
                part_request = VehiclePartRequest.objects.create(**validated_data)
                
                # Process each item in the items list
                for item_data in items_to_create:
                    # Validate quantity
                    product = item_data.get('product')
                    quantity = item_data.get('quantity', 0)
                    unit_price = item_data.get('unit_price', product.selling_price)
                    if quantity <= 0:
                        raise serializers.ValidationError({
                            "error": f"Quantity must be greater than zero for part: {item_data.get('part', '')}"
                        })
                    
                    if quantity > product.stock:
                        raise serializers.ValidationError({
                            "error": f"Quantity must be less than or equal to stock for part: {item_data.get('part', '')}"
                        })
                    
                    product.stock -= quantity
                    product.save()
                    
                    # Calculate price
                    price = unit_price * quantity
                    total += price
                    
                    # Create the related VehiclePartRequestItems
                    VehiclePartRequestItems.objects.create(
                        part_request=part_request,
                        product=product,
                        quantity=quantity,
                        unit_price=unit_price,
                        price=price,
                    )
                
                part_request.total_amount = total
                part_request.save()
            
            return part_request
            
        except Exception as e:
            # In case of any error, raise a validation error with the message
            raise serializers.ValidationError({
                "error": f"Failed to create part request: {str(e)}"
            })
    
    def update(self, instance, validated_data):
        # Update main model fields
        fields = [
            'model', 'ye_bale_nibret_sim', 'shanci_kutir', 'motor_kutir',
            'targa_kutir', 'silk_kutir', 'tin_kutir', 'ken', 'asrekabi_sim',
            'asrekabi_firma', 'asrekabi_ken', 'terekabi_sim', 'terekabi_firma',
            'terekabi_ken', 'user'
        ]
        total = 0
        
        for field in fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        
        # Handle items update if present
        if 'items' in validated_data:
            items_data = validated_data.pop('items')
            
            # Get existing items
            existing_items = {item.id: item for item in instance.items.all()}
            updated_item_ids = set()
            
            # Update or create items
            for item_data in items_data:
                item_id = item_data.get('id')

                if item_id and item_id in existing_items:
                    # Update existing item
                    item = existing_items[item_id]

                    quantity = item.quantity
                    product = item_data.get('product')
                    new_quantity = item_data.get('quantity')

                    print(new_quantity)
                    print(quantity)

                    for key, value in item_data.items():
                        if key != 'quantity':  # Skip quantity as it's handled separately
                            setattr(item, key, value)
                    
                    
                    if new_quantity and new_quantity > 0:
                        # Calculate the difference between new and existing quantity
                        quantity_difference = new_quantity - quantity
                        item.quantity = new_quantity

                        if product.stock >= quantity_difference:  # Ensure there is enough stock
                            # Reduce stock by the order quantity_difference
                            remaining_stock = product.stock - quantity_difference
                            product.stock = remaining_stock
                            product.save()  # Save the product instance
                        else:
                            raise serializers.ValidationError({
                                "error": f"Not enough stock for part: {product.name}"
                            })
                    
                    item.quantity = new_quantity
                    price = item_data.get('unit_price') * item_data.get('quantity')
                    item.price = price
                    item.save()
                    updated_item_ids.add(item_id)
                else:
                    product = item_data['product']
                    quantity = item_data.get('quantity')
                    unit_price = item_data.get('unit_price', product.selling_price)
                    price = unit_price * quantity

                    # Create new item
                    VehiclePartRequestItems.objects.create(
                        part_request=instance,
                        product=product,
                        quantity=quantity,
                        unit_price=unit_price,
                        price=price,
                    )

            # Delete items that weren't included in the update
            for item_id, item in existing_items.items():
                if item_id not in updated_item_ids:
                    item.delete()

            # Recalculate the total amount after deletions
            total_amount = instance.items.aggregate(total=Sum('price'))['total'] or 0
            instance.total_amount = total_amount
        
        instance.save()
        return instance


# The new implementation
class VehicleOldPartDeliveryLightSerializer(serializers.ModelSerializer):
    job_card = serializers.PrimaryKeyRelatedField(queryset=JobCard.objects.all())
    # Customer Info
    tegagn_mechanic_name = serializers.CharField(source='tegagn_mechanic.name', read_only=True)
    # Vehicle Info
    vehicle_model = serializers.CharField(source='vehicle.model', read_only=True)
    vehicle_targa_kutir = serializers.CharField(source='vehicle.license_plate', read_only=True)
    vehicle_shanci_kutir = serializers.CharField(source='vehicle.shanci_kutir', read_only=True)
    # Asrekabi
    asrekabi_name = serializers.CharField(source='asrekabi_sim.name', read_only=True)
    terekabi_name = serializers.CharField(source='terekabi_sim.name', read_only=True)
    terekabi_organization = serializers.CharField(source='terekabi_sim.organization', read_only=True)
    terekabi_phone = serializers.CharField(source='terekabi_sim.phone', read_only=True)


    class Meta:
        model = VehicleOldPartDelivery
        fields = [
            'id',
            'tegagn_mechanic_name',
            'vehicle_model',
            'vehicle_targa_kutir',
            'vehicle_shanci_kutir',
            'ken',
            'asrekabi_name',
            'terekabi_name',
            'terekabi_organization',
            'terekabi_phone',
            'user',
            'job_card'
        ]



class VehicleOldPartDeliveryItemsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    product_name = serializers.CharField(source='product.name', read_only=True)
    part_number = serializers.CharField(source='product.part_number', read_only=True)

    class Meta:
        model = VehicleOldPartDeliveryItems
        fields = ['id', 'product', 'product_name', 'part_number', 'quantity', 'fixed_parts']
        read_only_fields = ['id']
        extra_kwargs = {
            'old_part': {'required': False, 'read_only': True}
        }

class VehicleOldPartDeliverySerializer(serializers.ModelSerializer):
    items = VehicleOldPartDeliveryItemsSerializer(many=True)
    job_card = serializers.PrimaryKeyRelatedField(queryset=JobCard.objects.all())
    # Customer Info
    tegagn_mechanic_name = serializers.CharField(source='tegagn_mechanic.name', read_only=True)

    # Vehicle Info
    vehicle_model = serializers.CharField(source='vehicle.model', read_only=True)
    vehicle_shanci_kutir = serializers.CharField(source='vehicle.shanci_kutir', read_only=True)
    vehicle_motor_kutir = serializers.CharField(source='vehicle.motor_kutir', read_only=True)
    vehicle_targa_kutir = serializers.CharField(source='vehicle.license_plate', read_only=True)

    # Asrekabi
    asrekabi_name = serializers.CharField(source='asrekabi_sim.name', read_only=True)
    terekabi_name = serializers.CharField(source='terekabi_sim.name', read_only=True)
    terekabi_organization = serializers.CharField(source='terekabi_sim.organization', read_only=True)
    terekabi_phone = serializers.CharField(source='terekabi_sim.phone', read_only=True)
    terekabi_tin_number = serializers.CharField(source='terekabi_sim.tin_number', read_only=True)

    class Meta:
        model = VehicleOldPartDelivery
        fields = [
            'id',
            'tegagn_mechanic',
            'vehicle',
            'tegagn_mechanic_name',
            'vehicle_model',
            'vehicle_shanci_kutir',
            'vehicle_motor_kutir',
            'vehicle_targa_kutir',
            'ken',
            'asrekabi_sim',
            'asrekabi_name',
            'asrekabi_firma',
            'asrekabi_ken',
            'terekabi_sim',
            'terekabi_name',
            'terekabi_organization',
            'terekabi_phone',
            'terekabi_tin_number',
            'terekabi_firma',
            'terekabi_ken',
            'user',
            'job_card',
            'items'
        ]

        

    def create(self, validated_data, user=None):
        # Get the current user from the request context
        current_user = self.context["request"].user
        
        # Set the user field in the validated data if user is authenticated
        if current_user and hasattr(current_user, 'name'):
            validated_data['user'] = current_user.name
        
        # Extract items data from validated data
        items_to_create = validated_data.pop('items', [])
         # Reject creating a voucher with no items
        if not items_to_create:
            raise serializers.ValidationError({"error": "Order voucher must contain at least one item"})
        
        try:
            # All-or-nothing behavior
            with transaction.atomic():

                # Create the main VehiclePartRequest instance
                old_part = VehicleOldPartDelivery.objects.create(**validated_data)
                
                # Process each item in the items list
                for item_data in items_to_create:
                    # Validate quantity
                    product = item_data.get('product')
                    quantity = item_data.get('quantity')
                    fixed_parts = item_data.get('fixed_parts')

                    if quantity == 0:
                        item_data['quantity'] = None
                    else:
                        item_data['quantity'] = quantity

                    # if quantity <= 0:
                    #     raise serializers.ValidationError({
                    #         "error": f"Quantity must be greater than zero for part: {item_data.get('part', '')}"
                    #     })
                    
                    # Create the related VehicleOldPartDeliveryItems
                    VehicleOldPartDeliveryItems.objects.create(
                        old_part=old_part,
                        product=product,
                        quantity=quantity,
                        fixed_parts=fixed_parts
                    )
                
                old_part.save()
            
            return old_part
            
        except Exception as e:
            # In case of any error, raise a validation error with the message
            raise serializers.ValidationError({
                "error": f"Failed to create part request: {str(e)}"
            })

    def update(self, instance, validated_data):
        # Update main model fields
        fields = [
            'vehicle', 'tegagn_mechanic', 'ken', 'asrekabi_sim',
            'asrekabi_firma', 'asrekabi_ken', 'terekabi_sim', 'terekabi_firma',
            'terekabi_ken', 'user'
        ]
        
        for field in fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        
        # Handle items update
        if 'items' in validated_data:
            items_data = validated_data.pop('items')
            
            # Get existing items
            existing_items = {item.id: item for item in instance.items.all()}
            updated_item_ids = set()
            
            # Update or create items
            for item_data in items_data:
                item_id = item_data.get('id')
                
                if item_id and item_id in existing_items:
                    # Update existing item
                    item = existing_items[item_id]
                    for key, value in item_data.items():
                        setattr(item, key, value)
                    item.save()
                    updated_item_ids.add(item_id)
                else:
                    # Create new item
                    VehicleOldPartDeliveryItems.objects.create(
                        old_part=instance,
                        **item_data
                    )
                    updated_item_ids.add(item_id)
            
            # Delete items that weren't included in the update
            for item_id, item in existing_items.items():
                if item_id not in updated_item_ids:
                    item.delete()
        
        instance.save()
        return instance






class VehicleSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    organization = serializers.CharField(source='customer.organization', read_only=True)

    class Meta:
        model = Vehicle
        fields = ['id', 'customer', 'customer_name', 'organization', 'model', 'color', 'shanci_kutir', 'motor_kutir', 'year', 'license_plate', 'image', 'image2', 'image3', 'image4', 'user']

    def create(self, validated_data, user=None):
        # Get the current user from the request context
        current_user = self.context["request"].user
        
        # Set the user field in the validated data if user is authenticated
        if current_user and hasattr(current_user, 'name'):
            validated_data['user'] = current_user.name

        return super().create(validated_data)

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'
        # fields = ['id', 'worker', 'worker_name', 'job_card', 'status', 'price', 'service_package', 'service_package_name', 'package_status', 'task_description', 'assigned_services']
        extra_kwargs = {
            # 'job_card': {'required': False, 'read_only': True},
            'product': {'required': False, 'allow_null': True},
        }
    
    def create(self, validated_data, user=None):
        # Get the current user from the request context
        current_user = self.context["request"].user
        
        # Set the user field in the validated data if user is authenticated
        if current_user and hasattr(current_user, 'name'):
            validated_data['user'] = current_user.name
        
        product = validated_data.get('product')
        if product is not None:
            name = validated_data.get('name', product.name)
            part_number = validated_data.get('part_number', product.part_number)
            cost = validated_data.get('cost', product.selling_price)
        elif product is None:
            name = validated_data.get('name')
            part_number = validated_data.get('part_number')
            cost = validated_data.get('cost')
        description = validated_data.get('description', "")
        duration = validated_data.get('duration', "")
        user = validated_data['user']

        service = Service.objects.create(name=name, product=product, part_number=part_number, description=description, cost=cost, duration=duration, user=user)
        return service

class ServicePackageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ServicePackage
        # fields = ['id', 'name', 'description', 'cost', 'duration', 'Finishing_date']
        fields = "__all__"

    def create(self, validated_data, user=None):
        # Get the current user from the request context
        current_user = self.context["request"].user
        
        # Set the user field in the validated data if user is authenticated
        if current_user and hasattr(current_user, 'name'):
            validated_data['user'] = current_user.name

        return super().create(validated_data)

class AssignedServiceSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', required=False, read_only=True)
    class Meta:
        model = AssignedService
        fields = ['id', 'service', 'service_name', 'status', 'price', 'started_at', 'completed_at']

# Get
class AssignedServiceGetSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), write_only=True, source='service')

    class Meta:
        model = AssignedService
        fields = ['id', 'service', 'service_id', 'status', 'price', 'started_at', 'completed_at']



class JobCardLightSerializer(serializers.ModelSerializer):
    customer_name = serializers.StringRelatedField(source='customer', read_only=True)
    organization = serializers.StringRelatedField(source='customer.organization', read_only=True)
    vehicle_model = serializers.StringRelatedField(source='vehicle.model', read_only=True)
    vehicle_plate = serializers.StringRelatedField(source='vehicle.license_plate', read_only=True)
    class Meta:
        model = JobCard
        fields = ['id', 'customer_name', 'organization', 'vehicle_model', 'vehicle_plate', 'status', 'service_date', 'odometer_reading', 'receipt_id', 'total_cost', 'user']

class JobCardAssignmentLightSerializer(serializers.ModelSerializer):
    job_card = JobCardLightSerializer()
    worker = serializers.StringRelatedField()
    assigned_services = AssignedServiceGetSerializer(many=True)

    class Meta:
        model = JobCardAssignment
        fields = ['id', 'job_card', 'worker', 'status',  'price', 'service_package', 'package_status', 'assigned_services', 'task_description']



class JobCardAssignmentSerializer(serializers.ModelSerializer):
    worker = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    worker_name = serializers.StringRelatedField(source='worker.name', required=False, read_only=True)
    service_package_name = serializers.StringRelatedField(source='service_package.name', required=False, read_only=True)
    assigned_services = AssignedServiceSerializer(many=True)
    id = serializers.IntegerField(required=False)

    class Meta:
        model = JobCardAssignment
        fields = ['id', 'worker', 'worker_name', 'job_card', 'status', 'price', 'service_package', 'service_package_name', 'package_status', 'task_description', 'assigned_services']
        extra_kwargs = {
            'job_card': {'required': False, 'read_only': True},
            'price': {'required': False, 'allow_null': True},
        }

    def create(self, validated_data):
        req = self.context.get('request')
        actor = getattr(req.user, 'name', None) if req else None

        assigned_services_data = validated_data.pop('assigned_services')
        assignment = JobCardAssignment.objects.create(**validated_data)

        assignment._actor = actor
        assignment.save()

        for service_data in assigned_services_data:
            service_cost = service_data.get('price', service_data['service'].cost)
            price = service_cost
            service_total_cost += service_cost
            
            obj = AssignedService.objects.create(
                assignment=assignment,
                service=service_data['service'],
                status=service_data.get('status'),
                price=price
            )
            obj._actor = actor
            obj.save()
        return assignment
    
    def update(self, instance, validated_data):
        req = self.context.get('request')
        actor = getattr(req.user, 'name', None) if req else None
        
        instance._actor = actor
        instance.save()
        
        # service_obj._actor = actor
        # service_obj.save()



class JobCardSerializer(serializers.ModelSerializer):
    assignments = JobCardAssignmentSerializer(many=True)
    customer_name = serializers.StringRelatedField(source='customer', read_only=True)
    vehicle_info = serializers.StringRelatedField(source='vehicle', read_only=True)

    class Meta:
        model = JobCard
        fields = [
            'id', 'customer', 'customer_name', 'vehicle', 'vehicle_info',
            'service_date', 'status', 'notes', 'receipt_id', 'odometer_reading', 'total_cost', 'assignments'
        ]

    def create(self, validated_data):
        # Get the current user from the request context
        current_user = self.context["request"].user
        
        # Set the user field in the validated data if user is authenticated
        if current_user and hasattr(current_user, 'name'):
            validated_data['user'] = current_user.name
        
        all_jobcard = JobCard.objects.all().count()

        id = all_jobcard
        id = str(id).zfill(5)
        validated_data['receipt_id'] = id

        assignments_data = validated_data.pop('assignments')
        if not assignments_data:
            raise serializers.ValidationError({"error": "Job card must contain at least one assignment"})

        job_card = JobCard.objects.create(**validated_data)

        service_total_cost = 0
        service_package_total_cost = 0

        for assignment_data in assignments_data:
            # added code for the assignment log
            req = self.context.get("request")
            actor = getattr(req.user, 'name', None) if req else None
            
            assigned_services_data = assignment_data.pop('assigned_services')
            if assignment_data.get('service_package') is not None:
                service_package_cost = assignment_data.get('price', assignment_data.get('service_package').cost)
                price = service_package_cost           
                service_package_total_cost += service_package_cost

                assignment = JobCardAssignment.objects.create(
                    job_card=job_card,
                    worker=assignment_data.get('worker'),
                    service_package=assignment_data.get('service_package'),
                    price=price,
                    task_description=assignment_data.get('task_description', '')
                )
            else:
                assignment = JobCardAssignment.objects.create(
                    job_card=job_card,
                    worker=assignment_data.get('worker'),
                    task_description=assignment_data.get('task_description', '')
                )

            # added code for the assignment log
            assignment._actor = actor
            assignment.save()

            for service_data in assigned_services_data:
                if service_data['service'] is not None:
                    service_cost = service_data.get('price', service_data['service'].cost)
                    price = service_cost
                    service_total_cost += service_cost

                    as_obj = AssignedService.objects.create(
                        assignment=assignment,
                        service=service_data['service'],
                        status=service_data.get('status'),
                        price=price
                    ) # assigned a varialble as_obj
                    # added code for the assignment log
                    as_obj._actor = actor
                    as_obj.save()
        

        if service_total_cost:
            job_card.total_cost = service_total_cost
            job_card.save()
        elif service_package_total_cost:
            job_card.total_cost = service_package_total_cost
            job_card.save()
        return job_card
 
    #  trying assigned service update/create and this code is working both the assignment and assigned service update/create
    def update(self, instance, validated_data):
        req = self.context.get("request")
        actor = getattr(req.user, 'name', None) if req else None

        assignments_data = validated_data.pop('assignments', [])
    
        # Update the job card fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Get all existing assignment IDs
        existing_assignment_ids = set(instance.assignments.values_list('id', flat=True))
        updated_assignment_ids = set()
        
        # Handle assignments
        for assignment_data in assignments_data:
            assigned_services_data = assignment_data.pop('assigned_services', [])
            assignment_id = assignment_data.get('id')
            price = assignment_data.get('price')
            
            if assignment_id and assignment_id in existing_assignment_ids:
                # Update existing assignment
                assignment = JobCardAssignment.objects.get(id=assignment_id, job_card=instance)
                for attr, value in assignment_data.items():
                    setattr(assignment, attr, value)
                assignment._actor = actor
                assignment.save()
                updated_assignment_ids.add(assignment_id)
            else:
                # Create new assignment
                assignment = JobCardAssignment.objects.create(
                    job_card=instance,
                    **assignment_data
                )
                assignment._actor = actor
                assignment.save()
                updated_assignment_ids.add(assignment.id)
            
            # Get existing assigned services for this assignment
            existing_services = {
                as_obj.service_id: as_obj 
                for as_obj in assignment.assigned_services.all()
            }
            updated_service_ids = set()
            
            # Handle assigned services
            for service_data in assigned_services_data:
                service = service_data.get('service')
                status = service_data.get('status', 'in_progress')
                price = service_data.get('price', service.cost)
                
                if service.id in existing_services:
                    # Update existing service
                    service_obj = existing_services[service.id]
                    service_obj.status = status
                    service_obj.price = price
                    service_obj._actor = actor
                    service_obj.save()
                else:
                    # Create new assigned service
                    # service_cost = service_data.get('price', service_data['service'].cost)
                    # price = service_cost
                    # service_total_cost += service_cost
                    
                    as_obj = AssignedService.objects.create(
                        assignment=assignment,
                        service=service,
                        status=status,
                        price=price
                    )
                    as_obj._actor = actor
                    as_obj.save()
                updated_service_ids.add(service.id)
            
            # Remove services that weren't included in the update
            services_to_remove = set(existing_services.keys()) - updated_service_ids
            if services_to_remove:
                assignment.assigned_services.filter(service_id__in=services_to_remove).delete()
        
        # Delete assignments that weren't included in the update
        assignments_to_delete = existing_assignment_ids - updated_assignment_ids
        if assignments_to_delete:
            JobCardAssignment.objects.filter(
                id__in=assignments_to_delete,
                job_card=instance
            ).delete()
        
        # Sum service package costs + assigned service costs
        total_cost = Decimal('0')

        # Use select_related/prefetch_related for efficiency
        assignments_qs = instance.assignments.select_related('service_package') \
            .prefetch_related('assigned_services__service')

        for assignment in assignments_qs:
            # service package cost
            if assignment.service_package and assignment.service_package.cost is not None:
                total_cost += Decimal(str(assignment.price))

            # assigned services costs
            for asg in assignment.assigned_services.all():
                if asg.service and asg.service.cost is not None:

                    # total_cost += Decimal(str(asg.service.cost))
                    total_cost += Decimal(str(asg.price))

        instance.total_cost = total_cost
        instance.save(update_fields=['total_cost'])

        return instance


class JobCardGetEveryThingSerializer(serializers.ModelSerializer):
    assignments = JobCardAssignmentSerializer(many=True)
    vehicle_part_requests = VehiclePartRequestSerializer(required=False)
    vehicle_old_parts = VehicleOldPartDeliverySerializer(required=False)
    customer_name = serializers.StringRelatedField(source='customer', read_only=True)
    organization = serializers.StringRelatedField(source='customer.organization', read_only=True)
    vehicle_info = serializers.StringRelatedField(source='vehicle', read_only=True)
    # invoice = InvoiceGetSerializer(required=False)

    class Meta:
        model = JobCard
        fields = [
            'id', 'customer', 'customer_name', 'organization', 'vehicle', 'vehicle_info',
            'service_date', 'status', 'notes','receipt_id', 'odometer_reading', 'total_cost', 'user', 'assignments', 'vehicle_part_requests', 'vehicle_old_parts'
        ]





# Get
class InvoiceGetSerializer(serializers.ModelSerializer):
    job_card = JobCardGetEveryThingSerializer(required=False, read_only=True)
    customer_name = serializers.StringRelatedField(source='job_card.customer.name', read_only=True)
    organization_name = serializers.StringRelatedField(source='job_card.customer.organization', read_only=True)
    customer_phone = serializers.StringRelatedField(source='job_card.customer.phone', read_only=True)
    customer_tin = serializers.StringRelatedField(source='job_card.customer.tin_number', read_only=True)
    customer_email = serializers.StringRelatedField(source='job_card.customer.email', read_only=True)
    customer_address = serializers.StringRelatedField(source='job_card.customer.address', read_only=True)
    vehicle_info = serializers.StringRelatedField(source='job_card.vehicle.model', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'job_card', 'customer_name', 'organization_name', 'customer_phone', 
            'customer_tin', 'customer_email', 'customer_address', 'vehicle_info',
            'invoice_date', 'sub_total', 'vat', 'total_amount',
            'paid_amount', 'unpaid_amount', 'payment_status'
        ]
        extra_kwargs = {
            'total_amount': {'required': False},
            'total_amount': {'read_only': True}, # Make 'total_amount' read-only
        }



class InvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.StringRelatedField(source='job_card.customer.name', read_only=True)
    organization_name = serializers.StringRelatedField(source='job_card.customer.organization', read_only=True)
    vehicle_info = serializers.StringRelatedField(source='job_card.vehicle.model', read_only=True)
    class Meta:
        model = Invoice
        fields = [
            'id', 'job_card', 'customer_name', 'organization_name',  'vehicle_info',
            'invoice_date', 'sub_total', 'vat', 'total_amount',
            'paid_amount', 'unpaid_amount', 'payment_status', 'user'
        ]
        extra_kwargs = {
            'total_amount': {'required': False},
            'total_amount': {'read_only': True}, # Make 'total_amount' read-only
        }


    def create(self, validated_data, user=None):
        # Get the current user from the request context
        current_user = self.context["request"].user
        
        # Set the user field in the validated data if user is authenticated
        if current_user and hasattr(current_user, 'name'):
            validated_data['user'] = current_user.name

        job_card = validated_data.get('job_card')

        part_requests = VehiclePartRequest.objects.filter(job_card=job_card)
        part_requests_total = sum(pr.total_amount for pr in part_requests)
        sub_total = part_requests_total + job_card.total_cost
        vat = sub_total * Decimal(0.15)
        total_amount = sub_total + vat

        validated_data['sub_total'] = sub_total
        validated_data['vat'] = vat
        validated_data['total_amount'] = total_amount


        paid_amount = validated_data.get('paid_amount', 0)
        unpaid_amount = total_amount - paid_amount
        payment_status = 'Paid' if paid_amount >= total_amount else 'Pending'
        validated_data['paid_amount'] = paid_amount
        validated_data['unpaid_amount'] = unpaid_amount
        validated_data['payment_status'] = payment_status
        

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # paid_amount = validated_data.get('paid_amount')
        # unpaid_amount = instance.total_amount - paid_amount
        # payment_status = 'Paid' if paid_amount >= instance.total_amount else 'Pending'
        # validated_data['paid_amount'] = paid_amount
        # validated_data['unpaid_amount'] = unpaid_amount
        # validated_data['payment_status'] = payment_status


        new_paid = validated_data.get('paid_amount', 0)
        instance.payment_status = validated_data.get('payment_status', instance.payment_status)

        old_status = instance.payment_status
        old_paid = instance.paid_amount
        old_unpaid = instance.unpaid_amount

        print(f"old paid: {old_paid}")
        print(f"new paid: {new_paid}")


        instance.total = instance.total_amount or Decimal('0.00')
        instance.total = Decimal(str(instance.total))
        instance.save()

        if 'paid_amount' in validated_data:
            paid = instance.paid_amount + new_paid
            total = Decimal(str(instance.total or 0))
            print(f'paid sum: {paid}')
            
            if paid < 0:
                raise serializers.ValidationError("Paid amount cannot be negative")
            if paid > total:
                raise serializers.ValidationError("Paid amount cannot be greater than total amount")
            
            instance.paid_amount = paid
            print(f'instance paid: {instance.paid_amount}')
            # instance.save(update_fields=['paid_amount'])

        if instance.payment_status == 'Paid':
            instance.paid_amount = instance.total
            instance.unpaid_amount = Decimal('0.00')
            instance.payment_status = 'Paid'
        elif instance.payment_status == 'Pending' and instance.total >= instance.paid_amount:
            print(f"total: {instance.total}")
            print(f"paid: {instance.paid_amount}")
            instance.unpaid_amount = max(instance.total - instance.paid_amount, Decimal('0.00'))
            if instance.unpaid_amount == Decimal('0.00'):
                instance.payment_status = 'Paid'   
            instance.save(update_fields=['unpaid_amount'])
        elif instance.payment_status == 'Unpaid':
            instance.paid_amount = Decimal('0.00')
            instance.unpaid_amount = instance.total
            instance.payment_status = 'Unpaid'
        instance.save()


        return instance



# Order and OrderItem
class OrderItemSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)  # Read-only
    product_name = serializers.CharField(source='product.name', read_only=True)
    part_number = serializers.CharField(source='product.part_number', read_only=True)
    product_price = serializers.SerializerMethodField()
    id = serializers.IntegerField(required=False)
    quantity = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product', 'product_price', 'product_name', 'part_number', 'item_receipt', 'package', 'unit', 'quantity', 'unit_price', 'price', 'status']
        extra_kwargs = {
            'order': {'required': False},  # Make 'order' optional in the request
            'price': {'read_only': True}, # Make 'price' read-only if calculated
            'quantity': {'required': False, 'allow_null': True},
        }
    
    def get_product_price(self, obj):
        if obj.unit_price > 0:
            return str(obj.unit_price)
        elif obj.unit_price == 0 or obj.unit_price is None:
            if obj.product and obj.product.selling_price is not None:
                return str(obj.product.selling_price)
            else:
                return "0"
        else:
            return "0"
        

    def update(self, instance, validated_data):
        user = self.context['request'].user
        print(user)
        user_role = user.role
        user_name = user.name
        print(user, user_role, user_name)
        # Update order fields directly
        new_quantity = validated_data.get('quantity')
        new_status = validated_data.get('status')
        new_package = validated_data.get('package')
        new_unit_price = validated_data.get('unit_price')
        product = instance.product  # Access the product from the existing order item
        quantity = instance.quantity
        receipt = instance.order.receipt  # Access the receipt from the order
        package = instance.package
        unit_price = instance.unit_price
        piece = product.piece



        # If a salesman tries to cancel, set to Pending and raise error
        if new_status == 'Cancelled' and user_role == 'Salesman' or new_status == 'Cancelled' and user_role == 'Sales Manager':
            instance.status = 'Pending'
            instance.save()

            create_order_log(
                user=user_name,
                action="Request Cancel",
                model_name="OrderItem",
                object_id=instance.id,
                customer_info=instance.order.customer,
                product_name=instance.product.name,
                quantity=instance.quantity,
                price=instance.price,
                changes_on_update="Salesman requested cancellation"
            )

            raise serializers.ValidationError({
                "error": "You cannot cancel orders directly. Your cancellation request is now pending manager/admin approval."
            })

        if new_quantity and instance.status == 'Cancelled':
            raise serializers.ValidationError({
                "error": f"The order is already cancelled."
            })
        
        if new_package and instance.status == 'Cancelled':
            raise serializers.ValidationError({
                "error": f"The order is already cancelled."
            })


        if new_quantity and new_quantity <= 0:
            raise serializers.ValidationError({
                "error": f"Quantity must be greater than zero."
            })
        
        if new_package and new_package <= 0:
            raise serializers.ValidationError({
                "error": f"Package must be greater than zero."
            })
        
        if new_status:
            if new_status == 'Cancelled':
                product.stock += instance.quantity
                instance.quantity = 0
                instance.unit_price = 0
                instance.product_price = 0
                instance.price = 0
                instance.cost = 0
                instance.status = 'Cancelled' 
                if product.package is not None and package is not None:
                    product.package += package
                    instance.package = 0
                if receipt == "Receipt":
                    if product.receipt_no is not None:
                        product.receipt_no += quantity
                product.save()
                instance.save()
            elif new_status == 'Done':
                instance.status = 'Done' 
                instance.save()

        # updating if there is quantity
        if new_quantity and new_quantity > 0 and instance.status == 'Done':
            # Calculate the difference between new and existing quantity
            quantity_difference = new_quantity - quantity
            instance.quantity = new_quantity

            if product.stock >= quantity_difference:  # Ensure there is enough stock
                # Reduce stock by the order quantity_difference

                if receipt == "Receipt":
                    if package:
                        if product.package >= package:
                            product.package -= package
                            product.stock -= quantity_difference
                            if product.receipt_no is not None:
                                product.receipt_no -= quantity_difference
                            product.save()  # Save the product instance
                        elif product.package < package:
                            # raise ValidationError("The amount of package is insufficient.")
                            raise serializers.ValidationError({
                                "error": f"The amount of package is insufficient."
                            })
                            
                    elif package is None:
                        # Calculate the remaining stock and adjust the package count
                        remaining_stock = product.stock - quantity_difference
                        # remaining_packages = remaining_stock // piece  # Calculate remaining packages
                        # product.package = remaining_packages
                        product.stock = remaining_stock
                        if product.receipt_no is not None:
                            product.receipt_no -= quantity_difference
                        product.save()  # Save the product instance

                elif receipt == "No Receipt":
                    if package:
                        if product.package >= package:
                            product.package -= package
                            product.stock -= quantity_difference
                            product.save()  # Save the product instance
                        elif product.package < package:
                            raise serializers.ValidationError({
                                    "error": f"The amount of package is insufficient."
                                })
                    elif package is None:
                        # Calculate the remaining stock and adjust the package count
                        remaining_stock = product.stock - quantity_difference
                        # remaining_packages = remaining_stock // piece  # Calculate remaining packages
                        # product.package = remaining_packages
                        product.stock = remaining_stock
                        product.save()  # Save the product instance
                    
            else:
                raise serializers.ValidationError({
                        "error": f"Insufficient stock for {product.name}. Available stock is {product.stock}, but {quantity} was requested."
                    })
            # Update the instance's quantity
            instance.quantity = new_quantity

            # The total price without VAT
            if unit_price > 0 and new_unit_price is None:
                instance.price = unit_price * instance.quantity
            elif new_unit_price is not None:
                instance.unit_price = new_unit_price
                instance.price = new_unit_price * instance.quantity
            else:
                instance.price = product.selling_price * instance.quantity

        # updating if there is package
        if new_package and new_package > 0 and instance.status == 'Done' and piece is not None:
            # Calculate the difference between new and existing package
            package_difference = new_package - package
            print(f"package_difference: {package_difference}")
            package_quantity_difference = package_difference * piece
            print(f"package_quantity_difference: {package_quantity_difference}")
            print(f"product stock: {product.stock}")
            print(f"product package: {product.package}")
            print(f"product package calculated: {product.package - package_difference}")
            print(f"product stock calculated: {product.stock - package_quantity_difference}")
            instance.quantity = package_quantity_difference

            if product.stock >= package_quantity_difference:  # Ensure there is enough stock
                # Reduce stock by the order package_difference

                if receipt == "Receipt":
                    if package:
                        if product.package >= package_difference:
                            product.package -= package_difference
                            product.stock -= package_quantity_difference
                            if product.receipt_no is not None:
                                product.receipt_no -= package_quantity_difference
                            instance.package = new_package
                            instance.quantity = new_package * piece
                            product.save()  # Save the product instance
                        elif product.package < package_difference:
                            raise serializers.ValidationError({
                                "error": f"The amount of package is insufficient."
                            })    
                    elif package is None:
                        # Calculate the remaining stock and adjust the package count
                        remaining_stock = product.stock - package_quantity_difference
                        if piece:
                            remaining_packages = remaining_stock // piece  # Calculate remaining packages
                            product.package = remaining_packages
                        product.stock = remaining_stock
                        if product.receipt_no is not None:
                            product.receipt_no -= package_quantity_difference
                        product.save()  # Save the product instance

                elif receipt == "No Receipt":
                    if package:
                        if product.package >= package_difference:
                            product.package -= package_difference
                            product.stock -= package_quantity_difference
                            instance.package = new_package
                            instance.quantity = new_package * piece
                            product.save()  # Save the product instance
                        elif product.package < package_difference:
                            raise serializers.ValidationError({
                                "error": f"The amount of package is insufficient."
                            })
                    elif package is None:
                        # Calculate the remaining stock and adjust the package count
                        remaining_stock = product.stock - package_quantity_difference
                        remaining_packages = remaining_stock // piece  # Calculate remaining packages
                        product.package = remaining_packages
                        product.stock = remaining_stock
                        product.save()  # Save the product instance
                    
            else:
                raise serializers.ValidationError({
                        "error": f"Insufficient stock for {product.name}. Available stock is {product.stock}, but {quantity} was requested."
                    })

            # The total price without VAT
            if unit_price > 0 and new_unit_price is None:
                instance.price = unit_price * instance.quantity
            elif new_unit_price is not None:
                instance.unit_price = new_unit_price
                instance.price = new_unit_price * instance.quantity
            else:
                instance.price = product.selling_price * instance.quantity


        instance.save()

        return instance

class OrderLightSerializer(serializers.ModelSerializer):
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    customer_name = serializers.CharField(source='customer.organization', read_only=True)
    

    class Meta:
        model = Order
        fields = ['id', 'customer', 'customer_name', 'status', 'receipt', 'performa', 'receipt_id', 'order_date', 'sub_total', 'vat',  'total_amount', 'payment_status', 'paid_amount', 'unpaid_amount', 'user', 'number_of_items', 'credit']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    customer_name = serializers.CharField(source='customer.organization', read_only=True)
    

    class Meta:
        model = Order
        fields = ['id', 'customer', 'customer_name', 'status', 'receipt', 'performa', 'receipt_id', 'order_date', 'sub_total', 'vat',  'total_amount', 'payment_status', 'paid_amount', 'unpaid_amount', 'items', 'user', 'user_email', 'user_role', 'item_pending', 'number_of_items', 'credit']
        extra_kwargs = {
            'total_amount': {'required': False},
            'total_amount': {'read_only': True}, # Make 'total_amount' read-only
        }
    
    def create(self, validated_data, user=None):
        user = self.context["request"].user
        if user:
            validated_data['user'] = user.name
            validated_data['user_email'] = user.email
            validated_data['user_role'] = user.role

        
        receipt = validated_data['receipt']

        all_order = Order.objects.all().count()
        receipt_order = Order.objects.filter(receipt="Receipt").count()
        no_receipt_order = Order.objects.filter(receipt="No Receipt").count()
        if receipt == "Receipt":
            id = all_order - no_receipt_order
            id = str(id).zfill(4)
            validated_data['receipt_id'] = id
        else:
            validated_data['receipt_id'] = None



        payment_status = validated_data.get('payment_status', 'Paid')
        paid_amount = validated_data.get('paid_amount', 0)

        new_payment_status = payment_status
        new_paid_amount = paid_amount
        

        items_data = validated_data.pop('items')
        if not items_data:
            raise serializers.ValidationError({"error": "Order must contain at least one item"})

        

        
        # If we get here, all validations passed - create the order
        with transaction.atomic():
            # Track original product states so we can restore them if the order ends up with no items
            modified_products = {}

            def record_product_state(prod):
                if prod and getattr(prod, 'pk', None) and prod.pk not in modified_products:
                    modified_products[prod.pk] = {
                        'stock': prod.stock,
                        'package': prod.package,
                        'receipt_no': prod.receipt_no,
                    }

            def log_stock_change(prod, label, before, after):
                try:
                    print(f"[OrderStock] {label} | {prod.name} (id={prod.pk}) | stock {before} -> {after}")
                except Exception:
                    logger.exception("Failed to print stock change debug line")

            
            
            # First validate all items before creating anything
            for item_data in items_data:
                product = item_data['product']
                if product.stock is None:
                    raise serializers.ValidationError({
                        "error": f"Product {product.name} stock is not available."
                    })
            
            # Collect product ids (and bundle component ids) and lock them
            product_ids = set()
            bundle_product_ids = set()
            for item_data in items_data:
                p = item_data.get('product')
                if p and getattr(p, 'pk', None):
                    product_ids.add(p.pk)
                    if getattr(p, 'is_bundle', False):
                        bundle_product_ids.add(p.pk)

            component_ids = set()
            if bundle_product_ids:
                component_ids.update(
                    Component.objects.filter(bundle_id__in=bundle_product_ids).values_list('component_id', flat=True)
                )

            lock_ids = sorted(product_ids.union(component_ids))
            locked_products_map = {}
            if lock_ids:
                logger.debug(f"Locking product rows: {lock_ids}")
                locked_qs = Product.objects.select_for_update().filter(pk__in=lock_ids).order_by('pk')
                locked_products_map = {p.pk: p for p in locked_qs}



            # Create the Order instance           
            order = Order.objects.create(**validated_data)

            # Create each OrderItem
            for item_data in items_data:
                # This will call OrderItemSerializer.validate() for each item
                product = item_data['product']
                # Use locked product instance if available
                if getattr(product, 'pk', None) and product.pk in locked_products_map:
                    product = locked_products_map[product.pk]
                    # replace the reference in item_data so downstream code uses locked instance
                    item_data['product'] = product
                # record original product state before any mutation
                record_product_state(product)
                quantity = item_data.get('quantity')
                receipt = order.receipt
                item_data['item_receipt'] = receipt
                package = item_data.get('package')
                unit_price = item_data.get('unit_price', product.selling_price)  # Default to product's selling price if not provided
                item_data['unit'] = item_data.get('unit', product.unit)
                
                piece = product.piece

                if receipt == "Receipt":
                    if package:
                        if product.package >= package:
                            before_stock = product.stock
                            product.package -= package
                            quantity = package * product.piece
                            item_data['quantity'] = quantity
                            if quantity >  product.stock:
                                raise serializers.ValidationError({
                                    "error": f"Insufficient stock for {product.name}. Available stock is {product.package}, but {quantity} was requested."
                                })
                            product.stock -= quantity
                            if product.receipt_no is not None:
                                product.receipt_no -= quantity
                            product.save()  # Save the product instance
                            log_stock_change(product, "product", before_stock, product.stock)


                        elif product.package < package:
                            raise serializers.ValidationError({"error": f"Insufficient stock for {product.name}. Available stock is {product.stock}, but {quantity} was requested."})   
                    
                    elif package is None:
                        if quantity >  product.stock:
                            raise serializers.ValidationError({
                                "error": f"Insufficient stock for {product.name}. Available stock is {product.stock}, but {quantity} was requested."
                            })
                        # Calculate the remaining stock and adjust the package count
                        before_stock = product.stock
                        remaining_stock = product.stock - quantity
                        if product.piece is not None and product.package is not None:
                            # If piece and package are defined, calculate remaining packages
                            remaining_packages = remaining_stock // piece  # Calculate remaining packages
                            product.package = remaining_packages
                            product.stock = remaining_stock
                            product.save()
                            if product.receipt_no is not None:
                                # If receipt_no is defined, reduce it by the quantity
                                product.receipt_no -= quantity
                                product.save()  # Save the product instance
                            log_stock_change(product, "product", before_stock, product.stock)
                        else:
                            before_stock = product.stock
                            product.stock -= quantity
                            product.save()  # Save the product instance  
                            if product.receipt_no is not None:
                                # If receipt_no is defined, reduce it by the quantity
                                product.receipt_no -= quantity
                                product.save()  # Save the product instance
                            log_stock_change(product, "product", before_stock, product.stock)


                elif receipt == "No Receipt":
                    if package:
                        if product.package >= package:
                            before_stock = product.stock
                            product.package -= package
                            quantity = package * product.piece
                            item_data['quantity'] = quantity
                            if quantity >  product.stock:
                                # This shows the quantity as long as it is not greater than stock
                                raise serializers.ValidationError({
                                    "error": f"Insufficient quantity for {product.name}. Available stock is {product.stock}, but {quantity} quantity was requested."
                                })
                            product.stock -= quantity
                            product.save()  # Save the product instance
                            log_stock_change(product, "product", before_stock, product.stock)

                        elif product.package < package:
                            # This shows the quantity as long as it is not greater than stock
                            raise serializers.ValidationError({"error": f"Insufficient package for {product.name}. Available package is {product.package}, but {package} package was requested."})   
                    
                    elif package is None:
                        if quantity >  product.stock:
                            # This shows the quantity as long as it is not greater than stock
                            raise serializers.ValidationError({
                                "error": f"Insufficient stock for {product.name}. Available stock is {product.stock}, but {quantity} quantity was requested."
                            })
                        # Calculate the remaining stock and adjust the package count
                        before_stock = product.stock
                        remaining_stock = product.stock - quantity
                        if product.piece is not None and product.package is not None:
                            # If piece and package are defined, calculate remaining packages
                            remaining_packages = remaining_stock // piece  # Calculate remaining packages
                            product.package = remaining_packages
                            product.stock = remaining_stock
                            product.save()
                            log_stock_change(product, "product", before_stock, product.stock)
                            
                        else:
                            before_stock = product.stock
                            product.stock -= quantity
                            product.save()  # Save the product instance  
                            log_stock_change(product, "product", before_stock, product.stock) 

                total_price = unit_price * item_data['quantity']
                vat = total_price * Decimal(0.15)
                receipt_total_price = total_price + vat

                # Create the OrderItem and associate with the Order
                # OrderItem.objects.create(order=order, price=total_price, **item_data)

                try:
                    logger.debug("Creating OrderItem for order=%s product=%s quantity=%s", order.pk, getattr(item_data.get('product'), 'pk', None), item_data.get('quantity'))
                except Exception:
                    logger.exception("Failed to log OrderItem create intent")

                new_item = OrderItem.objects.create(order=order, price=total_price, **item_data)

                try:
                    logger.debug("Created OrderItem id=%s for order=%s", getattr(new_item, 'id', None), order.pk)
                except Exception:
                    logger.exception("Failed to log OrderItem creation")


                # Adding it into the log with every itration
                create_order_log(
                    user = user.name,
                    action="Create",
                    model_name="Order",
                    object_id=order.id,
                    customer_info = order.customer,
                    product_name = item_data['product'].name,
                    quantity = item_data['quantity'],
                    price = total_price,
                    changes_on_update = "Created Order Item",
                )
                
                # Adding it into the report with every itration
                if order.customer is None and order.receipt == "Receipt":
                    create_order_report(
                        user = user.name,
                        customer_name = "Anonymous Customer", 
                        customer_phone = " ",
                        customer_tin_number = " ",
                        order_date = order.order_date,
                        order_id = order.id,
                        item_receipt = item_data['item_receipt'],
                        unit = item_data['unit'],
                        product_name = item_data['product'].name,
                        product_price = unit_price,
                        quantity = item_data['quantity'],
                        sub_total = total_price,
                        vat = vat,
                        payment_status = order.payment_status,
                        total_amount = receipt_total_price
                    )
                elif order.customer is not None and order.receipt == "Receipt":
                    create_order_report(
                        user = user.name,
                        customer_name = order.customer.name,
                        customer_phone = order.customer.phone,
                        customer_tin_number = order.customer.tin_number,
                        order_date = order.order_date,
                        order_id = order.id,
                        item_receipt = item_data['item_receipt'],
                        unit = item_data['unit'],
                        product_name = item_data['product'].name,
                        product_price = unit_price,
                        quantity = item_data['quantity'],
                        sub_total = total_price,
                        vat = vat,
                        payment_status = order.payment_status,
                        total_amount = receipt_total_price
                    )
                elif order.customer is not None and order.receipt == "No Receipt":
                    create_order_report(
                        user = user.name,
                        customer_name = order.customer.name,
                        customer_phone = order.customer.phone,
                        customer_tin_number = order.customer.tin_number,
                        order_date = order.order_date,
                        order_id = order.id,
                        item_receipt = item_data['item_receipt'],
                        unit = item_data['unit'],
                        product_name = item_data['product'].name,
                        product_price = unit_price,
                        quantity = item_data['quantity'],
                        sub_total = total_price,
                        vat = 0,
                        payment_status = order.payment_status,
                        total_amount = total_price
                    )
                elif order.customer is None and order.receipt == "No Receipt":
                    create_order_report(
                        user = user.name,
                        customer_name = "Anonymous Customer", 
                        customer_phone = " ",
                        customer_tin_number = " ",
                        order_date = order.order_date,
                        order_id = order.id,
                        item_receipt = item_data['item_receipt'],
                        unit = item_data['unit'],
                        product_name = item_data['product'].name,
                        product_price = unit_price,
                        quantity = item_data['quantity'],
                        sub_total = total_price,
                        vat = 0,
                        payment_status = order.payment_status,
                        total_amount = total_price
                    )

            order.save()
            try:
                logger.debug("Final empty-order check for order=%s items_count=%s modified_products=%s", order.pk, order.items.count(), list(modified_products.keys()))
            except Exception:
                logger.exception("Failed to log final empty-order check for order=%s", getattr(order, 'pk', None))

            # Final safety check: if the created order has no items, restore modified products and delete the order
            if not order.items.exists():
                # restore product states
                for pid, vals in modified_products.items():
                    try:
                        p = Product.objects.get(pk=pid)
                        p.stock = vals.get('stock')
                        p.package = vals.get('package')
                        p.receipt_no = vals.get('receipt_no')
                        p.save()
                        logger.debug(f"Rolled back product id={pid} to stock={p.stock} package={p.package}")
                    except Exception:
                        logger.exception(f"Failed rolling back product id={pid}")

                # delete the order to avoid orphan
                try:
                    if order.pk and Order.objects.filter(pk=order.pk).exists():
                        order.delete()
                        logger.debug(f"Deleted empty order id={order.pk} after rollback")
                except Exception:
                    logger.exception("Failed deleting empty order")

                raise serializers.ValidationError({"error": "Order has no items; inventory changes rolled back."})
 
            
            total_amount = Decimal(str(order.total_amount or 0))  # Convert to Decimal
            paid = Decimal(str(paid_amount or 0))  # Convert to Decimal

            if payment_status == 'Pending':
                order.unpaid_amount = max(total_amount - paid, Decimal('0.00'))
                order.save()
            elif payment_status == 'Unpaid':
                order.paid_amount = Decimal('0.00')
                order.unpaid_amount = total_amount
                order.save()
            elif payment_status == 'Paid':
                order.paid_amount = total_amount
                order.unpaid_amount = Decimal('0.00')
                order.save()

            new_unpaid_amount = total_amount - paid

            # 🔍 Log changes

            OrderPaymentLog.objects.create(
                order=order,
                customer=order.customer,
                change_type="Status Create",
                field_name="payment_status",
                old_value=0,
                new_value=new_payment_status,
                user=user.name
            )

            OrderPaymentLog.objects.create(
                order=order,
                customer=order.customer,
                change_type="Payment Create",
                field_name="paid_amount",
                old_value=0,
                new_value=new_paid_amount,
                user=user.name
            )

            OrderPaymentLog.objects.create(
                order=order,
                customer=order.customer,
                change_type="Payment Create",
                field_name="Unpaid Amount",
                old_value=0,
                new_value=new_unpaid_amount,
                user=user.name
            )

        
        return order


    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        # print("items", items_data)

        user = self.context['request'].user
        user_role = user.role
        user_name = user.name
        # Update order fields directly
        instance.customer = validated_data.get('customer', instance.customer)
        instance.status = validated_data.get('status', instance.status)
        new_status = validated_data.get('status')
        new_paid = validated_data.get('paid_amount')

        old_status = instance.payment_status
        old_paid = instance.paid_amount
        old_unpaid = instance.unpaid_amount

        # If a salesman tries to cancel, set to Pending and raise error
        if new_status == 'Cancelled' and user_role == 'Salesman' or new_status == 'Cancelled' and user_role == 'Sales Manager':
            instance.status = 'Pending'
            instance.save()

            total_quantity = sum(item.quantity for item in instance.items.all())
            total_price = sum(item.price for item in instance.items.all())
            create_order_log(
                user=user_name,
                action="Request Cancel",
                model_name="Order",
                object_id=instance.id,
                customer_info=instance.customer,
                product_name="Whole Order",
                quantity=total_quantity,
                price=total_price,
                changes_on_update="Salesman requested cancellation"
            )

            raise serializers.ValidationError({
                "error": "You cannot cancel orders directly. Your cancellation request is now pending manager/admin approval."
            })
        
        # Update Performa basic fields excluding user
        for attr, value in validated_data.items():
            if attr == "user":
                continue
            setattr(instance, attr, value)
        instance.save()

        

        if items_data is not None:
            existing_items = {item.id: item for item in instance.items.all()}
            sent_ids = [item.get('id') for item in items_data if item.get('id')]

            # Delete items not included in the update
            for item in instance.items.all():
                if item.id not in sent_ids:
                    item.delete()

            # Add or update items
            for item_data in items_data:
                item_id = item_data.get('id')

                user = self.context['request'].user
                user_role = user.role
                user_name = user.name
                # Update order fields directly
                new_quantity = item_data.get('quantity')
                new_status = item_data.get('status')
                new_package = item_data.get('package')
                new_unit_price = item_data.get('unit_price')


                if item_id and item_id in existing_items:
                    item = existing_items[item_id]
                    
                    product = item.product  # Access the product from the existing order item
                    quantity = item.quantity
                    receipt = item.order.receipt  # Access the receipt from the order
                    package = item.package
                    unit_price = item.unit_price



                    # If a salesman tries to cancel, set to Pending and raise error
                    if new_status == 'Cancelled' and user_role == 'Salesman':
                        item.status = 'Pending'
                        item.save()

                        create_order_log(
                            user=user_name,
                            action="Request Cancel",
                            model_name="OrderItem",
                            object_id=item.id,
                            customer_info=item.order.customer,
                            product_name=item.product.name,
                            quantity=item.quantity,
                            price=item.price,
                            changes_on_update="Salesman requested cancellation"
                        )

                        raise serializers.ValidationError({
                            "error": "You cannot cancel orders directly. Your cancellation request is now pending manager/admin approval."
                        })


                    if new_quantity and item.status == 'Cancelled':
                        raise serializers.ValidationError({
                            "error": f"The order is already cancelled."
                        })
                    
                    if new_quantity and new_quantity <= 0:
                        raise serializers.ValidationError({
                            "error": f"Quantity must be greater than zero."
                        })
                    
                    if new_status:
                        if new_status == 'Cancelled':
                            product.stock += item.quantity
                            item.quantity = 0
                            item.unit_price = 0
                            item.product_price = 0
                            item.price = 0
                            item.cost = 0
                            item.status = 'Cancelled' 
                            if product.package is not None and package is not None:
                                product.package += package
                                item.package = 0
                            if receipt == "Receipt":
                                if product.receipt_no is not None:
                                    product.receipt_no += quantity
                            product.save()
                            item.save()
                        elif new_status == 'Done':
                            item.status = 'Done' 
                            item.save()



                    if new_quantity and new_quantity > 0 and item.status == 'Done':
                        # Calculate the difference between new and existing quantity
                        quantity_difference = new_quantity - quantity

                        piece = product.piece

                        if product.stock >= quantity_difference:  # Ensure there is enough stock
                            # Reduce stock by the order quantity_difference

                            if receipt == "Receipt":
                                if package:
                                    if product.package >= package:
                                        product.package -= package
                                        product.stock -= quantity_difference
                                        if product.receipt_no is not None:
                                            product.receipt_no -= quantity_difference
                                        product.save()  # Save the product item
                                    elif product.package < package:
                                        # raise ValidationError("The amount of package is insufficient.")
                                        raise serializers.ValidationError({
                                            "error": f"The amount of package is insufficient."
                                        })
                                        
                                elif package is None:
                                    if piece is not None:
                                        # Calculate the remaining stock and adjust the package count
                                        remaining_stock = product.stock - quantity_difference
                                        remaining_packages = remaining_stock // piece  # Calculate remaining packages
                                        product.package = remaining_packages
                                        product.stock = remaining_stock
                                        if product.receipt_no is not None:
                                            product.receipt_no -= quantity_difference
                                        product.save()  # Save the product item
                                    else:
                                        remaining_stock = product.stock - quantity_difference
                                        product.stock = remaining_stock
                                        product.save()  # Save the product item

                            elif receipt == "No Receipt":
                                if package:
                                    if product.package >= package:
                                        product.package -= package
                                        product.stock -= quantity_difference
                                        product.save()  # Save the product item
                                    elif product.package < package:
                                        raise serializers.ValidationError({
                                                "error": f"The amount of package is insufficient."
                                            })
                                elif package is None:
                                    if piece is not None:
                                        # Calculate the remaining stock and adjust the package count
                                        remaining_stock = product.stock - quantity_difference
                                        remaining_packages = remaining_stock // piece  # Calculate remaining packages
                                        product.package = remaining_packages
                                        product.stock = remaining_stock
                                        product.save()  # Save the product item
                                    else:
                                        remaining_stock = product.stock - quantity_difference
                                        product.stock = remaining_stock
                                        product.save()  # Save the product item

                                
                        else:
                            raise serializers.ValidationError({
                                    "error": f"Insufficient stock for {product.name}. Available stock is {product.stock}, but {quantity} was requested."
                                })
                        # Update the item's quantity
                        item.quantity = new_quantity

                        # The total price without VAT
                        if unit_price > 0 and new_unit_price is None:
                            item.price = unit_price * item.quantity
                        elif new_unit_price is not None:
                            item.unit_price = new_unit_price
                            item.price = new_unit_price * item.quantity
                        else:
                            item.price = product.selling_price * item.quantity

                    item.save()


                    for attr, value in item_data.items():
                        if attr != 'id':
                            setattr(item, attr, value)

                    item.price = item.quantity * item.unit_price
                    item.save()
                else:
                    # Remove 'id' if present, as it's not needed for new order item creation
                    item_data.pop('id', None)
                    item_data.pop('order', None)

                    product = item_data['product']
                    quantity = item_data.get('quantity')
                    receipt = instance.receipt
                    item_data['item_receipt'] = receipt
                    package = item_data.get('package')
                    unit_price = item_data.get('unit_price', product.selling_price)  # Default to product's selling price if not provided
                    piece = product.piece

                    if quantity is not None and product.stock < quantity:
                        raise serializers.ValidationError({
                            "error": f"Insufficient stock for {product.name}. Available stock is {product.stock}, but {quantity} was requested."
                        })
                    
                    if package is not None and product.package < package:
                        raise serializers.ValidationError({
                            "error": f"Insufficient package for {product.name}. Available package is {product.package}, but {package} was requested."
                        })
                    
                    if receipt == "Receipt":
                        if package:
                            if product.package >= package:
                                product.package -= package
                                quantity = package * product.piece
                                item_data['quantity'] = quantity
                                if quantity >  product.stock:
                                    raise serializers.ValidationError({
                                        "error": f"Insufficient stock for {product.name}. Available stock is {product.stock}, but {quantity} was requested."
                                    })
                                product.stock -= quantity
                                if product.receipt_no is not None:
                                    product.receipt_no -= quantity
                                product.save()  # Save the product instance

                            elif product.package < package:
                                raise serializers.ValidationError({"error": f"Insufficient package for {product.name}. Available package is {product.package}, but {package} was requested."})   
                        
                        elif package is None:
                            # Calculate the remaining stock and adjust the package count
                            remaining_stock = product.stock - quantity
                            if product.piece is not None and product.package is not None:
                                # If piece and package are defined, calculate remaining packages
                                remaining_packages = remaining_stock // piece  # Calculate remaining packages
                                product.package = remaining_packages
                                product.stock = remaining_stock
                                product.save()
                                if product.receipt_no is not None:
                                    # If receipt_no is defined, reduce it by the quantity
                                    product.receipt_no -= quantity
                                    product.save()  # Save the product instance
                            else:
                                product.stock -= quantity
                                product.save()  # Save the product instance  
                                if product.receipt_no is not None:
                                    # If receipt_no is defined, reduce it by the quantity
                                    product.receipt_no -= quantity
                                    product.save()  # Save the product instance      

                    elif receipt == "No Receipt":
                        if package:
                            if product.package >= package:
                                product.package -= package
                                quantity = package * piece
                                item_data['quantity'] = quantity
                                if quantity >  product.stock:
                                    # This shows the quantity as long as it is not greater than stock
                                    raise serializers.ValidationError({
                                        "error": f"Insufficient stock for {product.name}. Available stock is {product.stock}, but quantity {quantity} was requested."
                                    })
                                product.stock -= quantity
                                product.save()  # Save the product instance

                            elif product.package < package:
                                # This shows the quantity as long as it is not greater than stock
                                raise serializers.ValidationError({"error": f"Insufficient stock for {product.name}. Available package is {product.package}, but package {package} was requested."})   
                        
                        elif package is None:
                            # Calculate the remaining stock and adjust the package count
                            remaining_stock = product.stock - quantity
                            if product.piece is not None and product.package is not None:
                                # If piece and package are defined, calculate remaining packages
                                remaining_packages = remaining_stock // piece  # Calculate remaining packages
                                product.package = remaining_packages
                                product.stock = remaining_stock
                                product.save()
                                
                            else:
                                product.stock -= quantity
                                product.save()  # Save the product instance  

                    total_price = unit_price * item_data['quantity']
                    
                    # update_payment_status_on_new_order_item(order=instance, new_items=None)


                    if instance.pk is None:
                       instance.save()
                    OrderItem.objects.create(
                        order=instance,
                        price=total_price,
                        **item_data
                    )


        # Recalculate sub_total and total
        sub_total = sum(item.price for item in instance.items.all())
        instance.sub_total = sub_total
        instance.vat = instance.sub_total * Decimal('0.15')
        instance.total_amount = instance.sub_total + instance.vat


        if 'paid_amount' in validated_data:
            paid = old_paid + new_paid
            total = Decimal(str(instance.total_amount or 0))
            
            if paid < 0:
                raise serializers.ValidationError("Paid amount cannot be negative")
            if paid > total:
                raise serializers.ValidationError("Paid amount cannot be greater than total amount")
            
            instance.paid_amount = paid
            instance.total_amount = total
            instance.save()


        if instance.payment_status == 'Pending':
            instance.unpaid_amount = max(instance.total_amount - instance.paid_amount, Decimal('0.00'))
            if instance.unpaid_amount == Decimal('0.00'):
                instance.payment_status = 'Paid'
            instance.save()
        elif instance.payment_status == 'Unpaid':
            instance.paid_amount = Decimal('0.00')
            instance.unpaid_amount = instance.total_amount
            instance.save()
        elif instance.payment_status == 'Paid':
            instance.paid_amount = instance.total_amount
            instance.unpaid_amount = Decimal('0.00')
            instance.save()
        


        # 🔍 Log changes
        if instance.payment_status != old_status:
            OrderPaymentLog.objects.create(
                order=instance,
                customer=instance.customer,
                change_type="Status Change",
                field_name="payment_status",
                old_value=old_status,
                new_value=instance.payment_status,
                user=instance.user  # Optional if available
            )

        if instance.paid_amount != old_paid:
            OrderPaymentLog.objects.create(
                order=instance,
                customer=instance.customer,
                change_type="Payment Update",
                field_name="paid_amount",
                old_value=old_paid,
                new_value=instance.paid_amount,
                user=instance.user
            )
        
        if instance.unpaid_amount != old_unpaid:
            OrderPaymentLog.objects.create(
                order=instance,
                customer=instance.customer,
                change_type="Payment Update",
                field_name="unpaid_amount",
                old_value=old_unpaid,
                new_value=instance.unpaid_amount,
                user=instance.user
            )


        instance.save()

        return instance








# New Performa Serializer
class PerformaProductSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    product_name = serializers.CharField(source='product.name', read_only=True)
    class Meta:
        model = PerformaProduct
        fields = ['id', 'product', 'product_name', 'part_number', 'unit', 'description', 'quantity', 'unit_price', 'product_service_charge', 'total_price']
    
    def update(self, instance, validated_data):
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.unit_price = validated_data.get('unit_price', instance.unit_price)
        instance.product_service_charge = validated_data.get('product_service_charge', instance.product_service_charge)

        # Update Products basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        instance.total_price = instance.quantity * instance.unit_price
        instance.save()

        return instance



class PerformaPerformaLightSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = PerformaPerforma
        fields = ['id', 'issued_date', 'customer', 'customer_id', 'receipt', 'shanci_kutir', 'targa_kutir', 'service_charge', 'products_service_charge', 'sub_total', 'vat', 'total', 'user','number_of_items', 'products_service_charge']

class PerformaPerformaSerializer(serializers.ModelSerializer):
    products = PerformaProductSerializer(many=True)
    id = serializers.IntegerField(required=False)
    # products_service_charge, products_only_total

    class Meta:
        model = PerformaPerforma
        fields = ['id', 'issued_date', 'customer', 'customer_id', 'receipt', 'shanci_kutir', 'targa_kutir', 'service_charge', 'products_service_charge', 'sub_total', 'vat', 'total', 'user', 'number_of_items', 'products_service_charge', 'products_only_total', 'products']

    def create(self, validated_data):
        user = self.context["request"].user
        if user:
            validated_data['user'] = user.name

        issued_date=timezone.now()
        products_data = validated_data.pop('products')
        if not products_data:
            raise serializers.ValidationError({"error": "Performa Performa must contain at least one Performa Product"})
        expense = PerformaPerforma.objects.create(**validated_data)
        for product_data in products_data:
            PerformaProduct.objects.create(expense=expense, **product_data)
        return expense
    
    def update(self, instance, validated_data):
        products_data = validated_data.pop('products', None)
        receipt = validated_data.get('receipt', instance.receipt)
        service_charge = validated_data.get('service_charge', instance.service_charge)

        # Update performa fields (except products)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Only process products if products_data is provided (not None)
        if products_data is not None:
            # Update or create products
            existing_ids = [p.id for p in instance.products.all()]
            received_ids = [item.get('id') for item in products_data if item.get('id')]

            # Delete products not present in update data
            for product in instance.products.all():
                if product.id not in received_ids:
                    product.delete()

            for product_data in products_data:
                product_id = product_data.get('id')
                if product_id:
                    # Update existing product
                    product = PerformaProduct.objects.get(id=product_id, performa=instance)
                    for attr, value in product_data.items():
                        setattr(product, attr, value)
                    product.save()
                else:
                    # Create new product
                    # quantity = int(product_data.get('quantity', 0))
                    # unit_price = Decimal(str(product_data.get('unit_price', 0)))
                    # total_price = quantity * unit_price
                    # PerformaProduct.objects.create(performa=instance, total_price=total_price, **product_data)

                    # Creating with new Foreign Key Product
                    # for product_data in products_data:
                    product = product_data['product']
                    part_number = product.part_number
                    product_data['part_number'] = part_number
                    quantity = int(product_data.get('quantity', 0))
                    unit_price = Decimal(str(product_data.get('unit_price', product.selling_price)))
                    product_data['unit_price'] = unit_price
                    # if quantity >  product.stock:
                    #     raise serializers.ValidationError({
                    #         "error": f"Insufficient stock for {product.name}. Available stock is {product.stock}, but {quantity} was requested."
                    #     })

                    # remaining_stock = product.stock - quantity
                    product.stock -= quantity
                    product.save()
                    total_price = quantity * unit_price
                    PerformaProduct.objects.create(performa=instance, total_price=total_price, **product_data)

        # Recalculate totals
        product_sub_total = sum(item.total_price for item in instance.products.all())
        product_service_sub_total = sum(item.product_service_charge for item in instance.products.all())

        instance.products_service_charge = product_service_sub_total

        # service_sub_total = sum(item.service_charge for item in instance.products.all())
        sub_total = product_sub_total + product_service_sub_total
        instance.sub_total = sub_total + service_charge
        if receipt == "Receipt":
            instance.vat = instance.sub_total * Decimal('0.15')
        else:
            instance.vat = 0
        instance.total = instance.sub_total + instance.vat
        instance.save()
        
        return instance



class PerformaCustomerLightSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.organization', read_only=True)

    class Meta:
        model = PerformaCustomer
        fields = ['id','customer', 'customer_name', 'user']

class PerformaCustomerSerializer(serializers.ModelSerializer):
    performas = PerformaPerformaSerializer(many=True)
    customer_name = serializers.CharField(source='customer.organization', read_only=True, required=False)

    class Meta:
        model = PerformaCustomer
        fields = ['id', 'customer', 'customer_id', 'customer_name', 'user', 'performas']
        constraints = [
            UniqueConstraint(fields=['customer'], name='unique_customer')
        ]
    
    def create(self, validated_data):
        user = self.context["request"].user
        if user:
            validated_data['user'] = user.name

        user_name = validated_data['user']
        performas_data = validated_data.pop('performas')
        if not performas_data:
            raise serializers.ValidationError({"error": "Performa Customer must contain at least one Performa Performa"})

        total_amount = Decimal('0.00')  # Start total
        customer = PerformaCustomer.objects.create(**validated_data)

        customer_name = validated_data['customer'].organization
        customer_id = validated_data['customer'].id

        print(f"user name for Customer : {user_name}")
        print(f"customer name for Customer : {customer_name}")

        try:
            for performa_data in performas_data:
                products_data = performa_data.pop('products', [])
                receipt = performa_data.get('receipt', 'Receipt')
                service_charge = performa_data.get('service_charge', 0)
                # products_service_charge = performa_data.get('products_service_charge', 0)
                # print(service_charge)

                # First validate all items before creating anything
                # for product_data in products_data:
                #     product = product_data['product']
                #     if product.stock is None:
                #         raise serializers.ValidationError({
                #             "error": f"Product {product.name} stock is not available."
                #         })
                

                # Calculate total for this expense
                performa_product_sub_total = sum(Decimal(str(product.get('unit_price', 0))) * int(product.get('quantity', 0)) for product in products_data)
                
                performa_service_charge = Decimal(str(service_charge))
            
                performa_product_service_charge = sum(Decimal(str(product.get('product_service_charge', 0))) for product in products_data)
                
                products_service_charge = sum(Decimal(str(product.get('product_service_charge', 0))) for product in products_data)
            
                # performa_sub_total = performa_product_sub_total + performa_service_charge + performa_product_service_charge
                
                performa_sub_total = performa_product_sub_total + performa_product_service_charge

                if receipt == "Receipt":
                    performa_vat = performa_sub_total * Decimal('0.15')
                else:
                    performa_vat = 0
                performa_total = performa_sub_total + performa_vat + performa_service_charge

                total_amount += performa_total

                if validated_data['customer']:
                    performa_customer_name = customer_name
                    performa_customer_id = customer_id
                else:
                    performa_customer_name = "Customer"
                    performa_customer_id = "Id"
                    
                # Create the expense with computed total
                performa = PerformaPerforma.objects.create(customer_level=customer, user=user_name, total=performa_total, sub_total=performa_sub_total, vat=performa_vat, products_service_charge=products_service_charge, customer=performa_customer_name, customer_id=performa_customer_id, **performa_data)

                for product_data in products_data:
                    product = product_data['product']
                    part_number = product.part_number
                    product_data['part_number'] = part_number
                    quantity = int(product_data.get('quantity', 0))
                    unit_price = Decimal(str(product_data.get('unit_price', product.selling_price)))
                    product_data['unit_price'] = unit_price
                    # if quantity >  product.stock:
                    #     raise serializers.ValidationError({
                    #         "error": f"Insufficient stock for {product.name}. Available stock is {product.stock}, but {quantity} was requested."
                    #     })

                    # remaining_stock = product.stock - quantity
                    # product.stock -= quantity
                    # product.save()
                    total_price = quantity * unit_price
                    PerformaProduct.objects.create(performa=performa, total_price=total_price, **product_data)

            return customer

        except Exception as e:
            # Optional: rollback or raise a validation error
            raise serializers.ValidationError({"detail": f"Failed to create customer: {str(e)}"})

    def update(self, instance, validated_data):
        user = self.context["request"].user
        
        performas_data = validated_data.pop('performas', [])

        customer_name = instance.customer.organization

        # Update supplier fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        existing_ids = [e.id for e in instance.performas.all()]
        received_ids = [item.get('id') for item in performas_data if item.get('id')]

        # Delete expenses not in request
        for performa in instance.performas.all():
            if performa.id not in received_ids:
                performa.delete()

        for performa_data in performas_data:
            print(performa_data)
            performa_id = performa_data.get('id')
            products_data = performa_data.pop('products', [])

            if performa_id:
                # Update existing expense
                performa = PerformaPerforma.objects.get(id=performa_id, customer_level=instance)
                performa_serializer = PerformaPerformaSerializer(instance=performa, data={**performa_data, 'products': products_data})
                performa_serializer.is_valid(raise_exception=True)
                # performa_serializer.save()

            else:
                # Create new Performa

                service_charge = performa_data.get('service_charge', 0)
                performa_product_sub_total = sum(Decimal(str(product.get('unit_price', 0))) * int(product.get('quantity', 0)) for product in products_data)
                
                performa_service_charge = Decimal(str(service_charge))
            
                # performa_product_service_charge = sum(Decimal(str(product.get('product_service_charge', 0))) for product in products_data)
            
                # performa_sub_total = performa_product_sub_total + performa_product_service_charge
                performa_sub_total = performa_product_sub_total
                print(f"Performa Sub_total only not service charge: {performa_sub_total}")

                receipt = performa_data.get('receipt', 'Receipt')

                if receipt == "Receipt":
                    performa_vat = performa_sub_total * Decimal('0.15')
                else:
                    performa_vat = 0

                print(f"Performa vat only not service charge: {performa_vat}")

                products_service_charge = sum(Decimal(str(product.get('product_service_charge', 0))) for product in products_data)

                performa_total = performa_sub_total + performa_vat + performa_service_charge
                # Avoid duplicate 'total' key error
                performa_data.pop('total', None)
                performa = PerformaPerforma.objects.create(customer_level=instance, customer=customer_name, total=performa_total, sub_total=performa_sub_total, vat=performa_vat, products_service_charge=products_service_charge, user=user.name, **performa_data)

                for product_data in products_data:
                    product_id = product_data.get('id')
                    if product_id:
                        # Update existing product
                        product = PerformaProduct.objects.get(id=product_id, performa=instance)
                        for attr, value in product_data.items():
                            setattr(product, attr, value)
                        product.save()
                    else:
                        # Create new product
                        # quantity = int(product_data.get('quantity', 0))
                        # unit_price = Decimal(str(product_data.get('unit_price', 0)))
                        # total_price = quantity * unit_price

                        # PerformaProduct.objects.create(performa=performa, total_price=total_price, **product_data)

                        # The Foreign Key Product Adding
                        # for product_data in products_data:
                        product = product_data['product']
                        part_number = product.part_number
                        product_data['part_number'] = part_number
                        quantity = int(product_data.get('quantity', 0))
                        # product_service_charge = Decimal(str(product_data.get('product_service_charge', 0.00)))
                        unit_price = Decimal(str(product_data.get('unit_price', product.selling_price)))
                        product_data['unit_price'] = unit_price
                        # if quantity >  product.stock:
                        #     raise serializers.ValidationError({
                        #         "error": f"Insufficient stock for {product.name}. Available stock is {product.stock}, but {quantity} was requested."
                        #     })

                        # remaining_stock = product.stock - quantity
                        # product.stock -= quantity
                        # product.save()
                        total_price = quantity * unit_price
                        PerformaProduct.objects.create(performa=performa, total_price=total_price, **product_data)

        instance.save()            

        return instance


# The new implementation

class VehicleAcceptanceLightSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    organization = serializers.CharField(source='customer.organization', read_only=True)
    vehicle_model = serializers.CharField(source='vehicle.model', read_only=True)
    vehicle_shanci_kutir = serializers.CharField(source='vehicle.shanci_kutir', read_only=True)
    vehicle_motor_kutir = serializers.CharField(source='vehicle.motor_kutir', read_only=True)

    class Meta:
        model = VehicleAcceptance
        fields = [
            'id',
            'customer_name',
            'organization',
            'vehicle_model',
            'vehicle_shanci_kutir',
            'vehicle_motor_kutir',
            'ken',
            'user'
        ]

class VehicleAcceptanceSerializer(serializers.ModelSerializer):
    # Customer Info
    customer_name = serializers.CharField(source='customer.organization', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    customer_tin_number = serializers.CharField(source='customer.tin_number', read_only=True)

    # Vehicle Info
    vehicle_model = serializers.CharField(source='vehicle.model', read_only=True)
    vehicle_shanci_kutir = serializers.CharField(source='vehicle.shanci_kutir', read_only=True)
    vehicle_motor_kutir = serializers.CharField(source='vehicle.motor_kutir', read_only=True)
    vehicle_targa_kutir = serializers.CharField(source='vehicle.license_plate', read_only=True)

     # 1. Motor Part
    ye_fren_zeyt = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_meri_zeyt = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_motor_zeyt = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_radiator = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    battery = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    zinab_metregya = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    

    # 2. Outer Part
    maskerya = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    antenna = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ferfango = serializers.JSONField(required=False, default={"left": False, "right": False})
    ye_fit_mebrat = serializers.JSONField(required=False, default={"left": False, "right": False})
    frecha_mebrat = serializers.JSONField(required=False, default={"left": False, "right": False})
    makomiya_mebrat = serializers.JSONField(required=False, default={"left": False, "right": False})
    ye_fit_targa = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    nifas_mekelakeya = serializers.JSONField(required=False, default={"left": False, "right": False})
    spekiyo = serializers.JSONField(required=False, default={"left": False, "right": False})
    ye_ber_ijeta = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ika_mekelakeya = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_sivat_kidan = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_huala_targa = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_huala_mebrat_birchiko = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_ber_gomini_mestawat_lstic_frame = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_fit_prawlit = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_zinab_metregiya_ye_bilon_kidan = serializers.JSONField(required=False, default={"left": False, "right": False})
    birjineri_bilon = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_huala_prawlit_antsebaraki = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_fit_igir_fren_lock = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_huala_goma_libs = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    fortomegala = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    eskort_goma_mefcha = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})



    # 3. Inner Part
    tiras = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    meterkosha = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_welel_mintaf = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_wember_libs = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_wist_spekiyo = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_wist_mebrat = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    tep = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    isat_adega_mekelakeya = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    mebrat_mabriya = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    zinab_metregiya_mebrat = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    nedaj = serializers.CharField(required=False, allow_null=True)
    ye_tsehay_mekelakeya = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_wist_ber_mekfecha = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_mestewat_mawcha_mawreja = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_fit_ye_kofen_amorzrater = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_huala_ye_kofen_amorzrater = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    klaks = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_wist_dashboard_kis_kulf = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_kofen_gomini = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    ye_wuha_mercha = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})

    # 4. Outer Condition
    ye_ginbar_mestewat = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    antsebaraki = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    goma = serializers.CharField(required=False, allow_null=True)
    kirk = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    goma_mefcha = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    eskort_goma = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})
    kolenet = serializers.CharField(required=False, allow_null=True)
    ye_cherke_get = serializers.JSONField(required=False, default={"have": False, "don't_have": False, "broken": False})

    # Asrekabi
    asrekabi_name = serializers.CharField(source='asrekabi_sim.name', read_only=True)
    terekabi_name = serializers.CharField(source='terekabi_sim.name', read_only=True)
    ye_miwetabet_ken = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = VehicleAcceptance
        # fields = []
        fields = [
            'id',
            'customer',
            'vehicle',
            'customer_name',
            'customer_phone',
            'customer_tin_number',
            'vehicle_model',
            'vehicle_shanci_kutir',
            'vehicle_motor_kutir',
            'vehicle_targa_kutir',
            'ken',

            # Motor Part
            'ye_fren_zeyt',
            'ye_meri_zeyt',
            'ye_motor_zeyt',
            'ye_radiator',
            'battery',
            'zinab_metregya',

            # Outer Part
            'maskerya',
            'antenna',
            'ferfango',
            'ye_fit_mebrat',
            'frecha_mebrat',
            'makomiya_mebrat',
            'ye_fit_targa',
            'nifas_mekelakeya',
            'spekiyo',
            'ye_ber_ijeta',
            'ika_mekelakeya',
            'ye_sivat_kidan',
            'ye_huala_targa',
            'ye_huala_mebrat_birchiko',
            'ye_ber_gomini_mestawat_lstic_frame',
            'ye_fit_prawlit',
            'ye_zinab_metregiya_ye_bilon_kidan',
            'birjineri_bilon',
            'ye_huala_prawlit_antsebaraki',
            'ye_fit_igir_fren_lock',
            'ye_huala_goma_libs',
            'fortomegala',
            'eskort_goma_mefcha',

            # Inner Part
            'tiras',
            'meterkosha',
            'ye_welel_mintaf',
            'ye_wember_libs',
            'ye_wist_spekiyo',
            'ye_wist_mebrat',
            'tep',
            'isat_adega_mekelakeya',
            'mebrat_mabriya',
            'zinab_metregiya_mebrat',
            'nedaj',
            'ye_tsehay_mekelakeya',
            'ye_wist_ber_mekfecha',
            'ye_mestewat_mawcha_mawreja',
            'ye_fit_ye_kofen_amorzrater',
            'ye_huala_ye_kofen_amorzrater',
            'klaks',
            'ye_wist_dashboard_kis_kulf',
            'ye_kofen_gomini',
            'ye_wuha_mercha',

            # Outer Condition
            'ye_ginbar_mestewat',
            'antsebaraki',
            'goma',
            'kirk',
            'goma_mefcha',
            'eskort_goma',
            'kolenet',
            'ye_cherke_get',

            # Footer Section
            'asrekabi_sim',
            'asrekabi_name',
            'firma',
            'ken_footer',
            'terekabi_sim',
            'terekabi_name',
            'firma_2',
            'ken_2',
            'ye_miwetabet_ken',
            'user'
        ]

    def create(self, validated_data, user=None):
        # Get the current user from the request context
        current_user = self.context["request"].user
        
        # Set the user field in the validated data if user is authenticated
        if current_user and hasattr(current_user, 'name'):
            validated_data['user'] = current_user.name

        return super().create(validated_data)





# The new implementation
class VehicleOrderVoucherLightSerializer(serializers.ModelSerializer):
    job_card = serializers.PrimaryKeyRelatedField(queryset=JobCard.objects.all())
    # Customer Info
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    # Vehicle Info
    vehicle_model = serializers.CharField(source='vehicle.model', read_only=True)
    vehicle_targa_kutir = serializers.CharField(source='vehicle.license_plate', read_only=True)
    vehicle_shanci_kutir = serializers.CharField(source='vehicle.shanci_kutir', read_only=True)
    # Asrekabi
    asrekabi_name = serializers.CharField(source='asrekabi_sim.name', read_only=True)
    terekabi_name = serializers.CharField(source='terekabi_sim.name', read_only=True)


    class Meta:
        model = VehicleOrderVoucher
        fields = [
            'id',
            'customer',
            'vehicle',
            'customer_name',
            'customer_phone',
            'vehicle_model',
            'vehicle_targa_kutir',
            'vehicle_shanci_kutir',
            'ken',
            'asrekabi_name',
            'terekabi_name',
            'user',
            'job_card'
        ]



class VehicleOrderVoucherItemsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = VehicleOrderVoucherItems
        fields = ['id', 'item_name', 'quantity', 'fixed_parts']
        read_only_fields = ['id']
        extra_kwargs = {
            'voucher_order': {'required': False, 'read_only': True},
        }

class VehicleOrderVoucherSerializer(serializers.ModelSerializer):
    items = VehicleOrderVoucherItemsSerializer(many=True)
    job_card = serializers.PrimaryKeyRelatedField(queryset=JobCard.objects.all())
    # Customer Info
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    customer_tin_number = serializers.CharField(source='customer.tin_number', read_only=True)

    # Vehicle Info
    vehicle_model = serializers.CharField(source='vehicle.model', read_only=True)
    vehicle_shanci_kutir = serializers.CharField(source='vehicle.shanci_kutir', read_only=True)
    vehicle_motor_kutir = serializers.CharField(source='vehicle.motor_kutir', read_only=True)
    vehicle_targa_kutir = serializers.CharField(source='vehicle.license_plate', read_only=True)

    # Asrekabi
    asrekabi_name = serializers.CharField(source='asrekabi_sim.name', read_only=True)
    terekabi_name = serializers.CharField(source='terekabi_sim.name', read_only=True)

    class Meta:
        model = VehicleOrderVoucher
        fields = [
            'id',
            'customer',
            'vehicle',
            'customer_name',
            'customer_phone',
            'customer_tin_number',
            'vehicle_model',
            'vehicle_shanci_kutir',
            'vehicle_motor_kutir',
            'vehicle_targa_kutir',
            'ken',
            'asrekabi_sim',
            'asrekabi_name',
            'asrekabi_firma',
            'asrekabi_ken',
            'terekabi_sim',
            'terekabi_name',
            'terekabi_firma',
            'terekabi_ken',
            'user',
            'job_card',
            'items'
        ]
    

    def create(self, validated_data, user=None):
        # Get the current user from the request context
        current_user = self.context["request"].user
        
        # Set the user field in the validated data if user is authenticated
        if current_user and hasattr(current_user, 'name'):
            validated_data['user'] = current_user.name
        
        # Extract items data from validated data
        items_to_create = validated_data.pop('items', [])
        # Reject creating a voucher with no items
        if not items_to_create:
            raise serializers.ValidationError({"error": "Order voucher must contain at least one item"})
                
        try:
            # All-or-nothing behavior: Everything inside the block is committed only if the whole block completes successfully. If any exception is raised (e.g., a serializers.ValidationError), Django rolls back all DB changes made inside the block.
            with transaction.atomic():

                # Create the main VehiclePartRequest instance
                voucher_order = VehicleOrderVoucher.objects.create(**validated_data)
                
                # Process each item in the items list
                for item_data in items_to_create:
                    item_name=item_data.get('item_name')
                    quantity = item_data.get('quantity')
                    fixed_parts = item_data.get('fixed_parts')
                    # Validate quantity
                    if quantity == 0:
                        item_data['quantity'] = None
                    else:
                        item_data['quantity'] = quantity
                    
                    
                    # Create the related VehiclePartRequestItems
                    VehicleOrderVoucherItems.objects.create(
                        voucher_order=voucher_order,
                        item_name=item_name,
                        quantity=quantity,
                        fixed_parts=fixed_parts
                    )
            
            return voucher_order
            
        except Exception as e:
            # In case of any error, raise a validation error with the message
            raise serializers.ValidationError({
                "error": f"Failed to create order voucher: {str(e)}"
            })
    
    def update(self, instance, validated_data):
        # Update main model fields
        fields = [
            'model', 'ye_bale_nibret_sim', 'shanci_kutir', 'motor_kutir',
            'targa_kutir', 'silk_kutir', 'tin_kutir', 'ken', 'asrekabi_sim',
            'asrekabi_firma', 'asrekabi_ken', 'terekabi_sim', 'terekabi_firma',
            'terekabi_ken', 'ye_merekebiya_ken', 'user'
        ]
        
        for field in fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])


        # stamp the actor for logging
        req = self.context.get("request")
        if req and hasattr(req.user, 'name'):
            instance.user = req.user.name
        
        
        # Handle items update if present
        if 'items' in validated_data:
            items_data = validated_data.pop('items')
            
            # Get existing items
            existing_items = {item.id: item for item in instance.items.all()}
            updated_item_ids = set()
            
            # Update or create items
            for item_data in items_data:
                item_id = item_data.get('id')
                
                if item_id and item_id in existing_items:
                    # Update existing item
                    item = existing_items[item_id]
                    for key, value in item_data.items():
                        setattr(item, key, value)
                    item.save()
                    updated_item_ids.add(item_id)
                else:
                    # Create new item
                    VehicleOrderVoucherItems.objects.create(
                        voucher_order=instance,
                        **item_data
                    )
            
            # Delete items that weren't included in the update
            for item_id, item in existing_items.items():
                if item_id not in updated_item_ids:
                    item.delete()
        
        instance.save()
        return instance


#  Purchase

class PurchaseProductSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    product_name = serializers.CharField(source='product.name', read_only=True)
    part_number = serializers.CharField(source='product.part_number', read_only=True)
    class Meta:
        model = PurchaseProduct
        fields = ['id', 'product', 'product_name', 'part_number', 'unit', 'description', 'quantity', 'unit_price', 'total_price']
    
    def update(self, instance, validated_data):
        new_quantity = validated_data.get('quantity', instance.quantity)
        old_quantity = instance.quantity
        instance.unit_price = validated_data.get('unit_price', instance.unit_price)
        instance.unit = validated_data.get('unit', instance.unit)
        instance.description = validated_data.get('description', instance.description)

        unit_price = validated_data.get('unit_price')        
        
        # If update_stocks is provided, update the stock directly
        if new_quantity is not None:
            instance.total_price = new_quantity * instance.unit_price
        else:
            instance.total_price = instance.quantity * instance.unit_price
        # instance.save()

        product = instance.product
        if new_quantity and new_quantity != old_quantity:
            quantity_difference = new_quantity - old_quantity
        else: 
            quantity_difference = old_quantity
        print(f"Quantity difference: {quantity_difference}")
        print(f"new quantity: {new_quantity}")
        print(f"Old quantity: {old_quantity}")
        if product and unit_price > 0:
            product.selling_price = unit_price
            product.stock += quantity_difference
            print(product.stock, quantity_difference)
            if product.stock < 0:
                raise serializers.ValidationError(f" {product.name} stock is less than Zero ")
            product.save()
        instance.quantity = new_quantity
        
        # instance.expense.total = instance.expense.products.aggregate(total_price=Sum('total_price'))['total_price'] or Decimal('0.00')
        instance.expense.total = instance.expense.products.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
        instance.expense.save()
        instance.save()

        return instance


class PurchaseExpenseLightSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = PurchaseExpense
        fields = ['id', 'purchase_date', 'supplier', 'number_of_items', 'total', 'payment_status', 'paid_amount', 'unpaid_amount', 'user']

class PurchaseExpenseSerializer(serializers.ModelSerializer):
    products = PurchaseProductSerializer(many=True)
    id = serializers.IntegerField(required=False)

    class Meta:
        model = PurchaseExpense
        fields = ['id', 'purchase_date', 'supplier', 'number_of_items', 'total', 'payment_status', 'paid_amount', 'unpaid_amount', 'user', 'products']

    def create(self, validated_data):
        user = self.context["request"].user
        if user:
            validated_data['user'] = user.name

        purchase_date=timezone.now()
        products_data = validated_data.pop('products')
        if not products_data:
            raise serializers.ValidationError({"error": "Purchase Expense must contain at least one Purchase Product"})
        expense = PurchaseExpense.objects.create(**validated_data)
        for product_data in products_data:
            PurchaseProduct.objects.create(expense=expense, **product_data)
        return expense
    
    def update(self, instance, validated_data):
        products_data = validated_data.pop('products', [])

        # At the start of the update method, add:
        is_adding_new_products = any(not item.get('id') for item in products_data)

        new_paid = validated_data.get('paid_amount', 0)
        instance.payment_status = validated_data.get('payment_status', instance.payment_status)

        old_status = instance.payment_status
        old_paid = instance.paid_amount
        old_unpaid = instance.unpaid_amount

        for attr, value in validated_data.items():
            if attr != 'paid_amount' and attr != 'payment_status':
                setattr(instance, attr, value)
        instance.save()

        # Update or create products
        existing_ids = [p.id for p in instance.products.all()]
        received_ids = [item.get('id') for item in products_data if item.get('id')]

        for product_data in products_data:
            product_id = product_data.get('id')
            if not product_id:
                # Create new product
                product = product_data.get('product')
                if product:
                    product.stock += int(product_data.get('quantity', 0))
                    product.save()

                quantity = int(product_data.get('quantity', 0))
                unit_price = Decimal(str(product_data.get('unit_price', 0)))
                total_price = quantity * unit_price
                PurchaseProduct.objects.create(expense=instance, total_price=total_price, **product_data)


        instance.total = instance.products.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
        instance.total = Decimal(str(instance.total))
        instance.save()

        if 'paid_amount' in validated_data and instance.payment_status != 'Paid' and not is_adding_new_products:
            paid = instance.paid_amount + new_paid
            total = Decimal(str(instance.total or 0))
            
            if paid < 0:
                raise serializers.ValidationError("Paid amount cannot be negative")
            if paid > total:
                raise serializers.ValidationError("Paid amount cannot be greater than total amount")
            
            instance.paid_amount = paid
            instance.save()

        if instance.payment_status == 'Paid':
            instance.paid_amount = instance.total
            instance.unpaid_amount = Decimal('0.00')
            instance.payment_status = 'Paid'
        elif instance.payment_status == 'Pending' and instance.total >= instance.paid_amount:
            instance.unpaid_amount = max(instance.total - instance.paid_amount, Decimal('0.00'))
            if instance.unpaid_amount == Decimal('0.00'):
                instance.payment_status = 'Paid'   
        elif instance.payment_status == 'Unpaid':
            instance.paid_amount = Decimal('0.00')
            instance.unpaid_amount = instance.total
            instance.payment_status = 'Unpaid'
        instance.save()

        # 🔍 Log changes
        if instance.payment_status != old_status:
            ExpensePaymentLog.objects.create(
                expense=instance,
                supplier=instance.supplier,
                change_type="Status Change",
                field_name="payment_status",
                old_value=old_status,
                new_value=instance.payment_status,
                user=instance.user  # Optional if available
            )

        if instance.paid_amount != old_paid:
            ExpensePaymentLog.objects.create(
                expense=instance,
                supplier=instance.supplier,
                change_type="Payment Update",
                field_name="paid_amount",
                old_value=str(old_paid),
                new_value=str(instance.paid_amount),
                user=instance.user
            )
        
        instance.save()
        return instance


class PurchaseSupplierLightSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, required=False)

    class Meta:
        model = PurchaseSupplier
        fields = ['id', 'supplier', 'supplier_name', 'total_amount', 'payment_status', 'paid_amount', 'unpaid_amount', 'user']

class PurchaseSupplierSerializer(serializers.ModelSerializer):
    expenses = PurchaseExpenseSerializer(many=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, required=False)

    class Meta:
        model = PurchaseSupplier
        fields = ['id', 'supplier', 'supplier_name', 'total_amount', 'payment_status', 'paid_amount', 'unpaid_amount', 'user', 'expenses']
        constraints = [
            UniqueConstraint(fields=['supplier'], name='unique_supplier')
        ]
    
    def create(self, validated_data):
        user = self.context["request"].user
        if user:
            validated_data['user'] = user.name

        user_name = validated_data['user']

        expenses_data = validated_data.pop('expenses')
        if not expenses_data:
            raise serializers.ValidationError({"error": "Purchase Supplier must contain at least one Purchase Expense"})
        total_amount = Decimal('0.00')  # Start total
        supplier = PurchaseSupplier.objects.create(**validated_data)

        try:
            for expense_data in expenses_data:
                products_data = expense_data.pop('products', [])
                paid = expense_data.get('paid_amount')
                payment_status = expense_data.get('payment_status')


                # Calculate total for this expense
                expense_total = sum(Decimal(str(product.get('unit_price', 0))) * int(product.get('quantity', 0)) for product in products_data)
                total_amount += expense_total

                if paid and paid > expense_total:
                    raise serializers.ValidationError("Expense cannot be created with paid amount greater than total amount so re-create the expense by ging to manage purchase")

                if expense_data['payment_status'] == 'Paid':
                    expense_data['paid_amount'] = expense_total
                elif expense_data['payment_status'] == 'Unpaid':
                    expense_data['unpaid_amount'] = expense_total
                elif expense_data['payment_status'] == 'Pending':
                    if expense_data['paid_amount'] > 0:
                        expense_data['unpaid_amount'] = max(expense_total - expense_data['paid_amount'], Decimal('0.00'))
                    elif expense_data['paid_amount'] == 0 or expense_data['paid_amount'] is None:
                        expense_data['unpaid_amount'] = expense_total

                if validated_data.get('supplier'):
                    expense_supplier_name = str(validated_data['supplier'])  # Convert Supplier instance to string
                else:
                    expense_supplier_name = None
                    
                # Create the expense with computed total
                expense = PurchaseExpense.objects.create(supplier_level=supplier, supplier=expense_supplier_name, user=user_name, total=expense_total, **expense_data)

                for product_data in products_data:
                    product = product_data.get('product')
                    input_unit_price = product_data.get('unit_price')
                    if product:
                        if input_unit_price > 0:
                            product.stock += int(product_data.get('quantity', 0))
                            product.save()


                    quantity = int(product_data.get('quantity', 0))
                    # unit_price = Decimal(str(product_data.get('unit_price', 0)))
                    unit_price = input_unit_price
                    total_price = quantity * unit_price
                    PurchaseProduct.objects.create(expense=expense, total_price=total_price, **product_data)


            # After all expenses, update supplier's total_amount
            supplier.total_amount = total_amount
            supplier.save(update_fields=['total_amount'])

            return supplier

        except Exception as e:
            # Optional: rollback or raise a validation error
            raise serializers.ValidationError({"detail": f"Failed to create supplier: {str(e)}"})

    def update(self, instance, validated_data):
        expenses_data = validated_data.pop('expenses', [])
        # Capture original values before update
        old_status = instance.payment_status
        old_paid = instance.paid_amount
        old_unpaid = instance.unpaid_amount

        supplier_name = instance.supplier.name or None

        # Update supplier fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        for expense_data in expenses_data:
            expense_id = expense_data.get('id')
            products_data = expense_data.pop('products', [])

            if not expense_id:
                # Create new Expense
                paid_amount = expense_data.get('paid_amount', None)
                unpaid_amount = expense_data.get('unpaid_amount', None)
                expense_total = sum(Decimal(str(product.get('unit_price', 0))) * int(product.get('quantity', 0)) for product in products_data)
                unpaid_amount = expense_total - paid_amount if paid_amount else expense_total

                if paid_amount and paid_amount > expense_total:
                    raise serializers.ValidationError("Expense cannot be created with paid amount greater than total amount so re-create the expense by ging to manage purchase")

                
                # Inside your for-loop where you create a new expense:
                update_payment_status_on_new_expense_or_product(supplier=instance, expense=None)
                

                # Avoid duplicate 'total' key error
                expense_data.pop('total', None)
                expense = PurchaseExpense.objects.create(supplier_level=instance, supplier=supplier_name, total=expense_total, unpaid_amount=unpaid_amount, **expense_data)

                for product_data in products_data:
                    product_id = product_data.get('id')
                    if product_id:
                        # Update existing product
                        product = PurchaseProduct.objects.get(id=product_id, expense=instance)
                        for attr, value in product_data.items():
                            setattr(product, attr, value)
                        product.save()
                    else:
                        # Create new product
                        quantity = int(product_data.get('quantity', 0))
                        unit_price = Decimal(str(product_data.get('unit_price', 0)))
                        total_price = quantity * unit_price

                        PurchaseProduct.objects.create(expense=expense, total_price=total_price, **product_data)

        # Syncronizing the total, paid and unpaid with the expenses
        instance.total_amount = sum(expense.total for expense in instance.expenses.all())
        instance.paid_amount = sum(expense.paid_amount for expense in instance.expenses.all())        
        instance.unpaid_amount = sum(expense.unpaid_amount for expense in instance.expenses.all())
        
        # Updating the status of supplier
        total_amount = Decimal(str(instance.total_amount or 0))
        paid = Decimal(str(instance.paid_amount or 0))

        if instance.payment_status == 'Pending':
            if paid > 0:
                instance.unpaid_amount = max(total_amount - paid, Decimal('0.00'))
            elif paid == 0:
                instance.unpaid_amount = total_amount
        elif instance.payment_status == 'Unpaid':
            instance.paid_amount = Decimal('0.00')
            instance.unpaid_amount = total_amount
        elif instance.payment_status == 'Paid':
            instance.paid_amount = total_amount
            instance.unpaid_amount = Decimal('0.00')

        
        # Log changes
        if instance.payment_status != old_status:
            SupplierPaymentLog.objects.create(
                supplier=instance,
                change_type="Status Change",
                field_name="payment_status",
                old_value=old_status,
                new_value=instance.payment_status,
                user=instance.user  # Optional if available
            )

        if instance.paid_amount != old_paid:
            SupplierPaymentLog.objects.create(
                supplier=instance,
                change_type="Payment Update",
                field_name="paid_amount",
                old_value=str(old_paid),
                new_value=str(instance.paid_amount),
                user=instance.user
            )

        instance.save()            

        return instance




#  New Credit

class CreditProductSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    product_name = serializers.CharField(source='product.name', read_only=True)
    part_number = serializers.CharField(source='product.part_number', read_only=True)
    class Meta:
        model = CreditProduct
        fields = ['id', 'product', 'product_name', 'part_number', 'unit', 'description', 'quantity', 'unit_price', 'total_price']
    
    def update(self, instance, validated_data):
        new_quantity = validated_data.get('quantity', instance.quantity)
        old_quantity = instance.quantity
        instance.unit_price = validated_data.get('unit_price', instance.unit_price)
        instance.unit = validated_data.get('unit', instance.unit)
        instance.description = validated_data.get('description', instance.description)

        unit_price = validated_data.get('unit_price')        

        if new_quantity and new_quantity <= 0:
            raise serializers.ValidationError({
                "error": f"Quantity must be greater than zero."
            })
        
        # If update_stocks is provided, update the stock directly
        if new_quantity is not None:
            instance.total_price = new_quantity * instance.unit_price
        else:
            instance.total_price = instance.quantity * instance.unit_price
        # instance.save()

        product = instance.product
        if new_quantity and new_quantity != old_quantity:
            quantity_difference = new_quantity - old_quantity
        else: 
            quantity_difference = old_quantity
        print(f"Quantity difference: {quantity_difference}")
        print(f"new quantity: {new_quantity}")
        print(f"Old quantity: {old_quantity}")
        if product and unit_price > 0:
            product.stock += quantity_difference
            print(product.stock, quantity_difference)
            if product.stock < 0:
                raise serializers.ValidationError(f" {product.name} stock is less than Zero ")
            product.save()
        instance.quantity = new_quantity
        
        # instance.credit.total = instance.credit.products.aggregate(total_price=Sum('total_price'))['total_price'] or Decimal('0.00')
        instance.credit.total = instance.credit.products.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
        instance.credit.save()
        instance.save()

        return instance


class CreditCreditLightSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = CreditCredit
        fields = ['id', 'credit_date', 'customer', 'number_of_items', 'receipt', 'performa', 'sub_total', 'vat', 'total', 'payment_status', 'paid_amount', 'unpaid_amount', 'user']

class CreditCreditSerializer(serializers.ModelSerializer):
    products = CreditProductSerializer(many=True)
    id = serializers.IntegerField(required=False)

    class Meta:
        model = CreditCredit
        fields = ['id', 'credit_date', 'customer', 'number_of_items', 'receipt', 'performa', 'sub_total', 'vat', 'total', 'payment_status', 'paid_amount', 'unpaid_amount', 'user', 'products']

    def create(self, validated_data):
        user = self.context["request"].user
        if user:
            validated_data['user'] = user.name

        purchase_date=timezone.now()
        products_data = validated_data.pop('products')
        if not products_data:
            raise serializers.ValidationError({"error": "Credit must contain at least one Credit Product"})
        credit = CreditCredit.objects.create(**validated_data)
        for product_data in products_data:
            CreditProduct.objects.create(credit=credit, **product_data)
        return credit
    
    def update(self, instance, validated_data):
        products_data = validated_data.pop('products', [])

        # At the start of the update method, add:
        is_adding_new_products = any(not item.get('id') for item in products_data)
        receipt = instance.receipt

        new_paid = validated_data.get('paid_amount', 0)
        instance.payment_status = validated_data.get('payment_status', instance.payment_status)

        old_status = instance.payment_status
        old_paid = instance.paid_amount
        old_unpaid = instance.unpaid_amount

        for attr, value in validated_data.items():
            if attr != 'paid_amount' and attr != 'payment_status':
                setattr(instance, attr, value)
        instance.save()

        # Update or create products
        existing_ids = [p.id for p in instance.products.all()]
        received_ids = [item.get('id') for item in products_data if item.get('id')]

        for product_data in products_data:
            product_id = product_data.get('id')
            if not product_id:
                # Create new product
                # product = product_data.get('product')
                product = product_data['product']
                part_number = product.part_number
                product_data['part_number'] = part_number
                quantity = int(product_data.get('quantity', 0))
                unit_price = Decimal(str(product_data.get('unit_price', product.selling_price)))
                product_data['unit_price'] = unit_price
                if quantity is not None and product.stock < quantity:
                    raise serializers.ValidationError({
                        "error": f"Insufficient stock for {product.name}. Available stock is {product.stock}, but {quantity} was requested."
                    })

                product.stock -= quantity
                product.save()
                total_price = quantity * unit_price
                CreditProduct.objects.create(credit=instance, total_price=total_price, **product_data)


        sub_total = instance.products.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
        instance.sub_total = sub_total
        if receipt == "Receipt":
            instance.vat = instance.sub_total * Decimal('0.15')
        else:
            instance.vat = 0

        instance.total = instance.sub_total + instance.vat

        # instance.total = instance.products.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
        instance.total = Decimal(str(instance.total))
        instance.save()

        if 'paid_amount' in validated_data and instance.payment_status != 'Paid' and not is_adding_new_products:
            paid = instance.paid_amount + new_paid
            total = Decimal(str(instance.total or 0))
            
            if paid < 0:
                raise serializers.ValidationError("Paid amount cannot be negative")
            if paid > total:
                raise serializers.ValidationError("Paid amount cannot be greater than total amount")
            
            instance.paid_amount = paid
            instance.save()

        if instance.payment_status == 'Paid':
            instance.paid_amount = instance.total
            instance.unpaid_amount = Decimal('0.00')
            instance.payment_status = 'Paid'
        elif instance.payment_status == 'Pending' and instance.total >= instance.paid_amount:
            instance.unpaid_amount = max(instance.total - instance.paid_amount, Decimal('0.00'))
            if instance.unpaid_amount == Decimal('0.00'):
                instance.payment_status = 'Paid'   
        elif instance.payment_status == 'Unpaid':
            instance.paid_amount = Decimal('0.00')
            instance.unpaid_amount = instance.total
            instance.payment_status = 'Unpaid'
        
        instance.save()
        return instance


class CreditCustomerLightSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True, required=False)
    organization = serializers.CharField(source='customer.organization', read_only=True, required=False)

    class Meta:
        model = CreditCustomer
        fields = ['id', 'customer', 'customer_name', 'organization', 'total_amount', 'payment_status', 'paid_amount', 'unpaid_amount', 'user']

class CreditCustomerSerializer(serializers.ModelSerializer):
    credits = CreditCreditSerializer(many=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True, required=False)
    organization = serializers.CharField(source='customer.organization', read_only=True, required=False)

    class Meta:
        model = CreditCustomer
        fields = ['id', 'customer', 'customer_name', 'organization', 'total_amount', 'payment_status', 'paid_amount', 'unpaid_amount', 'user', 'credits']
        constraints = [
            UniqueConstraint(fields=['customer'], name='unique_customer')
        ]
    
    def create(self, validated_data):
        user = self.context["request"].user
        if user:
            validated_data['user'] = user.name

        user_name = validated_data['user']

        credits_data = validated_data.pop('credits')
        if not credits_data:
            raise serializers.ValidationError({"error": "Credit Customer must contain at least one Credit"})

        # If we get here, all validations passed - create the order
        with transaction.atomic():

            total_amount = Decimal('0.00')  # Start total
            customer = CreditCustomer.objects.create(**validated_data)

            try:
                for credit_data in credits_data:
                    products_data = credit_data.pop('products', [])
                    receipt = credit_data.get('receipt', 'Receipt')
                    paid = credit_data.get('paid_amount')
                    payment_status = credit_data.get('payment_status')

                    # products_data = validated_data.pop('products')
                    if not products_data:
                        raise serializers.ValidationError({"error": "Credit must contain at least one product"})


                    # First validate all products before creating anything
                    for product_data in products_data:
                        product = product_data['product']
                        if product.stock is None:
                            raise serializers.ValidationError({
                                "error": f"Product {product.name} stock is not available."
                            })


                    # Calculate total for this credit
                    # credit_total = sum(Decimal(str(product.get('unit_price', 0))) * int(product.get('quantity', 0)) for product in products_data)
                    credit_sub_total = sum(Decimal(str(product.get('unit_price', 0))) * int(product.get('quantity', 0)) for product in products_data)
                    if receipt == "Receipt":
                        credit_vat = credit_sub_total * Decimal('0.15')
                    else:
                        credit_vat = 0
                    credit_total = credit_sub_total + credit_vat
                    print(f"Credit Total: {credit_total}")

                    total_amount += credit_total
                    # total_amount += credit_total
                    print(f"Total Amount: {total_amount}")

                    if paid and paid > credit_total:
                        raise serializers.ValidationError("Credit cannot be created with paid amount greater than total amount so re-create the credit by going to manage Credit Customer")

                    if credit_data['payment_status'] == 'Paid':
                        credit_data['paid_amount'] = credit_total
                    elif credit_data['payment_status'] == 'Unpaid':
                        credit_data['unpaid_amount'] = credit_total
                    elif credit_data['payment_status'] == 'Pending':
                        if credit_data['paid_amount'] > 0:
                            credit_data['unpaid_amount'] = max(credit_total - credit_data['paid_amount'], Decimal('0.00'))
                        elif credit_data['paid_amount'] == 0 or credit_data['paid_amount'] is None:
                            credit_data['unpaid_amount'] = credit_total

                    if validated_data.get('customer'):
                        credit_customer_name = str(validated_data['customer'])  # Convert Customer instance to string
                    else:
                        credit_customer_name = None
                        
                    # Create the credit with computed total
                    credit = CreditCredit.objects.create(customer_level=customer, customer=credit_customer_name, user=user_name, sub_total=credit_sub_total, vat=credit_vat, total=credit_total, **credit_data)

                    for product_data in products_data:
                        product = product_data.get('product')
                        part_number = product.part_number
                        product_data['part_number'] = part_number
                        quantity = int(product_data.get('quantity', 0))
                        unit_price = Decimal(str(product_data.get('unit_price', product.selling_price)))
                        product_data['unit_price'] = unit_price
                        if quantity >  product.stock:
                            raise serializers.ValidationError({
                                "error": f"Insufficient stock for {product.name}. Available stock is {product.stock}, but {quantity} was requested."
                            })

                        product.stock -= quantity
                        product.save()
                        total_price = quantity * unit_price
                        CreditProduct.objects.create(credit=credit, total_price=total_price, **product_data)


                # After all credits, update customer's total_amount
                customer.total_amount = total_amount
                customer.save(update_fields=['total_amount'])

                return customer

            # except Exception as e:
            #     # Optional: rollback or raise a validation error
            #     raise serializers.ValidationError(e)
            except Exception as e:
                # Check if the exception has DRF-specific detail (.detail attribute)
                if hasattr(e, 'detail'):
                    detail = e.detail
                    
                    # Clean up dictionaries (e.g., {'error': ErrorDetail(...)})
                    if isinstance(detail, dict):
                        cleaned_detail = {k: str(v) for k, v in detail.items()}
                    # Clean up lists
                    elif isinstance(detail, list):
                        cleaned_detail = [str(item) for item in detail]
                    else:
                        cleaned_detail = str(detail)
                        
                    raise serializers.ValidationError(cleaned_detail)
                
                # Fallback for standard Python exceptions
                raise serializers.ValidationError(str(e))

    def update(self, instance, validated_data):
        credits_data = validated_data.pop('credits', [])
        # Capture original values before update
        old_status = instance.payment_status
        old_paid = instance.paid_amount
        old_unpaid = instance.unpaid_amount

        customer_name = instance.customer.name or None

        # Update customer fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        for credit_data in credits_data:
            credit_id = credit_data.get('id')
            products_data = credit_data.pop('products', [])

            if not credit_id:
                # Create new Credit
                paid_amount = credit_data.get('paid_amount', None)
                unpaid_amount = credit_data.get('unpaid_amount', None)
                receipt = credit_data.get('receipt', None)

                credit_sub_total = sum(Decimal(str(product.get('unit_price', 0))) * int(product.get('quantity', 0)) for product in products_data)
                # credit_sub_total = sum(Decimal(str(product.get('unit_price', 0))) * int(product.get('quantity', 0)) for product in products_data)
                if receipt == "Receipt":
                    credit_vat = credit_sub_total * Decimal('0.15')
                else:
                    credit_vat = 0
                credit_total = credit_sub_total + credit_vat
                # credit_total = sum(Decimal(str(product.get('unit_price', 0))) * int(product.get('quantity', 0)) for product in products_data)
                unpaid_amount = credit_total - paid_amount if paid_amount else credit_total

                if paid_amount and paid_amount > credit_total:
                    raise serializers.ValidationError("Credit cannot be created with paid amount greater than total amount so re-create the credit by going to manage Credit Customer")

                
                # Inside your for-loop where you create a new credit:
                update_payment_status_on_new_credit_or_product(customer=instance, credit=None)
                

                # Avoid duplicate 'total' key error
                credit_data.pop('total', None)
                credit = CreditCredit.objects.create(customer_level=instance, customer=customer_name, sub_total=credit_sub_total, vat=credit_vat, total=credit_total, unpaid_amount=unpaid_amount, **credit_data)

                for product_data in products_data:
                    product_id = product_data.get('id')
                    if product_id:
                        # Update existing product
                        product = CreditProduct.objects.get(id=product_id, credit=instance)
                        for attr, value in product_data.items():
                            setattr(product, attr, value)
                        product.save()
                    else:
                        # Create new product
                        # quantity = int(product_data.get('quantity', 0))
                        # unit_price = Decimal(str(product_data.get('unit_price', 0)))
                        # total_price = quantity * unit_price

                        product = product_data['product']
                        part_number = product.part_number
                        product_data['part_number'] = part_number
                        quantity = int(product_data.get('quantity', 0))
                        unit_price = Decimal(str(product_data.get('unit_price', product.selling_price)))
                        product_data['unit_price'] = unit_price
                        if quantity >  product.stock:
                            raise serializers.ValidationError({
                                "error": f"Insufficient stock for {product.name}. Available stock is {product.stock}, but {quantity} was requested."
                            })

                        # remaining_stock = product.stock - quantity
                        product.stock -= quantity
                        product.save()
                        total_price = quantity * unit_price

                        CreditProduct.objects.create(credit=credit, total_price=total_price, **product_data)

        # Syncronizing the total, paid and unpaid with the credits
        instance.total_amount = sum(credit.total for credit in instance.credits.all())
        instance.paid_amount = sum(credit.paid_amount for credit in instance.credits.all())        
        instance.unpaid_amount = sum(credit.unpaid_amount for credit in instance.credits.all())
        
        # Updating the status of customer
        total_amount = Decimal(str(instance.total_amount or 0))
        paid = Decimal(str(instance.paid_amount or 0))

        if instance.payment_status == 'Pending':
            if paid > 0:
                instance.unpaid_amount = max(total_amount - paid, Decimal('0.00'))
            elif paid == 0:
                instance.unpaid_amount = total_amount
        elif instance.payment_status == 'Unpaid':
            instance.paid_amount = Decimal('0.00')
            instance.unpaid_amount = total_amount
        elif instance.payment_status == 'Paid':
            instance.paid_amount = total_amount
            instance.unpaid_amount = Decimal('0.00')

        instance.save()            
        return instance





# Log Related
class OrderLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderLog
        fields = '__all__'

class OrderReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Report
        fields = '__all__'


class SupplierPaymentLogSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.supplier.name', read_only=True)

    class Meta:
        model = SupplierPaymentLog
        fields = ['id', 'supplier_name', 'change_type', 'field_name', 'old_value', 'new_value', 'user', 'supplier', 'timestamp']

class ExpensePaymentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpensePaymentLog
        fields = '__all__'

class OrderPaymentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderPaymentLog
        fields = '__all__'



class JobCardLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCardLog
        fields = [ 'id', 'user', 'action', 'model_name', 'object_id', 'timestamp', 'customer', 'vehicle', 'status', 'total_cost', 'odometer_reading', 'changes_on_update' ]

class JobCardAssignmentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCardAssignmentLog
        fields = [ 'id', 'user', 'action', 'model_name', 'object_id', 'timestamp', 'job_card_id', 'worker', 
                    'service_package', 'status', 'package_status', 'task_description', 'completed_at', 'changes_on_update' 
                ]

class AssignedServicesLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignedServiceLog
        fields = [ 'id', 'user', 'action', 'model_name', 'object_id', 'timestamp', 'assignment_id',
                    'worker', 'job_card_id', 'service', 'status', 'started_at', 'completed_at', 'changes_on_update'
                ]



class VehiclePartRequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehiclePartRequestLog
        fields = [ 'id', 'user', 'action', 'model_name', 'object_id', 'timestamp', 'job_card_id',
                    'customer', 'vehicle', 'total_amount', 'asrekabi', 'terekabi', 'changes_on_update'
                ]

class VehiclePartRequestItemLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehiclePartRequestItemLog
        fields = [ 'id', 'user', 'action', 'model_name', 'object_id', 'timestamp',
                    'part_request_id', 'product', 'quantity', 'unit_price', 'price', 'changes_on_update'
                ]



class VehicleOldPartDeliveryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleOldPartDeliveryLog
        fields = [ 'id', 'user', 'action', 'model_name', 'object_id', 'timestamp', 'job_card_id',
                    'tegagn_mechanic', 'vehicle', 'asrekabi', 'terekabi', 'changes_on_update'
                ]

class VehicleOldPartDeliveryItemLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleOldPartDeliveryItemLog
        fields = [ 'id', 'user', 'action', 'model_name', 'object_id', 'timestamp',
                    'old_part_id', 'product', 'quantity', 'fixed_parts', 'changes_on_update'
                ]



class VehicleOrderVoucherLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleOrderVoucherLog
        fields = [ 'id', 'user', 'action', 'model_name', 'object_id', 'timestamp', 'job_card_id',
                    'customer', 'vehicle', 'asrekabi', 'terekabi', 'changes_on_update'
                ]

class VehicleOrderVoucherItemLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleOrderVoucherItemLog
        fields = [ 'id', 'user', 'action', 'model_name', 'object_id', 'timestamp',
                    'voucher_order_id', 'item_name', 'quantity', 'fixed_parts', 'changes_on_update'
                ]
