# EZM Trade Management System

A Django-based trade management system for inventory, store management, and transactions.

## Features

- **User Management**: Custom user roles (Admin, Head Manager, Store Manager, Cashier)
- **Inventory Management**: Product catalog and stock management
- **Store Management**: Multi-store support with role-based access
- **Transaction Processing**: POS system for sales transactions
- **Authentication**: Role-based authentication with OTP support

## Installation

### Prerequisites

- Python 3.11 or higher
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd EZM_TRADE_MANAGMENT
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows (Git Bash)
   source venv/Scripts/activate
   
   # On Windows (Command Prompt)
   venv\Scripts\activate
   
   # On Windows (PowerShell)
   venv\Scripts\Activate.ps1
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the project root with the following variables:
   ```env
   EMAIL_HOST=your-smtp-host
   EMAIL_PORT=587
   EMAIL_HOST_USER=your-email@example.com
   EMAIL_HOST_PASSWORD=your-email-password
   EMAIL_USE_TLS=True
   DEFAULT_FROM_EMAIL=noreply@ezmtrade.com
   ```

5. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

   The application will be available at `http://127.0.0.1:8000/`

## Installed Packages

### Core Dependencies
- **Django 5.2.3**: Web framework
- **djangorestframework 3.16.0**: REST API framework
- **django-widget-tweaks 1.5.0**: Form widget customization
- **python-dotenv 1.1.0**: Environment variable management
- **PyJWT 2.9.0**: JSON Web Token handling

### Additional Features
- **django-crispy-forms 2.4**: Enhanced form rendering
- **crispy-bootstrap4 2025.6**: Bootstrap 4 support for forms
- **django-extensions 4.1**: Additional Django management commands
- **pillow 11.3.0**: Image processing support

### PDF Generation (Optional)
- **weasyprint 65.1**: PDF generation from HTML

**Note for Windows users**: WeasyPrint requires additional system libraries (GTK+). 
For installation instructions, see: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows

## Project Structure

```
EZM_TRADE_MANAGMENT/
├── core/                   # Main Django project settings
├── users/                  # User management app
├── store/                  # Store management app
├── Inventory/              # Inventory management app
├── transactions/           # Transaction processing app
├── templates/              # HTML templates
├── static/                 # Static files (CSS, JS, images)
├── requirements.txt        # Python dependencies
├── manage.py              # Django management script
└── db.sqlite3             # SQLite database (created after migration)
```

## Usage

1. **Admin Dashboard**: Access at `/admin/` with superuser credentials
2. **User Login**: Main login page at `/`
3. **Role-based Access**: Different dashboards based on user roles
4. **Inventory Management**: Add/edit products and manage stock levels
5. **Store Operations**: Process sales and manage store-specific data

## Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python manage.py test`
5. Submit a pull request

## License

[Add your license information here]
