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
        // A simple regex to check for formats like 1h, 4h, 1d, 1w, 1mo
        return /^\d+[hdwmHWMoO]+$/.test(s);
    }
}); 