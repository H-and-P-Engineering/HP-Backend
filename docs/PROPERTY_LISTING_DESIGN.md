<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Property Listing API Design](#property-listing-api-design)
  - [Overview](#overview)
  - [Architecture Alignment](#architecture-alignment)
  - [Data Model Design](#data-model-design)
    - [Property Base Entity](#property-base-entity)
    - [House Property Entity](#house-property-entity)
    - [Land Property Entity](#land-property-entity)
    - [Property Image Entity](#property-image-entity)
  - [Enums](#enums)
    - [PropertyType](#propertytype)
    - [CategoryKey](#categorykey)
    - [HouseType](#housetype)
    - [LandType](#landtype)
  - [API Endpoints](#api-endpoints)
    - [1. Create House Listing](#1-create-house-listing)
    - [2. Create Land Listing](#2-create-land-listing)
    - [3. List Properties (Minimal Data)](#3-list-properties-minimal-data)
    - [4. Get Property Details](#4-get-property-details)
    - [5. Update Property](#5-update-property)
    - [6. Delete Property](#6-delete-property)
    - [7. Get User's Listings](#7-get-users-listings)
  - [Business Rules](#business-rules)
    - [CreatePropertyRule](#createpropertyrule)
    - [GetPropertyDetailsRule](#getpropertydetailsrule)
    - [ListPropertiesRule](#listpropertiesrule)
    - [UpdatePropertyRule](#updatepropertyrule)
    - [DeletePropertyRule](#deletepropertyrule)
  - [Image Handling Strategy](#image-handling-strategy)
    - [Storage Options](#storage-options)
    - [Image Processing](#image-processing)
  - [Land Type Computation](#land-type-computation)
  - [Database Schema](#database-schema)
    - [properties Table](#properties-table)
    - [house_properties Table](#house_properties-table)
    - [land_properties Table](#land_properties-table)
    - [property_images Table](#property_images-table)
  - [Performance Considerations](#performance-considerations)
    - [Caching Strategy](#caching-strategy)
    - [Database Optimization](#database-optimization)
    - [Image Optimization](#image-optimization)
  - [Security Considerations](#security-considerations)
  - [Event-Driven Architecture](#event-driven-architecture)
    - [Events](#events)
    - [Event Handlers](#event-handlers)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Property Listing API Design

## Overview

This document outlines the design for implementing property listing APIs (houses and land) that integrate with the existing Housing & Properties backend system.

## Architecture Alignment

The implementation follows the existing Clean Architecture pattern:

```
Domain Layer (Entities & Enums)
    ↓
Application Layer (Business Rules)
    ↓
Infrastructure Layer (Repositories & Services)
    ↓
Presentation Layer (Views & Serializers)
```

## Data Model Design

### Property Base Entity

```python
@dataclass
class Property:
    id: int | None
    uuid: Type[UUID] | None
    user_id: int  # Agent/Owner
    type: PropertyType  # HOUSE or LAND
    category_key: CategoryKey
    price: Decimal
    city: str
    address: str
    is_active: bool
    views_count: int
    created_at: datetime | None
    updated_at: datetime | None
```

### House Property Entity

```python
@dataclass
class HouseProperty(Property):
    house_type: HouseType
    house_size: str | None  # Only for sale
    bedrooms: int
    bathrooms: int
    light_type: str
    road: str
    kitchen_facilities: list[str]
    good_water: bool
    bedroom_facilities: list[str]
    drainage_system: bool
    living_room_facilities: list[str]
    security: bool
    overview: str
    # Sale-specific fields
    survey: bool | None
    excision: bool | None
```

### Land Property Entity

```python
@dataclass
class LandProperty(Property):
    land_type: LandType  # Computed from land_size
    land_size: str
    survey: bool
    security: bool
    excision: bool
    water_treatment: bool
    certificate_of_occupancy: bool
    governors_consent: bool
    deed_of_assignment: bool
    drainage_system: bool
    good_road: str | bool
    good_water: bool
    overview: str
```

### Property Image Entity

```python
@dataclass
class PropertyImage:
    id: int | None
    property_id: int
    image_url: str
    is_primary: bool
    display_order: int
    created_at: datetime | None
```

## Enums

### PropertyType

```python
class PropertyType(StrEnum):
    HOUSE = "HOUSE"
    LAND = "LAND"
```

### CategoryKey

```python
class CategoryKey(StrEnum):
    SALE = "SALE"
    RENT = "RENT"
    SALE_RECENT = "SALE_RECENT"
    SALE_SEARCHED = "SALE_SEARCHED"
    RENT_RECENT = "RENT_RECENT"
    RENT_SEARCHED = "RENT_SEARCHED"
    BOUGHT = "BOUGHT"
```

### HouseType

```python
class HouseType(StrEnum):
    DUPLEX = "DUPLEX"
    STUDIO_APARTMENT = "STUDIO_APARTMENT"
    TWO_BEDROOM_FLAT = "TWO_BEDROOM_FLAT"
    THREE_BEDROOM_FLAT = "THREE_BEDROOM_FLAT"
    FOUR_PLUS_BEDROOM_FLAT = "FOUR_PLUS_BEDROOM_FLAT"
    CONDOMINIUM = "CONDOMINIUM"
    BUNGALOW = "BUNGALOW"
```

### LandType

```python
class LandType(StrEnum):
    SMALL = "450-900SQM"
    THREE_PLOTS = "1300-2700SQM"
    FOUR_PLOTS = "1800-3600SQM"
    FIVE_PLOTS = "2250-4500SQM"
    ONE_ACRE = "2700-5400SQM"
    LESS_THAN_ONE_HECTARE = "5400-10000SQM"
    LESS_THAN_TWO_HECTARES = "10900-21600SQM"
    LESS_THAN_30000SQM = "LESS_THAN_30000SQM"
    LESS_THAN_50000SQM = "LESS_THAN_50000SQM"
    GREATER_THAN_50000SQM = "GREATER_THAN_50000SQM"
```

## API Endpoints

### 1. Create House Listing

**Endpoint:** `POST /api/v1/properties/houses/`

**Authentication:** Required (HOUSE_AGENT, LAND_AGENT, VENDOR)

**Request Body:**
```json
{
  "category_key": "SALE",
  "price": 50000000.00,
  "city": "Lagos",
  "address": "15 Admiralty Way, Lekki Phase 1",
  "house_type": "DUPLEX",
  "house_size": "450sqm",
  "bedrooms": 4,
  "bathrooms": 5,
  "light_type": "24/7 prepaid",
  "road": "Tarred",
  "kitchen_facilities": ["Gas cooker", "Microwave"],
  "good_water": true,
  "bedroom_facilities": ["Air conditioning", "Wardrobe"],
  "drainage_system": true,
  "living_room_facilities": ["TV console", "Chandelier"],
  "security": true,
  "overview": "Luxury 4-bedroom duplex in prime Lekki location",
  "survey": true,
  "excision": true,
  "images": ["base64_string_1", "base64_string_2"]
}
```

### 2. Create Land Listing

**Endpoint:** `POST /api/v1/properties/land/`

**Authentication:** Required (LAND_AGENT, VENDOR)

**Request Body:**
```json
{
  "category_key": "SALE",
  "price": 25000000.00,
  "city": "Abuja",
  "address": "Airport Road, Lugbe",
  "land_size": "600sqm",
  "survey": true,
  "security": true,
  "excision": true,
  "water_treatment": true,
  "certificate_of_occupancy": true,
  "governors_consent": false,
  "deed_of_assignment": true,
  "drainage_system": true,
  "good_road": true,
  "good_water": true,
  "overview": "Prime land for residential development",
  "images": ["base64_string_1"]
}
```

### 3. List Properties (Minimal Data)

**Endpoint:** `GET /api/v1/properties/`

**Authentication:** Optional (affects category_key filtering)

**Query Parameters:**
- `type`: HOUSE | LAND (optional)
- `category_key`: Filter by category (optional)
- `city`: Filter by city (optional)
- `min_price`: Minimum price (optional)
- `max_price`: Maximum price (optional)
- `bedrooms`: Filter houses by bedrooms (optional)
- `house_type`: Filter houses by type (optional)
- `land_type`: Filter land by type (optional)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

**Response (List View):**
```json
{
  "success": true,
  "message": "Properties retrieved successfully",
  "data": {
    "count": 150,
    "next": "http://api.example.com/api/v1/properties/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "uuid": "123e4567-e89b-12d3-a456-426614174000",
        "type": "HOUSE",
        "category_key": "SALE",
        "price": "50000000.00",
        "city": "Lagos",
        "address": "15 Admiralty Way, Lekki Phase 1",
        "house_type": "DUPLEX",
        "bedrooms": 4,
        "bathrooms": 5,
        "light_type": "24/7 prepaid",
        "primary_image": "https://storage.example.com/images/house1.jpg",
        "agent": {
          "name": "John Doe",
          "email": "john@example.com",
          "profile_image": "https://storage.example.com/agents/john.jpg"
        }
      },
      {
        "id": 2,
        "uuid": "223e4567-e89b-12d3-a456-426614174001",
        "type": "LAND",
        "category_key": "SALE",
        "price": "25000000.00",
        "city": "Abuja",
        "address": "Airport Road, Lugbe",
        "land_type": "450-900SQM",
        "land_size": "600sqm",
        "survey": true,
        "security": true,
        "excision": true,
        "primary_image": "https://storage.example.com/images/land1.jpg",
        "agent": {
          "name": "Jane Smith",
          "email": "jane@example.com",
          "profile_image": "https://storage.example.com/agents/jane.jpg"
        }
      }
    ]
  },
  "status_code": 200
}
```

### 4. Get Property Details

**Endpoint:** `GET /api/v1/properties/{uuid}/`

**Authentication:** Optional

**Response (Detail View - House):**
```json
{
  "success": true,
  "message": "Property details retrieved successfully",
  "data": {
    "id": 1,
    "uuid": "123e4567-e89b-12d3-a456-426614174000",
    "type": "HOUSE",
    "category_key": "SALE",
    "price": "50000000.00",
    "city": "Lagos",
    "address": "15 Admiralty Way, Lekki Phase 1",
    "house_type": "DUPLEX",
    "house_size": "450sqm",
    "bedrooms": 4,
    "bathrooms": 5,
    "light_type": "24/7 prepaid",
    "road": "Tarred",
    "kitchen_facilities": ["Gas cooker", "Microwave"],
    "good_water": true,
    "bedroom_facilities": ["Air conditioning", "Wardrobe"],
    "drainage_system": true,
    "living_room_facilities": ["TV console", "Chandelier"],
    "security": true,
    "overview": "Luxury 4-bedroom duplex in prime Lekki location",
    "survey": true,
    "excision": true,
    "images": [
      {
        "url": "https://storage.example.com/images/house1.jpg",
        "is_primary": true,
        "display_order": 1
      },
      {
        "url": "https://storage.example.com/images/house2.jpg",
        "is_primary": false,
        "display_order": 2
      }
    ],
    "agent": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone_number": "+2341234567890",
      "profile_image": "https://storage.example.com/agents/john.jpg",
      "business_verified": true
    },
    "location_intelligence": {
      "location": {
        "latitude": 6.4281,
        "longitude": 3.4219
      },
      "nearby_services": [...],
      "road_connectivity_score": 85.0,
      "electricity_availability_score": 90.0
    },
    "views_count": 234,
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T10:00:00Z"
  },
  "status_code": 200
}
```

### 5. Update Property

**Endpoint:** `PATCH /api/v1/properties/{uuid}/`

**Authentication:** Required (Owner only)

**Request Body:** (Partial update supported)
```json
{
  "price": 48000000.00,
  "is_active": true
}
```

### 6. Delete Property

**Endpoint:** `DELETE /api/v1/properties/{uuid}/`

**Authentication:** Required (Owner only)

### 7. Get User's Listings

**Endpoint:** `GET /api/v1/properties/my-listings/`

**Authentication:** Required

**Query Parameters:** Same as list properties

## Business Rules

### CreatePropertyRule

**Validations:**
1. User must be HOUSE_AGENT, LAND_AGENT, or VENDOR
2. User must have verified business profile (for agents)
3. Price must be positive
4. At least one image required (max 10)
5. Required fields based on property type
6. For sale properties: house_size required for houses
7. Land type computed automatically from land_size

**Process:**
1. Validate user permissions
2. Validate property data
3. Process and store images
4. Compute land_type if land property
5. Get location intelligence for address
6. Create property record
7. Create property images
8. Publish PropertyCreatedEvent

### GetPropertyDetailsRule

**Process:**
1. Retrieve property by UUID
2. Check if property is active
3. Increment views_count
4. Fetch all images
5. Fetch agent details
6. Include cached location_intelligence
7. Return complete property data

### ListPropertiesRule

**Process:**
1. Apply filters (type, category, city, price range, etc.)
2. Filter active properties only
3. Join with users table for agent info
4. Fetch only primary image per property
5. Fetch minimal feature set based on type
6. Apply pagination
7. Order by created_at DESC (recent first)

### UpdatePropertyRule

**Validations:**
1. User must be property owner
2. Validate updated fields
3. Cannot change property type or user_id
4. Recompute land_type if land_size changed

### DeletePropertyRule

**Validations:**
1. User must be property owner
2. Soft delete by setting is_active = False

## Image Handling Strategy

### Storage Options

1. **Local Storage (Development)**
   - Store in MEDIA_ROOT
   - Serve via Django during development

2. **Cloud Storage (Production)**
   - Amazon S3 or similar
   - Generate signed URLs for access
   - CDN integration for performance

### Image Processing

1. Accept base64 encoded images in creation
2. Validate image size (max 5MB per image)
3. Validate format (JPEG, PNG only)
4. Generate thumbnails for list view
5. Store original for detail view
6. Set first image as primary by default

## Land Type Computation

```python
def compute_land_type(land_size_sqm: float) -> LandType:
    if 450 <= land_size_sqm <= 900:
        return LandType.SMALL
    elif 1300 <= land_size_sqm <= 2700:
        return LandType.THREE_PLOTS
    elif 1800 <= land_size_sqm <= 3600:
        return LandType.FOUR_PLOTS
    elif 2250 <= land_size_sqm <= 4500:
        return LandType.FIVE_PLOTS
    elif 2700 <= land_size_sqm <= 5400:
        return LandType.ONE_ACRE
    elif 5400 <= land_size_sqm <= 10000:
        return LandType.LESS_THAN_ONE_HECTARE
    elif 10900 <= land_size_sqm <= 21600:
        return LandType.LESS_THAN_TWO_HECTARES
    elif land_size_sqm < 30000:
        return LandType.LESS_THAN_30000SQM
    elif land_size_sqm < 50000:
        return LandType.LESS_THAN_50000SQM
    else:
        return LandType.GREATER_THAN_50000SQM
```

## Database Schema

### properties Table

```sql
CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    uuid UUID UNIQUE NOT NULL DEFAULT uuid7(),
    user_id INTEGER NOT NULL REFERENCES users(id),
    type VARCHAR(10) NOT NULL CHECK (type IN ('HOUSE', 'LAND')),
    category_key VARCHAR(20) NOT NULL,
    price DECIMAL(15, 2) NOT NULL,
    city VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    views_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_properties_user ON properties(user_id);
CREATE INDEX idx_properties_type ON properties(type);
CREATE INDEX idx_properties_category ON properties(category_key);
CREATE INDEX idx_properties_city ON properties(city);
CREATE INDEX idx_properties_price ON properties(price);
CREATE INDEX idx_properties_active ON properties(is_active);
```

### house_properties Table

```sql
CREATE TABLE house_properties (
    property_id INTEGER PRIMARY KEY REFERENCES properties(id) ON DELETE CASCADE,
    house_type VARCHAR(30) NOT NULL,
    house_size VARCHAR(50),
    bedrooms INTEGER NOT NULL,
    bathrooms INTEGER NOT NULL,
    light_type VARCHAR(100) NOT NULL,
    road VARCHAR(100) NOT NULL,
    kitchen_facilities JSONB DEFAULT '[]',
    good_water BOOLEAN NOT NULL,
    bedroom_facilities JSONB DEFAULT '[]',
    drainage_system BOOLEAN NOT NULL,
    living_room_facilities JSONB DEFAULT '[]',
    security BOOLEAN NOT NULL,
    overview TEXT,
    survey BOOLEAN,
    excision BOOLEAN
);
```

### land_properties Table

```sql
CREATE TABLE land_properties (
    property_id INTEGER PRIMARY KEY REFERENCES properties(id) ON DELETE CASCADE,
    land_type VARCHAR(30) NOT NULL,
    land_size VARCHAR(50) NOT NULL,
    survey BOOLEAN NOT NULL,
    security BOOLEAN NOT NULL,
    excision BOOLEAN NOT NULL,
    water_treatment BOOLEAN NOT NULL,
    certificate_of_occupancy BOOLEAN NOT NULL,
    governors_consent BOOLEAN NOT NULL,
    deed_of_assignment BOOLEAN NOT NULL,
    drainage_system BOOLEAN NOT NULL,
    good_road VARCHAR(100) NOT NULL,
    good_water BOOLEAN NOT NULL,
    overview TEXT
);
```

### property_images Table

```sql
CREATE TABLE property_images (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_property_images_property ON property_images(property_id);
CREATE INDEX idx_property_images_primary ON property_images(is_primary);
```

## Performance Considerations

### Caching Strategy

1. **List View Cache**
   - Cache property listings by filter combination
   - TTL: 5 minutes
   - Invalidate on new property creation

2. **Detail View Cache**
   - Cache individual property details
   - TTL: 15 minutes
   - Invalidate on property update

3. **Location Intelligence Cache**
   - Reuse existing location cache from location module
   - Store with property on creation
   - Update on property location change

### Database Optimization

1. Use appropriate indexes on filter fields
2. Implement pagination for list views
3. Use select_related for agent info in list queries
4. Use prefetch_related for images in detail queries
5. Consider read replicas for high traffic

### Image Optimization

1. Generate and serve thumbnails for list view
2. Lazy load images on detail view
3. Use CDN for image delivery
4. Implement progressive image loading

## Security Considerations

1. **Authorization**
   - Only property owners can update/delete
   - Only verified agents can create listings
   - Rate limiting on creation endpoints

2. **Input Validation**
   - Validate all user inputs
   - Sanitize text fields
   - Validate image formats and sizes
   - Prevent SQL injection via ORM

3. **Data Privacy**
   - Mask agent contact info in list view
   - Full details only in detail view
   - GDPR compliance for user data

## Event-Driven Architecture

### Events

```python
class PropertyCreatedEvent(DomainEvent):
    def __init__(self, property_id: int):
        self.property_id = property_id

class PropertyUpdatedEvent(DomainEvent):
    def __init__(self, property_id: int):
        self.property_id = property_id

class PropertyViewedEvent(DomainEvent):
    def __init__(self, property_id: int, viewer_id: int | None):
        self.property_id = property_id
        self.viewer_id = viewer_id
```

### Event Handlers

1. **PropertyCreatedEvent**
   - Generate location intelligence
   - Send notification to agent
   - Update user's listing count

2. **PropertyViewedEvent**
   - Increment view counter
   - Track viewer analytics
   - Update trending properties
