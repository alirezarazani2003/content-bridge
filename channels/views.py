from rest_framework import generics, permissions
from .models import Channel
from .serializers import ChannelSerializer
from auth_app.permissions import IsEmailVerified
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class ChannelCreateView(generics.CreateAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]

    @swagger_auto_schema(
        operation_summary="ثبت کانال جدید",
        operation_description="کاربر با ایمیل وریفای‌شده می‌تواند کانال تلگرام یا بله خود را ثبت کند. شناسه باید با @ شروع شود.",
        responses={
            201: openapi.Response("کانال با موفقیت ثبت شد"),
            400: openapi.Response("خطای اعتبارسنجی یا داده‌های نامعتبر"),
            403: openapi.Response("کاربر وریفای‌نشده یا احراز هویت‌نشده"),
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ChannelListView(generics.ListAPIView):
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="لیست کانال‌های کاربر",
        operation_description="نمایش لیست کانال‌هایی که کاربر فعلی ثبت کرده است.",
        responses={200: ChannelSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Channel.objects.filter(user=self.request.user)


class ChannelDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified, IsOwner]

    @swagger_auto_schema(
        operation_summary="مشاهده اطلاعات کانال",
        operation_description="نمایش جزئیات یک کانال خاص (فقط درصورتی که مالک آن باشید).",
        responses={
            200: ChannelSerializer(),
            403: "دسترسی غیرمجاز یا ایمیل تایید نشده",
            404: "کانال پیدا نشد"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="ویرایش کانال",
        operation_description="ویرایش اطلاعات یک کانال ثبت‌شده (فقط توسط مالک مجاز است).",
        responses={
            200: ChannelSerializer(),
            400: "ورودی نامعتبر",
            403: "عدم دسترسی",
            404: "یافت نشد"
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="حذف کانال",
        operation_description="حذف یک کانال (فقط توسط مالک مجاز است).",
        responses={
            204: "با موفقیت حذف شد",
            403: "عدم دسترسی",
            404: "یافت نشد"
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
