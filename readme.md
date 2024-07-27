### Setup Instructions

1. **Clone the Repository**

   Clone the project repository:

   ```bash
   git clone https://github.com/dev-r4hul/eld-app.git
   cd eld-app
   ```

2. **Create a Virtual Environment**

   Create a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**

   Install the requirements:

   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**

   - Copy the example environment file to create your own `.env` file:

     ```bash
     cp .env.example .env
     ```

   - Open the `.env` file and update the following configuration variables as needed:

     ```plaintext
     PROLOG_CLIENT_ID='YOUR_PROLOG_CLIENT_ID'
     PROLOG_CLIENT_SECRET='YOUR_PROLOG_CLIENT_SECRET'
     ```

5. **Database Setup**

     ```bash
     python manage.py makemigrations
     python manage.py migrate
     ```

6. **Run the Development Server**

   Start the Django development server:

   ```bash
   python manage.py runserver
   ```

   Access the application in your web browser at `http://localhost:8000`.