document.addEventListener('DOMContentLoaded', () => {
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const chatContainer = document.getElementById('chat-container');

    // Display the initial welcome message
    const welcomeText = `您好！请输入分析指令。格式：<br>
        <strong>[代码] [交易所(可选)] [时间周期(可选)]</strong>
        <br><br>
        <strong>说明:</strong><br>
        - <strong>代码:</strong> 股票代码或加密货币对 (例如: AAPL, BTC-USD)。<br>
        - <strong>交易所:</strong> 通常用于加密货币 (例如: KRAKEN, BINANCE)，股票可省略。<br>
        - <strong>时间周期:</strong> 例如 1h, 4h, 1d (日线), 1w (周线)。默认为 1d。
        <br><br>
        <strong>示例:</strong><br>
        <code>AAPL</code><br>
        <code>TSLA 4h</code><br>
        <code>BTC-USD KRAKEN 1h</code>`;
    appendMessage(welcomeText, 'ai');

    sendButton.addEventListener('click', analyzeStock);
    userInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            analyzeStock();
        }
    });

    function appendMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const p = document.createElement('p');
        p.innerHTML = text; // Use innerHTML to render line breaks
        messageDiv.appendChild(p);

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    async function analyzeStock() {
        const inputText = userInput.value.trim();
        if (!inputText) return;

        appendMessage(inputText, 'user');
        userInput.value = '';
        showLoadingIndicator();

        const parts = inputText.split(/\s+/).filter(p => p); // Filter out empty strings
        const stockSymbol = parts[0].toUpperCase();
        
        // Default values
        let exchange = null;
        let timeInterval = '1d';
        let num_candles = 150;

        // Logic to differentiate between exchange and interval
        if (parts.length === 2) {
            // Could be "BTC 1h" or "BTC KRAKEN"
            if (isInterval(parts[1])) {
                timeInterval = parts[1];
            } else {
                exchange = parts[1].toUpperCase();
            }
        } else if (parts.length >= 3) {
            // Assumes format "BTC KRAKEN 1h"
            exchange = parts[1].toUpperCase();
            timeInterval = parts[2];
        }

        const requestData = {
            ticker: stockSymbol,
            interval: timeInterval,
            num_candles: num_candles,
            exchange: exchange, // Will be null if not provided
        };

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData),
            });

            hideLoadingIndicator();

            if (!response.ok) {
                const errorData = await response.json();
                const detail = errorData.detail || `HTTP error! status: ${response.status}`;
                displayError(`分析失败: ${detail}`);
                return;
            }

            const data = await response.json();
            displayAnalysis(data);

        } catch (error) {
            hideLoadingIndicator();
            displayError(`请求错误: ${error.message}`);
        }
    }
    
    function showLoadingIndicator() {
        const existingIndicator = document.querySelector('.loading-indicator');
        if (existingIndicator) return;

        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message ai-message loading-indicator';
        loadingDiv.innerHTML = '<p>分析中...</p>';
        chatContainer.appendChild(loadingDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function hideLoadingIndicator() {
        const loadingIndicator = document.querySelector('.loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
    }

    function displayAnalysis(data) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ai-message';

        if (data.image) {
            const img = document.createElement('img');
            img.src = `data:image/png;base64,${data.image}`;
            img.alt = "Analysis Report";
            messageDiv.appendChild(img);
        } else {
            const errorP = document.createElement('p');
            errorP.textContent = '抱歉，生成分析报告失败，未返回图片。';
            messageDiv.appendChild(errorP);
        }

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Helper function to check if a string looks like a time interval
    function isInterval(s) {
        return /^\d+[hdw]$/i.test(s) || /日线|周线|月线|小时/.test(s);
    }

    function displayError(errorMessage) {
        appendMessage(errorMessage, 'error');
    }
}); 