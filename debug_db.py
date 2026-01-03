import os
import django
from django.db import connection
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mms.settings')
django.setup()

def check_tables():
    print(f"Connecting to database: {settings.DATABASES['default']['NAME']} on {settings.DATABASES['default']['HOST']}")
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Found {len(tables)} tables:")
        for t in tables:
            print(f" - {t}")
            
        # Try to drop app_meetinginfo if it exists
        if 'app_meetinginfo' in tables:
            print("\nAttempting to drop app_meetinginfo...")
            try:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
                cursor.execute("DROP TABLE IF EXISTS `app_meetinginfo`")
                print("SUCCESS: app_meetinginfo dropped.")
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            except Exception as e:
                print(f"FAILURE: Could not drop table. Error: {e}")

if __name__ == "__main__":
    check_tables()
