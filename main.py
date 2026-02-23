import traceback
from typing import List
from io import BytesIO

from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd

from processor import process_file

app = FastAPI(title="Demo")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload_files(request: Request, files: List[UploadFile] = File(...)):
    results_html = []

    for file in files:
        try:
            contents = await file.read()

            # Load into pandas directly from memory?
            df = pd.read_csv(BytesIO(contents))
            figures, summary = process_file(df)

            chart_blocks = []
            for i, fig in enumerate(figures):
                chart_html = fig.to_html(
                    full_html=False,
                    include_plotlyjs=False,
                    config={"displayModeBar": True, "scrollZoom": True},
                )

                chart_blocks.append(
                    f"""
                    <div class="chart-wrapper">
                        <div class="chart-header">
                            <span class="chart-label">Chart {i + 1}</span>
                        </div>
                        {chart_html}
                    </div>
                    """
                )

            summary_rows = "".join(
                f"<tr><td>{k}</td><td>{v}</td></tr>"
                for k, v in summary.items()
            )

            results_html.append(
                f"""
                <section class="file-result success">
                    <div class="file-header">
                        <span class="filename">📄 {file.filename}</span>
                        <span class="badge ok">Processed</span>
                    </div>
                    <details class="summary-details">
                        <summary>Dataset Summary</summary>
                        <table class="summary-table">
                            <tbody>{summary_rows}</tbody>
                        </table>
                    </details>
                    <div class="charts">{"".join(chart_blocks)}</div>
                </section>
                """
            )

        except Exception as exc:
            tb = traceback.format_exc()
            results_html.append(
                f"""
                <section class="file-result error">
                    <div class="file-header">
                        <span class="filename">📄 {file.filename}</span>
                        <span class="badge err">Error</span>
                    </div>
                    <pre class="error-msg">{exc}\n\n{tb}</pre>
                </section>
                """
            )

    return HTMLResponse("".join(results_html))
