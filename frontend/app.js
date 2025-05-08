/**
 * Main application script for the "What Beats Rock?" game
 * Handles game logic and UI interactions
 */

// Game state
const gameState = {
    sessionId: null,
    currentItem: 'rock',
    currentEmoji: '🪨',
    score: 0,
    isActive: false,
    history: [],
    usedItems: [] // Track items that have been used in the current game
};

// DOM Elements
const elements = {
    // Screens
    startScreen: document.getElementById('start-screen'),
    gameArea: document.getElementById('game-area'),
    gameOverScreen: document.getElementById('game-over-screen'),
    scoreboardSection: document.getElementById('scoreboard-section'),
    
    // Game elements
    currentItemText: document.getElementById('current-item-text'),
    currentItemEmoji: document.getElementById('current-item-emoji'),
    promptItem: document.getElementById('prompt-item'),
    userInput: document.getElementById('user-input'),
    comparisonForm: document.getElementById('comparison-form'),
    resultArea: document.getElementById('result-area'),
    resultTitle: document.getElementById('result-title'),
    resultDescription: document.getElementById('result-description'),
    resultEmoji: document.getElementById('result-emoji'),
    scoreDisplay: document.getElementById('score'),
    
    // Game over elements
    finalScore: document.getElementById('final-score'),
    highScoreMessage: document.getElementById('high-score-message'),
    itemsChain: document.getElementById('items-chain'),
    
    // History
    historyContainer: document.getElementById('history-container'),
    
    // Stats modal
    statsModal: document.getElementById('stats-modal'),
    comparisonsTab: document.getElementById('comparisons-tab'),
    comparisonsBody: document.getElementById('comparisons-body'),
    scoreboardTab: document.getElementById('scoreboard-tab'),
    
    // Scoreboard elements
    scoreboardBody: document.getElementById('scoreboard-body'),
    totalScores: document.getElementById('total-scores'),
    highestScore: document.getElementById('highest-score'),
    averageScore: document.getElementById('average-score'),
    sortBy: document.getElementById('sort-by'),
    sortDirection: document.getElementById('sort-direction'),
    minScore: document.getElementById('min-score'),
    maxScore: document.getElementById('max-score'),
    pageInfo: document.getElementById('page-info'),
    
    // Report modal
    reportModal: document.getElementById('report-modal'),
    reportForm: document.getElementById('report-form'),
    reportUserInput: document.getElementById('report-user-input'),
    reportCurrentItem: document.getElementById('report-current-item'),
    reportReason: document.getElementById('report-reason'),
    reportSuccess: document.getElementById('report-success'),
    reportError: document.getElementById('report-error'),
    
    // Buttons
    startGameBtn: document.getElementById('start-game-btn'),
    submitBtn: document.getElementById('submit-btn'),
    playAgainBtn: document.getElementById('play-again-btn'),
    viewStatsBtn: document.getElementById('view-stats-btn'),
    backToGameBtn: document.getElementById('back-to-game-btn'),
    prevPageBtn: document.getElementById('prev-page-btn'),
    nextPageBtn: document.getElementById('next-page-btn'),
    reportBtn: document.getElementById('report-btn'),
    submitReportBtn: document.getElementById('submit-report-btn'),
    cancelReportBtn: document.getElementById('cancel-report-btn'),
    closeReportModalBtn: document.getElementById('close-report-modal'),
    closeSuccessBtn: document.getElementById('close-success-btn'),
    retryReportBtn: document.getElementById('retry-report-btn'),
    tabButtons: document.querySelectorAll('.tab-btn'),
    closeModalBtn: document.querySelector('.close-btn'),
    
    
    // Edit comparison elements
    editComparisonModal: document.getElementById('edit-comparison-modal'),
    closeEditComparisonModalBtn: document.getElementById('close-edit-comparison-modal'),
    editComparisonForm: document.getElementById('edit-comparison-form'),
    editItem1: document.getElementById('edit-item1'),
    editItem2: document.getElementById('edit-item2'),
    item1WinsRadio: document.getElementById('item1-wins'),
    item2WinsRadio: document.getElementById('item2-wins'),
    editDescription: document.getElementById('edit-description'),
    editEmoji: document.getElementById('edit-emoji'),
    saveComparisonBtn: document.getElementById('save-comparison-btn'),
    cancelEditBtn: document.getElementById('cancel-edit-btn'),
    editSuccess: document.getElementById('edit-success'),
    editError: document.getElementById('edit-error'),
    closeEditSuccessBtn: document.getElementById('close-edit-success-btn'),
    retryEditBtn: document.getElementById('retry-edit-btn')
};

/**
 * Initialize the application
 */
function initApp() {
    // Add event listeners
    elements.startGameBtn.addEventListener('click', startGame);
    elements.comparisonForm.addEventListener('submit', handleSubmit);
    elements.playAgainBtn.addEventListener('click', startGame);
    elements.viewStatsBtn.addEventListener('click', () => openStatsModal('comparisons'));
    elements.closeModalBtn.addEventListener('click', closeStatsModal);
    
    // Add client-side validation for user input
    elements.userInput.addEventListener('input', validateUserInput);
    
    // Scoreboard functionality
    elements.prevPageBtn.addEventListener('click', () => navigateScoreboardPage(-1));
    elements.nextPageBtn.addEventListener('click', () => navigateScoreboardPage(1));
    
    // Auto-apply filter changes
    elements.sortBy.addEventListener('change', applyScoreboardFilters);
    elements.sortDirection.addEventListener('change', applyScoreboardFilters);
    elements.minScore.addEventListener('input', debounce(applyScoreboardFilters, 500));
    elements.maxScore.addEventListener('input', debounce(applyScoreboardFilters, 500));
    
    // Clear all filters button
    document.getElementById('clear-all-filters').addEventListener('click', () => {
        // Reset all filter values to defaults
        elements.sortBy.value = 'score';
        elements.sortDirection.value = 'desc';
        elements.minScore.value = '';
        elements.maxScore.value = '';
        
        // Apply the filters to refresh the data
        applyScoreboardFilters();
    });
    
    // Report functionality
    elements.reportBtn.addEventListener('click', openReportModal);
    elements.reportForm.addEventListener('submit', submitReport);
    elements.cancelReportBtn.addEventListener('click', closeReportModal);
    elements.closeReportModalBtn.addEventListener('click', closeReportModal);
    elements.closeSuccessBtn.addEventListener('click', closeReportModal);
    elements.retryReportBtn.addEventListener('click', resetReportForm);
    
    // Tab switching
    elements.tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
    
    // Initialize with empty history
    updateHistoryDisplay();
    
    
    // Edit comparison functionality
    elements.closeEditComparisonModalBtn.addEventListener('click', closeEditComparisonModal);
    elements.editComparisonForm.addEventListener('submit', saveComparisonChanges);
    elements.cancelEditBtn.addEventListener('click', closeEditComparisonModal);
    elements.closeEditSuccessBtn.addEventListener('click', closeEditComparisonModal);
    elements.retryEditBtn.addEventListener('click', resetEditForm);
}

/**
 * Start a new game
 */
/**
 * Start a new game
 * This function initializes a new game session by calling the backend API,
 * resetting the game state, and updating the UI.
 */
async function startGame() {
    try {
        // Show loading state
        elements.startGameBtn.disabled = true;
        elements.startGameBtn.textContent = 'Starting...';
        elements.playAgainBtn.disabled = true;
        elements.playAgainBtn.textContent = 'Starting...';
        
        // Reset game state
        resetGameState();
        
        // Call API to start game
        const response = await apiService.startGame();
        
        // Update game state with the response from the backend
        gameState.sessionId = response.session_id;
        gameState.currentItem = response.current_item;
        gameState.currentEmoji = getEmojiForItem(response.current_item);
        gameState.isActive = true;
        
        // Initialize used items with the starting item (rock)
        gameState.usedItems = [response.current_item];
        
        // Update UI with the new game state
        updateGameUI();
        
        // Update the used items display
        updateUsedItemsDisplay();
        
        // Switch to game screen
        showScreen('game');
        
        // Focus on input for better user experience
        elements.userInput.focus();
        
    } catch (error) {
        showError('Failed to start game: ' + error.message);
    } finally {
        // Reset button state regardless of success or failure
        elements.startGameBtn.disabled = false;
        elements.startGameBtn.textContent = 'Start Game';
        elements.playAgainBtn.disabled = false;
        elements.playAgainBtn.textContent = 'Play Again';
    }
}

/**
 * Handle form submission
 * @param {Event} event - The submit event
 */
/**
 * Handle form submission
 * This function processes the user's input when they submit what they think
 * beats the current item. It calls the backend API to determine if the input
 * is valid and updates the game state accordingly.
 *
 * @param {Event} event - The submit event
 */
async function handleSubmit(event) {
    event.preventDefault();
    
    // Don't process if game is not active
    if (!gameState.isActive) {
        return;
    }
    
    const userInput = elements.userInput.value.trim();
    
    // Don't process empty input
    if (!userInput) {
        return;
    }
    
    // Client-side validation before submission
    const validationResult = validateUserInputBeforeSubmit(userInput);
    if (!validationResult.valid) {
        showError(validationResult.message);
        return;
    }
    
    try {
        // Disable input and button while processing
        elements.userInput.disabled = true;
        elements.submitBtn.disabled = true;
        elements.submitBtn.textContent = 'Submitting...';
        
        // Hide previous result
        elements.resultArea.classList.add('hidden');
        
        // Call API to submit comparison
        const response = await apiService.submitComparison(
            gameState.sessionId,
            gameState.currentItem,
            userInput
        );
        
        // Add to history for display in the history section
        const historyItem = {
            currentItem: gameState.currentItem,
            currentEmoji: gameState.currentEmoji,
            userInput: userInput,
            result: response.result,
            description: response.description,
            emoji: response.emoji,
            count: response.count
        };
        
        // Store the last comparison for reporting and failure tracking
        gameState.lastComparison = {
            currentItem: gameState.currentItem,
            userInput: userInput,
            result: response.result
        };
        gameState.history.unshift(historyItem); // Add to beginning of array
        
        // Update game state with new score
        gameState.score = response.score;
        
        // Show result to the user
        showResult(response);
        
        // Update history display with the new item
        updateHistoryDisplay();
        
        // Check if game is over based on the response
        if (response.game_over) {
            gameState.isActive = false;
            
            // If end_game_data is included in the response, use it directly
            if (response.end_game_data) {
                // Show game over screen immediately since we're hiding the result area
                setTimeout(() => endGame(response.end_game_data), 500);
            }
        } else {
            // Update for next round with the new item
            gameState.currentItem = response.next_item;
            gameState.currentEmoji = response.emoji;
            
            // Add the user's input to the used items list
            gameState.usedItems.push(userInput);
            
            // Update the UI
            updateGameUI();
            updateUsedItemsDisplay();
            
            // Reset input field for next entry
            elements.userInput.value = '';
            
            // Re-enable input and button for next round
            elements.userInput.disabled = false;
            elements.submitBtn.disabled = false;
            elements.submitBtn.textContent = 'Submit';
            elements.userInput.focus();
        }
        
    } catch (error) {
        // Check if this is an item reuse error
        if (error.code === 'ITEM_ALREADY_USED') {
            // Show a more specific error message for item reuse
            showItemReuseError(error.message, userInput);
        } else {
            // Show generic error for other errors
            showError('Error: ' + error.message);
        }
        
        // Re-enable input and button on error
        elements.userInput.disabled = false;
        elements.submitBtn.disabled = false;
        elements.submitBtn.textContent = 'Submit';
    }
}

/**
 * End the current game and show game over screen
 */
async function endGame(endGameData = null) {
    try {
        // If end game data is provided, use it directly
        // This happens when the game ends due to a failed comparison
        if (endGameData) {
            // Update final score
            elements.finalScore.textContent = endGameData.final_score;
            
            // Show high score message if applicable
            if (endGameData.high_score) {
                elements.highScoreMessage.classList.remove('hidden');
            } else {
                elements.highScoreMessage.classList.add('hidden');
            }
            
            // If the game ended due to a failed comparison, add the failed item directly
            let itemsChain = [...endGameData.items_chain];
            
            // Check if the last item in history was a failure
            if (gameState.history.length > 0 && !gameState.history[0].result) {
                // Add the failed item if available (without the FAILURE text)
                if (gameState.lastComparison && gameState.lastComparison.userInput) {
                    // We'll mark this as a failure in the displayItemsChain function
                    itemsChain.push(gameState.lastComparison.userInput);
                }
            }
            
            // Display items chain
            displayItemsChain(itemsChain);
            
            // Show game over screen
            showScreen('gameOver');
            
            return;
        }
        
        // If no end game data is provided, make the API call
        // This handles cases where the game is manually ended
        const response = await apiService.endGame(gameState.sessionId);
        
        // Update final score
        elements.finalScore.textContent = response.final_score;
        
        // Show high score message if applicable
        if (response.high_score) {
            elements.highScoreMessage.classList.remove('hidden');
        } else {
            elements.highScoreMessage.classList.add('hidden');
        }
        
        // Check if the game ended due to a failed comparison
        let itemsChain = [...response.items_chain];
        
        // Check if the last item in history was a failure
        if (gameState.history.length > 0 && !gameState.history[0].result) {
            // Add the failed item if available (without the FAILURE text)
            if (gameState.lastComparison && gameState.lastComparison.userInput) {
                // We'll mark this as a failure in the displayItemsChain function
                itemsChain.push(gameState.lastComparison.userInput);
            }
        }
        
        // Display items chain
        displayItemsChain(itemsChain);
        
        // Show game over screen
        showScreen('gameOver');
        
    } catch (error) {
        showError('Error ending game: ' + error.message);
    }
}

/**
 * Show the result of a comparison
 * @param {Object} response - The comparison response from the API
 */
function showResult(response) {
    // Set result title
    if (response.result) {
        elements.resultTitle.textContent = 'Success!';
        elements.resultTitle.className = 'success';
    } else {
        // Check if we're about to transition to game over screen
        if (response.game_over && response.end_game_data) {
            // Don't show result area at all if we're about to show game over screen
            elements.resultArea.classList.add('hidden');
            return;
        } else {
            elements.resultTitle.textContent = 'Game Over!';
            elements.resultTitle.className = 'error';
        }
    }
    
    // Set description and emoji using safe methods
    utils.setTextContent(elements.resultDescription, response.description);
    utils.setTextContent(elements.resultEmoji, response.emoji);
    
    // Add count information and range description if available
    if (response.count) {
        // Create usage count container if it doesn't exist
        let usageCountContainer = document.getElementById('usage-count-container');
        if (!usageCountContainer) {
            usageCountContainer = document.createElement('div');
            usageCountContainer.id = 'usage-count-container';
            usageCountContainer.className = 'usage-count-container alert';
            
            // Add different alert colors based on count range
            if (response.count === 1) {
                usageCountContainer.classList.add('alert-info'); // Blue for first time
            } else if (response.count <= 5) {
                usageCountContainer.classList.add('alert-success'); // Green for 2-5
            } else if (response.count <= 10) {
                usageCountContainer.classList.add('alert-warning'); // Yellow for 6-10
            } else {
                usageCountContainer.classList.add('alert-danger'); // Red for 10+
            }
            
            // Insert after the current item card
            const currentItemElement = document.querySelector('.current-item');
            currentItemElement.parentNode.insertBefore(usageCountContainer, currentItemElement.nextSibling);
        }
        
        // Clear previous content - use safer method
        while (usageCountContainer.firstChild) {
            usageCountContainer.removeChild(usageCountContainer.firstChild);
        }
        
        // Create a wrapper div for inline display
        const inlineWrapper = document.createElement('div');
        inlineWrapper.className = 'text-center';
        
        // Create count display
        const countDisplay = utils.createElement(
            'span',
            `Used ${response.count} time${response.count !== 1 ? 's' : ''}`,
            'usage-count-display'
        );
        inlineWrapper.appendChild(countDisplay);
        
        // Add range description and emoji if available
        if (response.count_range_description && response.count_range_emoji) {
            const rangeDescription = document.createElement('span');
            rangeDescription.className = 'usage-range-description';
            
            const rangeEmoji = utils.createElement('span', response.count_range_emoji, 'usage-range-emoji');
            
            const rangeText = utils.createElement('span', response.count_range_description, 'usage-range-text');
            
            rangeDescription.appendChild(rangeEmoji);
            rangeDescription.appendChild(rangeText);
            
            inlineWrapper.appendChild(rangeDescription);
        }
        
        usageCountContainer.appendChild(inlineWrapper);
    }
    
    // Update score
    elements.scoreDisplay.textContent = response.score;
    
    // Show result area
    elements.resultArea.classList.remove('hidden');
}

/**
 * Update the game UI with current state
 */
function updateGameUI() {
    // Use safe DOM manipulation methods
    utils.setTextContent(elements.currentItemText, gameState.currentItem);
    utils.setTextContent(elements.currentItemEmoji, gameState.currentEmoji);
    utils.setTextContent(elements.promptItem, gameState.currentItem);
    utils.setTextContent(elements.scoreDisplay, gameState.score);
}

/**
 * Update the history display
 */
function updateHistoryDisplay() {
    elements.historyContainer.innerHTML = '';
    
    if (gameState.history.length === 0) {
        const emptyMessage = utils.createElement('div', 'No history yet. Start playing!', 'history-item');
        elements.historyContainer.appendChild(emptyMessage);
        return;
    }
    
    gameState.history.forEach(item => {
        const historyItem = utils.createElement('div', null, 'history-item');
        
        const emoji = utils.createElement('span', item.emoji, 'history-emoji');
        
        const text = document.createElement('div');
        text.className = 'history-text';
        
        // Create comparison div
        const comparison = document.createElement('div');
        
        // Create badge for user input item
        const userInputBadge = utils.createElement('span', utils.sanitizeText(item.userInput), 'item-badge');
        
        // Create "vs" text node
        const vsText = document.createTextNode(' vs ');
        
        // Create badge for current item
        const currentItemBadge = utils.createElement('span', utils.sanitizeText(item.currentItem), 'item-badge');
        
        // Append all elements to the comparison div
        comparison.appendChild(userInputBadge);
        comparison.appendChild(vsText);
        comparison.appendChild(currentItemBadge);
        
        const result = utils.createElement('div', item.description, 'history-result ' + (item.result ? 'success' : 'error'));
        
        // Add count information if available
        if (item.count && item.count > 1) {
            const countSpan = utils.createElement('span', `Used ${item.count} times`, 'usage-count');
            result.appendChild(countSpan);
            
            // We don't add the range description in the history items to keep it clean
        }
        
        text.appendChild(comparison);
        text.appendChild(result);
        
        historyItem.appendChild(emoji);
        historyItem.appendChild(text);
        
        elements.historyContainer.appendChild(historyItem);
    });
}

/**
 * Display the items chain on the game over screen
 * @param {Array} itemsChain - Array of items in the chain
 */
function displayItemsChain(itemsChain) {
    // Clear the items chain using a safer method
    while (elements.itemsChain.firstChild) {
        elements.itemsChain.removeChild(elements.itemsChain.firstChild);
    }
    
    // Create a horizontal container for the chain
    const chainContainer = utils.createElement('div', null, 'chain-container');
    elements.itemsChain.appendChild(chainContainer);
    
    // Check if the last item represents a failure (based on game history)
    const hasFailure = gameState.history.length > 0 && !gameState.history[0].result;
    
    itemsChain.forEach((item, index) => {
        // Use the same badge style as in the history items for consistency
        const chainItem = utils.createElement('div', null, 'chain-item item-badge');
        
        const itemText = utils.createElement('span', utils.sanitizeText(item));
        const itemEmoji = utils.createElement('span', getEmojiForItem(item));
        
        chainItem.appendChild(itemText);
        chainItem.appendChild(itemEmoji);
        
        chainContainer.appendChild(chainItem);
        
        // Add arrow or failure symbol between items
        if (index < itemsChain.length - 1) {
            // If this is the last successful item and the next is the failed item
            if (hasFailure && index === itemsChain.length - 2) {
                // Use X symbol for failure
                const failure = utils.createElement('span', '✕', 'chain-failure');
                chainContainer.appendChild(failure);
            } else {
                // Regular arrow for success
                const arrow = utils.createElement('span', '→', 'chain-arrow');
                chainContainer.appendChild(arrow);
            }
        }
    });
}

/**
 * Open the stats modal and load data for the specified tab
 * @param {string} tabName - The name of the tab to open (default: 'comparisons')
 */
async function openStatsModal(tabName = 'comparisons') {
    elements.statsModal.classList.remove('hidden');
    
    // Switch to the requested tab
    switchTab(tabName);
    
    try {
        if (tabName === 'comparisons') {
            // Load comparison stats
            const comparisonsResponse = await apiService.getComparisonStats();
            displayComparisonStats(comparisonsResponse.comparisons);
        } else if (tabName === 'scoreboard') {
            // Load scoreboard stats
            const stats = await apiService.getScoreboardStats();
            displayScoreboardStats(stats);
            
            // Load initial scoreboard data
            await loadScoreboardData();
        }
    } catch (error) {
        showError('Error loading stats: ' + error.message);
    }
}

/**
 * Close the stats modal
 */
function closeStatsModal() {
    elements.statsModal.classList.add('hidden');
}

/**
 * Display comparison statistics
 * @param {Array} comparisons - Array of comparison objects
 */
function displayComparisonStats(comparisons) {
    elements.comparisonsBody.innerHTML = '';
    
    if (comparisons.length === 0) {
        const row = document.createElement('tr');
        const cell = utils.createElement('td', 'No comparisons yet.', 'text-center');
        cell.colSpan = 4;
        row.appendChild(cell);
        elements.comparisonsBody.appendChild(row);
        return;
    }
    
    comparisons.forEach(comp => {
        const row = document.createElement('tr');
        
        // Create item1 cell with badge
        const item1Cell = document.createElement('td');
        const item1Badge = utils.createElement('span', utils.sanitizeText(comp.item1), 'item-badge');
        item1Cell.appendChild(item1Badge);
        
        // Create item2 cell with badge
        const item2Cell = document.createElement('td');
        const item2Badge = utils.createElement('span', utils.sanitizeText(comp.item2), 'item-badge');
        item2Cell.appendChild(item2Badge);
        
        // Create result cell with badges
        const resultCell = document.createElement('td');
        if (comp.item2_wins) {
            const winnerBadge = utils.createElement('span', utils.sanitizeText(comp.item2), 'item-badge');
            const beatsText = document.createTextNode(' beats ');
            const loserBadge = utils.createElement('span', utils.sanitizeText(comp.item1), 'item-badge');
            resultCell.appendChild(winnerBadge);
            resultCell.appendChild(beatsText);
            resultCell.appendChild(loserBadge);
        } else {
            const winnerBadge = utils.createElement('span', utils.sanitizeText(comp.item1), 'item-badge');
            const beatsText = document.createTextNode(' beats ');
            const loserBadge = utils.createElement('span', utils.sanitizeText(comp.item2), 'item-badge');
            resultCell.appendChild(winnerBadge);
            resultCell.appendChild(beatsText);
            resultCell.appendChild(loserBadge);
        }
        
        const countCell = utils.createElement('td', comp.count.toString());
        
        row.appendChild(item1Cell);
        row.appendChild(item2Cell);
        row.appendChild(resultCell);
        row.appendChild(countCell);
        
        elements.comparisonsBody.appendChild(row);
    });
}


/**
 * Switch between tabs in the stats modal
 * @param {string} tabName - The name of the tab to switch to
 */
function switchTab(tabName) {
    // Update active tab button
    elements.tabButtons.forEach(button => {
        if (button.getAttribute('data-tab') === tabName) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
    
    // Hide all tab content
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab content
    if (tabName === 'comparisons') {
        elements.comparisonsTab.classList.add('active');
    } else if (tabName === 'scoreboard') {
        elements.scoreboardTab.classList.add('active');
        
        // Load scoreboard data if switching to scoreboard tab
        // This ensures data is loaded regardless of how the user navigates to this tab
        loadScoreboardData().catch(error => {
            showError('Error loading scoreboard data: ' + error.message);
        });
    }
}

/**
 * Show a specific screen and hide others
 * @param {string} screenName - The name of the screen to show
 */
function showScreen(screenName) {
    // Hide all screens
    elements.startScreen.classList.add('hidden');
    elements.gameArea.classList.add('hidden');
    elements.gameOverScreen.classList.add('hidden');
    
    // Show the requested screen
    switch (screenName) {
        case 'start':
            elements.startScreen.classList.remove('hidden');
            break;
        case 'game':
            elements.gameArea.classList.remove('hidden');
            break;
        case 'gameOver':
            elements.gameOverScreen.classList.remove('hidden');
            break;
    }
}

/**
 * Reset the game state
 */
function resetGameState() {
    gameState.sessionId = null;
    gameState.currentItem = 'rock';
    gameState.currentEmoji = '🪨';
    gameState.score = 0;
    gameState.isActive = false;
    gameState.history = [];
    gameState.usedItems = []; // Reset used items
    
    // Reset UI
    elements.resultArea.classList.add('hidden');
    elements.userInput.value = '';
    elements.userInput.disabled = false;
    elements.submitBtn.disabled = false;
    elements.submitBtn.textContent = 'Submit';
    
    // Clear the usage count container if it exists
    const usageCountContainer = document.getElementById('usage-count-container');
    if (usageCountContainer) {
        usageCountContainer.remove();
    }
    
    // Update history display
    updateHistoryDisplay();
    
    // Update used items display
    updateUsedItemsDisplay();
}

/**
 * Show an error message
 * @param {string} message - The error message to display
 */
function showError(message) {
    console.error(message);
    alert(message);
}

/**
 * Show a specific error message for item reuse
 * @param {string} message - The error message from the server
 * @param {string} item - The item that was attempted to be reused
 */
function showItemReuseError(message, item) {
    console.error(message);
    
    // Show error in the result area instead of an alert for better UX
    utils.setTextContent(elements.resultTitle, 'Item Already Used!');
    elements.resultTitle.className = 'error';
    utils.setTextContent(elements.resultDescription, message);
    utils.setTextContent(elements.resultEmoji, '⚠️');
    elements.resultArea.classList.remove('hidden');
    
    // Highlight the item in the used items display
    highlightUsedItem(item);
}

/**
 * Highlight an item in the used items display
 * @param {string} item - The item to highlight
 */
function highlightUsedItem(item) {
    // Find the item in the used items display and add a highlight class
    const usedItemElements = document.querySelectorAll('.used-item');
    usedItemElements.forEach(element => {
        if (element.dataset.item.toLowerCase() === item.toLowerCase()) {
            element.classList.add('highlight-error');
            // Remove the highlight after 2 seconds
            setTimeout(() => {
                element.classList.remove('highlight-error');
            }, 2000);
        }
    });
}

/**
 * Update the display of used items
 */
function updateUsedItemsDisplay() {
    // Check if the used items container exists, if not create it
    let usedItemsContainer = document.getElementById('used-items-container');
    
    if (!usedItemsContainer) {
        // Create the container if it doesn't exist
        usedItemsContainer = document.createElement('div');
        usedItemsContainer.id = 'used-items-container';
        usedItemsContainer.className = 'used-items-container';
        
        // Add a heading
        const heading = utils.createElement('h4', 'Used Items:');
        usedItemsContainer.appendChild(heading);
        
        // Create the items list
        const itemsList = document.createElement('div');
        itemsList.id = 'used-items-list';
        itemsList.className = 'used-items-list';
        usedItemsContainer.appendChild(itemsList);
        
        // Add it to the game area, after the score area
        const scoreArea = document.querySelector('.score-area');
        elements.gameArea.insertBefore(usedItemsContainer, scoreArea.nextSibling);
    }
    
    // Get the items list
    const itemsList = document.getElementById('used-items-list');
    // Clear the items list using a safer method
    while (itemsList.firstChild) {
        itemsList.removeChild(itemsList.firstChild);
    }
    
    // If there are no used items, show a message
    if (gameState.usedItems.length === 0) {
        const noItemsSpan = utils.createElement('span', 'No items used yet', 'no-items');
        itemsList.appendChild(noItemsSpan);
        return;
    }
    
    // Add each used item to the list
    gameState.usedItems.forEach(item => {
        const itemElement = utils.createElement('span', utils.sanitizeText(item), 'used-item');
        itemElement.dataset.item = item;
        itemsList.appendChild(itemElement);
    });
}

/**
 * Get an emoji for an item
 * @param {string} item - The item to get an emoji for
 * @returns {string} The emoji for the item
 */
function getEmojiForItem(item) {
    // Default emoji mapping
    const emojiMap = {
        'rock': '🪨',
        'paper': '📄',
        'scissors': '✂️',
        'water': '💧',
        'fire': '🔥',
        'air': '💨',
        'earth': '🌍',
        'sun': '☀️',
        'moon': '🌙',
        'star': '⭐',
        'lightning': '⚡',
        'tree': '🌳',
        'flower': '🌸',
        'mountain': '⛰️',
        'ocean': '🌊',
        'rain': '🌧️',
        'snow': '❄️',
        'wind': '🌬️',
        'cloud': '☁️',
        'metal': '🔩',
        'wood': '🪵',
        'plastic': '🧫',
        'glass': '🥃',
        'diamond': '💎',
        'gold': '🥇',
        'silver': '🥈',
        'bronze': '🥉',
        'iron': '⚙️',
        'steel': '🔧',
        'time': '⏰',
        'space': '🌌',
        'love': '❤️',
        'hate': '💔',
        'life': '🧬',
        'death': '💀'
    };
    
    return emojiMap[item.toLowerCase()] || '❓';
}

/**
 * Open the report modal
 */
function openReportModal() {
    // Populate the report form with the last comparison
    if (gameState.lastComparison) {
        utils.setTextContent(elements.reportUserInput, gameState.lastComparison.userInput);
        utils.setTextContent(elements.reportCurrentItem, gameState.lastComparison.currentItem);
    }
    
    // Show the form, hide success/error messages
    elements.reportForm.classList.remove('hidden');
    elements.reportSuccess.classList.add('hidden');
    elements.reportError.classList.add('hidden');
    
    // Show the modal
    elements.reportModal.classList.remove('hidden');
}

/**
 * Close the report modal
 */
function closeReportModal() {
    elements.reportModal.classList.add('hidden');
    resetReportForm();
}

/**
 * Reset the report form
 */
function resetReportForm() {
    elements.reportReason.value = '';
    elements.reportForm.classList.remove('hidden');
    elements.reportSuccess.classList.add('hidden');
    elements.reportError.classList.add('hidden');
}

/**
 * Submit a report for a disputed comparison
 * @param {Event} event - The submit event
 */
async function submitReport(event) {
    event.preventDefault();
    
    // Don't process if no last comparison
    if (!gameState.lastComparison) {
        return;
    }
    
    try {
        // Disable submit button while processing
        elements.submitReportBtn.disabled = true;
        elements.submitReportBtn.textContent = 'Submitting...';
        
        // Get form data
        const reason = elements.reportReason.value.trim();
        
        // Call API to submit report
        const response = await apiService.reportComparison(
            gameState.sessionId,
            gameState.lastComparison.currentItem,
            gameState.lastComparison.userInput,
            reason || null
        );
        
        // Show success message
        elements.reportForm.classList.add('hidden');
        elements.reportSuccess.classList.remove('hidden');
        
    } catch (error) {
        console.error('Error submitting report:', error);
        
        // Show error message
        elements.reportForm.classList.add('hidden');
        elements.reportError.classList.remove('hidden');
    } finally {
        // Reset button state
        elements.submitReportBtn.disabled = false;
        elements.submitReportBtn.textContent = 'Submit Report';
    }
}

/**
 * Scoreboard state
 */
// Admin state
// Edit comparison state
const editComparisonState = {
    item1: '',
    item2: '',
    reportId: null
};

const scoreboardState = {
    currentPage: 1,
    pageSize: 10,
    totalPages: 1,
    totalCount: 0,
    sortBy: 'score',
    sortDirection: 'desc',
    minScore: null,
    maxScore: null,
    dateFrom: null,
    dateTo: null
};

// The openScoreboard function is now replaced by openStatsModal with 'scoreboard' parameter

/**
 * Load scoreboard data with current filters and pagination
 */
async function loadScoreboardData() {
    try {
        // Show loading state
        elements.scoreboardBody.innerHTML = '<tr><td colspan="4" class="loading-message">Loading scores...</td></tr>';
        
        // Get current filter values
        const options = {
            page: scoreboardState.currentPage,
            pageSize: scoreboardState.pageSize,
            sortBy: scoreboardState.sortBy,
            sortDirection: scoreboardState.sortDirection,
            minScore: scoreboardState.minScore,
            maxScore: scoreboardState.maxScore,
            dateFrom: scoreboardState.dateFrom,
            dateTo: scoreboardState.dateTo
        };
        
        // Fetch data from API
        const response = await apiService.getScoreboard(options);
        
        // Update state
        scoreboardState.totalPages = response.total_pages;
        scoreboardState.totalCount = response.total_count;
        
        // Display data
        displayScoreboardData(response.high_scores);
        updatePagination();
    } catch (error) {
        elements.scoreboardBody.innerHTML = `<tr><td colspan="4" class="error-message">Error: ${error.message}</td></tr>`;
    }
}

/**
 * Display scoreboard statistics
 * @param {Object} stats - The scoreboard statistics
 */
function displayScoreboardStats(stats) {
    console.log('Scoreboard stats received:', stats);
    
    // Check if stats object has the expected properties
    if (!stats || typeof stats !== 'object') {
        console.error('Invalid stats object received:', stats);
        return;
    }
    
    // Set values with fallbacks to prevent displaying "undefined"
    elements.totalScores.textContent = stats.total_count || 0;
    elements.highestScore.textContent = stats.highest_score || 0;
    elements.averageScore.textContent = stats.average_score ? Math.round(stats.average_score) : 0;
}

/**
 * Display scoreboard data
 * @param {Array} highScores - Array of high score objects
 */
function displayScoreboardData(highScores) {
    elements.scoreboardBody.innerHTML = '';
    
    if (highScores.length === 0) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 4;
        cell.textContent = 'No scores found matching your criteria.';
        cell.className = 'text-center';
        row.appendChild(cell);
        elements.scoreboardBody.appendChild(row);
        return;
    }
    
    // Calculate starting rank for current page
    const startRank = (scoreboardState.currentPage - 1) * scoreboardState.pageSize + 1;
    
    highScores.forEach((score, index) => {
        const row = document.createElement('tr');
        
        // Rank column
        const rankCell = document.createElement('td');
        rankCell.textContent = startRank + index;
        
        // Score column
        const scoreCell = document.createElement('td');
        scoreCell.textContent = score.score;
        
        // Items chain column
        const chainCell = document.createElement('td');
        
        // Create a container for the items chain
        const chainContainer = document.createElement('div');
        chainContainer.className = 'scoreboard-chain-container';
        
        // Add each item as a badge with arrows between them
        score.items_chain.forEach((item, idx) => {
            // Create badge for the item
            const itemBadge = utils.createElement('span', utils.sanitizeText(item), 'item-badge');
            chainContainer.appendChild(itemBadge);
            
            // Add arrow between items (except after the last item)
            if (idx < score.items_chain.length - 1) {
                const arrow = document.createTextNode(' → ');
                chainContainer.appendChild(arrow);
            }
        });
        
        chainCell.appendChild(chainContainer);
        
        // Date column
        const dateCell = document.createElement('td');
        const date = new Date(score.created_at);
        dateCell.textContent = `${date.toLocaleDateString()} ${date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
        
        // Add cells to row
        row.appendChild(rankCell);
        row.appendChild(scoreCell);
        row.appendChild(chainCell);
        row.appendChild(dateCell);
        
        // Add row to table
        elements.scoreboardBody.appendChild(row);
    });
}

/**
 * Navigate to a different page of reports
 * @param {number} direction - Direction to navigate (-1 for previous, 1 for next)
 */

/**
 * Open the edit comparison modal
 * @param {Object} report - The report object
 */
function openEditComparisonModal(report) {
    // Store the current report and comparison details
    editComparisonState.item1 = report.item1;
    editComparisonState.item2 = report.item2;
    editComparisonState.reportId = report.report_id;
    
    // Populate the form
    elements.editItem1.value = report.item1;
    elements.editItem2.value = report.item2;
    
    // Reset radio buttons and other fields
    elements.item1WinsRadio.checked = true;
    elements.item2WinsRadio.checked = false;
    elements.editDescription.value = '';
    elements.editEmoji.value = '';
    
    // Show the form, hide success/error messages
    elements.editComparisonForm.classList.remove('hidden');
    elements.editSuccess.classList.add('hidden');
    elements.editError.classList.add('hidden');
    
    // Show the modal
    elements.editComparisonModal.classList.remove('hidden');
}

/**
 * Close the edit comparison modal
 */
function closeEditComparisonModal() {
    elements.editComparisonModal.classList.add('hidden');
    resetEditForm();
}

/**
 * Reset the edit comparison form
 */
function resetEditForm() {
    elements.editComparisonForm.classList.remove('hidden');
    elements.editSuccess.classList.add('hidden');
    elements.editError.classList.add('hidden');
}

/**
 * Save changes to a comparison
 * @param {Event} event - The submit event
 */
async function saveComparisonChanges(event) {
    event.preventDefault();
    
    try {
        // Disable submit button while processing
        elements.saveComparisonBtn.disabled = true;
        elements.saveComparisonBtn.textContent = 'Saving...';
        
        // Get form data
        const item1 = elements.editItem1.value;
        const item2 = elements.editItem2.value;
        const item1Wins = elements.item1WinsRadio.checked;
        const item2Wins = elements.item2WinsRadio.checked;
        const description = elements.editDescription.value.trim();
        const emoji = elements.editEmoji.value.trim();
        
        // Validate form data
        if (!description) {
            alert('Please enter a description.');
            return;
        }
        
        if (!emoji) {
            alert('Please enter an emoji.');
            return;
        }
        
        // Call API to update comparison
        await apiService.updateComparison(
            item1,
            item2,
            item1Wins,
            item2Wins,
            description,
            emoji
        );
        
        // If there's a report ID, update its status to "reviewed"
        if (editComparisonState.reportId) {
            await apiService.updateReportStatus(editComparisonState.reportId, 'reviewed');
        }
        
        // Show success message
        elements.editComparisonForm.classList.add('hidden');
        elements.editSuccess.classList.remove('hidden');
        
        // Reload reports to reflect the change
        await loadAdminReports();
        
    } catch (error) {
        console.error('Error saving comparison changes:', error);
        
        // Show error message
        elements.editComparisonForm.classList.add('hidden');
        elements.editError.classList.remove('hidden');
    } finally {
        // Reset button state
        elements.saveComparisonBtn.disabled = false;
        elements.saveComparisonBtn.textContent = 'Save Changes';
    }
}

/**
 * Update pagination controls
 */
function updatePagination() {
    // Update page info text
    elements.pageInfo.textContent = `Page ${scoreboardState.currentPage} of ${scoreboardState.totalPages}`;
    
    // Enable/disable previous button
    elements.prevPageBtn.disabled = scoreboardState.currentPage <= 1;
    
    // Enable/disable next button
    elements.nextPageBtn.disabled = scoreboardState.currentPage >= scoreboardState.totalPages;
}

/**
 * Navigate to a different page
 * @param {number} direction - Direction to navigate (-1 for previous, 1 for next)
 */
function navigateScoreboardPage(direction) {
    const newPage = scoreboardState.currentPage + direction;
    
    // Validate page number
    if (newPage < 1 || newPage > scoreboardState.totalPages) {
        return;
    }
    
    // Update current page and reload data
    scoreboardState.currentPage = newPage;
    loadScoreboardData();
}

/**
 * Apply filters to the scoreboard
 */
function applyScoreboardFilters() {
    // Update state with filter values
    scoreboardState.sortBy = elements.sortBy.value;
    scoreboardState.sortDirection = elements.sortDirection.value;
    
    // Parse score filters
    scoreboardState.minScore = elements.minScore.value ? parseInt(elements.minScore.value) : null;
    scoreboardState.maxScore = elements.maxScore.value ? parseInt(elements.maxScore.value) : null;
    
    // Reset to first page when applying filters
    scoreboardState.currentPage = 1;
    
    // Reload data with new filters
    loadScoreboardData();
}

/**
 * Debounce function to limit how often a function is called
 * @param {Function} func - The function to debounce
 * @param {number} wait - The time to wait in milliseconds
 * @returns {Function} - The debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            func.apply(context, args);
        }, wait);
    };
}

/**
 * Validate user input as they type
 * Provides real-time feedback on input validity
 */
function validateUserInput(event) {
    const input = event.target;
    const value = input.value.trim();
    
    // Clear previous validation messages
    const existingErrorMsg = document.getElementById('input-validation-error');
    if (existingErrorMsg) {
        existingErrorMsg.remove();
    }
    
    // Skip validation for empty input
    if (!value) {
        input.classList.remove('invalid-input');
        return;
    }
    
    // Validate input length
    if (value.length > 50) {
        input.classList.add('invalid-input');
        showInputValidationError(input, 'Input too long (max 50 characters)');
        return;
    }
    
    // Validate input characters
    if (!/^[a-zA-Z0-9\s.,!?-]+$/.test(value)) {
        input.classList.add('invalid-input');
        showInputValidationError(input, 'Input contains invalid characters');
        return;
    }
    
    // Input is valid
    input.classList.remove('invalid-input');
}

/**
 * Show validation error message below input field
 */
function showInputValidationError(inputElement, message) {
    // Create error message element if it doesn't exist
    let errorMsg = document.getElementById('input-validation-error');
    if (!errorMsg) {
        errorMsg = document.createElement('div');
        errorMsg.id = 'input-validation-error';
        errorMsg.className = 'validation-error';
        inputElement.parentNode.insertBefore(errorMsg, inputElement.nextSibling);
    }
    
    // Set error message
    errorMsg.textContent = message;
}

/**
 * Validate user input before form submission
 * Returns an object with validation result and error message
 */
function validateUserInputBeforeSubmit(userInput) {
    // Validate input length
    if (userInput.length > 50) {
        return {
            valid: false,
            message: 'Input too long (max 50 characters)'
        };
    }
    
    // Validate input characters
    if (!/^[a-zA-Z0-9\s.,!?-]+$/.test(userInput)) {
        return {
            valid: false,
            message: 'Input contains invalid characters'
        };
    }
    
    // Check for potentially harmful inputs (simple XSS prevention)
    if (/<script|javascript:|onerror=|onclick=|alert\(|eval\(|document\.cookie/i.test(userInput)) {
        return {
            valid: false,
            message: 'Input contains potentially harmful content'
        };
    }
    
    return { valid: true };
}


// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', initApp);

// Validation styles are now in the external CSS file