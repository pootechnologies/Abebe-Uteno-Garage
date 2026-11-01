from django.urls import path
from .views import (
    CustomerListCreateAPIView, CustomerDetailAPIView,
    VehicleListCreateAPIView, VehicleDetailAPIView,
    ServiceListCreateAPIView, ServiceDetailAPIView,
    ServicePackageListCreateAPIView, ServicePackageDetailAPIView,
    JobCardListCreateAPIView, JobCardDetailAPIView,
    InvoiceListCreateAPIView, InvoiceDetailAPIView,
    VehicleAcceptanceListCreateAPIView, VehicleAcceptanceDetailAPIView,
    VehicleOldPartDeliveryItemsListCreateAPIView, VehicleOldPartDeliveryItemsDetailAPIView,
    VehicleOldPartDeliveryListCreateAPIView, VehicleOldPartDeliveryDetailAPIView,
    VehiclePartRequestListCreateAPIView, VehiclePartRequestDetailAPIView,
    VehiclePartRequestItemsListCreateAPIView, VehiclePartRequestItemsDetailAPIView,
    VehicleOrderVoucherListCreateAPIView, VehicleOrderVoucherDetailAPIView,
    VehicleOrderVoucherItemsListCreateAPIView, VehicleOrderVoucherItemsDetailAPIView,
    JobCardAssignmentListCreateAPIView, JobCardAssignmentDetailAPIView, 
    MyAssignedTasksAPIView, MyAssignedTasksDetailAPIView,
    UpdateAssignedServiceStatusAPIView, UpdateAssignmentPackageStatusAPIView, AssignmentVerificationAPIView, ExaminerUpdateAssignedServiceAPIView, ExaminerUpdateServicePackageAPIView,
    PerformaCustomerListCreateView,
    PerformaCustomerDetailView,
    PerformaPerformaListCreateView,
    PerformaPerformaDetailView,
    PerformaProductListCreateView,
    PerformaProductDetailView,
    ConvertPerformaToOrderAPIView,
    ConvertPerformaToCreditAPIView,

    OrderListCreatView,
    OrderDetailView,
    OrderItemListCreateView,
    OrderItemDetailView,
    OrderCreditListAPIView,
    OrderItemCreditListView,

    CreditCustomerListCreateView,
    CreditCustomerDetailView,
    CreditCreditListCreateView,
    CreditCreditDetailView,
    CreditProductListCreateView,
    CreditProductDetailView,

    ProductListCreateAPIView, 
    ProductRetrieveUpdateDeleteAPIView,

    SupplierListCreateAPIView,
    SupplierRetrieveUpdateDeleteAPIView,

    CategoryListCreateAPIView,
    CategoryRetrieveUpdateDeleteAPIView,

    CompanyListCreateAPIView,
    CompanyRetrieveUpdateDeleteAPIView,
    # Include others here too,

    PurchaseExpenseListCreateView,
    PurchaseExpenseDetailView,
    PurchaseProductListCreateView,
    PurchaseProductDetailView,
    PurchaseSupplierListCreateView,
    PurchaseSupplierDetailView,

    SupplierLogListView,
    ExpenseLogListView,
    OrderLogListView,
    OrderReceiptAPIView,
    CreditReceiptAPIView,
    PerformaReceiptAPIView,
    InvoiceReceiptAPIView,
    RecentOrderLimitedAPIView,
    RecentJobCardLimitedAPIView,
    RecentAcceptanceLimitedAPIView,
    
    JobCardStatusScheduledAPIView,
    JobCardStatusInProgressAPIView,
    JobCardStatusCompletedAPIView,
    JobCardStatusAPIView,

    DailyJobCardStatusScheduledAPIView,
    DailyJobCardStatusInProgressAPIView,
    DailyJobCardStatusCompletedAPIView,

    TotalOrderAPIView,
    TotalProductAPIView,
    TotalCustomerAPIView,
    TotalSupplierAPIView,
    TotalServiceAPIView,
    TotalServicePackageAPIView,
    TotalVehicleAPIView,
    TotalCategoryAPIView,
    TotalAcceptanceAPIView,
    TotalPerformaAPIView,
    TotalExpensesAPIView,
    RetriveTotalRevenueAPIView,

    AvailableJobCardPartRequestAPIView,
    AvailableJobCardOrderVoucherAPIView,
    AvailableJobCardOldPartAPIView,
    AvailableJobCardInvoiceAPIView,
    
    ExcelReportAPIView,
    
    JobCardLogAPIView,
    JobCardAssignmentLogAPIView,
    AssignedServiceLogAPIView,
    JobCardReceiptAPIView,

    DailySalesAPIView,
    WeeklySalesAPIView,
    MonthlySalesAPIView,
    YearlySalesAPIView,

    DailySalesEachUserAPIView,
    WeeklySalesEachUserAPIView,
    MonthlySalesEachUserAPIView,
    YearlySalesEachUserAPIView,

    VehiclePartRequestLogAPIView,
    VehiclePartRequestItemLogAPIView,

    VehicleOldPartDeliveryLogAPIView,
    VehicleOldPartDeliveryItemLogAPIView,

    VehicleOrderVoucherLogAPIView,
    VehicleOrderVoucherItemLogAPIView
)

urlpatterns = [
    path('customers/', CustomerListCreateAPIView.as_view()),
    path('customers/<int:pk>/', CustomerDetailAPIView.as_view()),
    
    path('vehicles/', VehicleListCreateAPIView.as_view()),
    path('vehicles/<int:pk>/', VehicleDetailAPIView.as_view()),

    path('services/', ServiceListCreateAPIView.as_view()),
    path('services/<int:pk>/', ServiceDetailAPIView.as_view()),
    
    path('servicepackages/', ServicePackageListCreateAPIView.as_view()),
    path('servicepackages/<int:pk>/', ServicePackageDetailAPIView.as_view()),

    path('jobcard/', JobCardListCreateAPIView.as_view()),
    path('jobcard/<int:pk>/', JobCardDetailAPIView.as_view()),
    
    path('jobcardassignment/', JobCardAssignmentListCreateAPIView.as_view()),
    path('jobcardassignment/<int:pk>/', JobCardAssignmentDetailAPIView.as_view()),

    path('my-assignments/', MyAssignedTasksAPIView.as_view(), name='my-assignments'),
    path('my-assignments/<int:assignment_id>/', MyAssignedTasksDetailAPIView.as_view(), name='my-assignments-detail'),
    path('my-assignments/<int:assignment_id>/services/<int:service_id>/', UpdateAssignedServiceStatusAPIView.as_view(), name='update-service-status'),
    path('my-assignments/<int:assignment_id>/package/', UpdateAssignmentPackageStatusAPIView.as_view(), name='update-package-status'),

    path('examiner/assigned-services/<int:assigned_service_id>/', ExaminerUpdateAssignedServiceAPIView.as_view(),name='examiner-update-assigned-service'),
    path('examiner/assigned-services-package/<int:assignment_id>/', ExaminerUpdateServicePackageAPIView.as_view(),name='examiner-update-service-package'),

    path('jobcardassignment/<int:assignment_id>/verify/', AssignmentVerificationAPIView.as_view(), name='verify-assignment'),


    path('partrequest/', VehiclePartRequestListCreateAPIView.as_view()),
    path('partrequest/<int:pk>/', VehiclePartRequestDetailAPIView.as_view()),
    path('partrequestitems/', VehiclePartRequestItemsListCreateAPIView.as_view()),
    path('partrequestitems/<int:pk>/', VehiclePartRequestItemsDetailAPIView.as_view()),
    
    path('ordervoucher/', VehicleOrderVoucherListCreateAPIView.as_view()),
    path('ordervoucher/<int:pk>/', VehicleOrderVoucherDetailAPIView.as_view()),
    path('ordervoucheritems/', VehicleOrderVoucherItemsListCreateAPIView.as_view()),
    path('ordervoucheritems/<int:pk>/', VehicleOrderVoucherItemsDetailAPIView.as_view()),

    path('invoices/', InvoiceListCreateAPIView.as_view()),
    path('invoices/<int:pk>/', InvoiceDetailAPIView.as_view()),
    path('invoices/<int:pk>/receipt/', InvoiceReceiptAPIView.as_view(), name='invoice-receipt'),
    
    path('acceptance/', VehicleAcceptanceListCreateAPIView.as_view()),
    path('acceptance/<int:pk>/', VehicleAcceptanceDetailAPIView.as_view()),

    path('oldpartitems/', VehicleOldPartDeliveryItemsListCreateAPIView.as_view()),
    path('oldpartitems/<int:pk>/', VehicleOldPartDeliveryItemsDetailAPIView.as_view()),

    path('oldpart/', VehicleOldPartDeliveryListCreateAPIView.as_view()),
    path('oldpart/<int:pk>/', VehicleOldPartDeliveryDetailAPIView.as_view()),

    path('performa-customers/', PerformaCustomerListCreateView.as_view(), name='performa-customer-list-create'),
    path('performa-customers/<pk>', PerformaCustomerDetailView.as_view(), name='performa-customer-list-create'),
    path('performa-performas/', PerformaPerformaListCreateView.as_view(), name='performa-performas-list-create'),
    path('performa-performas/<pk>', PerformaPerformaDetailView.as_view(), name='performa-performas-list-create'),
    path('performa-products/', PerformaProductListCreateView.as_view(), name='performa-product-list-create'),
    path('performa-products/<pk>', PerformaProductDetailView.as_view(), name='performa-product-list-create'),
    path('performa-performas/<int:performa_id>/convert-to-order/', ConvertPerformaToOrderAPIView.as_view(), name='convert-performa-to-order'),
    path('performa-performas/<int:performa_id>/convert-to-credit/', ConvertPerformaToCreditAPIView.as_view(), name='convert-performa-to-credit'),
    # path('performa-performas/<pk>/convert-to-order/', ConvertPerformaToOrderAPIView.as_view(), name='convert-performa-to-order'),
    path('performa-performas/<pk>/receipt/', PerformaReceiptAPIView.as_view(), name='performa-receipt'),


    path('purchase-products/', PurchaseProductListCreateView.as_view(), name='purchase-product-list-create'),
    path('purchase-products/<pk>', PurchaseProductDetailView.as_view(), name='purchase-product-list-create'),
    path('purchase-expenses/', PurchaseExpenseListCreateView.as_view(), name='purchase-expense-list-create'),
    path('purchase-expenses/<pk>', PurchaseExpenseDetailView.as_view(), name='purchase-expense-list-create'),
    path('purchase-suppliers/', PurchaseSupplierListCreateView.as_view(), name='purchase-supplier-list-create'),
    path('purchase-suppliers/<pk>', PurchaseSupplierDetailView.as_view(), name='purchase-supplier-list-create'),

    path('purchase-suppliers/<int:supplier_id>/logs', SupplierLogListView.as_view(), name='purchase-supplier-logs'),
    path('purchase-expenses/<int:expense_id>/logs', ExpenseLogListView.as_view(), name='purchase-expense-logs'),
    path('orders/<int:order_id>/logs', OrderLogListView.as_view(), name='order-logs'),



    path('products/', ProductListCreateAPIView.as_view(), name='products-list'),
    path('products/<pk>', ProductRetrieveUpdateDeleteAPIView.as_view(), name='products-retrieve'),

    path('suppliers/', SupplierListCreateAPIView.as_view(), name='suppliers-list'),
    path('suppliers/<pk>', SupplierRetrieveUpdateDeleteAPIView.as_view(), name='suppliers-retrieve'),

    path('orders/', OrderListCreatView.as_view(), name='orders-create'),
    path('orders/<pk>', OrderDetailView.as_view(), name='orders-retrieve'),
    path('orders/<pk>/receipt/', OrderReceiptAPIView.as_view(), name='order-receipt'),
    # path('orders-credit/<pk>/receipt/', CreditReceiptAPIView.as_view(), name='credit-receipt'),
    path('recent-orders/', RecentOrderLimitedAPIView.as_view(), name='recent-orders-limited'),
    path('recent-jobcard/', RecentJobCardLimitedAPIView.as_view(), name='recent-jobcard-limited'),
    path('recent-acceptance/', RecentAcceptanceLimitedAPIView.as_view(), name='recent-acceptance-limited'),

    path('orderitems/', OrderItemListCreateView.as_view(), name='orders-items-list'),
    path('orderitems/<pk>', OrderItemDetailView.as_view(), name='orders-items-retrieve'),

    path('report/', ExcelReportAPIView.as_view(), name='report-retrieve'),

    path('orders-credit/', OrderCreditListAPIView.as_view(), name='orders-credit-list'),
    path('orderitems-credit/', OrderItemCreditListView.as_view(), name='orders-credit-items-list'),

    # New Credit
    path('credit-products/', CreditProductListCreateView.as_view(), name='credit-product-list-create'),
    path('credit-products/<pk>', CreditProductDetailView.as_view(), name='credit-product-list-create'),
    path('credit-credits/', CreditCreditListCreateView.as_view(), name='credit-credit-list-create'),
    path('credit-credits/<pk>', CreditCreditDetailView.as_view(), name='credit-credit-list-create'),
    path('credit-customers/', CreditCustomerListCreateView.as_view(), name='credit-customer-list-create'),
    path('credit-customers/<pk>', CreditCustomerDetailView.as_view(), name='credit-customer-list-create'),
    path('credit-credits/<pk>/receipt/', CreditReceiptAPIView.as_view(), name='credit-receipt'),


    path('company/', CompanyListCreateAPIView.as_view(), name='company-list'),
    path('company/<pk>', CompanyRetrieveUpdateDeleteAPIView.as_view(), name='company-retrieve'),

    path('category/', CategoryListCreateAPIView.as_view(), name='category-list'),
    path('category/<pk>', CategoryRetrieveUpdateDeleteAPIView.as_view(), name='category-retrieve'),

    path('jobcard-status-scheduled/', JobCardStatusScheduledAPIView.as_view(), name='jobcard-status-scheduled'),
    path('jobcard-status-in-progress/', JobCardStatusInProgressAPIView.as_view(), name='jobcard-status-in-progress'),
    path('jobcard-status-completed/', JobCardStatusCompletedAPIView.as_view(), name='jobcard-status-completed'),
    path('jobcard-status/', JobCardStatusAPIView.as_view(), name='jobcard-status'),
    
    path('daily-jobcard-status-scheduled/', DailyJobCardStatusScheduledAPIView.as_view(), name='daily-jobcard-status-scheduled'),
    path('daily-jobcard-status-in-progress/', DailyJobCardStatusInProgressAPIView.as_view(), name='daily-jobcard-status-in-progress'),
    path('daily-jobcard-status-completed/', DailyJobCardStatusCompletedAPIView.as_view(), name='daily-jobcard-status-completed'),

    path('total-order/', TotalOrderAPIView.as_view(), name='total-order'),
    path('total-product/', TotalProductAPIView.as_view(), name='total-product'),
    path('total-supplier/', TotalSupplierAPIView.as_view(), name='total-supplier'),
    path('total-service/', TotalServiceAPIView.as_view(), name='total-service'),
    path('total-service-package/', TotalServicePackageAPIView.as_view(), name='total-service-package'),
    path('total-vehicle/', TotalVehicleAPIView.as_view(), name='total-vehicle'),
    path('total-acceptance/', TotalAcceptanceAPIView.as_view(), name='total-acceptance'),
    path('total-customer/', TotalCustomerAPIView.as_view(), name='total-customer'),
    path('total-category/', TotalCategoryAPIView.as_view(), name='total-category'),
    path('total-performa/', TotalPerformaAPIView.as_view(), name='total-performa'),
    path('total-expense/', TotalExpensesAPIView.as_view(), name='total-expense'),
    path('total-revenue/', RetriveTotalRevenueAPIView.as_view(), name='total-revenue'),

    path('available-jobcard-part-request/', AvailableJobCardPartRequestAPIView.as_view(), name='available-jobcard-part-request'),
    path('available-jobcard-order-voucher/', AvailableJobCardOrderVoucherAPIView.as_view(), name='available-jobcard-order-voucher'),
    path('available-jobcard-old-part/', AvailableJobCardOldPartAPIView.as_view(), name='available-jobcard-old-part'),
    path('available-jobcard-invoice/', AvailableJobCardInvoiceAPIView.as_view(), name='available-jobcard-invoice'),
    
    path('jobcard-log/', JobCardLogAPIView.as_view(), name='jobcard-log'),
    path('jobcard-assignment-log/', JobCardAssignmentLogAPIView.as_view(), name='jobcard-assignment-log'),
    path('assigned-service-log/', AssignedServiceLogAPIView.as_view(), name='assigned-service-log'),
    path('jobcard-receipt/<int:pk>/', JobCardReceiptAPIView.as_view(), name='jobcard-receipt'),

    path('daily-sales/', DailySalesAPIView.as_view(), name='daily-sales-retrieve'),
    path('monthly-sales/', MonthlySalesAPIView.as_view(), name='monthly-sales-retrieve'),
    path('weekly-sales/', WeeklySalesAPIView.as_view(), name='weekly-sales-retrieve'),
    path('yearly-sales/', YearlySalesAPIView.as_view(), name='yearly-sales-retrieve'),

    path('daily-sales-per-user/', DailySalesEachUserAPIView.as_view(), name='daily-sales-each-user-retrieve'),
    path('weekly-sales-per-user/', WeeklySalesEachUserAPIView.as_view(), name='weekly-sales-each-user-retrieve'),
    path('monthly-sales-per-user/', MonthlySalesEachUserAPIView.as_view(), name='monthly-sales-each-user-retrieve'),
    path('yearly-sales-per-user/', YearlySalesEachUserAPIView.as_view(), name='yearly-sales-each-user-retrieve'),

    path('vehicle-part-request-log/', VehiclePartRequestLogAPIView.as_view(), name='vehicle-part-request-log'),
    path('vehicle-part-request-item-log/', VehiclePartRequestItemLogAPIView.as_view(), name='vehicle-part-request-item-log'),

    path('vehicle-old-part-delivery-log/', VehicleOldPartDeliveryLogAPIView.as_view(), name='vehicle-old-part-delivery-log'),
    path('vehicle-old-part-delivery-item-log/', VehicleOldPartDeliveryItemLogAPIView.as_view(), name='vehicle-old-part-delivery-item-log'),
    
    path('vehicle-order_voucher-log/', VehicleOrderVoucherLogAPIView.as_view(), name='vehicle-order_voucher-log'),
    path('vehicle-order_voucher-item-log/', VehicleOrderVoucherItemLogAPIView.as_view(), name='vehicle-order_voucher-item-log'),

]
