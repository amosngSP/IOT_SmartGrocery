# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path
from .views import *
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login/', login_view, name="login"),
    path('register/', register_user, name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("inventory/", inventory, name='inventory'),
    path("inventory_data/", inventory_data, name='inventory_data'),
path("inventory_update/", inventory_update, name='inventory_update'),
    path("historical_graph/", historical_graph, name='historical_graph'),
path("live_graph/", live_graph, name='live_graph'),
path("get_barcode_status/", get_barcode_status, name='get_barcode_status'),
path("get_grocery_list/", get_grocery_list, name='get_grocery_list'),
path("toggle_barcode_status/", toggle_barcode_status, name='toggle_barcode_status'),
path("check_upc/", check_upc, name='check_upc'),
    path("product/", product, name='product')
]
