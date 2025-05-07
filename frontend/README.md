# What Beats Rock? Frontend

This is the frontend implementation for the "What Beats Rock?" application, a creative game where players suggest what beats the current item.

## Features

- Clean, responsive user interface built with HTML, CSS, and vanilla JavaScript
- Game UI component to display the current item and accept user input
- Results display component to show the outcome of each comparison
- Game history visualization
- Score tracking
- Statistics modal with tabs for common comparisons and high scores

## Project Structure

- `index.html` - Main HTML structure
- `styles.css` - CSS styling for the application
- `api.js` - JavaScript service for API calls to the backend
- `app.js` - Main application logic and UI interactions
- `server.js` - Simple Node.js static file server for local development

## How to Run

### Prerequisites

- Node.js installed on your machine
- Backend server running (see the backend README for instructions)

### Running the Frontend

1. Navigate to the frontend directory:
   ```
   cd whatbeats/frontend
   ```

2. Start the static file server:
   ```
   node server.js
   ```

3. Open your browser and go to:
   ```
   http://localhost:3000
   ```

## Game Flow

1. Click "Start Game" to begin a new game session
2. The game starts with "rock" as the initial item
3. Enter what you think beats the current item in the input field
4. Submit your answer
5. If your answer beats the current item:
   - Your score increases
   - The game continues with your answer as the new current item
6. If your answer doesn't beat the current item:
   - The game ends
   - Your final score and item chain are displayed
7. Click "Play Again" to start a new game

## API Integration

The frontend connects to the backend API endpoints:

- `POST /api/start-game`: Initialize a new game session
- `POST /api/submit-comparison`: Process user input
- `GET /api/game-status/{session_id}`: Get current game status
- `POST /api/end-game`: End the current game session
- `GET /api/stats/comparisons`: Get comparison statistics
- `GET /api/stats/high-scores`: Get high scores

## Configuration

The API base URL can be configured in `api.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

Change this to match your backend server URL if needed.

## Browser Compatibility

The application is designed to work with modern browsers that support ES6+ features:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Future Enhancements

- User authentication
- Persistent user profiles
- Social sharing features
- Mobile app version
- Different game modes