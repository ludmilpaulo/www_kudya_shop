# Kudya Platform - Integration Guide

This guide explains how all four repositories work together to create the complete Kudya e-commerce and food delivery platform.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Kudya Platform                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐   ┌──────────────┐   │
│  │  food_deliver│    │ kudya-client │   │KudyaParceiro │   │
│  │  (Next.js)   │    │(React Native)│   │(React Native)│   │
│  │  Web App     │    │ Customer App │   │ Partner App  │   │
│  └──────┬───────┘    └──────┬───────┘   └──────┬───────┘   │
│         │                   │                   │            │
│         │                   │                   │            │
│         └───────────────────┼───────────────────┘            │
│                             │                                │
│                             ▼                                │
│                  ┌──────────────────────┐                    │
│                  │   www_kudya_shop     │                    │
│                  │   (Django REST API)  │                    │
│                  │   Backend Server     │                    │
│                  └──────────┬───────────┘                    │
│                             │                                │
│                             ▼                                │
│                  ┌──────────────────────┐                    │
│                  │  PostgreSQL/SQLite   │                    │
│                  │  Database            │                    │
│                  └──────────────────────┘                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Repositories

### 1. www_kudya_shop (Backend API)
**Repository**: https://github.com/ludmilpaulo/www_kudya_shop.git
**Technology**: Django 5.2.1, Django REST Framework 3.14.0
**Purpose**: Core backend API that serves all frontend applications

**Key Responsibilities**:
- User authentication and authorization
- Store/restaurant management
- Product catalog
- Order processing
- Payment handling
- Driver management
- Email notifications
- File storage (images, documents)

**API Base URL**: `https://kudya.pythonanywhere.com`

### 2. food_deliver (Web Application)
**Repository**: https://github.com/ludmilpaulo/food_deliver.git
**Technology**: Next.js 15.3.3, React 18, TypeScript
**Purpose**: Customer-facing web application

**Key Features**:
- Browse stores and products
- Shopping cart and checkout
- User authentication
- Order tracking
- Responsive design
- SEO optimized

**URL**: `https://www.sdkudya.com`

### 3. kudya-client (Customer Mobile App)
**Repository**: https://github.com/ludmilpaulo/kudya-client.git
**Technology**: React Native 0.79.2, Expo SDK 53
**Purpose**: Customer mobile application (iOS & Android)

**Key Features**:
- Mobile shopping experience
- Location-based store discovery
- Real-time order tracking
- Push notifications
- Offline support

### 4. KudyaParceiro (Partner/Driver App)
**Repository**: https://github.com/ludmilpaulo/KudyaParceiro.git
**Technology**: React Native 0.79.2, Expo SDK 53
**Purpose**: Store owner and delivery driver application

**Key Features**:
- Store management
- Product management
- Order management
- Delivery tracking
- Earnings reports

## API Integration

All three frontend applications communicate with the same backend API.

### API Endpoints by Feature

#### Authentication
- `POST /conta/login/` - User login (all apps)
- `POST /conta/logout/` - User logout
- `POST /customer/signup/` - Customer registration
- `POST /driver/signup/` - Driver registration

#### Stores
- `GET /store/stores/` - List all stores
- `GET /store/stores/{id}/` - Get store details
- `POST /store/fornecedor/` - Register new store
- `PUT /store/stores/{id}/` - Update store
- `GET /store/store-categories/` - List categories
- `GET /store/store-types/` - List store types

#### Products
- `GET /store/products/` - List all products
- `GET /store/products/{id}/` - Get product details
- `POST /store/add-product/` - Add product (Partner app)
- `PUT /store/update-product/{id}/` - Update product (Partner app)
- `DELETE /store/delete-product/{id}/` - Delete product (Partner app)

#### Orders
- `POST /customer/customer/order/add/` - Create order (Customer apps)
- `GET /customer/customer/order/history/` - Order history (Customer apps)
- `GET /store/store/orders/` - Get store orders (Partner app)
- `PUT /store/store/status/` - Update order status (Partner app)

#### User Profile
- `GET /customer/customer/profile/` - Get customer profile
- `PUT /customer/customer/profile/update/` - Update profile
- `GET /driver/` - Get driver profile

## Data Flow Examples

### Customer Orders a Product

1. **Customer browses products** (Web or Mobile App)
   - `GET /store/stores/` - Get available stores
   - `GET /store/products/` - Get products

2. **Customer adds to cart** (Client-side)
   - Redux store updated
   - LocalStorage/AsyncStorage persistence

3. **Customer checks out**
   - `POST /customer/customer/order/add/`
   - Backend creates order
   - Backend sends notification to store

4. **Store owner receives order** (Partner App)
   - `GET /store/store/orders/` - Fetch new orders
   - Push notification received

5. **Store owner prepares order** (Partner App)
   - `PUT /store/store/status/` - Update to "preparing"

6. **Driver delivers** (Partner App - Driver mode)
   - `GET /driver/orders/` - Get assigned deliveries
   - `PUT /order/{id}/status/` - Update delivery status

7. **Customer tracks order** (Customer App)
   - `GET /customer/customer/order/history/`
   - Real-time updates via polling or websockets

## Environment Configuration

### Backend (.env)
```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,kudya.pythonanywhere.com
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-password
FRONTEND_URL=https://www.sdkudya.com
```

### Web App (.env.local)
```env
NEXT_PUBLIC_BASE_API=https://kudya.pythonanywhere.com
NEXT_PUBLIC_GOOGLE_API_KEY=your-key
```

### Customer Mobile App (configs/variable.tsx & services/types.ts)
```typescript
export const apiUrl = "https://kudya.pythonanywhere.com";
export const googleAPi = "your-google-api-key";
```

### Partner App (services/types.ts)
```typescript
export const baseAPI = "https://kudya.pythonanywhere.com";
export const googleAPi = "your-google-api-key";
```

## Development Setup

### 1. Backend Setup

```bash
cd www_kudya_shop
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Backend will run at: `http://127.0.0.1:8000`

### 2. Web App Setup

```bash
cd food_deliver
npm install
cp .env.example .env.local
# Edit .env.local to point to backend
npm run dev
```

Web app will run at: `http://localhost:3000`

### 3. Customer Mobile App Setup

```bash
cd kudya-client
npm install
# Edit services/types.ts to point to local backend
npm start
```

### 4. Partner App Setup

```bash
cd KudyaParceiro
npm install
# Edit services/types.ts to point to local backend
npm start
```

## Production Deployment

### Backend
- **Platform**: PythonAnywhere
- **URL**: https://kudya.pythonanywhere.com
- **Database**: PostgreSQL (recommended) or SQLite
- **Static Files**: Served via whitenoise or CDN
- **Media Files**: Cloud storage (AWS S3, Cloudinary)

### Web App
- **Platform**: Vercel (recommended) or Netlify
- **URL**: https://www.sdkudya.com
- **Build Command**: `npm run build`
- **Environment**: Set in platform dashboard

### Mobile Apps
- **Platform**: Expo Application Services (EAS)
- **iOS**: App Store
- **Android**: Google Play Store
- **Build**: `eas build --platform all`

## API Versioning

Currently using API v1 (implicit). For future versions:
- `/api/v2/stores/`
- Update `baseAPI` in all frontend apps

## Authentication Flow

1. **User signs up**:
   - Frontend: `POST /customer/signup/` or `/driver/signup/`
   - Backend creates user and returns token

2. **User logs in**:
   - Frontend: `POST /conta/login/`
   - Backend validates and returns JWT token
   - Frontend stores token (localStorage/AsyncStorage)

3. **Authenticated requests**:
   - Frontend sends token in header: `Authorization: Token <token>`
   - Backend validates token and returns data

4. **Token expiration**:
   - Frontend detects 401 response
   - Redirects to login page

## Error Handling

### Backend Responses

**Success (200-299)**:
```json
{
  "data": { ... },
  "message": "Success"
}
```

**Client Error (400-499)**:
```json
{
  "error": "Invalid request",
  "details": { ... }
}
```

**Server Error (500-599)**:
```json
{
  "error": "Internal server error"
}
```

### Frontend Handling

All apps use try-catch blocks and display user-friendly errors:

```typescript
try {
  const response = await axios.get(`${baseAPI}/stores/`);
  return response.data;
} catch (error) {
  console.error("Error:", error);
  // Show toast/alert to user
}
```

## Testing

### Backend
```bash
cd www_kudya_shop
python manage.py test
```

### Frontend Apps
```bash
# Web app
cd food_deliver
npm run test  # if configured

# Mobile apps
cd kudya-client
npm test  # if configured
```

## Monitoring and Logging

### Backend
- Django logging configured in `settings.py`
- Error tracking: Sentry (optional)
- Server logs: PythonAnywhere dashboard

### Frontend
- Browser console (web app)
- React Native debugger (mobile apps)
- Sentry for error tracking (optional)

## Common Issues and Solutions

### CORS Errors
**Problem**: Web app can't access backend API
**Solution**: Add domain to `CORS_ALLOWED_ORIGINS` in Django settings

### Authentication Errors
**Problem**: Token not being sent
**Solution**: Check axios interceptors and token storage

### Image Upload Issues
**Problem**: Images not displaying
**Solution**: Check `MEDIA_URL` and `MEDIA_ROOT` in Django, ensure correct paths in frontend

### Mobile App Not Connecting
**Problem**: Can't reach local backend
**Solution**: Use computer's IP address instead of `localhost` in mobile apps

## Support

For issues or questions:
- **Email**: ludmilpaulo@gmail.com
- **GitHub Issues**: Open an issue in the relevant repository

## License

Copyright © 2025 Kudya. All rights reserved.

---

Last Updated: October 13, 2025

