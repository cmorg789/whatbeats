/**
 * Utility functions for the WhatBeats application
 * Includes security-focused functions for input sanitization and safe DOM manipulation
 */

/**
 * Sanitize HTML string to prevent XSS attacks
 * Uses DOMPurify library for robust sanitization
 * 
 * @param {string} html - The HTML string to sanitize
 * @returns {string} Sanitized HTML string
 */
function sanitizeHTML(html) {
    if (!html) return '';
    return DOMPurify.sanitize(html, {
        ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'span', 'br'],
        ALLOWED_ATTR: []
    });
}

/**
 * Sanitize plain text by escaping HTML special characters
 * Use this when you want to display text without any HTML formatting
 * 
 * @param {string} text - The text to sanitize
 * @returns {string} Sanitized text with HTML entities escaped
 */
function sanitizeText(text) {
    if (!text) return '';
    const element = document.createElement('div');
    element.textContent = text;
    return element.innerHTML;
}

/**
 * Safely set text content of an element
 * Prevents XSS by using textContent instead of innerHTML
 * 
 * @param {HTMLElement} element - The DOM element to update
 * @param {string} text - The text to set
 */
function setTextContent(element, text) {
    if (!element) return;
    element.textContent = text;
}

/**
 * Safely set HTML content of an element
 * Sanitizes HTML before setting it to prevent XSS
 * 
 * @param {HTMLElement} element - The DOM element to update
 * @param {string} html - The HTML to set
 */
function setHTML(element, html) {
    if (!element) return;
    element.innerHTML = sanitizeHTML(html);
}

/**
 * Create a text node and append it to an element
 * Safer alternative to innerHTML for adding text content
 * 
 * @param {HTMLElement} element - The DOM element to append to
 * @param {string} text - The text to append
 */
function appendText(element, text) {
    if (!element || !text) return;
    const textNode = document.createTextNode(text);
    element.appendChild(textNode);
}

/**
 * Create an element with text content
 * Safer way to create elements with content
 * 
 * @param {string} tagName - The HTML tag name
 * @param {string} text - The text content
 * @param {string} className - Optional CSS class name
 * @returns {HTMLElement} The created element
 */
function createElement(tagName, text, className) {
    const element = document.createElement(tagName);
    if (text) {
        setTextContent(element, text);
    }
    if (className) {
        element.className = className;
    }
    return element;
}

// Export the utility functions
window.utils = {
    sanitizeHTML,
    sanitizeText,
    setTextContent,
    setHTML,
    appendText,
    createElement
};