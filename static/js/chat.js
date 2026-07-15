document.addEventListener('DOMContentLoaded', () => {
    // Load initial database counts
    fetchStats();

    // Auto-resize textarea
    const chatInput = document.getElementById('chat-input');
    chatInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });

    // Enter key submits (without shift)
    chatInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitMessage();
        }
    });
});

/**
 * Fetch and update database statistics in the sidebar
 */
async function fetchStats() {
    try {
        const response = await fetch('/api/db-stats/');
        const data = await response.json();
        if (data.success) {
            document.getElementById('stat-categories').innerText = data.stats.categories.toLocaleString();
            document.getElementById('stat-products').innerText = data.stats.products.toLocaleString();
            document.getElementById('stat-users').innerText = data.stats.users.toLocaleString();
            document.getElementById('stat-orders').innerText = data.stats.orders.toLocaleString();
            document.getElementById('stat-transactions').innerText = data.stats.transactions.toLocaleString();
            document.getElementById('stat-total').innerText = data.stats.total.toLocaleString();
        }
    } catch (error) {
        console.error('Failed to fetch statistics:', error);
    }
}

/**
 * Submit natural language question to the API
 */
async function submitMessage() {
    const chatInput = document.getElementById('chat-input');
    const messageText = chatInput.value.trim();
    if (!messageText) return;

    // Reset input
    chatInput.value = '';
    chatInput.style.height = 'auto';

    // 1. Render User Message bubble
    appendMessage(messageText, 'user');

    // 2. Render Typing Loader
    const loaderId = appendTypingLoader();
    scrollToBottom();

    try {
        const response = await fetch('/api/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: messageText })
        });
        
        const data = await response.json();
        removeTypingLoader(loaderId);

        if (data.success) {
            // Append AI response with details
            appendAIResponse(data.explanation, data.sql, data.columns, data.rows);
            // Refresh stats in case a read query triggers cache update or for parity
            fetchStats();
        } else {
            // Check if SQL was generated despite database execution error
            const sql = data.sql || '';
            const explanation = data.explanation || 'Sorry, I encountered an issue executing that command.';
            const errorMsg = data.error || 'Unknown database error.';
            appendAIError(explanation, sql, errorMsg);
        }
    } catch (error) {
        removeTypingLoader(loaderId);
        appendMessage('Failed to communicate with AI agent. Please make sure the server is online.', 'ai', true);
    }
    scrollToBottom();
}

/**
 * Helper to click suggestions
 */
function sendSampleQuestion(question) {
    const chatInput = document.getElementById('chat-input');
    chatInput.value = question;
    chatInput.focus();
    // Simulate resize
    chatInput.style.height = 'auto';
    chatInput.style.height = chatInput.scrollHeight + 'px';
    submitMessage();
}

/**
 * Reset database via API
 */
async function resetDatabase() {
    const btn = document.getElementById('btn-reset-db');
    const originalText = btn.innerHTML;
    
    if (!confirm('Are you sure you want to delete all present data and regenerate 10,000+ realistic ecommerce rows? This takes around 2 seconds.')) {
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Seeding Database...';

    // Notify in chat
    appendMessage('System instruction: Purging database and generating 10,000+ new records...', 'user');
    const loaderId = appendTypingLoader();
    scrollToBottom();

    try {
        const response = await fetch('/api/reset-db/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        const data = await response.json();
        removeTypingLoader(loaderId);

        if (data.success) {
            appendMessage(data.message, 'ai');
            fetchStats();
        } else {
            appendMessage(`Database Seeding failed: ${data.error}`, 'ai', true);
        }
    } catch (error) {
        removeTypingLoader(loaderId);
        appendMessage('Network failure during database reset.', 'ai', true);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
        scrollToBottom();
    }
}

/**
 * Append standard chat message
 */
function appendMessage(text, sender, isError = false) {
    const messagesContainer = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message message-${sender}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = sender === 'user' ? '<i class="bi bi-person-fill"></i>' : '<i class="bi bi-robot"></i>';

    const content = document.createElement('div');
    content.className = 'message-content';
    if (isError) {
        content.classList.add('border-danger', 'text-danger', 'bg-danger-subtle');
    }
    
    // Convert newlines to breaks
    content.innerHTML = `<p class="mb-0">${text.replace(/\n/g, '<br>')}</p>`;

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(content);
    messagesContainer.appendChild(msgDiv);
}

/**
 * Render typing animation
 */
function appendTypingLoader() {
    const id = 'loader_' + Date.now();
    const messagesContainer = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message message-ai`;
    msgDiv.id = id;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="bi bi-robot"></i>';

    const content = document.createElement('div');
    content.className = 'message-content';
    content.innerHTML = `
        <div class="typing-loader">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        </div>
    `;

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(content);
    messagesContainer.appendChild(msgDiv);
    return id;
}

function removeTypingLoader(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

/**
 * Render AI response with SQL block and Results Table
 */
function appendAIResponse(explanation, sql, columns, rows) {
    const messagesContainer = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message message-ai w-100'; // Make it wider on large screens

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="bi bi-robot"></i>';

    const content = document.createElement('div');
    content.className = 'message-content w-100';

    // 1. Natural Language Explanation
    let html = `<p class="mb-2"><strong>Result:</strong> ${explanation}</p>`;

    // 2. Collapsible SQL Panel
    if (sql) {
        const uniqueCollapseId = 'sql_' + Date.now();
        html += `
            <div class="query-block mt-3">
                <div class="query-header">
                    <span>Generated PostgreSQL Query</span>
                    <div class="d-flex align-items-center gap-2">
                        <button class="btn-copy-sql" onclick="copyToClipboard('${escapeJsString(sql)}', this)">
                            <i class="bi bi-clipboard me-1"></i>Copy
                        </button>
                        <a class="text-light" data-bs-toggle="collapse" href="#${uniqueCollapseId}" role="button" aria-expanded="false">
                            <i class="bi bi-chevron-down"></i>
                        </a>
                    </div>
                </div>
                <div class="collapse show" id="${uniqueCollapseId}">
                    <pre class="query-code"><code>${escapeHtml(sql)}</code></pre>
                </div>
            </div>
        `;
    }

    // 3. Tabular Query Results
    if (columns && columns.length > 0) {
        html += `<div class="table-responsive-custom mt-3">`;
        html += `<table class="table-custom"><thead><tr>`;
        columns.forEach(col => {
            html += `<th>${escapeHtml(col)}</th>`;
        });
        html += `</tr></thead><tbody>`;

        if (rows && rows.length > 0) {
            rows.forEach(row => {
                html += `<tr>`;
                row.forEach(val => {
                    let cellVal = val === null ? '<em class="text-muted">null</em>' : escapeHtml(String(val));
                    html += `<td>${cellVal}</td>`;
                });
                html += `</tr>`;
            });
        } else {
            html += `<tr><td colspan="${columns.length}" class="text-center text-muted py-3">No matching records found.</td></tr>`;
        }
        
        html += `</tbody></table></div>`;
    } else {
        html += `<p class="text-muted mt-2 mb-0"><i class="bi bi-info-circle me-1"></i>No data columns returned by query.</p>`;
    }

    content.innerHTML = html;
    msgDiv.appendChild(avatar);
    msgDiv.appendChild(content);
    messagesContainer.appendChild(msgDiv);
}

/**
 * Render AI error block
 */
function appendAIError(explanation, sql, errorMsg) {
    const messagesContainer = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message message-ai w-100';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="bi bi-robot"></i>';

    const content = document.createElement('div');
    content.className = 'message-content w-100';

    let html = `<p class="mb-2"><strong>Result:</strong> ${explanation}</p>`;

    if (sql) {
        const uniqueCollapseId = 'sql_' + Date.now();
        html += `
            <div class="query-block mt-3">
                <div class="query-header">
                    <span>Generated SQL (Failed to Execute)</span>
                    <div class="d-flex align-items-center gap-2">
                        <button class="btn-copy-sql" onclick="copyToClipboard('${escapeJsString(sql)}', this)">
                            <i class="bi bi-clipboard me-1"></i>Copy
                        </button>
                        <a class="text-light" data-bs-toggle="collapse" href="#${uniqueCollapseId}" role="button" aria-expanded="false">
                            <i class="bi bi-chevron-down"></i>
                        </a>
                    </div>
                </div>
                <div class="collapse show" id="${uniqueCollapseId}">
                    <pre class="query-code" style="color: #ef4444;"><code style="color: #ef4444;">${escapeHtml(sql)}</code></pre>
                </div>
            </div>
        `;
    }

    html += `
        <div class="alert alert-danger mt-3 mb-0" role="alert">
            <h5 class="alert-heading h6 mb-1"><i class="bi bi-exclamation-triangle-fill me-2"></i>Database Error</h5>
            <p class="mb-0 small" style="font-family: monospace;">${escapeHtml(errorMsg)}</p>
        </div>
    `;

    content.innerHTML = html;
    msgDiv.appendChild(avatar);
    msgDiv.appendChild(content);
    messagesContainer.appendChild(msgDiv);
}

/**
 * Scroll message history to the bottom
 */
function scrollToBottom() {
    const chatContainer = document.getElementById('chat-messages');
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * HTML Escaper
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

/**
 * Escape single quotes for inline javascript strings
 */
function escapeJsString(str) {
    return str.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\n/g, '\\n').replace(/\r/g, '\\r');
}

/**
 * Copy button clipboard functionality
 */
function copyToClipboard(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
        const icon = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-check2 text-success me-1"></i>Copied!';
        setTimeout(() => {
            btn.innerHTML = icon;
        }, 2000);
    }).catch(err => {
        console.error('Could not copy SQL query:', err);
    });
}
