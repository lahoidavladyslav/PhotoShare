Project "PhotoShare" 
About
PhotoShare is a web application that allows users to share, comment, rate, and search photos.

Usage
This project exposes many endpoints through a REST API. To access these APIs, use any API client (like Postman) or the interactive Swagger documentation available at http://localhost:8000/docs after launching the application.

Technologies
In this project we used the following technologies:

Python

FastAPI

PostgreSQL (for the database)

SQLAlchemy & Alembic (ORM and migrations)

Docker (for containerization)

Pytest & AsyncMock (for unit testing)

Cloudinary (for image hosting)

🚀 Starting
To run the PhotoShare project locally, follow these steps:

1. Clone the repository:

Bash
git clone https://github.com/lahoidavladyslav/PhotoShare
cd PhotoShare
2. Create a virtual environment and install dependencies:

Bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
3. Configure environment variables:
Create a file named .env using .env.example as a template and set up your credentials (JWT secret, Cloudinary keys, etc.).

4. Set up the database with Docker:
Run the following command to create and start a PostgreSQL Docker container:

Bash
docker run --name postgres -e POSTGRES_DB=ProjectDB -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=567234 -p 5432:5432 -d postgres
5. Install migrations in the DB:

Bash
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
6. Run the application:

Bash
uvicorn src.main:app --host localhost --port 8000 --reload
(Note: If your main.py is located in the root directory, use uvicorn main:app --host localhost --port 8000 --reload)

Access the application at http://localhost:8000 or 127.0.0.1:8000 in your web browser.

Testing
The application's business logic is covered by automated unit tests with >95% coverage. To run the tests and view the coverage report, use the following command:

Bash
pytest tests/ --cov=src.repository --cov-report=term-missing

Build and run the containers:
Start both the PostgreSQL database and the FastAPI application in the background:

docker-compose up -d --build

Install migrations in the DB:
Run Alembic migrations inside the running API container to set up your database tables:

docker exec -it photoshare_api alembic upgrade head

