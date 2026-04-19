from django.urls import path
from . import views

app_name = 'trainees'

urlpatterns = [
    path('dashboard/', views.TraineeDashboardView.as_view(), name='trainee-dashboard'),
    path('shop/', views.AvatarShopView.as_view(), name='avatar-shop'),
    path('shop/purchase/<int:pk>/', views.AvatarPurchaseView.as_view(), name='avatar-purchase'),
    path('inventory/', views.InventoryListView.as_view(), name='inventory'),
    path('inventory/equip/<int:pk>/', views.EquipAvatarView.as_view(), name='equip-avatar'),
    path('gallery/', views.AvatarGalleryView.as_view(), name='avatar-gallery'),
]
