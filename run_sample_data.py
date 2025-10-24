#!/usr/bin/env python
"""
Script to create sample data with proper Turkish characters
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
    # Run the management command to create sample data
    execute_from_command_line(['manage.py', 'create_sample_data'])
