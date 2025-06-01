import gradio as gr
import os
import tempfile
from typing import Tuple, Optional

os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

from core.code_agent import CodeAgent, ExecutionResult


class CodeGeneratorUI:
    """Clean UI wrapper for the CodeAgent with proper separation of concerns."""

    def __init__(self):
        self.agent = CodeAgent(verbose=False)

    def generate_and_execute_code(
        self, 
        user_request: str, 
        max_retries: int
    ) -> Tuple[str, str, str, str, Optional[str]]:
        """
        Generate and execute code based on user request.

        Returns:
            Tuple of (status_html, final_answer, generated_code, execution_info, download_file)
        """
        if not user_request.strip():
            return (
                self._create_status_html("error", "❌ Error", "Please enter a valid request"),
                "",
                "",
                "",
                None
            )

        self.agent.max_retries = max_retries

        try:
            result = self.agent.generate_and_execute(user_request)

            status_html = self._create_status_html_from_result(result)
            final_answer = result.output or "Code executed successfully (no output)" if result.success else f"**Error:** {result.error_message}"
            generated_code = self.agent.get_full_code(result) or "No code generated"
            execution_info = self._create_execution_info(result)
            download_file = self._create_download_file(generated_code) if result.success else None

            return status_html, final_answer, generated_code, execution_info, download_file

        except Exception as e:
            error_status = self._create_status_html("error", "❌ Fatal Error", f"An unexpected error occurred: {str(e)}")
            return error_status, f"**Fatal Error:** {str(e)}", "", "", None

    def generate_code_only(
        self, 
        user_request: str, 
        max_retries: int
    ) -> Tuple[str, str, str, Optional[str]]:
        """
        Generate code without executing it.

        Returns:
            Tuple of (status_html, generated_code, execution_info, download_file)
        """
        if not user_request.strip():
            return (
                self._create_status_html("error", "❌ Error", "Please enter a valid request"),
                "",
                "",
                None
            )

        self.agent.max_retries = max_retries

        try:
            result = self.agent.generate_code_only(user_request)

            status_html = self._create_status_html_from_result(result)
            generated_code = self.agent.get_full_code(result) or "No code generated"
            execution_info = self._create_execution_info(result)
            download_file = self._create_download_file(generated_code) if result.success else None

            return status_html, generated_code, execution_info, download_file

        except Exception as e:
            error_status = self._create_status_html("error", "❌ Fatal Error", f"An unexpected error occurred: {str(e)}")
            return error_status, "", "", None

    def _create_status_html_from_result(self, result: ExecutionResult) -> str:
        """Create status HTML from execution result."""
        if result.success:
            return self._create_status_html(
                "success",
                "✅ Success",
                "Code generated and executed successfully!" if result.output is not None else "Code generated successfully!"
            )
        else:
            return self._create_status_html(
                "error",
                "❌ Failed",
                result.error_message or "Unknown error occurred"
            )

    def _create_status_html(self, status_type: str, title: str, message: str) -> str:
        """Create HTML for status display."""
        return f"""
        <div class="status-card status-{status_type}">
            <h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 600;">{title}</h3>
            <p style="margin: 0; font-size: 1rem; opacity: 0.95;">{message}</p>
        </div>
        """

    def _create_execution_info(self, result: ExecutionResult) -> str:
        """Create execution information HTML."""
        return f"""
        <div class="metrics-container">
            <div class="metric-card">
                <div class="metric-value">{result.execution_time:.2f}s</div>
                <div class="metric-label">Execution Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{result.iterations}</div>
                <div class="metric-label">Iterations</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{"✅" if result.success else "❌"}</div>
                <div class="metric-label">Status</div>
            </div>
        </div>
        """

    def _create_download_file(self, code_content: str) -> Optional[str]:
        """Create a temporary file for download."""
        if not code_content or not code_content.strip():
            return None

        try:
            temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                prefix='generated_code_',
                delete=False,
                encoding='utf-8'
            )

            temp_file.write(code_content)
            temp_file.close()

            return temp_file.name

        except Exception as e:
            print(f"Error creating download file: {e}")
            return None


def load_custom_css() -> str:
    """Load custom CSS styles."""
    return """
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

    * {
        font-family: 'Roboto', sans-serif !important;
    }

    .gradio-container {
        max-width: 1400px !important;
        margin: 0 auto !important;
        background: #f8fafc !important;
        min-height: 100vh;
        padding: 20px;
    }

    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border-radius: 20px !important;
        padding: 40px 30px !important;
        margin-bottom: 30px !important;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3) !important;
        text-align: center !important;
    }

    .header-title {
        color: white !important;
        font-size: 3rem !important;
        font-weight: 700 !important;
        margin-bottom: 15px !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    }

    .header-subtitle {
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 1.3rem !important;
        font-weight: 400 !important;
        margin: 0 !important;
    }

    /* Input section styling */
    .input-container {
        background: white !important;
        border-radius: 20px !important;
        padding: 30px !important;
        margin-bottom: 25px !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1) !important;
        border: 1px solid #e2e8f0 !important;
    }

    .input-container .block {
        border: none !important;
        background: transparent !important;
    }

    .input-container label {
        color: #2d3748 !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        margin-bottom: 8px !important;
    }

    .input-container textarea, .input-container input {
        border: 2px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 15px !important;
        font-size: 16px !important;
        background: #f7fafc !important;
        transition: all 0.3s ease !important;
    }

    .input-container textarea:focus, .input-container input:focus {
        border-color: #667eea !important;
        background: white !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }

    /* Button styling */
    .btn-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 15px 25px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        color: white !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
        min-height: 50px !important;
    }

    .btn-primary:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6) !important;
    }

    .btn-secondary {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 15px 25px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        color: white !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(72, 187, 120, 0.4) !important;
        min-height: 50px !important;
    }

    .btn-secondary:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(72, 187, 120, 0.6) !important;
    }

    /* Status cards */
    .status-card {
        border-radius: 15px !important;
        padding: 25px !important;
        margin-bottom: 25px !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1) !important;
        border: 1px solid #e2e8f0 !important;
    }

    .status-success {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%) !important;
        color: white !important;
        border: none !important;
    }

    .status-error {
        background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%) !important;
        color: white !important;
        border: none !important;
    }

    .status-ready {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%) !important;
        color: white !important;
        border: none !important;
    }

    /* Output containers */
    .output-container {
        background: white !important;
        border-radius: 20px !important;
        padding: 25px !important;
        margin: 15px 0 !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1) !important;
        border: 1px solid #e2e8f0 !important;
    }

    .output-section {
        background: #f8fafc !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 20px !important;
    }

    .output-section textarea {
        background: #f8fafc !important;
        border: none !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
    }

    /* Metrics styling */
    .metrics-container {
        display: flex !important;
        gap: 20px !important;
        margin-bottom: 20px !important;
        flex-wrap: wrap !important;
    }

    .metric-card {
        background: white !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 15px !important;
        padding: 20px !important;
        text-align: center !important;
        flex: 1 !important;
        min-width: 120px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
    }

    .metric-value {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #667eea !important;
        margin-bottom: 5px !important;
    }

    .metric-label {
        font-size: 0.9rem !important;
        color: #718096 !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    /* Tab styling */
    .tab-nav {
        background: white !important;
        border-radius: 20px !important;
        padding: 5px !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1) !important;
        border: 1px solid #e2e8f0 !important;
        margin-bottom: 20px !important;
    }

    .tab-nav button {
        background: #f7fafc !important;
        border: none !important;
        padding: 15px 25px !important;
        font-weight: 600 !important;
        color: #4a5568 !important;
        transition: all 0.3s ease !important;
    }

    .tab-nav button.selected {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }

    /* Code block styling */
    .code-container {
        background: #f8fafc !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 15px !important;
        overflow: hidden !important;
    }

    .code-container .code {
        background: #f8fafc !important;
        border: none !important;
        border-radius: 15px !important;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
    }

    .code-container pre {
        background: #f8fafc !important;
        color: #2d3748 !important;
        padding: 20px !important;
        margin: 0 !important;
        border-radius: 15px !important;
        overflow-x: auto !important;
    }

    .code-container code {
        background: #f8fafc !important;
        color: #2d3748 !important;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace !important;
    }

    /* Fix line numbers styling */
    .code-container .hljs-ln-numbers {
        background: #f8fafc !important;
        color: #a0aec0 !important;
        border-right: 1px solid #e2e8f0 !important;
        padding-right: 10px !important;
        margin-right: 10px !important;
        text-align: right !important;
        user-select: none !important;
    }

    .code-container .hljs-ln-code {
        background: #f8fafc !important;
        padding-left: 10px !important;
    }

    /* Python syntax highlighting with light theme */
    .code-container .hljs-keyword {
        color: #667eea !important;
        font-weight: 600 !important;
    }

    .code-container .hljs-string {
        color: #48bb78 !important;
    }

    .code-container .hljs-number {
        color: #ed8936 !important;
    }

    .code-container .hljs-comment {
        color: #a0aec0 !important;
        font-style: italic !important;
    }

    .code-container .hljs-function {
        color: #764ba2 !important;
    }

    .code-container .hljs-built_in {
        color: #4299e1 !important;
    }

    .code-container .hljs-variable {
        color: #2d3748 !important;
    }

    /* Gradio code component specific overrides */
    .gradio-container .code_wrap {
        background: #f8fafc !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 15px !important;
    }

    .gradio-container .code_wrap .code {
        background: #f8fafc !important;
        color: #2d3748 !important;
    }

    .gradio-container .code_wrap pre {
        background: #f8fafc !important;
        color: #2d3748 !important;
    }

    /* Override any dark theme remnants */
    .gradio-container .code_wrap,
    .gradio-container .code_wrap *,
    .gradio-container .hljs {
        background: #f8fafc !important;
        color: #2d3748 !important;
    }

    /* Scrollbar styling for code blocks */
    .code-container pre::-webkit-scrollbar {
        height: 8px !important;
        width: 8px !important;
    }

    .code-container pre::-webkit-scrollbar-track {
        background: #e2e8f0 !important;
        border-radius: 4px !important;
    }

    .code-container pre::-webkit-scrollbar-thumb {
        background: #cbd5e0 !important;
        border-radius: 4px !important;
    }

    .code-container pre::-webkit-scrollbar-thumb:hover {
        background: #a0aec0 !important;
    }

    /* Download button styling - Updated */
    .download-btn,
    .download-btn button,
    .download-btn .download-button {
        background: linear-gradient(135deg, #805ad5 0%, #6b46c1 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 15px 25px !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(128, 90, 213, 0.4) !important;
        cursor: pointer !important;
        width: 100% !important;
        min-height: 50px !important;
    }

    .download-btn:hover,
    .download-btn button:hover,
    .download-btn .download-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(128, 90, 213, 0.6) !important;
        background: linear-gradient(135deg, #9f7aea 0%, #805ad5 100%) !important;
    }

    /* Fix for DownloadButton container */
    .download-btn .block {
        border: none !important;
        background: transparent !important;
        border-radius: 12px !important;
    }

    /* Ensure the entire button area is clickable */
    .download-btn .download-button,
    .download-btn button {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-decoration: none !important;
        border-radius: 12px !important;
    }

    /* Remove any file-specific styling that might interfere */
    .download-btn .file-preview,
    .download-btn .file-name {
        display: none !important;
    }

    /* Footer styling */
    .footer-container {
        background: white !important;
        border-radius: 15px !important;
        padding: 25px !important;
        margin-top: 30px !important;
        text-align: center !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
        border: 1px solid #e2e8f0 !important;
    }

    .footer-container p {
        color: #718096 !important;
        margin: 8px 0 !important;
        font-size: 0.95rem !important;
    }

    /* Responsive design */
    @media (max-width: 768px) {
        .gradio-container {
            padding: 10px !important;
        }

        .header-title {
            font-size: 2rem !important;
        }

        .header-subtitle {
            font-size: 1.1rem !important;
        }

        .metrics-container {
            flex-direction: column !important;
        }

        .metric-card {
            min-width: auto !important;
        }
    }
    """


def create_gradio_interface():
    """Create and configure the Gradio interface."""

    ui = CodeGeneratorUI()

    with gr.Blocks(
        css=load_custom_css(),
        title="AI Code Generator",
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="purple",
            neutral_hue="gray",
            font=[gr.themes.GoogleFont("Roboto"), "Arial", "sans-serif"]
        )
    ) as interface:

        # Header
        gr.HTML("""
        <div class="header-container">
            <h1 class="header-title">🤖 AI Code Generator</h1>
            <p class="header-subtitle">Transform your ideas into executable Python code with AI</p>
        </div>
        """)

        # Input Section
        with gr.Group(elem_classes=["input-container"]):
            user_request = gr.Textbox(
                label="📝 Describe what you want to code",
                placeholder="e.g., Create a function to calculate the 100th prime number",
                lines=4,
                elem_classes=["input-field"]
            )

            # Examples right below the input
            gr.Examples(
                examples=[
                    ["Calculate the 101s prime number"],
                    ["Calculate the 97th prime number"],
                    ["Return a prettified plain text table with the historical prices of the BTC-USD ticker for the last 20 days from Yahoo Finance"],
                    ["Create a password generator with customizable length and character sets"],
                    ["Return current weather conditions for the following cities: Vancouver (BC), Kyiv (UA), Washington(DC), San Francisco(CA), in the format of a prettified plain text table using the Open-Meteo API."],
                    ["Convert 20 Fahrenheit to Celsius"]
                ],
                inputs=[user_request],
                label="💡 Click any example to try it out"
            )

            with gr.Row():
                max_retries = gr.Slider(
                    minimum=1,
                    maximum=5,
                    value=3,
                    step=1,
                    label="🔄 Max Retry Attempts",
                    info="Number of attempts if code generation fails"
                )

            with gr.Row():
                generate_and_run_btn = gr.Button(
                    "🚀 Generate & Execute Code",
                    variant="primary",
                    elem_classes=["btn-primary"],
                    scale=1
                )
                generate_only_btn = gr.Button(
                    "📝 Generate Code Only",
                    variant="secondary",
                    elem_classes=["btn-secondary"],
                    scale=1
                )

        status_display = gr.HTML(
            value='<div class="status-card status-ready"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 600;">🎯 Ready</h3><p style="margin: 0; font-size: 1rem; opacity: 0.95;">Enter your request above to get started</p></div>'
        )

        with gr.Tabs(elem_classes=["tab-nav"]) as tabs:

            with gr.TabItem("🎯 Final Result", elem_id="result-tab"):
                with gr.Group(elem_classes=["output-container"]):
                    final_answer = gr.Textbox(
                        label="📋 Execution Output",
                        placeholder="The result of your code will appear here...",
                        lines=10,
                        interactive=False,
                        elem_classes=["output-section"]
                    )

            with gr.TabItem("💻 Generated Code", elem_id="code-tab"):
                execution_info = gr.HTML(value="")

                with gr.Group(elem_classes=["output-container"]):
                    generated_code = gr.Code(
                        label="🐍 Python Code",
                        language="python",
                        interactive=False,
                        elem_classes=["code-container"]
                    )

                    with gr.Row():
                        download_btn = gr.DownloadButton(
                            label="💾 Download Code",
                            visible=False,
                            elem_classes=["download-btn"]
                        )

        def handle_generate_and_execute(request, retries):
            status, answer, code, info, file_path = ui.generate_and_execute_code(request, retries)
            return status, answer, code, info, gr.DownloadButton(
                label="💾 Download Code",
                value=file_path,
                visible=bool(file_path),
                elem_classes=["download-btn"]
            )

        generate_and_run_btn.click(
            fn=handle_generate_and_execute,
            inputs=[user_request,
                    max_retries],
            outputs=[status_display,
                     final_answer,
                     generated_code,
                     execution_info,
                     download_btn],
            show_progress=True
        )

        def handle_generate_only(request, retries):
            status, code, info, file_path = ui.generate_code_only(request,
                                                                  retries)

            return status, "", code, info, gr.DownloadButton(
                label="💾 Download Code",
                value=file_path,
                visible=bool(file_path),
                elem_classes=["download-btn"]
            )

        generate_only_btn.click(
            fn=handle_generate_only,
            inputs=[user_request,
                    max_retries],
            outputs=[status_display,
                     final_answer,
                     generated_code,
                     execution_info,
                     download_btn],
            show_progress=True
        )

        gr.HTML("""
        <div class="footer-container">
            <p>🔒 Your code is generated and executed securely in an isolated environment</p>
            <p>⚡ Powered by OpenAI GPT-4 and LangGraph workflow engine</p>
        </div>
        """)

    return interface


def launch_app(
    server_name: str = os.getenv("GRADIO_HOST", "127.0.0.1"),
    server_port: int = int(os.getenv("GRADIO_PORT", "7860")),
    share: bool = False,
    debug: bool = False
):
    """Launch the Gradio application."""

    gr.analytics_enabled = False

    interface = create_gradio_interface()

    print("🚀 Starting AI Code Generator...")
    print(f"📍 Server will be available at: http://{server_name}:{server_port}")

    interface.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        debug=debug,
        show_error=True,
        quiet=False
    )
