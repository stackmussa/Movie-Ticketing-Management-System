# Movie Ticketing Management System

> A robust, high-performance web application demonstrating the capabilities of FastAPI and Streamlit. This system provides a comprehensive platform for users to discover movies, book tickets securely, and interact with community reviews.

## Architecture Overview
The application is built using a modern, decoupled architecture:
* **Backend framework**: FastAPI
* **Frontend framework**: Streamlit (with custom HTML/CSS rendering)
* **Database Engine**: Microsoft SQL Server
* **Authentication mechanism**: JWT with Argon2 password hashing

## Core Capabilities

### Dynamic Movie Discovery
The primary dashboard lists upcoming shows tailored to the user's selected city. It features an advanced predictive search bar for instantaneous title lookups. Users can filter the database by specific genres or select exact show dates via a calendar interface. The system integrates directly with the OMDb API, automatically fetching and displaying critical reception data, including IMDb and Rotten Tomatoes ratings.

### Interactive Seating & Booking Engine
The booking interface leverages a visual seat map, allowing users to choose across tiered seating categories (Platinum, Gold, and Standard). To maintain transaction integrity, the engine enforces maximum ticket limits per order and actively cross-references the user's existing schedule to prevent overlapping bookings. Upon seat selection, a strict five-minute session timer holds the reservation until the simulated payment is finalized.

### Community Reviews
A dedicated review module aggregates user feedback across the entire platform. Users can submit star ratings and detailed written reviews, as well as engage in threaded conversations by replying to others. The backend strictly enforces authorization rules, guaranteeing that users can only manage and delete content they own.

### Secure Order Management
Authenticated users gain access to their complete booking history and the status of pending transactions. The system allows users to securely cancel active orders, optionally capturing a predefined or custom cancellation reason for analytical purposes.

## Project Structure

```text
├── app/
│   ├── config.py
│   ├── jwt_Security.py
│   ├── logger.py
│   ├── passHash.py
│   └── queries.py
├── backend/
│   ├── api.py
│   ├── schema.py
│   └── routers/
│       ├── auth.py
│       ├── bookings.py
│       └── shows.py
├── DB/
│   └── Schema.sql
├── Frontend/
│   ├── Booking.py
│   ├── components.py
│   ├── Dashboard.py
│   ├── Login.py
│   ├── MyOrders.py
│   ├── Payment.py
│   ├── Register.py
│   ├── Reviews.py
│   └── UpcomingShows.py
├── .env
├── .gitignore
├── app.log
├── main.py
├── readme.md
├── requirements.txt
└── secret.py
```

## Installation and Setup

### 1. Database Initialization
Ensure that SQL Server is running locally on your machine with a database named `TicketSystem`. The FastAPI backend is configured to automatically construct the required tables and schema upon the initial startup.

### 2. Environment Configuration
Create a `.env` file in the root directory of the project. Define the required environment variables as shown below:

```env
JSON_SK=your_secure_secret_key_here
OMDB_API_KEY=your_omdb_api_key_here
```
*Note: The `OMDB_API_KEY` is required to fetch real-time movie ratings on the dashboard. You can obtain a free key from the OMDb website.*

### 3. Dependency Installation
Install the necessary Python packages using pip:

```bash
pip install -r requirements.txt
```

### 4. Launching the Application
The system requires both the backend and frontend to be running simultaneously in separate terminal instances.

Start the FastAPI backend server:
```bash
uvicorn app.api:app --reload
```

In a new terminal window, initialize the Streamlit frontend:
```bash
streamlit run main.py
```

The application will automatically open in your default web browser once the Streamlit server boots up.
