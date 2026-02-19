# Ashesi Off-Campus Online Store - Backend

## 🔧 How to Run the Project

### 1. Clone the repository

```bash
git clone <repo_url>
cd backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up the database

```bash
python manage.py migrate
```

### 5. Load sample data (shops, products, etc.)

```bash
./load_sample_data.sh
# or on Windows:
# bash load_sample_data.sh
```

This will populate the database with sample shops, food items, electronics, and groceries.

### 6. Start the Django API server

```bash
python manage.py runserver
```

The API will be available at: `http://127.0.0.1:8000/`

---

## 📦 For Maintainers: Exporting Data

If you've added new data to the database and want to update the fixtures:

```bash
./export_data.sh
```

This will export the current database data to the `fixtures/` folder.

---
