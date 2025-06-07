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

    /**
     * Appends a message to the chat container.
     * @param {string} text The message content.
     * @param {string} type The message type ('user', 'ai', 'error', 'loading').
     */
    function appendMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const p = document.createElement('p');
        p.innerHTML = text; // Use innerHTML to render HTML tags like <br>
        messageDiv.appendChild(p);

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    /**
     * Generates a friendly, persona-driven error message for invalid user input.
     * @param {string} userInput The original (incorrect) user input.
     * @returns {string} A friendly error message.
     */
    function getFriendlyErrorMessage(userInput) {
        const scenarios = {
            empty: [
                "主人，你想分析哪只股票呀？请告诉我它的代码哦！✨ 比如：AAPL",
                "呜哇...好像没有看到股票代码呢...请告诉我你想分析谁呀？(^o^)/"
            ],
            generic: [
                "唔...这个指令我有点看不懂耶～(>ω<) 能不能检查一下格式是不是像 'AAPL 1h' 这样的呢？",
                "啊哦，好像哪里不对啦～ 指令的格式是 '[代码] [交易所] [周期]' 哦！",
                "这个是什么咒语吗？(・_・;) 我需要 'TSLA 4h' 或 'BTC-USD KRAKEN' 这样的指令才能开始分析呢！"
            ]
        };
    
        let messages = scenarios.generic;
        if (!userInput || userInput.trim() === "") {
            messages = scenarios.empty;
        }
        
        const randomIndex = Math.floor(Math.random() * messages.length);
        return messages[randomIndex];
    }

    /**
     * Handles the main logic of parsing input, validating, and calling the API.
     */
    async function analyzeStock() {
        const inputText = userInput.value.trim();
        
        // Add user message to chat and clear input
        appendMessage(inputText, 'user');
        userInput.value = '';
        
        showLoadingIndicator();

        const parts = inputText.split(/\s+/).filter(p => p);
        const tickerRegex = /^[A-Z0-9\.-]+$/i;

        // --- Input Validation ---
        if (parts.length === 0 || !tickerRegex.test(parts[0])) {
            hideLoadingIndicator();
            const friendlyError = getFriendlyErrorMessage(inputText);
            appendMessage(friendlyError, 'error');
            return; // Stop execution if input is invalid
        }

        const stockSymbol = parts[0].toUpperCase();
        
        let exchange = null;
        let timeInterval = '1d';
        let num_candles = 150;

        if (parts.length === 2) {
            if (isInterval(parts[1])) {
                timeInterval = parts[1];
            } else {
                exchange = parts[1].toUpperCase();
            }
        } else if (parts.length >= 3) {
            exchange = parts[1].toUpperCase();
            timeInterval = parts[2];
        }

        const requestData = {
            ticker: stockSymbol,
            interval: timeInterval,
            num_candles: num_candles,
            exchange: exchange,
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
                const detail = errorData.detail || `HTTP error ${response.status}`;
                appendMessage(`唔...服务器好像出了一点小问题...(${detail})，请稍后再试一下吧！`, 'error');
                return;
            }

            const data = await response.json();
            displayAnalysis(data);

        } catch (error) {
            hideLoadingIndicator();
            appendMessage(`呜哇，连接好像断开啦... (${error.message})`, 'error');
        }
    }
    
    function showLoadingIndicator() {
        const existingIndicator = document.querySelector('.loading-indicator');
        if (existingIndicator) return;

        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message loading-message';
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

    /**
     * Displays the final analysis report image.
     * @param {object} data The API response data, containing the image.
     */
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
            errorP.textContent = '抱歉，分析报告生成了，但是没有返回图片呢...';
            messageDiv.appendChild(errorP);
        }

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    /**
     * Checks if a given string matches a time interval format.
     * @param {string} s The string to check.
     * @returns {boolean}
     */
    function isInterval(s) {
        // A simple regex to check for formats like 1h, 4h, 1d, 1w
        return /^\d+[hdw]$/i.test(s);
    }
}); 