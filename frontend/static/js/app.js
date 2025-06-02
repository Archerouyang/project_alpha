document.addEventListener('DOMContentLoaded', () => {
    const stockCodeInput = document.getElementById('stock-code');
    const analyzeButton = document.getElementById('analyze-button');
    
    const resultsSection = document.getElementById('results-section');
    const reportTitle = document.getElementById('report-title');
    const chartImage = document.getElementById('chart-image');
    const analysisText = document.getElementById('analysis-text');
    
    const loadingSection = document.getElementById('loading-section');
    const errorSection = document.getElementById('error-section');
    const errorMessage = document.getElementById('error-message');

    analyzeButton.addEventListener('click', async () => {
        const stockCode = stockCodeInput.value.trim().toUpperCase();
        if (!stockCode) {
            showError("Please enter a stock code.");
            return;
        }

        showLoading(true);
        hideError();
        hideResults();

        try {
            const formData = new FormData();
            formData.append('stock_code', stockCode);

            const response = await fetch('/api/analyze/', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: "An unknown error occurred."}) );
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.error) {
                showError(result.error);
            } else if (result.data) {
                displayResults(result.data);
            } else {
                // Fallback for initial backend responses that might not match final schema
                if (result.stock_code && result.chart_image_url && result.analysis_text){
                    displayResults(result); 
                } else if (result.stock_code && result.status === "analysis_pending") { 
                    showError(`Analysis for ${result.stock_code} is pending. Backend placeholder response.`);
                } else {
                    showError("Received an unexpected response format from the server.");
                }
            }

        } catch (error) {
            console.error("Fetch error:", error);
            showError(error.message || "Failed to fetch analysis. Check console for details.");
        } finally {
            showLoading(false);
        }
    });

    function displayResults(data) {
        reportTitle.textContent = `Analysis Report for ${data.stock_code}`;
        chartImage.src = data.chart_image_url;
        chartImage.alt = `${data.stock_code} Chart`;
        analysisText.textContent = data.analysis_text;
        resultsSection.style.display = 'block';
    }

    function showLoading(isLoading) {
        loadingSection.style.display = isLoading ? 'block' : 'none';
    }

    function hideResults() {
        resultsSection.style.display = 'none';
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorSection.style.display = 'block';
    }

    function hideError() {
        errorSection.style.display = 'none';
    }
}); 