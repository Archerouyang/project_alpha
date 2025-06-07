document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    const handleUserInput = () => {
        const command = userInput.value.trim();
        if (!command) return;

        appendMessage(command, 'user');
        userInput.value = '';
        processCommand(command);
    };

    sendButton.addEventListener('click', handleUserInput);
    userInput.addEventListener('keyup', (event) => {
        if (event.key === 'Enter') {
            handleUserInput();
        }
    });

    function appendMessage(text, type, data = null) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${type}-message`);

        if (type === 'ai' && data) {
            // Create image element
            if (data.image_base64) {
                const img = document.createElement('img');
                img.src = data.image_base64; // The string already includes "data:image/png;base64,"
                img.alt = 'Analysis Chart';
                messageDiv.appendChild(img);
            }
            // Create text content element
            if (data.analysis_text) {
                const textContent = document.createElement('div');
                textContent.classList.add('analysis-content');
                textContent.textContent = data.analysis_text; // Use textContent to handle \n correctly with 'white-space: pre-wrap'
                messageDiv.appendChild(textContent);
            }
        } else {
            messageDiv.textContent = text;
        }

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return messageDiv;
    }

    function processCommand(command) {
        // New simplified regex: symbol is mandatory, interval is optional
        // Example matches: "TSLA", "TSLA 4h", "AAPL 日线"
        const commandRegex = /^([A-Z0-9\.-]+)\s*(\S+)?$/i;
        const match = command.match(commandRegex);

        if (!match) {
            appendMessage('格式错误，请输入：[股票代码] [时间周期(可选)]', 'error');
            return;
        }

        const symbol = match[1];
        const intervalRaw = match[2]; // This might be undefined if not provided

        // Map user-friendly intervals to API-friendly intervals
        const intervalMap = {
            "1小时": "1h", "4小时": "4h", "日线": "1d", "周线": "1w", "月线": "1mo",
            "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w", "1mo": "1mo"
        };
        // Default to '1d' if interval is not provided or not in map
        const interval = intervalRaw ? (intervalMap[intervalRaw] || '1d') : '1d';

        const payload = {
            ticker: symbol.toUpperCase(),
            interval: interval,
            num_candles: 150,
            // These fields are no longer parsed from the input but could be added back
            // exchange: undefined,
            // language: undefined,
        };

        callAnalyzeApi(payload);
    }

    async function callAnalyzeApi(payload) {
        const loadingMessage = appendMessage('分析中，请稍候...', 'loading');

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            chatContainer.removeChild(loadingMessage);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            appendMessage(null, 'ai', data);

        } catch (error) {
            if (chatContainer.contains(loadingMessage)) {
                chatContainer.removeChild(loadingMessage);
            }
            appendMessage(`分析失败: ${error.message}`, 'error');
            console.error('Fetch error:', error);
        }
    }

    function displayAnalysis(data) {
        const chatContainer = document.getElementById('chat-container');

        // Create a new message container for the AI's response
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ai-message';

        // Create the image element for the report
        if (data.image) {
            const img = document.createElement('img');
            img.src = `data:image/png;base64,${data.image}`;
            img.alt = "Analysis Report";
            img.className = "analysis-image"; // Use a specific class for styling if needed
            messageDiv.appendChild(img);
        } else {
            // If there's no image, display an error message
            const errorP = document.createElement('p');
            errorP.textContent = '抱歉，生成分析报告失败，未返回图片。';
            messageDiv.appendChild(errorP);
        }

        // Append the new message to the chat container and scroll down
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function displayError(errorMessage) {
        appendMessage(errorMessage, 'error');
    }
}); 