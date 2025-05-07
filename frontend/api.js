/**
 * API Service for the "What Beats Rock?" game
 * Handles all communication with the backend API
 */

// Base URL for API requests - change this to match your backend URL
// This should point to where your FastAPI backend is running
const API_BASE_URL = 'http://localhost:8000';

// API endpoints
const API_ENDPOINTS = {
    START_GAME: '/api/start-game',
    SUBMIT_COMPARISON: '/api/submit-comparison',
    GAME_STATUS: '/api/game-status', // Note: /{session_id} is appended in the getGameStatus method
    END_GAME: '/api/end-game',
    COMPARISONS: '/api/stats/comparisons',
    HIGH_SCORES: '/api/stats/high-scores',
    SCOREBOARD: '/api/scoreboard',
    SCOREBOARD_STATS: '/api/scoreboard/stats',
    REPORT_COMPARISON: '/api/report-comparison',
    // Admin endpoints
    ADMIN_REPORTS: '/api/admin/reports',
    ADMIN_UPDATE_COMPARISON: '/api/admin/comparisons',
    ADMIN_UPDATE_REPORT_STATUS: '/api/admin/reports' // Note: /{report_id}/status is appended in the method
};

/**
 * API service object with methods for each API endpoint
 */
const apiService = {
    /**
     * Start a new game session
     * @returns {Promise} Promise resolving to the start game response
     */
    /**
     * Start a new game session
     * This calls the backend to create a new game session starting with "rock"
     * No parameters are needed for this request
     *
     * @returns {Promise} Promise resolving to the start game response with session_id, current_item, and message
     */
    startGame: async function() {
        try {
            const response = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.START_GAME}`);
            return response.data;
        } catch (error) {
            console.error('Error starting game:', error);
            throw this.handleError(error);
        }
    },

    /**
     * Submit a comparison to the backend
     * @param {string} sessionId - The current game session ID
     * @param {string} currentItem - The current item in the game
     * @param {string} userInput - The user's input for what beats the current item
     * @returns {Promise} Promise resolving to the comparison response
     */
    /**
     * Submit a comparison to the backend
     * This is the main game action where the user suggests what beats the current item
     * The backend will determine if the suggestion is valid and return the result
     *
     * @param {string} sessionId - The current game session ID
     * @param {string} currentItem - The current item in the game
     * @param {string} userInput - The user's input for what beats the current item
     * @returns {Promise} Promise resolving to the comparison response with result, description, emoji, etc.
     */
    submitComparison: async function(sessionId, currentItem, userInput) {
        try {
            const response = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.SUBMIT_COMPARISON}`, {
                session_id: sessionId,
                current_item: currentItem,
                user_input: userInput
            });
            return response.data;
        } catch (error) {
            console.error('Error submitting comparison:', error);
            throw this.handleError(error);
        }
    },

    /**
     * Get the current game status
     * @param {string} sessionId - The game session ID
     * @returns {Promise} Promise resolving to the game status response
     */
    getGameStatus: async function(sessionId) {
        try {
            const response = await axios.get(`${API_BASE_URL}${API_ENDPOINTS.GAME_STATUS}/${sessionId}`);
            return response.data;
        } catch (error) {
            console.error('Error getting game status:', error);
            throw this.handleError(error);
        }
    },

    /**
     * End the current game session
     * @param {string} sessionId - The game session ID
     * @returns {Promise} Promise resolving to the end game response
     */
    endGame: async function(sessionId) {
        try {
            const response = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.END_GAME}`, {
                session_id: sessionId
            });
            return response.data;
        } catch (error) {
            console.error('Error ending game:', error);
            throw this.handleError(error);
        }
    },

    /**
     * Get comparison statistics
     * @param {number} limit - Maximum number of comparisons to return
     * @returns {Promise} Promise resolving to the comparison stats response
     */
    getComparisonStats: async function(limit = 20) {
        try {
            // Add explicit headers for CORS
            const config = {
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                // Enable withCredentials for CORS with credentials
                withCredentials: true
            };
            
            const response = await axios.get(
                `${API_BASE_URL}${API_ENDPOINTS.COMPARISONS}?limit=${limit}`,
                config
            );
            return response.data;
        } catch (error) {
            console.error('Error getting comparison stats:', error);
            // Log more detailed error information
            if (error.response) {
                console.error('Response data:', error.response.data);
                console.error('Response status:', error.response.status);
                console.error('Response headers:', error.response.headers);
            }
            throw this.handleError(error);
        }
    },

    /**
     * Get high scores (legacy method)
     * @param {number} limit - Maximum number of high scores to return
     * @returns {Promise} Promise resolving to the high scores response
     */
    getHighScores: async function(limit = 10) {
        try {
            const response = await axios.get(`${API_BASE_URL}${API_ENDPOINTS.HIGH_SCORES}?limit=${limit}`);
            return response.data;
        } catch (error) {
            console.error('Error getting high scores:', error);
            throw this.handleError(error);
        }
    },

    /**
     * Get scoreboard data with pagination, sorting, and filtering
     * @param {Object} options - Options for the scoreboard request
     * @param {number} options.page - Page number (default: 1)
     * @param {number} options.pageSize - Number of items per page (default: 10)
     * @param {string} options.sortBy - Field to sort by: 'score' or 'created_at' (default: 'score')
     * @param {string} options.sortDirection - Sort direction: 'asc' or 'desc' (default: 'desc')
     * @param {number} options.minScore - Minimum score filter (optional)
     * @param {number} options.maxScore - Maximum score filter (optional)
     * @param {string} options.dateFrom - Start date filter in ISO format (optional)
     * @param {string} options.dateTo - End date filter in ISO format (optional)
     * @returns {Promise} Promise resolving to the scoreboard response
     */
    getScoreboard: async function(options = {}) {
        try {
            // Set default values
            const params = {
                page: options.page || 1,
                page_size: options.pageSize || 10,
                sort_by: options.sortBy || 'score',
                sort_direction: options.sortDirection || 'desc'
            };
            
            // Add optional filters if provided
            if (options.minScore !== undefined) params.min_score = options.minScore;
            if (options.maxScore !== undefined) params.max_score = options.maxScore;
            if (options.dateFrom) params.date_from = options.dateFrom;
            if (options.dateTo) params.date_to = options.dateTo;
            
            const response = await axios.get(`${API_BASE_URL}${API_ENDPOINTS.SCOREBOARD}`, { params });
            return response.data;
        } catch (error) {
            console.error('Error getting scoreboard data:', error);
            throw this.handleError(error);
        }
    },
    
    /**
     * Get scoreboard statistics
     * @returns {Promise} Promise resolving to the scoreboard stats response
     */
    getScoreboardStats: async function() {
        try {
            console.log('Fetching scoreboard stats from:', `${API_BASE_URL}${API_ENDPOINTS.SCOREBOARD_STATS}`);
            const response = await axios.get(`${API_BASE_URL}${API_ENDPOINTS.SCOREBOARD_STATS}`);
            console.log('Scoreboard stats API response:', response.data);
            return response.data;
        } catch (error) {
            console.error('Error getting scoreboard stats:', error);
            // Log more detailed error information
            if (error.response) {
                console.error('Response data:', error.response.data);
                console.error('Response status:', error.response.status);
                console.error('Response headers:', error.response.headers);
            }
            throw this.handleError(error);
        }
    },

    /**
     * Handle API errors
     * @param {Error} error - The error object
     * @returns {Error} A formatted error object with additional properties for special error types
     */
    /**
     * Report a disputed comparison
     * @param {string} sessionId - The current game session ID
     * @param {string} item1 - The current item in the game
     * @param {string} item2 - The user's input that was rejected
     * @param {string} reason - Optional reason for the report
     * @returns {Promise} Promise resolving to the report response
     */
    reportComparison: async function(sessionId, item1, item2, reason = null) {
        try {
            const response = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.REPORT_COMPARISON}`, {
                session_id: sessionId,
                item1: item1,
                item2: item2,
                reason: reason
            });
            return response.data;
        } catch (error) {
            console.error('Error reporting comparison:', error);
            throw this.handleError(error);
        }
    },

    handleError: function(error) {
        if (error.response) {
            // The request was made and the server responded with a status code
            // that falls out of the range of 2xx
            const message = error.response.data.detail || 'An error occurred';
            
            // Check for item already used error (422 status code)
            if (error.response.status === 422 && error.response.data.code === 'ITEM_ALREADY_USED') {
                const customError = new Error(message);
                customError.code = 'ITEM_ALREADY_USED';
                return customError;
            }
            
            return new Error(message);
        } else if (error.request) {
            // The request was made but no response was received
            return new Error('No response from server. Please check your connection.');
        } else {
            // Something happened in setting up the request that triggered an Error
            return new Error('Error setting up request. Please try again.');
        }
    },

    /**
     * Get reports for admin view with pagination, sorting, and filtering
     * @param {Object} options - Options for the admin reports request
     * @param {number} options.page - Page number (default: 1)
     * @param {number} options.pageSize - Number of items per page (default: 10)
     * @param {Array} options.statusFilters - Optional array of statuses to filter by
     * @param {string} options.sortBy - Field to sort by (default: 'created_at')
     * @param {string} options.sortDirection - Sort direction: 'asc' or 'desc' (default: 'desc')
     * @returns {Promise} Promise resolving to the admin reports response
     */
    getAdminReports: async function(options = {}) {
        try {
            // Set default values
            const params = {
                page: options.page || 1,
                page_size: options.pageSize || 10,
                sort_by: options.sortBy || 'created_at',
                sort_direction: options.sortDirection || 'desc'
            };
            
            // Add optional status filters if provided
            if (options.statusFilters && options.statusFilters.length > 0) {
                params.status = options.statusFilters.join(',');
            }
            
            const response = await axios.get(`${API_BASE_URL}${API_ENDPOINTS.ADMIN_REPORTS}`, { params });
            return response.data;
        } catch (error) {
            console.error('Error getting admin reports:', error);
            throw this.handleError(error);
        }
    },
    
    /**
     * Update a comparison based on admin corrections
     * @param {string} item1 - The first item in the comparison
     * @param {string} item2 - The second item in the comparison
     * @param {boolean} item1Wins - Whether the first item beats the second
     * @param {boolean} item2Wins - Whether the second item beats the first
     * @param {string} description - A brief explanation of the result
     * @param {string} emoji - A relevant emoji for the comparison
     * @returns {Promise} Promise resolving to the updated comparison
     */
    updateComparison: async function(item1, item2, item1Wins, item2Wins, description, emoji) {
        try {
            const response = await axios.put(`${API_BASE_URL}${API_ENDPOINTS.ADMIN_UPDATE_COMPARISON}`, {
                item1: item1,
                item2: item2,
                item1_wins: item1Wins,
                item2_wins: item2Wins,
                description: description,
                emoji: emoji
            });
            return response.data;
        } catch (error) {
            console.error('Error updating comparison:', error);
            throw this.handleError(error);
        }
    },
    
    /**
     * Update the status of a report
     * @param {string} reportId - The unique report ID
     * @param {string} status - The new status (e.g., "pending", "reviewed", "approved", "rejected")
     * @returns {Promise} Promise resolving to the updated report
     */
    updateReportStatus: async function(reportId, status) {
        try {
            const response = await axios.put(`${API_BASE_URL}${API_ENDPOINTS.ADMIN_UPDATE_REPORT_STATUS}/${reportId}/status`, {
                status: status
            });
            return response.data;
        } catch (error) {
            console.error('Error updating report status:', error);
            throw this.handleError(error);
        }
    }
};