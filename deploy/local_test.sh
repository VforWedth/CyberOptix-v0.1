#!/bin/bash

# Local test deployment script for LaptopMart Myanmar
# Run this on your development machine to test deployment locally

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Starting local test deployment...${NC}"

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: Please run this script from the Django project root directory${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Run migrations
echo -e "${YELLOW}Running database migrations...${NC}"
python manage.py makemigrations
python manage.py migrate

# Collect static files
echo -e "${YELLOW}Collecting static files...${NC}"
python manage.py collectstatic --noinput

# Test Gunicorn
echo -e "${YELLOW}Testing Gunicorn server...${NC}"
echo -e "${GREEN}Starting Gunicorn on http://localhost:8000${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"

# Start Gunicorn with our configuration
gunicorn --config deploy/gunicorn.conf.py inferno.wsgi:application