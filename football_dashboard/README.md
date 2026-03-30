# Football Academy Management System

A comprehensive full-stack web application for managing football academies, schools, clubs, and talent scouting in Rwanda. Built with Python Flask backend and vanilla HTML/CSS/JS frontend.

![Football Academy](https://img.shields.io/badge/Football-Academy-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

### Multi-Role Access Control
- **School**: Manage school football team players and view performance
- **Academy**: Handle academy players, training schedules, and development
- **Club**: Club management, match scheduling, player lineup, and photo ML upload
- **Scout**: Find talent across all entities, create reports, manage favorites
- **FERWAFA**: View all players, clubs, academies - national oversight
- **Super Admin**: Full system access, user management, settings

### Core Functionality
- **Player Management**: Add, edit, delete players with auto-generated registration numbers
- **Match Management**: Schedule matches, set lineups, track results
- **Statistics**: Track goals, assists, minutes played, cards
- **AI Performance Analytics**: Real-time tracking of distance covered, top speed, and sprint count
- **Live Updates**: Data refreshes and AI metric recalculations
- **Machine Learning**: YOLOv8-based player identification and tracking
- **GPS Integration**: Placeholder and historical GPS tracking support
- **Responsive Design**: High-fidelity dark mode interface for mobile and desktop

## Project Structure

```
football_dashboard/
├── backend/                  # Python Flask backend
│   ├── app.py              # Main Flask application
│   ├── routes/
│   │   ├── auth.py         # Authentication routes
│   │   ├── players.py      # Players CRUD
│   │   ├── matches.py      # Matches CRUD
│   │   ├── stats.py        # Statistics routes
│   │   └── dashboard.py    # Dashboard data
│   ├── models/
│   │   ├── user_model.py   # User database operations
│   │   └── player_model.py # Player database operations
│   └── utils/
│       └── helpers.py      # Utility functions
├── frontend/               # HTML/CSS/JS frontend
│   ├── index.html          # Login page
│   ├── dashboard.html      # Main dashboard
│   ├── school.html         # School dashboard
│   ├── academy.html        # Academy dashboard
│   ├── club.html           # Club dashboard
│   ├── scout.html          # Scout dashboard
│   ├── ferwafa.html       # FERWAFA dashboard
│   ├── superadmin.html     # Admin dashboard
│   ├── css/
│   │   └── style.css       # Professional blue/white theme
│   └── js/
│       └── main.js         # Frontend JavaScript
├── database/
│   └── football_dashboard.sql  # MySQL schema
└── README.md               # This file
```

## Prerequisites

### Backend Requirements
- Python 3.8+
- MySQL 5.7+ (or XAMPP)
- pip

### Frontend Requirements
- Modern web browser (Chrome, Firefox, Edge)
- Internet connection for Font Awesome icons

## Installation

### 1. Database Setup (MySQL/XAMPP)

1. Start XAMPP and ensure MySQL is running
2. Open phpMyAdmin or MySQL Workbench
3. Import the database schema:

```bash
mysql -u root -p < database/football_dashboard.sql
```

Or via phpMyAdmin:
- Navigate to http://localhost/phpmyadmin
- Create a new database named `football_dashboard`
- Import the SQL file

### 2. Backend Setup

```bash
# Navigate to backend directory
cd football_dashboard/backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file for configuration
# Copy values from .env.example if provided, or set:
# DB_HOST=localhost
# DB_USER=root
# DB_PASSWORD=
# DB_NAME=football_dashboard
# SECRET_KEY=your-secret-key-here
# JWT_SECRET_KEY=your-jwt-secret-here

# Run database migrations (Crucial for AI metrics)
python run_safe_migration.py

# Run the server
python app.py
```

The backend will run on `http://localhost:5000`

### 3. Frontend Setup

Simply open the HTML files in a web browser:

```bash
# Option 1: Open directly
# Navigate to football_dashboard/frontend/index.html

# Option 2: Use a simple HTTP server
cd football_dashboard/frontend
python -m http.server 8000
# Then open http://localhost:8000
```

## Default Login Credentials

| Username  | Password   | Role        |
|-----------|------------|-------------|
| admin     | password123 | superadmin  |
| ferwafa   | password123 | ferwafa     |
| school1   | password123 | school      |
| academy1  | password123 | academy     |
| club1     | password123 | club        |
| scout1    | password123 | scout       |

**Note**: Passwords are hashed using bcrypt. The sample password for all accounts is `password123`.

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - Register new user
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user

### Players
- `GET /api/players` - Get all players
- `GET /api/players/<id>` - Get player by ID
- `POST /api/players` - Create new player
- `PUT /api/players/<id>` - Update player
- `DELETE /api/players/<id>` - Delete player
- `POST /api/players/upload-photo` - Upload player photo for ML

### Matches
- `GET /api/matches` - Get all matches
- `GET /api/matches/<id>` - Get match by ID
- `POST /api/matches` - Create new match
- `PUT /api/matches/<id>` - Update match
- `DELETE /api/matches/<id>` - Delete match
- `POST /api/matches/<id>/lineup` - Set match lineup

### Statistics
- `GET /api/stats/player/<id>` - Get player statistics
- `GET /api/stats/top-scorers` - Get top scorers
- `GET /api/stats/top-assists` - Get top assists
- `GET /api/stats/live` - Get live statistics

### Dashboard
- `GET /api/dashboard/overview` - Get dashboard overview
- `GET /api/dashboard/recent-matches` - Get recent match results
- `GET /api/dashboard/upcoming-matches` - Get upcoming matches
- `GET /api/dashboard/performance` - Get performance data

## Database Schema

### Key Tables

- **users**: System users with role-based access
- **players**: Player information with unique registration numbers
- **matches**: Match scheduling and results
- **statistics**: Player match statistics
- **schools/academies/clubs**: Entity management
- **match_lineups**: Starting XI and bench players
- **training_sessions**: Training schedules
- **gps_data**: GPS tracking placeholder
- **ml_processing**: Machine learning processing queue

### Auto-Generated Registration Numbers

- School players: `SCH-{entity_id}-{unique_id}`
- Academy players: `ACA-{entity_id}-{unique_id}`
- Club players: `CLB-{entity_id}-{unique_id}`

### Live Updates

The system includes a scheduled event that updates match status every 15 minutes:
- Scheduled → Live (when match starts)
- Live → Completed (after 90 minutes)

## Machine Learning Integration

### Photo Upload for Player Identification

The club role includes photo upload functionality for player recognition:

1. Navigate to Club Dashboard → Photo ML section
2. Upload player photos (drag & drop or browse)
3. System processes images using CPU-friendly pipelines
4. Results show face detection status and confidence scores
5. Photos are deleted after processing (not stored in database)

**Note**: Actual ML implementation requires additional libraries like OpenCV or face_recognition.

## GPS Integration (Placeholder)

The `gps_data` table is ready for future GPS tracking integration:
- Store latitude/longitude data
- Track player movement during training
- Performance metrics from GPS devices
- Multiple camera support ready

## Role-Based UI

Each role sees a customized interface:

| Feature              | School | Academy | Club | Scout | FERWAFA | Admin |
|---------------------|:------:|:-------:|:----:|:-----:|:-------:|:-----:|
| View Players        |   ✓    |    ✓    |  ✓   |   ✓   |    ✓    |   ✓   |
| Add/Edit Players    |   ✓    |    ✓    |  ✓   |       |         |   ✓   |
| Manage Matches      |        |         |  ✓   |       |    ✓    |   ✓   |
| Set Lineup          |        |         |  ✓   |       |         |   ✓   |
| Upload Photos (ML)  |        |         |  ✓   |       |         |   ✓   |
| View All Entities   |        |         |      |   ✓   |    ✓    |   ✓   |
| Manage Users        |        |         |      |       |         |   ✓   |
| System Settings     |        |         |      |       |         |   ✓   |

## Technologies Used

### Backend
- **Flask**: Web framework
- **Flask-JWT-Extended**: JWT authentication
- **Flask-Bcrypt**: Password hashing
- **Flask-CORS**: Cross-origin support
- **MySQL Connector**: Database connection

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Custom styling with CSS variables
- **Vanilla JavaScript**: No framework dependencies
- **Font Awesome**: Icons

### Database
- **MySQL**: Relational database
- **Stored Procedures**: Business logic
- **Events**: Scheduled tasks
- **Views**: Data aggregation

## Configuration

### Backend Configuration

Update `app.py` with your database credentials:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',  # Empty for XAMPP default
    'database': 'football_dashboard',
    'charset': 'utf8mb4'
}
```

### Environment Variables (Optional)

```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=football_dashboard
export SECRET_KEY=your-secret-key
export JWT_SECRET_KEY=your-jwt-secret
```

## Development

### Running the Application

```bash
# Terminal 1: Start backend
cd football_dashboard/backend
python app.py

# Terminal 2: Start frontend server (optional)
cd football_dashboard/frontend
python -m http.server 8000
```

Access the application at:
- Frontend: http://localhost:8000 (or open HTML files directly)
- Backend API: http://localhost:5000/api

### Adding New Features

1. **Backend Routes**: Add new route files in `backend/routes/`
2. **Database Tables**: Add new tables in `database/football_dashboard.sql`
3. **Frontend Pages**: Create new HTML files in `frontend/`
4. **Styles**: Add custom CSS to `frontend/css/style.css`
5. **JavaScript**: Add functions to `frontend/js/main.js`

## Security Considerations

- Passwords are hashed using bcrypt
- JWT tokens for authentication
- Role-based access control on all endpoints
- SQL injection prevention via parameterized queries
- CORS configured for frontend origin
- Audit logging for sensitive actions

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check MySQL is running
   - Verify credentials in `app.py`
   - Ensure database exists

2. **Token Expiration**
   - Login again to get new token
   - Tokens expire after 24 hours

3. **CORS Errors**
   - Ensure frontend is served from allowed origin
   - Check Flask-CORS configuration

4. **Page Not Found**
   - Ensure you're logged in
   - Check browser console for errors

## License

MIT License

Copyright (c) 2024 Football Academy Management System

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Support

For issues and feature requests, please create an issue in the project repository.

---

Built with ❤️ for Rwandan Football Development
