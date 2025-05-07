# WhatBeats Game Flow Sequence Diagram

This diagram illustrates the interactions between the Client (user/browser), Frontend (JavaScript), and Backend (FastAPI) during a typical game session in the WhatBeats application.

```mermaid
sequenceDiagram
    participant Client as Client
    participant Frontend as Frontend (JS)
    participant Backend as Backend (FastAPI)
    
    %% Game Initialization
    Client->>Frontend: Start Game
    Frontend->>Backend: POST /api/start-game
    Backend-->>Frontend: Return Session ID & Initial Item (rock)
    Frontend-->>Client: Display Game Screen
    
    %% Game Play - Successful Comparison
    Client->>Frontend: Submit Comparison (paper beats rock)
    Frontend->>Backend: POST /api/submit-comparison
    Backend-->>Frontend: Return Success Result
    Frontend-->>Client: Update Current Item to "paper"
    
    %% Game Play - Failed Comparison
    Client->>Frontend: Submit Invalid Comparison
    Frontend->>Backend: POST /api/submit-comparison
    Backend-->>Frontend: Return Failure Result (Game Over)
    Frontend-->>Client: Display Game Over Message
    
    %% Game End
    Frontend->>Backend: POST /api/end-game
    Backend-->>Frontend: Return Final Score & Items Chain
    Frontend-->>Client: Display Game Over Screen
    
    %% View Statistics & Scoreboard
    Client->>Frontend: View Stats/Scoreboard
    Frontend->>Backend: GET /api/stats/comparisons
    Backend-->>Frontend: Return Comparison Statistics
    Frontend->>Backend: GET /api/scoreboard
    Backend-->>Frontend: Return Scoreboard Data
    Frontend-->>Client: Display Statistics & Scoreboard
```

## Key Game Flow Steps

1. **Game Initialization**
   - User starts a new game
   - Backend creates a new game session with "rock" as the initial item
   - Frontend displays the game screen with the initial item

2. **Game Play**
   - User submits what they think beats the current item
   - Backend validates if the user's input beats the current item
   - If valid, the game continues with the user's input as the new current item
   - If invalid, the game ends

3. **Game End**
   - Frontend calls the backend to end the game
   - Backend finalizes the game session and saves high scores if applicable
   - Frontend displays the game over screen with final score and items chain

4. **Statistics & Scoreboard**
   - User can view comparison statistics and the scoreboard
   - Frontend fetches the relevant data from the backend
   - Frontend displays the statistics and scoreboard to the user