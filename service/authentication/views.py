from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class LoginView(APIView):
    def post(self, _request, *_args, **_kwargs):
        return Response({"detail": "Not implemented yet."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class RefreshView(APIView):
    def post(self, _request, *_args, **_kwargs):
        return Response({"detail": "Not implemented yet."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class LogoutView(APIView):
    def post(self, _request, *_args, **_kwargs):
        return Response({"detail": "Not implemented yet."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class MeView(APIView):
    def get(self, _request, *_args, **_kwargs):
        return Response({"detail": "Not implemented yet."}, status=status.HTTP_501_NOT_IMPLEMENTED)
