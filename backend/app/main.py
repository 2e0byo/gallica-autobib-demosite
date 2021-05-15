from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from gallica_autobib.pipeline import BibtexParser, RisParser
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from pydantic import BaseModel


class BibliographyData(BaseModel):
    content: str
    name: str


app = FastAPI()

app.mount("/pdfs", StaticFiles(directory="pdfs"), name="pdfs")
templates = Jinja2Templates(directory="templates")


pool = ProcessPoolExecutor(6)


@app.post("/bibtex/", response_class=HTMLResponse)
async def resolve_bibtex(data: BibliographyData, request: Request):
    """Resolve a bibtex submission if possible"""
    parser = BibtexParser(Path("pdfs"), clean=False)
    parser.pool(pool)
    parser.process_args = {"skip_existing": True}
    parser.read(data.content)
    await parser.submit()
    return templates.TemplateResponse(
        "response.html", dict(request=request, obj=parser, name=data.name)
    )


@app.get("/")
async def root():
    return {"message": "Hello World"}
