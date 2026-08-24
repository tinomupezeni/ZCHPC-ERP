import os
import sys
import django
from django.core.management import execute_from_command_line
from waitress import serve

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_root.settings')
os.environ['USE_SQLITE'] = 'True'
os.environ['DEBUG'] = 'False'

def run_migrations():
    print("Checking for database migrations...")
    try:
        execute_from_command_line([sys.argv[0], 'migrate', '--noinput'])
        print("Migrations complete.")
    except Exception as e:
        print(f"Migration error: {e}")

def seed_data():
    print("Ensuring system modules are seeded...")
    try:
        from seed_modules import modules
        from modules.identity.infrastructure.persistence.models import SystemModule
        
        for m_data in modules:
            module, created = SystemModule.objects.get_or_create(
                identifier=m_data['identifier'],
                defaults=m_data
            )
            if not created:
                # Update existing module info but keep active status
                module.name = m_data['name']
                module.description = m_data['description']
                module.dependencies = m_data['dependencies']
                module.save()
        print("Seeding complete.")
    except Exception as e:
        print(f"Seeding error: {e}")

def start_server():
    from erp_root.wsgi import application
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting ZCHPC ERP Backend on http://localhost:{port}")
    # Waitress is used as the production-grade server for Windows
    serve(application, host='127.0.0.1', port=port)

if __name__ == '__main__':
    # Initialize Django
    django.setup()
    
    # Setup database
    run_migrations()
    seed_data()
    
    # Run the server
    start_server()
