#!/bin/bash

# Load sample data from fixtures into the database
# Run this script after cloning the project and running migrations

echo "🔄 Loading sample data into the database..."
echo ""

# Check if fixtures directory exists
if [ ! -d "fixtures" ]; then
    echo "❌ Error: fixtures directory not found!"
    echo "   Make sure you're in the backend directory and fixtures exist."
    exit 1
fi

# Run migrations first to ensure database schema is up to date
echo "  → Running migrations..."
python manage.py migrate

echo ""
echo "  → Loading Shops..."
python manage.py loaddata fixtures/shops.json

echo "  → Loading Food Items..."
python manage.py loaddata fixtures/food_items.json

echo "  → Loading Electronics Items..."
python manage.py loaddata fixtures/electronics_items.json

echo "  → Loading Grocery Items..."
python manage.py loaddata fixtures/grocery_items.json

# Uncomment if you exported orders
# echo "  → Loading Orders..."
# python manage.py loaddata fixtures/orders.json
# python manage.py loaddata fixtures/order_items.json

echo ""
echo "✅ Sample data loaded successfully!"
echo ""
echo "You can now run the server with: python manage.py runserver"
