from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import date, timedelta
from models import (
    init_db, SessionLocal, RoutineTemplate, RoutineDaily, 
    Reason, Task, Substance, Consumption, Productivity,
    Objectives, ImmigrationStep
)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Monter le dossier static pour le CSS
app.mount("/static", StaticFiles(directory="static"), name="static")

init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========== PAGE PRINCIPALE ==========
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    
    # Récupérer les tâches du jour
    tasks = db.query(Task).filter(Task.date == today).all()
    
    return templates.TemplateResponse("home.html", {
        "request": request,
        "today": today,
        "tasks": tasks
    })

# ========== ROUTINE ==========
@app.get("/routine", response_class=HTMLResponse)
async def routine_page(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    
    # Créer routine du jour si elle n'existe pas
    existing = db.query(RoutineDaily).filter(RoutineDaily.date == today).first()
    if not existing:
        template_items = db.query(RoutineTemplate).order_by(RoutineTemplate.order).all()
        for item in template_items:
            db.add(RoutineDaily(date=today, item_name=item.item_name))
        db.commit()
    
    routine = db.query(RoutineDaily).filter(RoutineDaily.date == today).all()
    
    return templates.TemplateResponse("routine.html", {
        "request": request,
        "routine": routine
    })

@app.post("/routine/toggle/{item_id}")
async def toggle_routine(item_id: int, db: Session = Depends(get_db)):
    item = db.query(RoutineDaily).filter(RoutineDaily.id == item_id).first()
    if item:
        item.done = not item.done
        db.commit()
    return RedirectResponse(url="/routine", status_code=303)

# ========== MY REASONS ==========
@app.get("/reasons", response_class=HTMLResponse)
async def reasons_page(request: Request, db: Session = Depends(get_db)):
    reasons = db.query(Reason).all()
    return templates.TemplateResponse("reasons.html", {
        "request": request,
        "reasons": reasons
    })

@app.post("/reasons/add")
async def add_reason(text: str = Form(...), db: Session = Depends(get_db)):
    db.add(Reason(text=text))
    db.commit()
    return RedirectResponse(url="/reasons", status_code=303)

@app.post("/reasons/delete/{reason_id}")
async def delete_reason(reason_id: int, db: Session = Depends(get_db)):
    reason = db.query(Reason).filter(Reason.id == reason_id).first()
    if reason:
        db.delete(reason)
        db.commit()
    return RedirectResponse(url="/reasons", status_code=303)

# ========== OBJECTIFS ==========
@app.get("/objectives", response_class=HTMLResponse)
async def objectives_page(request: Request, db: Session = Depends(get_db)):
    obj = db.query(Objectives).first()
    if not obj:
        obj = Objectives()
        db.add(obj)
        db.commit()
    
    steps = db.query(ImmigrationStep).order_by(ImmigrationStep.order).all()
    
    return templates.TemplateResponse("objectives.html", {
        "request": request,
        "objectives": obj,
        "immigration_steps": steps
    })

@app.post("/objectives/update")
async def update_objective(
    objective_type: str = Form(...),
    progress: int = Form(None),
    notes: str = Form(None),
    current_weight: float = Form(None),
    sleep_hours: float = Form(None),
    food_satisfaction: int = Form(None),
    db: Session = Depends(get_db)
):
    obj = db.query(Objectives).first()
    
    if objective_type == "studies":
        obj.studies_progress = progress
        obj.studies_notes = notes
    elif objective_type == "weight":
        obj.current_weight = current_weight
    elif objective_type == "sleep":
        obj.sleep_hours = sleep_hours
    elif objective_type == "food":
        obj.food_satisfaction = food_satisfaction
    
    db.commit()
    return RedirectResponse(url="/objectives", status_code=303)

@app.post("/objectives/toggle_step/{step_id}")
async def toggle_immigration_step(step_id: int, db: Session = Depends(get_db)):
    step = db.query(ImmigrationStep).filter(ImmigrationStep.id == step_id).first()
    if step:
        step.done = not step.done
        db.commit()
    return RedirectResponse(url="/objectives", status_code=303)

@app.post("/objectives/add_step")
async def add_immigration_step(title: str = Form(...), db: Session = Depends(get_db)):
    max_order = db.query(ImmigrationStep).count()
    db.add(ImmigrationStep(title=title, order=max_order))
    db.commit()
    return RedirectResponse(url="/objectives", status_code=303)

# ========== PLANIFIER ==========
@app.get("/plan", response_class=HTMLResponse)
async def plan_page(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    
    # Trouver le vendredi le plus proche (passé ou présent)
    days_since_friday = (today.weekday() - 4) % 7
    start_of_week = today - timedelta(days=days_since_friday)
    
    # Semaine = vendredi → jeudi (7 jours)
    week = [(start_of_week + timedelta(days=i)) for i in range(7)]
    
    # Tâches de la semaine
    week_tasks = {}
    for day in week:
        week_tasks[day] = db.query(Task).filter(Task.date == day).all()
    
    return templates.TemplateResponse("plan.html", {
        "request": request,
        "week": week,
        "week_tasks": week_tasks,
        "today": today
    })

@app.post("/plan/add")
async def add_task(
    task_date: str = Form(...),
    title: str = Form(...),
    time: str = Form(None),
    db: Session = Depends(get_db)
):
    db.add(Task(date=date.fromisoformat(task_date), title=title, time=time))
    db.commit()
    return RedirectResponse(url="/plan", status_code=303)

@app.post("/plan/toggle/{task_id}")
async def toggle_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.done = not task.done
        db.commit()
    return RedirectResponse(url="/plan", status_code=303)

# ========== SOBRIÉTÉ ==========
@app.get("/sobriety", response_class=HTMLResponse)
async def sobriety_page(request: Request, db: Session = Depends(get_db)):
    substances = db.query(Substance).all()
    
    # Dernières consommations
    consumptions = {}
    for sub in substances:
        consumptions[sub.id] = db.query(Consumption)\
            .filter(Consumption.substance_id == sub.id)\
            .order_by(Consumption.date.desc())\
            .limit(5)\
            .all()
    
    today = date.today()
    
    return templates.TemplateResponse("sobriety.html", {
        "request": request,
        "substances": substances,
        "consumptions": consumptions,
        "today": today
    })

@app.post("/sobriety/add_substance")
async def add_substance(name: str = Form(...), db: Session = Depends(get_db)):
    db.add(Substance(name=name))
    db.commit()
    return RedirectResponse(url="/sobriety", status_code=303)

@app.post("/sobriety/add_consumption")
async def add_consumption(
    substance_id: int = Form(...),
    consumption_date: str = Form(...),
    quantity: str = Form(None),
    note: str = Form(None),
    db: Session = Depends(get_db)
):
    db.add(Consumption(
        substance_id=substance_id,
        date=date.fromisoformat(consumption_date),
        quantity=quantity,
        note=note
    ))
    db.commit()
    return RedirectResponse(url="/sobriety", status_code=303)

# ========== PRODUCTIVITÉ ==========
@app.get("/productivity", response_class=HTMLResponse)
async def productivity_page(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    prod = db.query(Productivity).filter(Productivity.date == today).first()
    
    # Historique (30 derniers jours, excluant aujourd'hui)
    history = db.query(Productivity)\
        .filter(Productivity.date < today)\
        .order_by(Productivity.date.desc())\
        .limit(30)\
        .all()
    
    return templates.TemplateResponse("productivity.html", {
        "request": request,
        "today": today,
        "prod": prod,
        "history": history
    })

@app.post("/productivity/save")
async def save_productivity(
    prod_date: str = Form(...),
    score: float = Form(...),
    note: str = Form(None),
    db: Session = Depends(get_db)
):
    target_date = date.fromisoformat(prod_date)
    prod = db.query(Productivity).filter(Productivity.date == target_date).first()
    
    if prod:
        prod.score = score
        prod.note = note
    else:
        db.add(Productivity(date=target_date, score=score, note=note))
    
    db.commit()
    return RedirectResponse(url="/productivity", status_code=303)