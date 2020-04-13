from django.urls import include, path
from rest_framework import routers

from knox import views as knox_views

from . import views


app_name = 'api'

router = routers.DefaultRouter()
# router.register(r'/auth/token', views.AppTokenViewSet)

urlpatterns = [
    path('v0.1/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # knox login URLs.
    path('auth/user/', views.UserAPIView.as_view()),  # 유저 조회
    path('auth/register/', views.RegisterAPIView.as_view()),  # 유저 등록
    path('auth/login/', views.LoginAPIView.as_view()),  # 로그인
    path('auth/logout/', knox_views.LogoutView.as_view(), name='knox_logout'),  # 로그아웃
    path('auth/token/', views.AppTokenViewSet.as_view({'post': 'create'})),  # 기기 토큰 생성
    path('auth/token/<int:pk>/', views.AppTokenViewSet.as_view({'delete': 'destroy'})),  # 기기 토큰 삭제
]