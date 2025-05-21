# Flask-Trading-Signal-Dashboard
This is a robust Flask-based web application designed to manage, distribute, and track forex trading signals with real-time updates and role-based access control. The system uses MongoDB for data storage and provides dedicated dashboards for Users, Admins, and Super Admins.

Key Features:

🔐 User Authentication & Role Management
Secure registration and login with password hashing. Supports three user roles: User, Admin, and Super Admin, each with distinct privileges and views.

📈 Trading Signal Management (Admin)
Admins can create new trading signals with key attributes like asset, entry price, stop loss, multiple take profit levels, and risk level.
Signals can be updated with win/loss status and automatically calculated pip differences.

👤 User Dashboard
Users can view and save trading signals. Each saved signal includes metadata like date, asset, outcome (Win/Loss/Undetermined), and pip performance.

🔄 Real-Time Signal Broadcasting
Signals are streamed in real-time to the front end using Server-Sent Events (SSE) for live updates without page refreshes.

🛠️ Admin User Management
Admins can add, edit, and delete users, and assign roles directly from the admin dashboard.

📊 Win/Loss Tracking & Pip Calculation
When win/loss status is updated for a signal, the system automatically calculates pip difference based on the asset type (JPY vs non-JPY pairs).

🧩 Modular & Extensible
Easily extendable to support additional features like notifications, analytics, or third-party API integrations.

Tech Stack:

Backend: Flask, MongoDB, PyMongo

Frontend: Jinja2 templating (HTML), Bootstrap or custom styling

Security: Werkzeug password hashing, Flask sessions

Live Streaming: Server-Sent Events (SSE)

Data Format: JSON/BSON handling with bson.json_util
![Capture d’écran (348)](https://github.com/user-attachments/assets/e0545ee2-ed2b-4e0d-8537-d8d99c91b903)
![Capture d’écran (349)](https://github.com/user-attachments/assets/ecd8bc18-b0e6-4629-90ea-41a6e51e3ec5)
![Capture d’écran (350)](https://github.com/user-attachments/assets/75475e12-d450-40bb-a8d2-b7379f85ca95)
![Capture d’écran (351)](https://github.com/user-attachments/assets/94f1de40-502c-4578-b756-95cf3ff5cefe)
![Capture d’écran (352)](https://github.com/user-attachments/assets/97d33068-ee5b-418f-ae39-02d9bdcfd90a)
![Capture d’écran (353)](https://github.com/user-attachments/assets/146f5a21-7f4e-48ed-a46e-f287ba9d44c9)
![Capture d’écran (354)](https://github.com/user-attachments/assets/35e54e92-4373-456f-8eeb-e3610ccd0242)

