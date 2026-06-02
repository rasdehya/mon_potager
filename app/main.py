import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pathlib import Path

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

from .database import get_db, engine, Base
from .models import (
    Famille,
    Legume,
    Variete,
    Calendrier,
    Maladie,
    Potager,
    PotagerItem,
    PotagerCalendrier,
)
from .seed import init_db
from . import settings as app_settings
from . import ai_client
from . import rag as rag_engine

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    logger.info("Démarrage de l'application...")
    global settings_data, TYPE_LABELS, TYPE_COLORS
    settings_data = app_settings.load()
    TYPE_LABELS = settings_data["labels"]
    TYPE_COLORS = settings_data["colors"]
    Base.metadata.create_all(bind=engine)
    init_db()
    logger.info("Base de données prête")
    yield
    ai_client.stop_server()
    logger.info("Application arrêtée")


app = FastAPI(title="Mon Potager - Guide de Culture", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

settings_data = app_settings.load()
TYPE_LABELS = settings_data["labels"]
TYPE_COLORS = settings_data["colors"]

MOIS_NOMS = [
    "",
    "Janvier",
    "Février",
    "Mars",
    "Avril",
    "Mai",
    "Juin",
    "Juillet",
    "Août",
    "Septembre",
    "Octobre",
    "Novembre",
    "Décembre",
]

TOTAL_WEEKS = 48


def week_pos(mois, semaine):
    return (mois - 1) * 4 + semaine


def bar_style(mois_debut, semaine_debut, mois_fin, semaine_fin):
    start = week_pos(mois_debut, semaine_debut)
    end = week_pos(mois_fin, semaine_fin)
    left = (start - 1) / TOTAL_WEEKS * 100
    width = (end - start + 1) / TOTAL_WEEKS * 100
    return f"left:{left:.2f}%;width:{width:.2f}%;"


# ── Home ──
@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    familles = db.query(Famille).all()
    total_legumes = db.query(Legume).count()
    total_varietes = db.query(Variete).count()
    potagers = db.query(Potager).order_by(Potager.annee.desc()).all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "familles": familles,
            "total_legumes": total_legumes,
            "total_varietes": total_varietes,
            "potagers": potagers,
        },
    )


# ── Search ──
@app.get("/recherche", response_class=HTMLResponse)
def recherche(request: Request, q: str = "", db: Session = Depends(get_db)):
    results = var_results = []
    if q:
        qq = f"%{q}%"
        results = (
            db.query(Legume)
            .filter(
                or_(
                    Legume.nom.ilike(qq),
                    Legume.description.ilike(qq),
                    Legume.nom_scientifique.ilike(qq),
                )
            )
            .all()
        )
        var_results = db.query(Variete).filter(Variete.nom.ilike(qq)).all()
    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "q": q,
            "results": results,
            "var_results": var_results,
        },
    )


# ── Familles ──
@app.get("/familles", response_class=HTMLResponse)
def liste_familles(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "famille_list.html",
        {
            "request": request,
            "familles": db.query(Famille).all(),
        },
    )


# ── Légumes ──
@app.get("/legumes", response_class=HTMLResponse)
def liste_legumes(request: Request, db: Session = Depends(get_db)):
    famille_id = request.query_params.get("famille_id")
    if famille_id:
        legumes = db.query(Legume).filter(Legume.famille_id == int(famille_id)).all()
        current_famille = db.get(Famille, int(famille_id))
    else:
        legumes = db.query(Legume).all()
        current_famille = None
    return templates.TemplateResponse(
        "legume_list.html",
        {
            "request": request,
            "legumes": legumes,
            "familles": db.query(Famille).all(),
            "current_famille": current_famille,
        },
    )


# ── Détail légume ──
@app.get("/legume/{legume_id}", response_class=HTMLResponse)
def detail_legume(legume_id: int, request: Request, db: Session = Depends(get_db)):
    legume = db.get(Legume, legume_id)
    if not legume:
        return templates.TemplateResponse(
            "404.html", {"request": request}, status_code=404
        )
    varietes = db.query(Variete).filter(Variete.legume_id == legume_id).all()
    calendrier = (
        db.query(Calendrier)
        .filter(Calendrier.legume_id == legume_id)
        .order_by(Calendrier.mois_debut)
        .all()
    )
    maladies = db.query(Maladie).filter(Maladie.legume_id == legume_id).all()

    calendar_types_used = []
    for t in TYPE_LABELS:
        entries = [c for c in calendrier if c.type == t]
        if entries:
            calendar_types_used.append(
                {
                    "key": t,
                    "label": TYPE_LABELS[t],
                    "color": TYPE_COLORS[t],
                    "entries": entries,
                }
            )

    return templates.TemplateResponse(
        "legume_detail.html",
        {
            "request": request,
            "legume": legume,
            "varietes": varietes,
            "calendrier": calendrier,
            "maladies": maladies,
            "calendar_types": calendar_types_used,
            "MOIS_NOMS": MOIS_NOMS,
            "TYPE_LABELS": TYPE_LABELS,
            "TYPE_COLORS": TYPE_COLORS,
            "bar_style": bar_style,
            "TOTAL_WEEKS": TOTAL_WEEKS,
        },
    )


# ── PDF ──
@app.get("/legume/{legume_id}/pdf", response_class=HTMLResponse)
def legume_pdf(legume_id: int, request: Request, db: Session = Depends(get_db)):
    legume = db.get(Legume, legume_id)
    if not legume:
        return templates.TemplateResponse(
            "404.html", {"request": request}, status_code=404
        )
    varietes = db.query(Variete).filter(Variete.legume_id == legume_id).all()
    calendrier = (
        db.query(Calendrier)
        .filter(Calendrier.legume_id == legume_id)
        .order_by(Calendrier.mois_debut)
        .all()
    )
    maladies = db.query(Maladie).filter(Maladie.legume_id == legume_id).all()
    return templates.TemplateResponse(
        "legume_pdf.html",
        {
            "request": request,
            "legume": legume,
            "varietes": varietes,
            "calendrier": calendrier,
            "maladies": maladies,
            "MOIS_NOMS": MOIS_NOMS,
            "TYPE_LABELS": TYPE_LABELS,
            "bar_style": bar_style,
        },
    )


# ── Potager – list ──
@app.get("/potager", response_class=HTMLResponse)
def potager_list(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "potager_list.html",
        {
            "request": request,
            "potagers": db.query(Potager).order_by(Potager.annee.desc()).all(),
        },
    )


# ── Potager – create ──
@app.get("/potager/creer", response_class=HTMLResponse)
def potager_creer_form(request: Request):
    return templates.TemplateResponse(
        "potager_form.html", {"request": request, "potager": None}
    )


@app.post("/potager/creer")
def potager_creer(
    annee: int = Form(...),
    nom: str = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    p = Potager(annee=annee, nom=nom, notes=notes, active=1)
    db.add(p)
    db.commit()
    return RedirectResponse(f"/potager/{p.id}", status_code=302)


# ── Potager – détail ──
@app.get("/potager/{potager_id}", response_class=HTMLResponse)
def potager_detail(
    potager_id: int, request: Request, mois: int = 0, db: Session = Depends(get_db)
):
    potager = db.get(Potager, potager_id)
    if not potager:
        return templates.TemplateResponse(
            "404.html", {"request": request}, status_code=404
        )
    items = (
        db.query(PotagerItem)
        .filter(PotagerItem.potager_id == potager_id)
        .order_by(PotagerItem.ordre)
        .all()
    )
    legumes = db.query(Legume).order_by(Legume.nom).all()

    for item in items:
        item._bars = []
        for cal in item.calendrier:
            item._bars.append(
                {
                    "cal": cal,
                    "style": bar_style(
                        cal.mois_debut, cal.semaine_debut, cal.mois_fin, cal.semaine_fin
                    ),
                    "color": TYPE_COLORS.get(cal.type, "#666"),
                    "label": TYPE_LABELS.get(cal.type, cal.type),
                }
            )

    focus_mois = mois if 1 <= mois <= 12 else 0
    return templates.TemplateResponse(
        "potager_detail.html",
        {
            "request": request,
            "potager": potager,
            "items": items,
            "legumes": legumes,
            "MOIS_NOMS": MOIS_NOMS,
            "TYPE_LABELS": TYPE_LABELS,
            "TYPE_COLORS": TYPE_COLORS,
            "focus_mois": focus_mois,
            "bar_style": bar_style,
            "TOTAL_WEEKS": TOTAL_WEEKS,
        },
    )


# ── Potager – ajouter item ──
@app.post("/potager/{potager_id}/ajouter")
def potager_ajouter(
    potager_id: int,
    legume_id: int = Form(default=0),
    type_item: str = Form("legume"),
    nom_custom: str = Form(""),
    variete_id: int = Form(default=0),
    quantite: str = Form(""),
    emplacement: str = Form(""),
    compagnons: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    item = PotagerItem(
        potager_id=potager_id,
        legume_id=legume_id if legume_id > 0 else None,
        variete_id=variete_id if variete_id > 0 else None,
        type=type_item,
        nom_custom=nom_custom,
        quantite=quantite,
        emplacement=emplacement,
        compagnons=compagnons,
        notes=notes,
    )
    db.add(item)
    db.flush()
    if legume_id > 0:
        for cal in db.query(Calendrier).filter(Calendrier.legume_id == legume_id).all():
            db.add(
                PotagerCalendrier(
                    item_id=item.id,
                    type=cal.type,
                    mois_debut=cal.mois_debut,
                    semaine_debut=cal.semaine_debut,
                    mois_fin=cal.mois_fin,
                    semaine_fin=cal.semaine_fin,
                    details=cal.details,
                )
            )
    db.commit()
    return RedirectResponse(f"/potager/{potager_id}", status_code=302)


@app.post("/potager/item/{item_id}/editer")
def potager_edit_item(
    item_id: int,
    nom_custom: str = Form(""),
    variete_id: int = Form(default=0),
    quantite: str = Form(""),
    emplacement: str = Form(""),
    compagnons: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    item = db.get(PotagerItem, item_id)
    if item:
        item.nom_custom = nom_custom
        item.variete_id = variete_id if variete_id > 0 else None
        item.quantite = quantite
        item.emplacement = emplacement
        item.compagnons = compagnons
        item.notes = notes
        db.commit()
        return RedirectResponse(f"/potager/{item.potager_id}", status_code=302)
    return RedirectResponse("/potager", status_code=302)


@app.post("/potager/item/{item_id}/supprimer")
def potager_supprimer_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(PotagerItem, item_id)
    if item:
        pid = item.potager_id
        db.delete(item)
        db.commit()
        return RedirectResponse(f"/potager/{pid}", status_code=302)
    return RedirectResponse("/potager", status_code=302)


@app.post("/potager/calendrier/{cal_id}/editer")
def potager_edit_calendrier(
    cal_id: int,
    mois_debut: int = Form(...),
    mois_fin: int = Form(...),
    details: str = Form(""),
    semaine_debut: int = Form(1),
    semaine_fin: int = Form(4),
    db: Session = Depends(get_db),
):
    cal = db.get(PotagerCalendrier, cal_id)
    if cal:
        cal.mois_debut = mois_debut
        cal.semaine_debut = semaine_debut
        cal.mois_fin = mois_fin
        cal.semaine_fin = semaine_fin
        cal.details = details
        db.commit()
        return RedirectResponse(f"/potager/{cal.item.potager_id}", status_code=302)
    return RedirectResponse("/potager", status_code=302)


@app.post("/potager/item/{item_id}/calendrier/ajouter")
def potager_add_calendrier(
    item_id: int,
    type_cal: str = Form(...),
    mois_debut: int = Form(...),
    mois_fin: int = Form(...),
    details: str = Form(""),
    semaine_debut: int = Form(1),
    semaine_fin: int = Form(4),
    db: Session = Depends(get_db),
):
    item = db.get(PotagerItem, item_id)
    if item:
        db.add(
            PotagerCalendrier(
                item_id=item_id,
                type=type_cal,
                mois_debut=mois_debut,
                semaine_debut=semaine_debut,
                mois_fin=mois_fin,
                semaine_fin=semaine_fin,
                details=details,
            )
        )
        db.commit()
        return RedirectResponse(f"/potager/{item.potager_id}", status_code=302)
    return RedirectResponse("/potager", status_code=302)


@app.post("/potager/calendrier/{cal_id}/supprimer")
def potager_delete_calendrier(cal_id: int, db: Session = Depends(get_db)):
    cal = db.get(PotagerCalendrier, cal_id)
    if cal:
        pid = cal.item.potager_id
        db.delete(cal)
        db.commit()
        return RedirectResponse(f"/potager/{pid}", status_code=302)
    return RedirectResponse("/potager", status_code=302)


@app.get("/api/legume/{legume_id}/varietes")
def api_varietes(legume_id: int, db: Session = Depends(get_db)):
    return [
        {
            "id": v.id,
            "nom": v.nom,
            "description": v.description,
            "particularites": v.particularites,
        }
        for v in db.query(Variete).filter(Variete.legume_id == legume_id).all()
    ]


# ── AI Chat ──
@app.get("/api/chat/health")
async def chat_health():
    logger.info("Health check opencode serve")
    result = await ai_client.check_health(auto_start=True)
    logger.info(f"Health result: {result}")
    return JSONResponse(result)


@app.post("/api/chat/session")
async def chat_create_session():
    logger.info("Création session chat")
    health = await ai_client.check_health(auto_start=True)
    if not health["ok"]:
        logger.error(f"Health check échoué: {health.get('error')}")
        return JSONResponse(
            {
                "ok": False,
                "error": health.get("error", "Impossible de démarrer opencode serve"),
            },
            status_code=503,
        )
    sid = await ai_client.create_session()
    if sid:
        logger.info(f"Session créée: {sid}")
        return JSONResponse(
            {"session_id": sid, "ok": True, "started": health.get("started", False)}
        )
    logger.error("Session créée mais ID invalide")
    return JSONResponse(
        {"ok": False, "error": "Session créée mais ID invalide"}, status_code=503
    )


# ── Settings ──
AVAILABLE_MODELS = [
    "opencode/deepseek-v4-flash-free",
    "opencode/deepseek-v4-flash",
    "opencode/claude-sonnet-4-6",
    "opencode/claude-haiku-4-5",
    "opencode/gpt-5.4-mini",
    "opencode/gemini-3-flash",
]


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "settings": settings_data,
            "models": AVAILABLE_MODELS,
            "TYPE_LABELS": TYPE_LABELS,
            "TYPE_COLORS": TYPE_COLORS,
        },
    )


@app.post("/settings")
async def settings_save(request: Request):
    global settings_data, TYPE_LABELS, TYPE_COLORS
    form = await request.form()

    new_settings = {
        "llm": {
            "model": form.get("llm_model", "opencode/deepseek-v4-flash-free"),
            "enabled": True,
        },
        "rag": {
            "enabled": form.get("rag_enabled") == "on",
            "k": max(1, min(10, int(form.get("rag_k", 3)))),
        },
        "colors": {},
        "labels": {},
    }

    for key in TYPE_COLORS:
        fval = form.get(f"color_{key}")
        if fval:
            new_settings["colors"][key] = fval

    for key in TYPE_LABELS:
        fval = form.get(f"label_{key}")
        if fval:
            new_settings["labels"][key] = fval

    app_settings.save(new_settings)
    settings_data = app_settings.load()
    TYPE_LABELS = settings_data["labels"]
    TYPE_COLORS = settings_data["colors"]
    logger.info(f"Settings mis à jour: model={new_settings['llm']['model']}")
    return RedirectResponse("/settings", status_code=302)


@app.post("/settings/reset")
def settings_reset():
    global settings_data, TYPE_LABELS, TYPE_COLORS
    app_settings.reset()
    settings_data = app_settings.load()
    TYPE_LABELS = settings_data["labels"]
    TYPE_COLORS = settings_data["colors"]
    return RedirectResponse("/settings", status_code=302)


@app.get("/api/models")
def api_models():
    return AVAILABLE_MODELS


# ── Admin ──
@app.get("/admin", response_class=HTMLResponse)
def admin_index(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/admin/legumes", response_class=HTMLResponse)
def admin_legumes(request: Request, db: Session = Depends(get_db)):
    legumes = db.query(Legume).order_by(Legume.nom).all()
    familles = db.query(Famille).all()
    return templates.TemplateResponse(
        "admin_legumes.html",
        {"request": request, "legumes": legumes, "familles": familles},
    )


@app.post("/admin/legumes/creer")
def admin_legume_creer(
    nom: str = Form(...),
    nom_scientifique: str = Form(""),
    famille_id: int = Form(...),
    exposition: str = Form(""),
    sol: str = Form(""),
    arrosage: str = Form(""),
    description: str = Form(""),
    conseils_culture: str = Form(""),
    db: Session = Depends(get_db),
):
    l = Legume(
        nom=nom,
        nom_scientifique=nom_scientifique,
        famille_id=famille_id,
        exposition=exposition,
        sol=sol,
        arrosage=arrosage,
        description=description,
        conseils_culture=conseils_culture,
    )
    db.add(l)
    db.commit()
    return RedirectResponse("/admin/legumes", status_code=302)


@app.get("/admin/legumes/{legume_id}", response_class=HTMLResponse)
def admin_legume_edit(legume_id: int, request: Request, db: Session = Depends(get_db)):
    legume = db.get(Legume, legume_id)
    if not legume:
        return RedirectResponse("/admin/legumes", status_code=302)
    varietes = db.query(Variete).filter(Variete.legume_id == legume_id).all()
    calendrier = (
        db.query(Calendrier)
        .filter(Calendrier.legume_id == legume_id)
        .order_by(Calendrier.mois_debut)
        .all()
    )
    maladies = db.query(Maladie).filter(Maladie.legume_id == legume_id).all()
    familles = db.query(Famille).all()
    return templates.TemplateResponse(
        "admin_legume_edit.html",
        {
            "request": request,
            "legume": legume,
            "varietes": varietes,
            "calendrier": calendrier,
            "maladies": maladies,
            "familles": familles,
            "TYPE_LABELS": TYPE_LABELS,
        },
    )


@app.post("/admin/legumes/{legume_id}/editer")
def admin_legume_editer(
    legume_id: int,
    nom: str = Form(...),
    nom_scientifique: str = Form(""),
    famille_id: int = Form(...),
    exposition: str = Form(""),
    sol: str = Form(""),
    arrosage: str = Form(""),
    description: str = Form(""),
    conseils_culture: str = Form(""),
    db: Session = Depends(get_db),
):
    l = db.get(Legume, legume_id)
    if l:
        l.nom = nom
        l.nom_scientifique = nom_scientifique
        l.famille_id = famille_id
        l.exposition = exposition
        l.sol = sol
        l.arrosage = arrosage
        l.description = description
        l.conseils_culture = conseils_culture
        db.commit()
    return RedirectResponse(f"/admin/legumes/{legume_id}", status_code=302)


@app.post("/admin/legumes/{legume_id}/supprimer")
def admin_legume_supprimer(legume_id: int, db: Session = Depends(get_db)):
    l = db.get(Legume, legume_id)
    if l:
        db.delete(l)
        db.commit()
    return RedirectResponse("/admin/legumes", status_code=302)


# ── Admin Variétés ──
@app.post("/admin/varietes/{vid}/editer")
def admin_variete_editer(
    vid: int,
    nom: str = Form(...),
    description: str = Form(""),
    particularites: str = Form(""),
    db: Session = Depends(get_db),
):
    v = db.get(Variete, vid)
    if v:
        v.nom = nom
        v.description = description
        v.particularites = particularites
        db.commit()
    return RedirectResponse(f"/admin/legumes/{v.legume_id}", status_code=302)


@app.get("/admin/varietes/{vid}/supprimer")
def admin_variete_supprimer(vid: int, db: Session = Depends(get_db)):
    v = db.get(Variete, vid)
    lid = v.legume_id if v else None
    if v:
        db.delete(v)
        db.commit()
    return RedirectResponse(f"/admin/legumes/{lid}", status_code=302)


@app.post("/admin/legumes/{legume_id}/varietes/ajouter")
def admin_variete_ajouter(
    legume_id: int,
    nom: str = Form(...),
    description: str = Form(""),
    particularites: str = Form(""),
    db: Session = Depends(get_db),
):
    db.add(
        Variete(
            legume_id=legume_id,
            nom=nom,
            description=description,
            particularites=particularites,
        )
    )
    db.commit()
    return RedirectResponse(f"/admin/legumes/{legume_id}", status_code=302)


# ── Admin Calendrier ──
@app.post("/admin/calendrier/{cid}/editer")
def admin_cal_editer(
    cid: int,
    type: str = Form(...),
    mois_debut: int = Form(...),
    semaine_debut: int = Form(1),
    mois_fin: int = Form(...),
    semaine_fin: int = Form(4),
    details: str = Form(""),
    db: Session = Depends(get_db),
):
    c = db.get(Calendrier, cid)
    if c:
        c.type = type
        c.mois_debut = mois_debut
        c.semaine_debut = semaine_debut
        c.mois_fin = mois_fin
        c.semaine_fin = semaine_fin
        c.details = details
        db.commit()
        return RedirectResponse(f"/admin/legumes/{c.legume_id}", status_code=302)
    return RedirectResponse("/admin/legumes", status_code=302)


@app.get("/admin/calendrier/{cid}/supprimer")
def admin_cal_supprimer(cid: int, db: Session = Depends(get_db)):
    c = db.get(Calendrier, cid)
    lid = c.legume_id if c else None
    if c:
        db.delete(c)
        db.commit()
    return RedirectResponse(f"/admin/legumes/{lid}", status_code=302)


@app.post("/admin/legumes/{legume_id}/calendrier/ajouter")
def admin_cal_ajouter(
    legume_id: int,
    type: str = Form(...),
    mois_debut: int = Form(...),
    semaine_debut: int = Form(1),
    mois_fin: int = Form(...),
    semaine_fin: int = Form(4),
    details: str = Form(""),
    db: Session = Depends(get_db),
):
    db.add(
        Calendrier(
            legume_id=legume_id,
            type=type,
            mois_debut=mois_debut,
            semaine_debut=semaine_debut,
            mois_fin=mois_fin,
            semaine_fin=semaine_fin,
            details=details,
        )
    )
    db.commit()
    return RedirectResponse(f"/admin/legumes/{legume_id}", status_code=302)


# ── Admin Maladies ──
@app.post("/admin/maladies/{mid}/editer")
def admin_maladie_editer(
    mid: int,
    type: str = Form(...),
    nom: str = Form(...),
    symptomes: str = Form(""),
    traitement: str = Form(""),
    prevention: str = Form(""),
    db: Session = Depends(get_db),
):
    m = db.get(Maladie, mid)
    if m:
        m.type = type
        m.nom = nom
        m.symptomes = symptomes
        m.traitement = traitement
        m.prevention = prevention
        db.commit()
        return RedirectResponse(f"/admin/legumes/{m.legume_id}", status_code=302)
    return RedirectResponse("/admin/legumes", status_code=302)


@app.get("/admin/maladies/{mid}/supprimer")
def admin_maladie_supprimer(mid: int, db: Session = Depends(get_db)):
    m = db.get(Maladie, mid)
    lid = m.legume_id if m else None
    if m:
        db.delete(m)
        db.commit()
    return RedirectResponse(f"/admin/legumes/{lid}", status_code=302)


@app.post("/admin/legumes/{legume_id}/maladies/ajouter")
def admin_maladie_ajouter(
    legume_id: int,
    type: str = Form(...),
    nom: str = Form(...),
    symptomes: str = Form(""),
    traitement: str = Form(""),
    prevention: str = Form(""),
    db: Session = Depends(get_db),
):
    db.add(
        Maladie(
            legume_id=legume_id,
            type=type,
            nom=nom,
            symptomes=symptomes,
            traitement=traitement,
            prevention=prevention,
        )
    )
    db.commit()
    return RedirectResponse(f"/admin/legumes/{legume_id}", status_code=302)


# ── Admin Familles ──
@app.get("/admin/familles", response_class=HTMLResponse)
def admin_familles(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "admin_familles.html", {"request": request, "familles": db.query(Famille).all()}
    )


@app.post("/admin/familles/creer")
def admin_famille_creer(
    nom: str = Form(...), description: str = Form(""), db: Session = Depends(get_db)
):
    db.add(Famille(nom=nom, description=description))
    db.commit()
    return RedirectResponse("/admin/familles", status_code=302)


@app.post("/admin/familles/{fid}/editer")
def admin_famille_editer(
    fid: int,
    nom: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    f = db.get(Famille, fid)
    if f:
        f.nom = nom
        f.description = description
        db.commit()
    return RedirectResponse("/admin/familles", status_code=302)


@app.get("/admin/familles/{fid}/supprimer")
def admin_famille_supprimer(fid: int, db: Session = Depends(get_db)):
    f = db.get(Famille, fid)
    if f:
        db.delete(f)
        db.commit()
    return RedirectResponse("/admin/familles", status_code=302)


# ── Admin RAG ──
@app.get("/admin/rag", response_class=HTMLResponse)
def admin_rag(request: Request):
    docs = rag_engine.list_docs()
    ok = rag_engine.is_available()
    return templates.TemplateResponse(
        "admin_rag.html", {"request": request, "docs": docs, "rag_ok": ok}
    )


@app.post("/admin/rag/upload")
async def admin_rag_upload(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    file = form.get("file")
    title = form.get("title", "")
    if not file or not file.filename.endswith(".pdf"):
        return RedirectResponse("/admin/rag?error=format", status_code=302)
    content = await file.read()
    dest = rag_engine.PDF_DIR / file.filename
    with open(dest, "wb") as f:
        f.write(content)
    result = rag_engine.ingest_pdf(str(dest), title)
    if not result.get("ok"):
        return RedirectResponse(
            "/admin/rag?error=" + result.get("error", "echec"), status_code=302
        )
    return RedirectResponse("/admin/rag", status_code=302)


@app.get("/admin/rag/{doc_id}/supprimer")
def admin_rag_supprimer(doc_id: str):
    rag_engine.delete_doc(doc_id)
    return RedirectResponse("/admin/rag", status_code=302)


# ── RAG integration in AI Chat ──
@app.post("/api/chat/send")
async def chat_send_rag(request: Request):
    body = await request.json()
    session_id = body.get("session_id")
    text = body.get("text", "")
    context = body.get("context", "")
    logger.info(
        f"Message chat reçu: session={session_id}, text={text[:80]!r}, "
        f"context_len={len(context)}"
    )
    if not session_id or not text:
        logger.warning("session_id ou text manquant")
        return JSONResponse(
            {"ok": False, "error": "session_id et text requis"}, status_code=400
        )

    rag_context = rag_engine.get_context(text, k=3)
    logger.info(f"RAG context trouvé: {len(rag_context)} caractères")
    full_context = context
    if rag_context:
        full_context = f"{context}\n\n---\nDocuments de référence :\n{rag_context}\n---\nUtilise ces documents pour répondre si pertinent."

    health = await ai_client.check_health(auto_start=True)
    logger.info(f"Health check opencode: {health}")
    if not health["ok"]:
        logger.error(f"Health check échoué: {health}")
        return JSONResponse(
            {"ok": False, "error": health.get("error", "Serveur indisponible")},
            status_code=503,
        )
    reply = await ai_client.send_message(session_id, text, full_context)
    if reply is not None:
        logger.info(f"Réponse reçue: {len(reply)} caractères")
        return JSONResponse({"ok": True, "reply": reply})
    logger.error("Pas de réponse de l'assistant")
    return JSONResponse(
        {"ok": False, "error": "Pas de réponse de l'assistant"}, status_code=503
    )
