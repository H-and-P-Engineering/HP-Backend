from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from app.infrastructure.location.events import ProcessLocationEvent
from app.presentation.factory import get_process_location_query_rule
from app.presentation.responses import StandardResponse
from app.presentation.serializers.examples import (
    ErrorResponseExampleSerializer,
    SuccessResponseExampleSerializer,
)
from app.presentation.serializers.location import (
    LocationIntelligenceResponseSerializer,
    NearbyServiceRequestSerializer,
)


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
def find_nearby_services(request: Request) -> Response:
    serializer = NearbyServiceRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    process_location_query_rule = get_process_location_query_rule()

    location_intelligence = process_location_query_rule(
        latitude=validated_data.get("latitude"),
        longitude=validated_data.get("longitude"),
        address=validated_data.get("address"),
        service_types=validated_data.get("service_types"),
        radius_km=validated_data.get("radius_km", 5.0),
        event=ProcessLocationEvent,
    )

    response_serializer = LocationIntelligenceResponseSerializer(location_intelligence)

    return StandardResponse.success(
        data=response_serializer.data,
        message="Location intelligence retrieved successfully",
    )
