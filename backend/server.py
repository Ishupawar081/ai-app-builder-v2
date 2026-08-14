from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

from planner import generate_plan, generate_initial_app, generate_backend_code, fix_app_code, ai_edit_file, ai_explain_code
from agent import build_app, update_app, save_file, run_dev_server, list_project_files, read_file, write_file, run_cmd, get_paths, create_downloadable_app

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ID = "main_app"

class PlanRequest(BaseModel):
    user_input: str

class BuildRequest(BaseModel):
    user_input: str
    plan: dict | None = None

class EditRequest(BaseModel):
    file_name: str
    instruction: str

class SaveRequest(BaseModel):
    file_name: str
    content: str

class CmdRequest(BaseModel):
    cmd: str

@app.post("/api/plan")
def api_plan(req: PlanRequest):
    plan = generate_plan(req.user_input)
    return {"plan": plan}

@app.post("/api/build")
def api_build(req: BuildRequest):
    result = build_app(req.user_input, PROJECT_ID, req.plan)
    return {"result": result}

@app.post("/api/update")
def api_update(req: PlanRequest):
    result = update_app(req.user_input, PROJECT_ID)
    return {"result": result}

@app.get("/api/files")
def api_files():
    try:
        files = list_project_files(PROJECT_ID)
        return {"files": files}
    except Exception:
        return {"files": []}

@app.get("/api/file")
def api_file(path: str):
    base = os.path.join("..", "projects", f"app_{PROJECT_ID}")
    full_path = os.path.join(base, path)
    content = read_file(full_path)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {"content": content}

@app.post("/api/save")
def api_save(req: SaveRequest):
    result = save_file(req.file_name, req.content, PROJECT_ID)
    return {"result": result}

@app.post("/api/edit")
def api_edit(req: EditRequest):
    base = os.path.join("..", "projects", f"app_{PROJECT_ID}")
    full_path = os.path.join(base, req.file_name)
    content = read_file(full_path)
    if not content:
        raise HTTPException(status_code=404, detail="File not found")
    
    updated = ai_edit_file(content, os.path.basename(req.file_name), req.instruction)
    return {"updated": updated}

@app.post("/api/terminal")
def api_terminal(req: CmdRequest):
    base = os.path.join("..", "projects", f"app_{PROJECT_ID}")
    rc, out = run_cmd(req.cmd, base, timeout=60)
    return {"rc": rc, "output": out}

@app.post("/api/devserver")
def api_devserver():
    msg = run_dev_server(PROJECT_ID)
    return {"message": msg}

@app.get("/api/download")
def api_download():
    zip_path = create_downloadable_app(PROJECT_ID)
    return FileResponse(
        zip_path, 
        media_type="application/zip", 
        filename=f"app_{PROJECT_ID}.zip",
        headers={"Content-Disposition": f"attachment; filename=app_{PROJECT_ID}.zip"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
