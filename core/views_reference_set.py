from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ReferenceSet


class ReferenceSetCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)


class ReferenceSetView(APIView):
    def post(self, request):
        ser = ReferenceSetCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        rs = ReferenceSet.objects.create(name=ser.validated_data["name"])  # type: ignore
        return Response({"id": str(rs.id), "name": rs.name, "is_active": rs.is_active}, status=201)

    def get(self, request):
        data = [
            {"id": str(rs.id), "name": rs.name, "is_active": rs.is_active}
            for rs in ReferenceSet.objects.order_by("-created_at")
        ]
        return Response({"items": data})
