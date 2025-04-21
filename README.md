# News Website

A Flask-based news website that fetches and displays news articles from NewsAPI.

## Features

- Fetch top headlines from NewsAPI
- Filter news by categories
- Responsive design
- Clean and modern UI

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your NewsAPI key:
   ```
   NEWS_API_KEY=your_api_key_here
   ```
   You can get a free API key from [NewsAPI](https://newsapi.org/)

4. Run the application:
   ```bash
   python app.py
   ```

5. Open your browser and navigate to `http://localhost:5000` 

## Project Structure

- `app.py` - Main Flask application
- `templates/` - HTML templates
  - `base.html` - Base template
  - `home.html` - Home page
  - `news.html` - News listing page
- `static/css/` - CSS styles
  - `style.css` - Main stylesheet
- `.env` - Environment variables
- `requirements.txt` - Python dependencies

## API Integration

The application uses NewsAPI to fetch news articles. The API is called in the following routes:
- `/news` - Fetches top headlines
- `/categories` - Fetches news by categories.

## Error Handling

The application includes basic error handling for API requests. If the API call fails, an empty list of articles will be returned and displayed to the user. 

by - Mayank Malviya