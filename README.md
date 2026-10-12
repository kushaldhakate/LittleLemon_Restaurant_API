# Little Lemon API

Django REST Framework + Djoser backend API for the Little Lemon restaurant course project.

## Setup (macOS/Linux)
```bash
cd LittleLemon
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations LittleLemonAPI
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/admin/` for the admin panel and `http://127.0.0.1:8000/api/` for API routes.

## Authentication
Register a customer: `POST /api/auth/users/` with `username`, `password`, `re_password`.
Obtain token: `POST /api/auth/token/login/` with `username`, `password`.
Send authenticated requests with header `Authorization: Token YOUR_TOKEN`.

## Main endpoints
- `GET /api/categories`
- `GET/POST /api/menu-items/`; `GET/PUT/PATCH/DELETE /api/menu-items/{id}/`
- `GET/POST/DELETE /api/groups/manager/users` (manager/admin only; POST body `{"username":"..."}`)
- `GET/POST/DELETE /api/groups/delivery-crew/users` (manager/admin only)
- `GET/PATCH /api/featured` (manager/admin only; PATCH body `{"item_id": 1}`)
- `GET/POST/DELETE /api/cart/menu-items` (authenticated user)
- `GET/POST /api/orders`
- `PATCH/DELETE /api/orders/{id}`

Menu items support filtering with `?category=1`, `?featured=true`, search with `?search=pasta`, ordering with `?ordering=price` or `?ordering=-price`, and page-number pagination (`?page=2`).

## Notes
Create the groups `Manager` and `Delivery crew` in Django admin or use the group endpoints (which create them automatically). Use admin/staff account for manager operations.
