# backend/core/report_converter.py
import base64
import markdown2
from playwright.async_api import async_playwright

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
            with open(chart_image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
            image_data_uri = f"data:image/png;base64,{encoded_string}"
        except FileNotFoundError:
            print(f"Error: Chart image not found at {chart_image_path}")
            # Create a placeholder if the image is missing
            image_data_uri = "https://via.placeholder.com/1200x800.png?text=Chart+Image+Not+Found"


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
                    color: #333;
                    background-color: #f8f9fa;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: {self.width}px;
                    margin: 0 auto;
                    background-color: #fff;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    padding: 30px;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: #2c3e50;
                    margin-top: 1.5em;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 8px;
                    margin-top: 20px;
                    margin-bottom: 20px;
                }}
                code {{
                    background-color: #e9ecef;
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
                    border: 1px solid #dee2e6;
                    padding: 0.75em;
                    text-align: left;
                }}
                th {{
                    background-color: #f8f9fa;
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

    async def markdown_to_image(
        self,
        markdown_text: str,
        chart_image_path: str,
        output_image_path: str
    ) -> bool:
        """
        Converts a markdown string and a chart image into a single image file.
        """
        print(f"ReportConverter: Starting conversion of markdown to image: {output_image_path}")

        html_content = self._create_html(markdown_text, chart_image_path)

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                
                await page.set_viewport_size({ "width": self.width + 60, "height": 1080 })
                
                await page.set_content(html_content)
                
                container_element = await page.query_selector('.container')
                if not container_element:
                    print("Error: Could not find the .container element in the HTML.")
                    await browser.close()
                    return False

                await container_element.screenshot(path=output_image_path)
                await browser.close()

                print(f"ReportConverter: Successfully saved final report to {output_image_path}")
                return True
        except Exception as e:
            print(f"ReportConverter: An error occurred during image generation: {e}")
            return False 