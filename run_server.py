#!/usr/bin/env python
"""
Script to run Django development server with proper encoding
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayip_esya.settings')
django.setup()

from django.core.management import execute_from_command_line

if __name__ == '__main__':
    # Set environment variables for proper encoding
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['LANG'] = 'tr_TR.UTF-8'
    os.environ['LC_ALL'] = 'tr_TR.UTF-8'
    
    # Run the development server
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])
