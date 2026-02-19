#!/bin/bash

# Export Django database data to fixtures
# Run this script to create fixture files from your current database

echo "🔄 Exporting database data to fixtures..."

# Create fixtures directory if it doesn't exist
mkdir -p fixtures

# Export Shops (core data)
echo "  → Exporting Shops..."
python manage.py dumpdata api.Shop --indent 2 > fixtures/shops.json

# Export Food Items
echo "  → Exporting Food Items..."
python manage.py dumpdata api.FoodItems --indent 2 > fixtures/food_items.json

# Export Electronics Items
echo "  → Exporting Electronics Items..."
python manage.py dumpdata api.ElectronicsItems --indent 2 > fixtures/electronics_items.json

# Export Grocery Items
echo "  → Exporting Grocery Items..."
python manage.py dumpdata api.GroceryItems --indent 2 > fixtures/grocery_items.json

# Optional: Export sample orders (comment out if you don't want to share order history)
# echo "  → Exporting Orders..."
# python manage.py dumpdata api.Order --indent 2 > fixtures/orders.json
# python manage.py dumpdata api.OrderItem --indent 2 > fixtures/order_items.json

echo ""
echo "✅ Export complete! Fixture files created in ./fixtures/"
echo ""
echo "Files created:"
ls -la fixtures/
echo ""
echo "⚠️  Note: User data and payments were NOT exported for security reasons."
echo "    To include them, uncomment the relevant lines in this script."
