# Neon PostgreSQL Setup Guide for EZM Trade Management

This guide will help you migrate your EZM Trade Management project from SQLite to Neon PostgreSQL.

## Prerequisites

1. **Neon Account**: You already have a Neon database set up
2. **Connection String**: `postgresql://neondb_owner:npg_CRVEs6MTg9cv@ep-noisy-boat-a9tqvkrl-pooler.gwc.azure.neon.tech/neondb?sslmode=require&channel_binding=require`

## Step 1: Install PostgreSQL Adapter

```bash
pip install psycopg2-binary==2.9.9
```

## Step 2: Database Configuration

The `core/settings.py` file has been updated to use Neon PostgreSQL. The configuration includes:

- **Engine**: `django.db.backends.postgresql`
- **Host**: `ep-noisy-boat-a9tqvkrl-pooler.gwc.azure.neon.tech`
- **Database**: `neondb`
- **User**: `neondb_owner`
- **SSL Mode**: `require` (required for Neon)

## Step 3: Test Database Connection

Run the test script to verify your Neon connection:

```bash
python test_neon_connection.py
```

This script will:
- Test the database connection
- Run Django's database check
- Apply migrations
- Verify everything is working

## Step 4: Migrate Data (Optional)

If you want to migrate existing data from SQLite to Neon:

```bash
python migrate_to_neon.py
```

This script will:
- Create a backup of your SQLite database
- Set up the Neon database with all migrations
- Create a superuser account
- Verify all tables are created correctly

## Step 5: Verify Installation

1. **Run Django checks**:
   ```bash
   python manage.py check
   ```

2. **Test migrations**:
   ```bash
   python manage.py migrate
   ```

3. **Create superuser** (if not done by migration script):
   ```bash
   python manage.py createsuperuser
   ```

4. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

## Step 6: Verify Functionality

Test these key features to ensure everything works with Neon:

1. **User Management**: Login, registration, password changes
2. **Inventory Management**: Products, suppliers, stock management
3. **Order Processing**: Purchase orders, delivery tracking
4. **Payment Processing**: Chapa integration
5. **Store Management**: Store operations, cashier functions

## Troubleshooting

### Common Issues

1. **Connection Errors**:
   - Verify your Neon connection string is correct
   - Check that `psycopg2-binary` is installed
   - Ensure SSL mode is set to `require`

2. **Migration Errors**:
   - Run `python manage.py makemigrations` first
   - Check for any custom model changes
   - Verify all apps are in `INSTALLED_APPS`

3. **Performance Issues**:
   - Neon provides connection pooling
   - Consider adding `CONN_MAX_AGE = 600` to database settings for connection reuse

### Error Messages

- **"connection to server failed"**: Check your internet connection and Neon database status
- **"authentication failed"**: Verify username and password in connection string
- **"database does not exist"**: Check database name in connection string

## Production Considerations

For production deployment, consider these additional settings:

```python
# Add to settings.py for production
if not DEBUG:
    # Security settings
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    # HTTPS settings
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Database connection pooling
    DATABASES['default']['CONN_MAX_AGE'] = 600
```

## Benefits of Neon PostgreSQL

1. **Serverless**: Automatically scales based on usage
2. **Branching**: Create database branches for development
3. **Backup**: Automatic backups and point-in-time recovery
4. **Performance**: Optimized for read-heavy workloads
5. **Security**: Built-in SSL encryption and security features

## Monitoring and Maintenance

1. **Monitor Database Usage**: Check Neon dashboard for usage metrics
2. **Backup Strategy**: Neon provides automatic backups
3. **Performance Monitoring**: Use Django's database logging for query analysis
4. **Connection Pooling**: Neon handles this automatically

## Support

If you encounter issues:

1. Check the Neon documentation: https://neon.tech/docs
2. Review Django PostgreSQL documentation: https://docs.djangoproject.com/en/5.2/ref/databases/#postgresql-notes
3. Check the test scripts for specific error messages

## Next Steps

After successful migration:

1. Test all application features thoroughly
2. Update your deployment scripts to use Neon
3. Consider setting up database monitoring
4. Plan for data backup and recovery procedures
5. Update your CI/CD pipeline to use Neon for testing

---

**Note**: Keep your SQLite backup until you're completely confident that everything works with Neon PostgreSQL. 