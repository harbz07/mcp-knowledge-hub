// Sanctuary MCP Knowledge Hub JavaScript
const API_URL = 'https://knowledge-hub-mcp.harveytagalicud7.workers.dev';

// Create animated stars
function createStars() {
    const starsContainer = document.querySelector('.stars');
    const starCount = 50;
    
    for (let i = 0; i < starCount; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        star.style.cssText = `
            position: absolute;
            width: 2px;
            height: 2px;
            background: rgba(255, 255, 255, ${Math.random() * 0.8 + 0.2});
            border-radius: 50%;
            left: ${Math.random() * 100}%;
            top: ${Math.random() * 100}%;
            animation: twinkle ${Math.random() * 3 + 2}s infinite;
            animation-delay: ${Math.random() * 2}s;
        `;
        starsContainer.appendChild(star);
    }
}

// Tab functionality
function initializeTabs() {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Remove active class from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            // Add active class to clicked tab
            this.classList.add('active');
        });
    });
}

// Search functionality
function initializeSearch() {
    const searchInput = document.querySelector('.search-input');
    searchInput.addEventListener('input', function() {
        const query = this.value.toLowerCase();
        // Filter cards based on search query
        filterCards(query);
    });
}

function filterCards(query) {
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        if (text.includes(query) || query === '') {
            card.style.display = 'block';
            card.style.opacity = '1';
        } else {
            card.style.opacity = '0.3';
        }
    });
}

// MCP API Functions
async function makeRequest(method, arguments) {
    const requestBody = {
        jsonrpc: "2.0",
        id: Math.floor(Math.random() * 10000),
        method: "tools/call",
        params: {
            name: method,
            arguments: arguments
        }
    };

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error.message);
        }
        
        return data.result;
    } catch (error) {
        throw new Error(`Request failed: ${error.message}`);
    }
}

// Update familiar data from MCP
async function updateFamiliarData() {
    try {
        const result = await makeRequest('get_recent_contexts', { limit: 5 });
        updateFamiliarTable(result.content);
    } catch (error) {
        console.error('Failed to update familiar data:', error);
    }
}

function updateFamiliarTable(contexts) {
    const tableBody = document.querySelector('.familiars-overview tbody');
    if (!tableBody) return;

    // Clear existing rows
    tableBody.innerHTML = '';

    // Add context data as familiars
    contexts.forEach((context, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${context.source || 'Unknown'}</td>
            <td>${context.tags ? context.tags[0] : 'Context'}</td>
            <td>${new Date().toLocaleDateString()}</td>
        `;
        tableBody.appendChild(row);
    });
}

// Update ritual timer
function updateTimer() {
    const timeElement = document.querySelector('.time');
    if (!timeElement) return;

    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    timeElement.textContent = `${hours}:${minutes}`;
}

// Update Luna's reflection prompts from MCP
async function updateLunaPrompts() {
    try {
        const result = await makeRequest('search_contexts', { 
            query: 'reflection', 
            limit: 3 
        });
        
        const promptList = document.querySelector('.prompt-list');
        if (promptList && result.content) {
            promptList.innerHTML = '';
            result.content.forEach(context => {
                const promptItem = document.createElement('div');
                promptItem.className = 'prompt-item';
                promptItem.textContent = `💎 ${context.content.substring(0, 30)}...`;
                promptList.appendChild(promptItem);
            });
        }
    } catch (error) {
        console.error('Failed to update Luna prompts:', error);
    }
}

// Update altars from MCP files
async function updateAltars() {
    try {
        const result = await makeRequest('list_files', { limit: 5 });
        
        const altarLists = document.querySelectorAll('.altar-list');
        altarLists.forEach((altarList, index) => {
            if (result.content && result.content[index]) {
                const altarItem = document.createElement('div');
                altarItem.className = 'altar-item';
                altarItem.innerHTML = `
                    <span>${result.content[index].filename || 'Unknown Altar'}</span>
                    <span class="arrow">→</span>
                `;
                altarList.appendChild(altarItem);
            }
        });
    } catch (error) {
        console.error('Failed to update altars:', error);
    }
}

// Network graph animation
function animateNetworkGraph() {
    const nodes = document.querySelectorAll('.node');
    nodes.forEach((node, index) => {
        node.style.animationDelay = `${index * 0.5}s`;
        node.style.animation = 'pulse 2s ease-in-out infinite';
    });
}

// Add pulse animation
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.7; }
        50% { transform: scale(1.1); opacity: 1; }
    }
`;
document.head.appendChild(style);

// Initialize everything
document.addEventListener('DOMContentLoaded', function() {
    // Create animated stars
    createStars();
    
    // Initialize tabs
    initializeTabs();
    
    // Initialize search
    initializeSearch();
    
    // Update timer every minute
    updateTimer();
    setInterval(updateTimer, 60000);
    
    // Update data from MCP
    updateFamiliarData();
    updateLunaPrompts();
    updateAltars();
    
    // Animate network graph
    animateNetworkGraph();
    
    // Add hover effects to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Add click handlers for interactive elements
    const altarItems = document.querySelectorAll('.altar-item');
    altarItems.forEach(item => {
        item.addEventListener('click', function() {
            // Add glow effect
            this.style.textShadow = '0 0 10px #7dd3fc';
            setTimeout(() => {
                this.style.textShadow = 'none';
            }, 1000);
        });
    });
    
    // Add click handlers for ritual items
    const ritualItems = document.querySelectorAll('.ritual-item');
    ritualItems.forEach(item => {
        item.addEventListener('click', function() {
            // Add glow effect
            this.style.textShadow = '0 0 10px #7dd3fc';
            setTimeout(() => {
                this.style.textShadow = 'none';
            }, 1000);
        });
    });
});

// Periodic data updates
setInterval(() => {
    updateFamiliarData();
    updateLunaPrompts();
    updateAltars();
}, 30000); // Update every 30 seconds 