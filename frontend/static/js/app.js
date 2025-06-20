document.addEventListener('DOMContentLoaded', () => {
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const chatContainer = document.getElementById('chat-container');

    // Display the initial welcome message in persona
    const welcomeText = `主人，您好！我是您的专属K线分析助手～ (´∀｀)♡<br>
        <br>
        使用说明：<br>
        1. 必填：资产代码（如 <code>AAPL</code>、<code>BTC-USD</code>）<br>
        2. 可选：时间间隔（如 <code>5min</code>、<code>15min</code>、<code>30min</code>、<code>1h</code>、<code>1d</code>）<br>
        3. 可选：交易所（仅加密货币，如 <code>BTC-USD KRAKEN</code>）<br>
        <br>
        示例：<br>
        <code>AAPL 5min</code><br>
        <code>TSLA 1h</code><br>
        <code>MSFT 30min</code><br>
        <code>GOOG 1d</code><br>
        <code>BTC-USD KRAKEN</code><br>
        <br>
        我随时待命哦！(｡･ω･｡)ﾉ`;
    appendMessage(welcomeText, 'ai');

    sendButton.addEventListener('click', handleSend);
    userInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault(); // Prevents new line on enter
            handleSend();
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
     * Handles the main logic of sending user input to the backend.
     * It first validates the instruction, then triggers the analysis if valid.
     */
    async function handleSend() {
        const inputText = userInput.value.trim();
        if (!inputText) return;

        appendMessage(inputText, 'user');
        userInput.value = '';
        
        showLoadingIndicator("正在理解您的指令...");

        try {
            // Step 1: Validate and correct the instruction via the LLM
            const validationResponse = await fetch('/api/validate_instruction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_input: inputText }),
            });

            const validationData = await validationResponse.json();

            if (!validationResponse.ok) {
                hideLoadingIndicator();
                appendMessage(validationData.detail || '哦豁，验证指令的时候服务器出错了...', 'error');
                return;
            }
            
            // Show the AI's "thought" or clarification
            hideLoadingIndicator();
            if (validationData.explanation) {
                appendMessage(validationData.explanation, 'ai');
            }

            // Step 2: Based on validation, either proceed to analysis or stop
            if (validationData.status === 'valid') {
                showLoadingIndicator("收到指令！正在生成分析报告...");
                await callAnalysisAPI(validationData.command);
            } else {
                // For "clarification_needed" or "irrelevant", we just showed the message.
                // The flow stops here, waiting for new user input.
                hideLoadingIndicator();
            }

        } catch (error) {
            hideLoadingIndicator();
            appendMessage(`呜哇，连接好像断开啦... (${error.message})`, 'error');
        }
    }

    /**
     * Parses the corrected command and calls the analysis API.
     * @param {string} command The validated and corrected command string.
     */
    async function callAnalysisAPI(command) {
        // Parse the command string provided by the validation LLM
        const parts = command.split(/\s+/).filter(p => p);
        const stockSymbol = parts[0];
        const exchange = parts.length > 1 && !isInterval(parts[1]) ? parts[1] : null;
        const timeInterval = parts.find(isInterval) || '1d';
        const numCandlesStr = parts.find(p => /^\d+$/.test(p) && p !== stockSymbol);
        const numCandles = numCandlesStr ? parseInt(numCandlesStr, 10) : 150;
        
        const requestData = {
            ticker: stockSymbol,
            interval: timeInterval,
            num_candles: numCandles,
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
                appendMessage(`唔...服务器在生成报告时好像出了一点小问题...(${detail})，请稍后再试一下吧！`, 'error');
                return;
            }

            const data = await response.json();
            displayAnalysis(data);

        } catch (error) {
            hideLoadingIndicator();
            appendMessage(`呜哇，连接分析服务的时候断开啦... (${error.message})`, 'error');
        }
    }
    
    function showLoadingIndicator(message = "分析中...") {
        const existingIndicator = document.querySelector('.loading-message');
        if (existingIndicator) {
            existingIndicator.querySelector('p').innerHTML = message;
            return;
        }

        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message loading-message';
        loadingDiv.innerHTML = `<p>${message}</p>`;
        chatContainer.appendChild(loadingDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function hideLoadingIndicator() {
        const loadingIndicator = document.querySelector('.loading-message');
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
        // 支持格式：5min, 5m, 15min, 30min, 1h, 1d
        return /^\d+(?:min|m|h|d)$/i.test(s);
    }
}); 