# Kudya Shop - Backend API

Django REST API backend for the Kudya food delivery and e-commerce platform.

## Overview

This is the main backend server that powers:
- **Kudya Web App** (food_deliver) - Next.js customer web application
- **Kudya Mobile App** (kudya-client) - React Native customer mobile app
- **Kudya Parceiro** (KudyaParceiro) - React Native partner/driver mobile app

## Features

- 🏪 Store/Restaurant management
- 📦 Product/Menu catalog
- 🛒 Order management
- 🚗 Driver/Delivery tracking
- 👥 Customer management
- 💳 Payment processing
- 📊 Reporting and analytics
- 💼 Career applications
- 📧 Email notifications

## Tech Stack

- **Framework**: Django 5.2.1
- **API**: Django REST Framework 3.14.0
- **Database**: SQLite (default) / PostgreSQL (production)
- **Authentication**: Token-based authentication
- **Rich Text Editor**: CKEditor 5
- **Task Queue**: Celery
- **WebSockets**: Django Channels
- **PDF Generation**: ReportLab, WeasyPrint

## Installation

### Prerequisites

- Python 3.8+
- pip
- virtualenv (recommended)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/ludmilpaulo/www_kudya_shop.git
cd www_kudya_shop
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file (use `.env.example` as template):
```bash
cp .env.example .env
```

5. Update `.env` with your configuration:
```env
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,kudya.pythonanywhere.com
EMAIL_HOST=your-smtp-host
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-password
```

6. Run migrations:
```bash
python manage.py migrate
```

7. Create a superuser:
```bash
python manage.py createsuperuser
```

8. Run the development server:
```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000`

## API Endpoints

### Authentication
- `POST /conta/login/` - User login
- `POST /conta/logout/` - User logout
- `POST /conta/reset-password/` - Password reset request
- `POST /conta/reset-password-confirm/` - Password reset confirmation

### Stores/Restaurants
- `GET /store/stores/` or `GET /restaurant/stores/` - List all stores
- `GET /store/stores/{id}/` or `GET /restaurant/stores/{id}/` - Get store details
- `POST /store/fornecedor/` or `POST /restaurant/fornecedor/` - Register new store
- `PUT /store/stores/{id}/` or `PUT /restaurant/stores/{id}/` - Update store
- `GET /store/store-categories/` or `GET /restaurant/store-categories/` - List store categories
- `GET /store/store-types/` or `GET /restaurant/store-types/` - List store types

### Products
- `GET /store/products/` or `GET /restaurant/products/` - List all products
- `GET /store/products/{id}/` or `GET /restaurant/products/{id}/` - Get product details
- `POST /store/add-product/` or `POST /restaurant/add-product/` - Add new product
- `PUT /store/update-product/{id}/` or `PUT /restaurant/update-product/{id}/` - Update product
- `DELETE /store/delete-product/{id}/` or `DELETE /restaurant/delete-product/{id}/` - Delete product
- `GET /store/product-categories/` or `GET /restaurant/product-categories/` - List product categories

### Orders
- `GET /order/` - List orders
- `POST /customer/customer/order/add/` - Create new order
- `PUT /store/store/status/` or `PUT /restaurant/restaurant/status/` - Update order status
- `GET /customer/customer/order/history/` - Get customer order history

### Customers
- `POST /customer/signup/` - Customer registration
- `GET /customer/customer/profile/` - Get customer profile
- `PUT /customer/customer/profile/update/` - Update customer profile
- `GET /customer/customer/stores/` - Get nearby stores

### Drivers
- `GET /driver/` - List drivers
- `POST /driver/signup/` - Driver registration
- `GET /driver/orders/` - Get driver orders

### Info & Careers
- `GET /info/` - Get app information
- `GET /careers/` - List job openings
- `POST /careers/apply/` - Submit job application

## URL Aliases

The API supports both `/store/` and `/restaurant/` URL prefixes for backward compatibility with legacy frontend applications. Both endpoints point to the same views and functionality.

## Environment Variables

See `.env.example` for all available environment variables.

## Production Deployment

### PythonAnywhere

1. Upload code to PythonAnywhere
2. Set up virtual environment
3. Configure WSGI file
4. Set environment variables in `.env`
5. Run migrations
6. Collect static files: `python manage.py collectstatic`

### Other Platforms

Configure according to your hosting provider's Django deployment guide. Ensure:
- `DEBUG=False` in production
- Proper `ALLOWED_HOSTS` configuration
- Secure `SECRET_KEY`
- Use PostgreSQL or MySQL instead of SQLite
- Configure proper email settings
- Set up HTTPS

## Security Notes

- Never commit `.env` file to version control
- Keep `SECRET_KEY` secure
- Use strong passwords for email accounts
- Enable HTTPS in production
- Regularly update dependencies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

Copyright © 2025 Kudya. All rights reserved.

## Support

For support, email: support@maindodigital.com
