# backend/core/report_converter.py
import base64
import markdown2
import os
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from typing import Optional, Dict, Any

class ReportConverter:
    def __init__(self, width: int = 800):
        """
        Initializes the ReportConverter.
        Args:
            width: The width of the output image in pixels.
        """
        self.width = width

    def _create_html(
        self,
        markdown_text: str,
        chart_image_path: str,
        ticker: str,
        interval: str,
        key_data: Dict[str, Any],
        author: Optional[str] = None,
        avatar_path: Optional[str] = None
    ) -> str:
        """
        Converts markdown text and a chart image into a single HTML document.
        """
        html_body = markdown2.markdown(markdown_text, extras=["fenced-code-blocks", "tables"])

        try:
            abs_chart_path = os.path.abspath(chart_image_path)
            with open(abs_chart_path, "rb") as image_file:
                chart_encoded_string = base64.b64encode(image_file.read()).decode()
            chart_data_uri = f"data:image/png;base64,{chart_encoded_string}"
        except FileNotFoundError:
            chart_data_uri = "https://via.placeholder.com/960x540.png?text=Chart+Image+Not+Found"

        avatar_data_uri = ""
        if avatar_path and os.path.exists(avatar_path):
            try:
                with open(os.path.abspath(avatar_path), "rb") as image_file:
                    avatar_encoded_string = base64.b64encode(image_file.read()).decode()
                avatar_data_uri = f"data:image/png;base64,{avatar_encoded_string}"
            except Exception as e:
                print(f"Error encoding avatar image: {e}")

        key_data_html = ""
        data_map = {
            "latest_close": "最新收盘价", "period_high": "周期高点", "period_low": "周期低点",
            "bollinger_upper": "布林带上轨", "bollinger_middle": "布林带中轨", "bollinger_lower": "布林带下轨"
        }
        for key, label in data_map.items():
            value = key_data.get(key, 'N/A')
            key_data_html += f"""
            <div class="dashboard-item">
                <span class="label">{label}</span>
                <span class="value">{value}</span>
            </div>
            """

        disclaimer_text = "本分析内容仅为技术分析参考，非财务建议，仅供参考。投资有风险，入市需谨慎。请根据自身风险承受能力做出投资决策。"
        # 调整为中国时区时间 (UTC+8)
        generation_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

        html_template = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>技术分析报告</title>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
            <style>
                body {{
                    font-family: 'Inter', sans-serif; background-color: #e2e8f0; margin: 0; padding: 40px;
                    -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
                }}
                .container {{
                    width: {self.width}px; margin: 0 auto; background-color: #ffffff; border-radius: 16px;
                    box-shadow: 0 10px 35px rgba(0, 0, 0, 0.08); overflow: hidden;
                }}
                .header {{
                    background-color: #2d3748; color: #ffffff; padding: 25px 40px;
                    display: flex; align-items: center; gap: 20px;
                }}
                .title-block h1 {{ font-size: 1.8em; margin: 0; font-weight: 700; }}
                .title-block h2 {{ font-size: 1em; margin: 0; color: #a0aec0; font-weight: 400; }}
                .content-wrapper {{ padding: 30px 40px; }}
                img.main-chart {{
                    max-width: 100%; border-radius: 10px; margin-bottom: 25px; border: 1px solid #e2e8f0;
                }}
                .dashboard {{
                    display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 30px;
                }}
                .dashboard-item {{
                    background-color: #f7fafc; border: 1px solid #e2e8f0; border-radius: 8px;
                    padding: 12px; text-align: center;
                }}
                .dashboard-item .label {{ display: block; font-size: 0.8em; color: #718096; margin-bottom: 5px;}}
                .dashboard-item .value {{ display: block; font-size: 1.1em; color: #2d3748; font-weight: 600;}}
                .section {{ margin-bottom: 25px; }}
                .section-title {{
                    display: flex; align-items: center; gap: 10px; margin-bottom: 15px;
                    color: #2d3748; font-size: 1.2em; font-weight: 600;
                }}
                .content-card {{
                    background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;
                    padding: 20px; line-height: 1.7; color: #4a5568;
                }}
                .disclaimer-card {{
                    background-color: #fffaf0; border-color: #feebc8; border-left-color: #f6ad55;
                }}
                .disclaimer-card .text {{ font-size: 0.9em; color: #975a16; }}
                .footer {{
                    background-color: #f7fafc; padding: 20px 40px; border-top: 1px solid #e2e8f0;
                    display: flex; justify-content: space-between; align-items: center; font-size: 0.85em;
                }}
                .author-info {{ display: flex; align-items: center; gap: 10px; color: #4a5568; }}
                .avatar {{ width: 32px; height: 32px; border-radius: 50%; }}
                .timestamp {{ color: #718096; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="title-block">
                        <h1>📊 技术分析报告</h1>
                        <h2>{ticker.upper()} | {interval.upper()}</h2>
                    </div>
                </div>
                <div class="content-wrapper">
                    <img src="{chart_data_uri}" alt="Chart" class="main-chart"/>
                    <div class="dashboard">{key_data_html}</div>
                    
                    <div class="section">
                      <div class="section-title"><span>📈 技术分析</span></div>
                      <div class="content-card">{html_body}</div>
                    </div>

                    <div class="section">
                      <div class="section-title"><span>⚠️ 免责声明</span></div>
                      <div class="content-card disclaimer-card">
                        <p class="text">{disclaimer_text}</p>
                      </div>
                    </div>
                </div>
                <div class="footer">
                    <div class="author-info">
                        <img src="{avatar_data_uri}" alt="author" class="avatar">
                        <span>✍️ Analyzed by @{author}</span>
                    </div>
                    <div class="timestamp">📅 Generated on: {generation_time}</div>
                </div>
            </div>
        </body>
        </html>
        """
        return html_template

    def markdown_to_image(
        self,
        markdown_text: str, chart_image_path: str, output_image_path: str,
        ticker: str, interval: str, key_data: Dict[str, Any],
        author: Optional[str] = None, avatar_path: Optional[str] = None
    ) -> bool:
        """
        Converts a markdown string and a chart image into a single image file using sync Playwright.
        """
        print(f"ReportConverter: Starting sync conversion for new design...")
        html_content = self._create_html(
            markdown_text=markdown_text, chart_image_path=chart_image_path,
            ticker=ticker, interval=interval, key_data=key_data,
            author=author, avatar_path=avatar_path
        )
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.set_content(html_content)
                page.locator('.container').screenshot(path=output_image_path)
                browser.close()
                print(f"ReportConverter: Successfully saved new report to {output_image_path}")
                return True
        except Exception as e:
            print(f"ReportConverter: An error occurred during image generation: {e}")
            return False 