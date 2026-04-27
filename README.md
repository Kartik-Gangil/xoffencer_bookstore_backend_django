# xoffencer_bookstore_backend_django

A Django-based backend API for a bookstore application. This project leverages modern Django features and integrates with various libraries to provide a robust and scalable solution.

## Features

*   **RESTful API:** Built with Django REST Framework for efficient data handling.
*   **Authentication:** Secure user authentication and authorization using `dj-rest-auth` and `django-allauth`.
*   **Token-based Authentication:** JWT (JSON Web Token) support for stateless authentication via `djangorestframework-simplejwt`.
*   **CORS Support:** Handles Cross-Origin Resource Sharing with `django-cors-headers` for seamless frontend integration.
*   **Filtering:** Advanced filtering capabilities for API endpoints using `django-filter`.
*   **Database:** Supports MySQL as the primary database, configured with `PyMySQL`.
*   **Environment Variables:** Manages sensitive configuration settings using `python-decouple`.
*   **External API Integration:** Includes support for integrating with external services like Delhivery API via the `requests` library.
*   **Payment Gateway Integration:** Integrated with Cashfree Payment Gateway for secure transaction processing.

## Project Structure

```
xoffencer_bookstore_backend_django/
├── manage.py
├── requirements.txt
├── core/           # Core Django app (settings, urls, etc.)
├── books/          # App for book-related models and views
├── users/          # App for user-related models and views
├── orders/         # App for order management
├── payment/        # App for payment processing
└── ...             # Other apps as needed
```

## Technologies Used

*   **Python:** 3.10+
*   **Django:** 5.2.4
*   **Django REST Framework:** For building RESTful APIs.
*   **djangorestframework-simplejwt:** For JWT authentication.
*   **django-allauth:** For robust authentication and social account integration.
*   **dj-rest-auth:** For simplified authentication API endpoints.
*   **django-cors-headers:** For managing CORS.
*   **django-filter:** For API filtering.
*   **PyMySQL:** MySQL database connector.
*   **python-decouple:** For managing environment variables.
*   **requests:** For making HTTP requests.
*   **cashfree-pg:** For Cashfree Payment Gateway integration.

## Getting Started

### Prerequisites

*   Python 3.10+ installed
*   Pip package installer
*   Virtual environment (recommended)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your_username/xoffencer_bookstore_backend_django.git
    cd xoffencer_bookstore_backend_django
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the root directory of the project and add your database credentials, secret key, and other necessary configurations. Refer to `python-decouple` documentation for details.
    Example `.env` file:
    ```env
    SECRET_KEY=your_django_secret_key_here
    DEBUG=True
    DATABASE_URL=mysql://user:password@host:port/database_name
    # ... other configurations
    ```

5.  **Run migrations:**
    ```bash
    python manage.py migrate
    ```

6.  **Create a superuser (optional):**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Start the development server:**
    ```bash
    python manage.py runserver
    ```

The API will be accessible at `http://127.0.0.1:8000/`.

## Usage

*(Describe how to use the API endpoints. This section would typically include examples of API requests and responses for key functionalities like user registration, login, fetching books, placing orders, etc. You can use tools like Postman or Swagger/OpenAPI documentation for this.)*

## Contributing

Contributions are welcome! Please refer to the `CONTRIBUTING.md` file for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
