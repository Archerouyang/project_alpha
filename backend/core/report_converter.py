# backend/core/report_converter.py
import base64
import markdown2
import os
from playwright.sync_api import sync_playwright

class ReportConverter:
    def __init__(self, width: int = 800):
        """
        Initializes the ReportConverter.
        Args:
            width: The width of the output image in pixels.
        """
        self.width = width

    def _create_html(self, markdown_text: str, chart_image_path: str) -> str:
        """
        Converts markdown text and a chart image into a single HTML document.
        """
        # Convert markdown to HTML
        html_body = markdown2.markdown(markdown_text, extras=["fenced-code-blocks", "tables"])
        
        # Encode the chart image in base64
        try:
            # Ensure the path is absolute for reliability in different contexts
            abs_chart_path = os.path.abspath(chart_image_path)
            with open(abs_chart_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
            image_data_uri = f"data:image/png;base64,{encoded_string}"
        except FileNotFoundError:
            print(f"Error: Chart image not found at {abs_chart_path}")
            # Create a placeholder if the image is missing
            image_data_uri = "https://via.placeholder.com/1280x720.png?text=Chart+Image+Not+Found"


        # The final HTML structure with embedded CSS for styling
        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Technical Analysis Report</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    line-height: 1.6;
                    color: #e0e0e0;
                    background-color: #121212;
                    margin: 0;
                    padding: 0; /* Remove padding from body */
                }}
                .container {{
                    width: {self.width}px;
                    margin: 0 auto;
                    background-color: #1e1e1e;
                    /* No border-radius or shadow needed if we screenshot the element directly */
                    padding: 30px;
                    box-sizing: border-box; /* Important for accurate width */
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: #00bcd4; /* Brighter color for titles */
                    margin-top: 1.5em;
                    border-bottom: 1px solid #444;
                    padding-bottom: 0.3em;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 8px;
                    margin-top: 20px;
                    margin-bottom: 20px;
                }}
                code {{
                    background-color: #333;
                    color: #e0e0e0;
                    padding: 0.2em 0.4em;
                    margin: 0;
                    font-size: 85%;
                    border-radius: 3px;
                }}
                pre {{
                    background-color: #2c3e50;
                    color: #f8f9fa;
                    padding: 1em;
                    border-radius: 5px;
                    overflow-x: auto;
                }}
                pre code {{
                    background-color: transparent;
                    padding: 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 1em;
                }}
                th, td {{
                    border: 1px solid #444;
                    padding: 0.75em;
                    text-align: left;
                }}
                th {{
                    background-color: #333;
                    color: #00bcd4;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <img src="{image_data_uri}" alt="Technical Analysis Chart" />
                {html_body}
            </div>
        </body>
        </html>
        """
        return html_template

    def markdown_to_image(
        self,
        markdown_text: str,
        chart_image_path: str,
        output_image_path: str
    ) -> bool:
        """
        Converts a markdown string and a chart image into a single image file using sync Playwright.
        """
        print(f"ReportConverter: Starting sync conversion of markdown to image: {output_image_path}")

        html_content = self._create_html(markdown_text, chart_image_path)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                
                # Set content first
                page.set_content(html_content)
                
                # Find the container element
                container_element = page.query_selector('.container')
                if not container_element:
                    print("Error: Could not find the .container element in the HTML.")
                    browser.close()
                    return False

                # Take screenshot of the specific element
                container_element.screenshot(path=output_image_path)
                browser.close()

                print(f"ReportConverter: Successfully saved final report to {output_image_path}")
                return True
        except Exception as e:
            print(f"ReportConverter: An error occurred during image generation: {e}")
            return False 