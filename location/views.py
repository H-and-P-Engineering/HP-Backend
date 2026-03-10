from adrf.decorators import api_view
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from core.responses import StandardResponse
from core.serializers import (
    ErrorResponseExampleSerializer,
    SuccessResponseExampleSerializer,
)
from .serializers import (
    DistanceRequestSerializer,
    DistanceResponseSerializer,
    LocationIntelligenceResponseSerializer,
    NearbyServiceRequestSerializer,
)
from core.container import container


@extend_schema(
    request=NearbyServiceRequestSerializer,
    responses={
        200: SuccessResponseExampleSerializer,
        400: ErrorResponseExampleSerializer,
        500: ErrorResponseExampleSerializer,
    },
    description="Find nearby services and location intelligence for authenticated users",
    tags=["Location Intelligence"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
async def find_nearby_services(request: Request) -> Response:
    serializer = NearbyServiceRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    location_intelligence = (
        await container.location_intelligence_service().get_location_intelligence(
            latitude=validated_data.get("latitude"),
            longitude=validated_data.get("longitude"),
            address=validated_data.get("address"),
            service_types=validated_data.get("service_types"),
            radius_km=validated_data.get("radius_km", 5.0),
        )
    )

    response_serializer = LocationIntelligenceResponseSerializer(location_intelligence)

    return StandardResponse.success(
        data=response_serializer.data,
        message="Location intelligence retrieved successfully",
    )


@extend_schema(
    request=DistanceRequestSerializer,
    responses={
        200: SuccessResponseExampleSerializer,
        400: ErrorResponseExampleSerializer,
        500: ErrorResponseExampleSerializer,
    },
    description="Calculate distance from a property (origin) to any destination",
    tags=["Location Intelligence"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
async def calculate_distance(request: Request) -> Response:
    serializer = DistanceRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    distance_result = await container.travel_service().calculate_distance(
        origin_latitude=validated_data.get("origin_latitude"),
        origin_longitude=validated_data.get("origin_longitude"),
        origin_address=validated_data.get("origin_address"),
        destination_latitude=validated_data.get("destination_latitude"),
        destination_longitude=validated_data.get("destination_longitude"),
        destination_address=validated_data.get("destination_address"),
    )

    response_serializer = DistanceResponseSerializer(distance_result)

    return StandardResponse.success(
        data=response_serializer.data,
        message="Distance calculated successfully",
    )
