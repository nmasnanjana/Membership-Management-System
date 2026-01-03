import os
import subprocess
import logging
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
from django.db import connection

logger = logging.getLogger('audit')

@user_passes_test(lambda u: u.is_superuser)
def database_management(request):
    """
    View for database management (Import/Export)
    Only accessible by superusers.
    """
    
    # Get database settings
    db_settings = settings.DATABASES['default']
    db_name = db_settings['NAME']
    db_user = db_settings['USER']
    db_password = db_settings['PASSWORD']
    db_host = db_settings['HOST']
    db_port = db_settings['PORT']
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'export_full':
            return export_database(db_name, db_user, db_password, db_host, db_port)
            
        elif action == 'export_custom':
            selected_tables = request.POST.getlist('tables')
            if not selected_tables:
                messages.error(request, 'Please select at least one table to export.')
                return redirect('database_management')
            return export_database(db_name, db_user, db_password, db_host, db_port, tables=selected_tables)
            
        elif action == 'import':
            sql_file = request.FILES.get('sql_file')
            if not sql_file:
                messages.error(request, 'Please upload a SQL file.')
                return redirect('database_management')
            
            if not sql_file.name.endswith('.sql'):
                messages.error(request, 'Invalid file type. Please upload a .sql file.')
                return redirect('database_management')
                
            # Save file temporarily
            temp_path = os.path.join(settings.MEDIA_ROOT, 'temp_import.sql')
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            with open(temp_path, 'wb+') as destination:
                for chunk in sql_file.chunks():
                    destination.write(chunk)
            
            try:
                import_database(db_name, db_user, db_password, db_host, db_port, temp_path)
                messages.success(request, 'Database restored successfully.')
                logger.info(f"Database restored by {request.user.username} from {sql_file.name}")
            except Exception as e:
                logger.error(f"Database restore failed: {str(e)}")
                messages.error(request, f'Database restore failed: {str(e)}')
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            return redirect('database_management')

    # Get all tables for custom export
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]

    # Import context_data to ensure navbar and footer are shown
    from .views import context_data
    context = context_data(request)
    context.update({
        'tables': tables,
        'page_name': 'Database Management'
    })
    return render(request, 'admin/database_management.html', context)


def export_database(db_name, db_user, db_password, db_host, db_port, tables=None):
    """
    Helper function to export database using mysqldump
    """
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"backup_{db_name}_{timestamp}.sql"
    
    # Construct command
    # Note: Using subprocess with shell=False for security, passing args as list
    cmd = [
        'mysqldump',
        f'--host={db_host}',
        f'--port={db_port}',
        f'--user={db_user}',
        f'--password={db_password}',
        '--skip-ssl',
        db_name
    ]
    
    if tables:
        cmd.extend(tables)
        filename = f"backup_custom_{timestamp}.sql"
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"mysqldump failed: {error.decode('utf-8')}")
            raise Exception(f"Export failed: {error.decode('utf-8')}")
            
        response = HttpResponse(output, content_type='application/sql')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        logger.error(f"Export exception: {str(e)}")
        # In a real view we might want to return a redirect with error message, 
        # but since we are returning a file response, we raise to be caught or show error page.
        # Here we just return a simple error response for simplicity or re-raise
        raise e


def import_database(db_name, db_user, db_password, db_host, db_port, file_path):
    """
    Helper function to import database using mysql
    """
    # Drop all tables first to ensure clean import
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"Found {len(tables)} tables to drop in {db_name}: {tables}")
            
            if tables:
                # Wrap table names in backticks
                tables_formatted = [f"`{t}`" for t in tables]
                drop_query = f"DROP TABLE IF EXISTS {', '.join(tables_formatted)}"
                logger.info(f"Executing drop query: {drop_query[:100]}...") # Log start of query
                cursor.execute(drop_query)
                logger.info("Tables dropped successfully.")
            else:
                logger.info("No tables found to drop.")
                
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    except Exception as e:
        logger.error(f"Error dropping tables: {str(e)}")
        raise Exception(f"Error dropping tables: {str(e)}")

    # Construct command
    cmd = [
        'mysql',
        f'--host={db_host}',
        f'--port={db_port}',
        f'--user={db_user}',
        f'--password={db_password}',
        '--skip-ssl',
        db_name
    ]
    
    with open(file_path, 'r') as f:
        try:
            process = subprocess.Popen(cmd, stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Import failed: {error.decode('utf-8')}")
                
        except Exception as e:
            raise e
