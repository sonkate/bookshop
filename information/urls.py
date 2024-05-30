from django.urls import path
from information import views

"""
Define path for HTML pages
"""

urlpatterns = [
    path("", views.home, name = "home"),
    path("get_book_by_id", views.get_book_by_id, name = "get_book_by_id"),
    path("book", views.get_book, name = "get_book"),
    path("add_book_wishlist", views.add_book_wishlist, name = "add_book_wishlist"),
    path("remove_book_wishlist", views.remove_book_wishlist, name = "remove_book_wishlist"),
    path("get_wishlist/<str:id>", views.get_wishlist, name = "get_wishlist"),
    path("get_bought_book_list/<str:id>", views.get_bought_book_list, name = "get_bought_book_list"),
    path("buy_book", views.buy_book, name = "buy_book"),
    path("sign_up", views.sign_up, name = "sign_up"),
    path("sign_in", views.sign_in, name = "sign_in"),
    path("get_user_info/<str:id>", views.get_user_info, name = "get_user_info"),
    path("update_user_info", views.update_user_info, name = "update_user_info"),
]