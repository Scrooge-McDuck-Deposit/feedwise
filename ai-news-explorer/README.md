# AI News Explorer

## Overview
AI News Explorer is a web application designed to help users discover trending news articles and content based on their preferences. The application features an interactive bubble chart on the homepage, allowing users to visualize the popularity of various news topics. Users can search for specific topics, express their preferences through likes and dislikes, and manage their content sources.

## Features
- **Interactive Bubble Chart**: Visual representation of trending news articles based on user interactions.
- **Search Functionality**: Users can search for specific topics to find relevant news.
- **Content Recommendations**: An AI agent analyzes user preferences and recommends articles accordingly.
- **User Preferences Management**: Users can like, dislike, and exclude sources from their feed.
- **Categorized Content**: Users can explore news by categories if they are unsure of what to read.
- **Brainless Mode**: A fun section displaying trending memes and light-hearted content.

## Project Structure
```
ai-news-explorer
├── src
│   ├── app.py
│   ├── config.py
│   ├── agent
│   │   ├── __init__.py
│   │   ├── recommender.py
│   │   ├── trend_analyzer.py
│   │   └── preference_engine.py
│   ├── feeds
│   │   ├── __init__.py
│   │   ├── rss_parser.py
│   │   ├── social_scraper.py
│   │   └── source_registry.py
│   ├── components
│   │   ├── __init__.py
│   │   ├── home.py
│   │   ├── categories.py
│   │   ├── brainless.py
│   │   └── preferences.py
│   ├── charts
│   │   ├── __init__.py
│   │   └── bubble_chart.py
│   ├── styles
│   │   └── custom.css
│   └── utils
│       ├── __init__.py
│       ├── session_manager.py
│       ├── trend_scoring.py
│       └── source_classifier.py
├── data
│   ├── sources.json
│   └── categories.json
├── tests
│   ├── __init__.py
│   ├── test_agent.py
│   ├── test_feeds.py
│   ├── test_charts.py
│   └── test_utils.py
├── .streamlit
│   └── config.toml
├── requirements.txt
└── README.md
```

## Content Sources
1. **Social Media**:
   - Twitter (X)
   - Facebook
   - Instagram
   - TikTok

2. **News Websites**:
   - Ansa
   - Il Post
   - Hardware Upgrade
   - Punto Informatico
   - Le Scienze

3. **Blogs and Online Magazines**:
   - TechCrunch
   - Wired
   - The Verge
   - Medium

4. **Video Platforms**:
   - YouTube
   - Vimeo

5. **Podcasts**:
   - Spotify
   - Apple Podcasts

6. **RSS Feeds**:
   - Various news outlets providing RSS feeds for real-time updates.

## Installation
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ai-news-explorer.git
   cd ai-news-explorer
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   streamlit run src/app.py
   ```

## Usage
- Upon launching the application, users will see the homepage with trending news displayed in a bubble chart.
- Users can search for specific topics using the search bar.
- By clicking on news articles, users can express their preferences through likes and dislikes.
- Users can navigate to different sections, including categories and the brainless mode for memes.

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License
This project is open-source and available under the MIT License.