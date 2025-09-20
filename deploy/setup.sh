#!/bin/bash

# LaptopMart Myanmar Deployment Setup Script
# Run this script on your production server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting LaptopMart Myanmar deployment setup...${NC}"

# Variables (UPDATE THESE)
PROJECT_DIR="/var/www/laptopmart"
VENV_DIR="$PROJECT_DIR/venv"
USER="www-data"
GROUP="www-data"

# Create project directory
echo -e "${YELLOW}Creating project directory...${NC}"
sudo mkdir -p $PROJECT_DIR
sudo chown -R $USER:$GROUP $PROJECT_DIR

# Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
sudo apt update
sudo apt install -y nginx postgresql postgresql-contrib python3-pip python3-venv python3-dev \
    libpq-dev build-essential supervisor certbot python3-certbot-nginx

# Create virtual environment
echo -e "${YELLOW}Creating Python virtual environment...${NC}"
cd $PROJECT_DIR
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Database setup
echo -e "${YELLOW}Setting up PostgreSQL database...${NC}"
sudo -u postgres psql -c "CREATE DATABASE laptopmart_db;"
sudo -u postgres psql -c "CREATE USER laptopmart_user WITH PASSWORD 'secure_password_here';"
sudo -u postgres psql -c "ALTER ROLE laptopmart_user SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE laptopmart_user SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE laptopmart_user SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE laptopmart_db TO laptopmart_user;"

# Django setup
echo -e "${YELLOW}Running Django migrations and collecting static files...${NC}"
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

# Create superuser (interactive)
echo -e "${YELLOW}Create Django superuser (you'll be prompted for details):${NC}"
python manage.py createsuperuser

# Setup Nginx
echo -e "${YELLOW}Configuring Nginx...${NC}"
sudo cp deploy/nginx.conf /etc/nginx/sites-available/laptopmart

# Update paths in nginx config
sudo sed -i "s|/path/to/your/project|$PROJECT_DIR|g" /etc/nginx/sites-available/laptopmart

# Enable the site
sudo ln -sf /etc/nginx/sites-available/laptopmart /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # Remove default site

# Test nginx configuration
sudo nginx -t

# Setup systemd service
echo -e "${YELLOW}Setting up systemd service...${NC}"
sudo cp deploy/laptopmart.service /etc/systemd/system/

# Update paths in service file
sudo sed -i "s|/path/to/your/project|$PROJECT_DIR|g" /etc/systemd/system/laptopmart.service
sudo sed -i "s|/path/to/your/venv|$VENV_DIR|g" /etc/systemd/system/laptopmart.service

# Set correct ownership
sudo chown -R $USER:$GROUP $PROJECT_DIR

# Reload systemd and start services
sudo systemctl daemon-reload
sudo systemctl enable laptopmart
sudo systemctl start laptopmart

# Start/restart services
sudo systemctl restart nginx
sudo systemctl restart laptopmart

# Check status
echo -e "${GREEN}Checking service status...${NC}"
sudo systemctl status laptopmart --no-pager -l
sudo systemctl status nginx --no-pager -l

echo -e "${GREEN}Setup complete! Your application should be available at:${NC}"
echo -e "${GREEN}http://your-server-ip${NC}"

echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update your DNS records to point to this server"
echo "2. Install SSL certificate with: sudo certbot --nginx -d your-domain.com"
echo "3. Update Django settings for production (DEBUG=False, etc.)"
echo "4. Set up monitoring and backups"