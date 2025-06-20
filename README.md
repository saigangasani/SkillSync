# SkillSync

A Flask-based web application for skill assessment and team matching. The application allows users to upload their resumes, extract skills, and get matched with compatible team members.

## Features

- **User Authentication**: Login system with UFID and username
- **Resume Upload**: Upload .docx files to extract skills
- **Skill Assessment**: AI-powered skill extraction and verification
- **Team Matching**: Algorithm to match users based on skill compatibility
- **Rating System**: Track user ratings and selected skills

## Tech Stack

- **Backend**: Flask, SQLAlchemy
- **Database**: SQLite
- **AI Integration**: OpenAI API for skill extraction
- **File Processing**: docx2txt for document parsing
- **Deployment**: Gunicorn (Heroku ready)

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd SkillSync
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   Create a `.env` file in the root directory:

```
api_key=your_openai_api_key_here
```

5. Run the application:

```bash
python final.py
```

The application will be available at `http://localhost:5000`

## Project Structure

```
SkillSync/
├── final.py              # Main application file
├── requirements.txt      # Python dependencies
├── Procfile             # Heroku deployment configuration
├── .env                 # Environment variables (not tracked)
├── uploads/             # File upload directory
└── var/                 # Database storage
```

## Usage

1. **Login**: Enter your name and UFID to access the system
2. **Upload Resume**: Upload a .docx file containing your skills and experience
3. **Skill Extraction**: The system will extract skills from your resume
4. **Skill Verification**: Answer questions to verify your skill level
5. **Team Matching**: Get matched with compatible team members

## API Endpoints

- `GET/POST /` - Login page
- `GET/POST /upload` - File upload and skill extraction
- `POST /submit_skills` - Submit selected skills for assessment
- `POST /feedback_skills` - Submit skill verification answers
- `GET /match_teams` - Generate team matches
- `GET /teams` - View all teams

## Database Models

- **User**: Stores user information (UFID, username)
- **Rating**: Stores user ratings and selected skills
- **Team**: Stores team information and members

## Deployment

The application is configured for Heroku deployment with the included `Procfile`. Simply push to Heroku and the application will be deployed automatically.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
