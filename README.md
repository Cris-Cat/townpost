# 📌 CityBoard

**CityBoard** is a community-driven, moderated event discovery and submission platform built with Django. It allows users to submit local events, notices, and happenings, which are then reviewed by administrators before going live. The platform features location-based filtering, secure image handling, and a clean, cork-board-inspired UI.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Features

- **Community Submissions** — Users can submit events, notices, and multi-day events.
- **Moderation Workflow** — All submissions and edits enter a `Pending` state and require Admin approval.
- **Location Filtering** — Filter events by Country and City using a lightweight JSON-based location system.
- **Secure Image Handling** — Automatic EXIF data stripping, image resizing, and format conversion for privacy and performance.
- **Spam Protection** — Integrated [Altcha](https://altcha.org/) CAPTCHA for all public forms.
- **Passwordless Editing** — Users can edit their posts later using a secure, time-limited secret token sent via URL.

---

## 🛠️ Tech Stack

| Component   | Technology                                                  |
| ----------- | ----------------------------------------------------------- |
| Backend     | Python, Django                                              |
| Frontend    | HTML5, CSS3, Vanilla JavaScript, Alpine.js                  |
| Database    | SQLite (default, easily swappable to PostgreSQL/MySQL)      |
| Security    | Altcha (Proof-of-work CAPTCHA)                              |
| Image Processing | Pillow                                                 |

---

## 📁 Folder Structure

```text
cityboard/
├── data/
│   └── locations.json          # JSON file containing countries and cities
├── events/                     # Main Django application
│   ├── migrations/             # Database migrations
│   ├── templates/events/       # App-specific HTML templates
│   ├── admin.py                # Admin panel configurations
│   ├── context_processors.py   # Global context (location filters)
│   ├── forms.py                # Form validations and logic
│   ├── models.py               # Database models (Event, Category, etc.)
│   ├── utils.py                # Image processing & JSON reader utilities
│   └── views.py                # View logic and routing
├── media/                      # User-uploaded files (e.g., events/post_12/image.jpg)
├── static/                     # Global CSS, JS, and static assets
├── templates/                  # Base templates (e.g., base.html)
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## 🚀 Installation & Setup

Follow these steps to get CityBoard running on your local machine.

### 1. Prerequisites

Make sure you have **Python 3.8+** and **pip** installed.

### 2. Clone the Repository

```bash
git clone https://github.com/your-username/cityboard.git
cd cityboard
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

```bash
# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** If you don't have a `requirements.txt` yet, run `pip freeze > requirements.txt` after installing `django`, `Pillow`, and `altcha`.

### 5. Apply Migrations

```bash
python manage.py migrate
```

### 6. Create a Superuser (Admin)

```bash
python manage.py createsuperuser
```

### 7. Run the Development Server

```bash
python manage.py runserver
```

Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

## ⚙️ Configuration & Settings

### Environment Variables

In a production environment, you should use environment variables for sensitive settings. Update `settings.py` or use a `.env` file for:

- `SECRET_KEY` — Your Django secret key.
- `DEBUG` — Set to `False` in production.
- `ALLOWED_HOSTS` — Your domain name.
- `ALTCHA_HMAC_SECRET` — Your secret key for Altcha CAPTCHA verification.

### Media & Static Files

Ensure your `settings.py` has the correct paths for media and static files so images and CSS load correctly:

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
```

---

## 🛡️ Admin & Moderation Settings

CityBoard relies heavily on the Django Admin panel for content moderation.

### Access Admin

Go to [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) and log in with your superuser credentials.

### Manage Categories

Add or edit event categories (e.g., Music, Sports, Notices) and assign emojis.

### Approve Events

1. Navigate to **Events**.
2. Filter by **Status: Pending**.
3. Open an event, change the **Status** dropdown to `Approved`, and click **Save**.

> **Note:** If there are pending edits on an approved event, saving as `Approved` will automatically apply the pending changes to the live post.

### Manage Images

You can view, reorder, or delete images directly from the Event admin page using the inline image manager.

---

## 📄 File Locations & Formats

### 1. Location Data (`data/locations.json`)

CityBoard uses a lightweight JSON file instead of database tables for locations to improve performance.

**Format:** The file must be a dictionary where keys are country names and values are arrays of city names.

```json
{
  "United States": ["New York", "Los Angeles", "Chicago"],
  "United Kingdom": ["London", "Manchester", "Edinburgh"],
  "Germany": ["Berlin", "Munich", "Hamburg"]
}
```

If you update this file, simply restart the Django server for the changes to reflect in the dropdowns.

### 2. Image Uploads (`media/events/`)

When a user uploads images, they are processed and saved in the `media/` directory.

- **Path Format:** `media/events/post_{event_id}/{filename}.jpg`
- **Processing:** Upon upload, the `utils.py` script automatically:
  1. Verifies the file is a valid image.
  2. Strips all EXIF/GPS metadata (protecting user privacy).
  3. Resizes the image to a maximum of `1024x1024` pixels while maintaining aspect ratio.
  4. Converts and saves the image as a high-quality JPEG to save storage space.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. **Fork** the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a **Pull Request**

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.