from datetime import datetime, date
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from FarmHouse_Website.serializer import *
from django.core.cache import cache

class BaseViewSet(viewsets.ModelViewSet):
    def initialize_request(self, request, *args, **kwargs):
        request = super().initialize_request(request, *args, **kwargs)

        # Set default role if not present in session
        if not request.session.get('role'):
            request.session['role'] = 'Customer'
            request.session['status'] = 'unverified'
            #request.session['customerEmail'] = request.data['customerEmail']
        
        return request

class BookingViewSet(BaseViewSet):
    queryset = Bookings.objects.all()
    serializer_class = BookingsSerializer

    def create(self, request):

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            check_in_date = serializer.validated_data['checkInDate']
            check_out_date = serializer.validated_data['checkOutDate']

            validity_status, message = utils.validate_booking_dates(check_in_date, check_out_date)
            print(message)

            if not validity_status:
                return Response({'error': message}, status=status.HTTP_406_NOT_ACCEPTABLE)

            conflict_status, conflicts = utils.check_booking_availability(check_in_date, check_out_date)
            if conflict_status:
                return Response(data=conflicts, status=status.HTTP_409_CONFLICT)

            if 'IDimage' not in serializer.validated_data:
                return Response({'message': 'IDimage is required'}, status=status.HTTP_206_PARTIAL_CONTENT)

            email = serializer.validated_data.get('guestEmail')
            serializer.validated_data['bookingDate'] = date.today()
            # serializer.validated_data['guestEmail'] = email
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

class MenuViewSet(BaseViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer

class ReviewsViewSet(BaseViewSet):
    queryset = Reviews.objects.all()
    serializer_class = ReviewsSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):

            if not Bookings.objects.filter(guestPhone = request.data['guestPhone']).exists():
                return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

            try:
                serializer.validated_data['bookingId'] = Bookings.objects.get(guestPhone=request.data['guestPhone']).bookingId
                serializer.validated_data['reviewDate'] = datetime.today()
                saved_review = serializer.save()

                if utils.setMedia(media_list=request.FILES.getlist('media_list'),
                                review=Reviews.objects.get(reviewId=saved_review.reviewId)):
                    return Response(status=status.HTTP_200_OK)
                else:
                    return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                print(e)

# class Authorization(APIView):
    
#     def get(self, request):
#         email = request.data.get('guestEmail')
#         if email:
#             if Bookings.objects.filter(guestEmail=email).exists():
#                 return Response(status=status.HTTP_100_CONTINUE)
#             elif utils.sendOtpVerificationMail(receiver=email):
#                 request.session['customerEmail'] = email
#                 return Response(status=status.HTTP_200_OK)
#             else:
#                 return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#         return Response(status=status.HTTP_400_BAD_REQUEST)

#     def post(self, request):
#         customerEmail = request.session.get('customerEmail')
#         otp = request.data.get('otp')

#         if customerEmail and otp:
#             if cache.get(customerEmail) == otp:
#                 request.session['status'] = "verified"
#                 cache.delete(customerEmail)
#                 return Response(status=status.HTTP_200_OK)
#             return Response(status=status.HTTP_401_UNAUTHORIZED)

#         return Response(status=status.HTTP_400_BAD_REQUEST)
