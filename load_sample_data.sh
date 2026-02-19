#!/bin/bash

# Load sample data from fixtures into the database
# Run this script after cloning the project and running migrations.
#
# If migrate fails with "table api_shop already exists", your DB is out of sync.
# Use: ./load_sample_data.sh --fresh   (resets DB and loads data)
# Or fix once: python manage.py migrate api 0010_shop_alter_fooditems_options_alter_userprofile_role_and_more --fake
#              python manage.py migrate
# Then run this script again.

echo "🔄 Loading sample data into the database..."
echo ""

# Optional: reset DB for a clean run (e.g. first-time or after migration issues)
if [ "${1:-}" = "--fresh" ]; then
    if [ -f "db.sqlite3" ]; then
        echo "  → Removing existing db.sqlite3 (--fresh)..."
        rm -f db.sqlite3
    fi
    shift
fi

# Check if fixtures directory exists
if [ ! -d "fixtures" ]; then
    echo "❌ Error: fixtures directory not found!"
    echo "   Make sure you're in the backend directory and fixtures exist."
    exit 1
fi

# Run migrations first to ensure database schema is up to date
echo "  → Running migrations..."
if ! python manage.py migrate 2>&1; then
    # Duplicate migration branch: second 0010 also creates api_shop; fake it and retry
    if python manage.py migrate api 0010_shop_alter_fooditems_options_and_more --fake 2>/dev/null; then
        echo "  → Re-running migrations after faking duplicate 0010..."
        python manage.py migrate || exit 1
    else
        echo ""
        echo "❌ Migrate failed. If you see 'table api_shop already exists', run:"
        echo "   ./load_sample_data.sh --fresh"
        echo "   (or delete db.sqlite3, then run this script again)"
        exit 1
    fi
fi

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
