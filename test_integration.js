/**
 * Integration Test Script for What Beats Rock? Application
 * 
 * This script tests the integration between the frontend and backend
 * by making API calls to verify that all endpoints are working correctly.
 * 
 * Usage: node test_integration.js
 */

const axios = require('axios');

// Configuration
const API_BASE_URL = 'http://localhost:8000';
const API_ENDPOINTS = {
    START_GAME: '/api/start-game',
    SUBMIT_COMPARISON: '/api/submit-comparison',
    GAME_STATUS: '/api/game-status', // Note: /{session_id} is appended in the getGameStatus method
    END_GAME: '/api/end-game',
    COMPARISONS: '/api/stats/comparisons',
    HIGH_SCORES: '/api/stats/high-scores'
};

// Test cases
const tests = [
    {
        name: 'Health Check',
        fn: async () => {
            const response = await axios.get(`${API_BASE_URL}/health`);
            return response.data.status === 'ok';
        }
    },
    {
        name: 'Start Game',
        fn: async () => {
            const response = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.START_GAME}`);
            const data = response.data;
            return data.session_id && data.current_item === 'rock' && data.message;
        }
    },
    {
        name: 'Submit Comparison',
        fn: async () => {
            // First start a game to get a session ID
            const startResponse = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.START_GAME}`);
            const sessionId = startResponse.data.session_id;
            
            // Then submit a comparison
            const response = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.SUBMIT_COMPARISON}`, {
                session_id: sessionId,
                current_item: 'rock',
                user_input: 'paper'
            });
            
            const data = response.data;
            return data.result === true && data.next_item === 'paper' && data.score === 1;
        }
    },
    {
        name: 'Game Status',
        fn: async () => {
            // First start a game to get a session ID
            const startResponse = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.START_GAME}`);
            const sessionId = startResponse.data.session_id;
            
            // Then get the game status
            const response = await axios.get(`${API_BASE_URL}${API_ENDPOINTS.GAME_STATUS}/${sessionId}`);
            
            const data = response.data;
            return data.session_id === sessionId && data.current_item === 'rock' && data.is_active === true;
        }
    },
    {
        name: 'End Game',
        fn: async () => {
            // First start a game to get a session ID
            const startResponse = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.START_GAME}`);
            const sessionId = startResponse.data.session_id;
            
            // Then end the game
            const response = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.END_GAME}`, {
                session_id: sessionId
            });
            
            const data = response.data;
            return data.session_id === sessionId && typeof data.final_score === 'number';
        }
    },
    {
        name: 'Get Comparison Stats',
        fn: async () => {
            const response = await axios.get(`${API_BASE_URL}${API_ENDPOINTS.COMPARISONS}`);
            return Array.isArray(response.data.comparisons);
        }
    },
    {
        name: 'Get High Scores',
        fn: async () => {
            const response = await axios.get(`${API_BASE_URL}${API_ENDPOINTS.HIGH_SCORES}`);
            return Array.isArray(response.data.high_scores);
        }
    },
    {
        name: 'Full Game Flow',
        fn: async () => {
            // 1. Start a game
            const startResponse = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.START_GAME}`);
            const sessionId = startResponse.data.session_id;
            
            // 2. Submit a winning comparison (rock -> paper)
            const firstComparison = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.SUBMIT_COMPARISON}`, {
                session_id: sessionId,
                current_item: 'rock',
                user_input: 'paper'
            });
            
            if (!firstComparison.data.result) {
                throw new Error('First comparison failed: paper should beat rock');
            }
            
            // 3. Submit another winning comparison (paper -> scissors)
            const secondComparison = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.SUBMIT_COMPARISON}`, {
                session_id: sessionId,
                current_item: 'paper',
                user_input: 'scissors'
            });
            
            if (!secondComparison.data.result) {
                throw new Error('Second comparison failed: scissors should beat paper');
            }
            
            // 4. Submit a losing comparison to end the game (scissors -> rock)
            const thirdComparison = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.SUBMIT_COMPARISON}`, {
                session_id: sessionId,
                current_item: 'scissors',
                user_input: 'rock'
            });
            
            // This should be false because in our game, we're looking for what beats the current item
            // not what the current item beats
            if (thirdComparison.data.result) {
                throw new Error('Third comparison should have failed: rock doesn\'t beat scissors in this context');
            }
            
            // 5. End the game
            const endResponse = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.END_GAME}`, {
                session_id: sessionId
            });
            
            return endResponse.data.final_score === 2;
        }
    }
];

// Run all tests
async function runTests() {
    console.log('Starting integration tests for What Beats Rock? application...\n');
    
    let passed = 0;
    let failed = 0;
    
    for (const test of tests) {
        process.stdout.write(`Testing ${test.name}... `);
        
        try {
            const result = await test.fn();
            
            if (result) {
                console.log('✅ PASSED');
                passed++;
            } else {
                console.log('❌ FAILED (Unexpected result)');
                failed++;
            }
        } catch (error) {
            console.log('❌ FAILED');
            console.error(`  Error: ${error.message}`);
            if (error.response) {
                console.error(`  Status: ${error.response.status}`);
                console.error(`  Data: ${JSON.stringify(error.response.data)}`);
            }
            failed++;
        }
    }
    
    console.log(`\nTest Results: ${passed} passed, ${failed} failed`);
    
    if (failed === 0) {
        console.log('\n✅ All tests passed! The frontend and backend are integrated correctly.');
    } else {
        console.log('\n❌ Some tests failed. Please check the errors above.');
    }
}

// Check if the backend is running
async function checkBackendStatus() {
    try {
        await axios.get(`${API_BASE_URL}/health`);
        return true;
    } catch (error) {
        return false;
    }
}

// Main function
async function main() {
    console.log('Checking if backend is running...');
    
    const isBackendRunning = await checkBackendStatus();
    
    if (!isBackendRunning) {
        console.error('❌ Backend is not running. Please start the backend server first.');
        console.log('You can start the backend with: cd backend && python run.py');
        process.exit(1);
    }
    
    console.log('✅ Backend is running.');
    
    await runTests();
}

// Run the main function
main().catch(error => {
    console.error('An unexpected error occurred:');
    console.error(error);
    process.exit(1);
});