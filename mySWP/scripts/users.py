# CLI command to run this script: 
# python3 manage.py shell < scripts/users.py

from django.contrib.auth.models import User

def create_user(username, password):
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        print(f"User '{username}' already exists.")
    else:
        # Create and save the user
        user = User.objects.create_user(username=username, password=password)
        user.save()
        print(f"User '{username}' created successfully!")

'''
create_user("user0", "0")
create_user("user1", "1")
create_user("user2", "2")
create_user("user3", "3")
'''
