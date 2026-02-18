# Project improvement suggestions

Suggestions for the Ashesi off-campus online store (backend + frontend).

---

## 1. Immediate fixes Done
- **Runtime / toolchain**: Run backend on **Django 5.2.x with Python 3.14**, or **Django 4.2 with Python ≤3.12**. Avoid unsupported combinations (e.g. Django 4.2 + Python 3.14).

- [x] Updated `requirements.txt` to resolve dependency conflicts.
- [x] Backend: `FRONTEND_URL` read from env in `settings.py` and `settingsprod.py` (with safe defaults).
- [x] Backend: Production CORS fixed: `CORS_ALLOWED_ORIGINS` explicit list, `CORS_ALLOW_CREDENTIALS` (typo fixed in settingsprod).
- [x] Frontend: Keep using `REACT_APP_API_URL` from `.env` only (no hardcoded API URL in code)—already the case.

---

## 2. Backend code quality

- **Split `api/views.py`**: Break into modules by domain (e.g. `auth.py`, `orders.py`, `payments.py`, `dashboard.py`, `items.py`) so each file stays under ~500 lines and is easier to maintain.
- **Avoid string literals for status/roles**: Use constants or enums for order status, user roles, payment status, etc., and reference them everywhere instead of raw strings.
- **Explicit shop type**: Replace “infer shop type from shop name” logic with an explicit `Shop.shop_type` (or similar) field so behaviour is predictable and maintainable.
- **Validation and error shape**: Validate query params (e.g. `shop_id`) and return clear 400 responses; use a consistent API error format (e.g. `{ "detail": "..." }` or `{ "errors": { ... } }`).
- **Pagination and filtering**: Add pagination to list endpoints; support query filters (search, status, date range, shop).
- **Tests**: Add API tests for auth (register, verify, login, password reset), role-based access, order create/update, and payment initiate/verify (with Paystack mocked).

---

## 3. Security and operations

- **Rate limiting**: Throttle sensitive endpoints (register, login, password reset) - Optional.
- **Audit trail**: Record who changed an order status and when (e.g. simple `OrderStatusHistory` or audit log).
- **Payments**: Add Paystack **webhooks** so payment status is updated even if the user never hits the verify endpoint.
- **Logging and health**: Use structured logging for auth, orders, payments; add an `/api/health/` (or similar) endpoint for monitoring.

---

## 4. Frontend code quality and UX

- **Role constants**: Define a single `UserRoles` (or similar) and use it everywhere instead of comparing to string literals (`'super_admin'`, `'shop_manager'`, etc.).
- **Role labels and routes**: Ensure every role has a label and a default route (e.g. include `shop_manager` in `ROLE_LABELS` and `ROLE_ROUTES`).
- **API error handling**: Use one Axios response interceptor for 401 (refresh or redirect to login), consistent error messages, and optional retries.
- **Reusable loading/error UI**: Use a shared `Loader` and error/empty states; add an error boundary for the app.
- **Cart per shop**: Store cart keyed by shop (e.g. `cart_${shopId}`) so switching shops does not mix items from different shops.

---

## 5. High-impact feature ideas

- **Account area**: Order history, saved delivery info, simple “receipt” view.
- **Inventory / availability**: Stock or availability flags, “out of stock” handling, optional scheduling (e.g. for food).
- **Staff dashboard**: Live order queue, filters, export, basic analytics.
- **Notifications**: Email or SMS for order status changes - future work
- **Discovery**: Product/search and categories; “popular” or “recent” items.

---
