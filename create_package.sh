#!/bin/bash
# create_package_structure.sh

PACKAGE_NAME="django_user_permissions"

# Create main package directory
mkdir -p $PACKAGE_NAME

# Create core files
touch $PACKAGE_NAME/__init__.py
touch $PACKAGE_NAME/models.py
touch $PACKAGE_NAME/backends.py
touch $PACKAGE_NAME/permissions.py
touch $PACKAGE_NAME/mixins.py
touch $PACKAGE_NAME/utils.py
touch $PACKAGE_NAME/settings.py
touch $PACKAGE_NAME/signals.py

# Create migrations directory (required for Django models)
mkdir -p $PACKAGE_NAME/migrations
touch $PACKAGE_NAME/migrations/__init__.py

# Create management command directory
mkdir -p $PACKAGE_NAME/management/commands
touch $PACKAGE_NAME/management/__init__.py
touch $PACKAGE_NAME/management/commands/__init__.py
touch $PACKAGE_NAME/management/commands/sync_user_permissions.py

echo "Package structure for '$PACKAGE_NAME' created successfully."
echo ""
echo "Next steps:"
echo "1. cd $PACKAGE_NAME"
echo "2. Ask me for each file's code, e.g., 'give me models.py'"