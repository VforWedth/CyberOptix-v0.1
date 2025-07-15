# CyberOptix LaptopMart Myanmar v0.1

A Django‑based e‑commerce platform tailored for Myanmar laptop buyers. Version 0.1 focuses on core shopping functionality: user authentication, product catalog, filtering, cart management, and payment integration.

---

## 🚀 Features

* **User Roles**: Customer & Admin with registration, login, and profile management.
* **Product Catalog**: Browse laptops by brand, RAM, CPU, and category.
* **Filters & Search**: Dynamic filtering by specifications (RAM size, CPU type, brand).
* **Shopping Cart**: Add, update, and remove items with real‑time price calculation.
* **Checkout & Payments**: Integrated with Stripe for secure transactions.
* **Admin Dashboard**: Manage products (CRUD) directly through a simple UI.
* **Responsive Design**: Mobile‑first layout with Bootstrap.

---

## 🛠️ Technologies

* **Backend**: Django 3.2, Django REST Framework
* **Database**: PostgreSQL (via `psycopg2-binary`)
* **Frontend**: Django Templates + Bootstrap
* **Payments**: Stripe SDK
* **Image Handling**: Pillow
* **Version Control**: Git & GitHub

---

## 📦 Installation

1. **Clone the repo**

   ```bash
   git clone https://github.com/VforWedth/CyberOptix.git
   cd CyberOptix/inferno
   ```

2. **Create and activate venv**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   source .venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**

   ```bash
   pip install -r ../requirements.txt
   ```

4. **Configure environment**

   * Copy `.env.example` to `.env` and fill in:

     ```ini
     SECRET_KEY=<your_django_secret_key>
     DATABASE_URL=postgres://USER:PASSWORD@HOST:PORT/DB_NAME
     STRIPE_SECRET_KEY=<your_stripe_key>
     ```

5. **Run migrations & start server**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py runserver
   ```

---

## 🎓 Usage

* Visit `http://127.0.0.1:8000/` in your browser.
* Register as a Customer or login as Admin to manage products.
* Browse and filter laptops, add to cart, and complete checkout via Stripe.

---

## 📝 Project Structure

```
CyberOptix/
├─ inferno/                 # Django project
│  ├─ settings.py
│  ├─ urls.py
│  ├─ wsgi.py
│  └─ asgi.py
├─ flame/                   # Core e‑commerce app
│  ├─ models.py
│  ├─ views.py
│  ├─ urls.py
│  └─ templates/
├─ requirements.txt        # v0.1 dependencies
└─ README.md
```

---

## 👥 Contributors

* **Mg Phone Moe Htet** ([2022\_miit\_cse\_041@miit.edu.mm](mailto:2022_miit_cse_041@miit.edu.mm))
* **Ma Yu Thet Htar OO** ([2022\_miit\_cse\_054@miit.edu.mm](mailto:2022_miit_cse_054@miit.edu.mm))
* **Ma Yin Myat NoeOo** ([2022\_miit\_cse\_056@miit.edu.mm](mailto:2022_miit_cse_056@miit.edu.mm))
* **Ma Ei Thu Zar New** ([2022\_miit\_cse\_058@miit.edu.mm](mailto:2022_miit_cse_058@miit.edu.mm))

**Supervisor:** Dr. Sin Thi Yar Myint, FCS, MIIT

**Instructor:** Dr. Myat Thu Zar Tun, Pro‑rector, MIIT

---

## 📄 License

MIT License © 2025 CyberOptix Team
