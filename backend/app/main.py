from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from gallica_autobib.pipeline import BibtexParser, RisParser
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.DEBUG)


class BibliographyData(BaseModel):
    content: str
    name: str


app = FastAPI()

app.mount("/pdfs", StaticFiles(directory="pdfs"), name="pdfs")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


pool = ProcessPoolExecutor(6)

with Path("static/index.html").open() as f:
    index = f.read()


@app.get("/")
async def root():
    return RedirectResponse("/static/index.html")


# @app.get("/", response_class=HTMLResponse)
# async def root():
#     return index


@app.post("/api/parser", response_class=HTMLResponse)
async def parser(
    request: Request,
    name: str = Form(...),
    bibdata: str = Form(...),
    bibtype: str = Form(...),
):
    if bibtype == "bibtex":
        parser = BibtexParser(Path("pdfs"), clean=False)
    else:
        parser = RisParser(Path("pdfs"), clean=False)
    parser.pool(pool)
    parser.process_args = {"skip_existing": True}
    parser.read(bibdata)
    await parser.submit()
    return templates.TemplateResponse(
        "response.html", dict(request=request, obj=parser, name=name)
    )


@app.post("/api/bibtex", response_class=HTMLResponse)
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
