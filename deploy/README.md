# LaptopMart Myanmar Deployment Guide

This directory contains all the necessary configuration files for deploying your Django application using Gunicorn + Nginx.

## Files Overview

- `gunicorn.conf.py` - Gunicorn WSGI server configuration
- `nginx.conf` - Nginx reverse proxy configuration
- `laptopmart.service` - Systemd service file for auto-start
- `setup.sh` - Automated deployment script for Ubuntu/Debian servers
- `local_test.sh` - Local testing script for development
- `settings_production.py` - Production Django settings

## Quick Local Test

1. Make the test script executable:
```bash
chmod +x deploy/local_test.sh
```

2. Run the local test:
```bash
./deploy/local_test.sh
```

3. Visit `http://localhost:8000` to test your application

## Production Deployment

### Prerequisites

- Ubuntu 20.04+ or Debian 10+ server
- Domain name (optional for testing)
- Root or sudo access

### Automated Setup

1. Upload your project to the server:
```bash
rsync -avz --exclude='.git' --exclude='venv' . user@server:/var/www/laptopmart/
```

2. Make setup script executable and run:
```bash
chmod +x deploy/setup.sh
sudo ./deploy/setup.sh
```

### Manual Setup Steps

If you prefer manual setup:

#### 1. Install System Dependencies
```bash
sudo apt update
sudo apt install nginx postgresql python3-pip python3-venv
```

#### 2. Setup Database
```bash
sudo -u postgres createdb laptopmart_db
sudo -u postgres createuser laptopmart_user
sudo -u postgres psql -c "ALTER USER laptopmart_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE laptopmart_db TO laptopmart_user;"
```

#### 3. Setup Python Environment
```bash
cd /var/www/laptopmart
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Configure Django
```bash
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```

#### 5. Setup Nginx
```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/laptopmart
sudo ln -s /etc/nginx/sites-available/laptopmart /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
```

#### 6. Setup Systemd Service
```bash
sudo cp deploy/laptopmart.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable laptopmart
sudo systemctl start laptopmart
```

#### 7. Start Services
```bash
sudo systemctl restart nginx
sudo systemctl restart laptopmart
```

## Configuration Files Explanation

### Gunicorn Configuration (`gunicorn.conf.py`)

- **Workers**: Set to `CPU cores * 2 + 1` for optimal performance
- **Binding**: Configured to bind to `127.0.0.1:8000`
- **Timeout**: 30 seconds to handle slow requests
- **Logging**: Configured to log to stdout/stderr

### Nginx Configuration (`nginx.conf`)

- **Reverse Proxy**: Forwards requests from port 80 to Gunicorn on port 8000
- **Static Files**: Serves CSS, JS, images directly without hitting Django
- **Security Headers**: Adds security headers to all responses
- **Gzip**: Compresses responses to reduce bandwidth

### Systemd Service (`laptopmart.service`)

- **Auto-start**: Automatically starts the application on server boot
- **Process Management**: Restarts the application if it crashes
- **User**: Runs as `www-data` user for security

## Environment Variables

Create a `.env` file in your project root with:

```env
SECRET_KEY=your-super-secret-key-here
DB_NAME=laptopmart_db
DB_USER=laptopmart_user
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
GOOGLE_OAUTH_CLIENT_ID=your-oauth-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-oauth-client-secret
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
```

## Testing Your Deployment

1. Check service status:
```bash
sudo systemctl status laptopmart
sudo systemctl status nginx
```

2. View logs:
```bash
sudo journalctl -u laptopmart -f
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

3. Test the application:
```bash
curl -I http://localhost
curl -I http://localhost/static/
```

## Common Issues & Solutions

### Gunicorn won't start
- Check the service logs: `sudo journalctl -u laptopmart -f`
- Verify paths in the service file are correct
- Ensure virtual environment has all dependencies

### Static files not loading
- Run `python manage.py collectstatic`
- Check Nginx configuration paths match your STATIC_ROOT
- Verify file permissions: `sudo chown -R www-data:www-data /var/www/laptopmart/`

### Database connection errors
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check database credentials in `.env` file
- Ensure database and user exist

### Permission denied errors
- Set correct ownership: `sudo chown -R www-data:www-data /var/www/laptopmart/`
- Check file permissions: `chmod +x manage.py`

## SSL/HTTPS Setup

For production with a domain:

1. Install Certbot:
```bash
sudo apt install certbot python3-certbot-nginx
```

2. Get SSL certificate:
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

3. Update Django settings:
```python
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
```

## Monitoring & Maintenance

### Log Rotation
Logs are automatically rotated when using the production settings.

### Backup Strategy
- Database: `pg_dump laptopmart_db > backup.sql`
- Media files: `tar -czf media_backup.tar.gz media/`
- Code: Use Git for version control

### Updates
1. Pull latest code
2. Activate virtual environment
3. Install new dependencies: `pip install -r requirements.txt`
4. Run migrations: `python manage.py migrate`
5. Collect static files: `python manage.py collectstatic`
6. Restart services: `sudo systemctl restart laptopmart`

## Performance Tuning

- Adjust Gunicorn workers based on your server specs
- Use Redis for caching (already configured in production settings)
- Consider using a CDN for static files
- Monitor with tools like New Relic or DataDog

## Security Checklist

- [ ] DEBUG = False in production
- [ ] Strong SECRET_KEY
- [ ] Database credentials secured
- [ ] SSL certificate installed
- [ ] Security headers configured
- [ ] Regular security updates
- [ ] Firewall configured (UFW recommended)
- [ ] Fail2ban for brute force protection