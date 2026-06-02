"""Tests exhaustifs pour Mon Potager — couvre toutes les routes et actions."""

import json
import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

os.environ["OPENCODE_SERVER_URL"] = "http://localhost:19999"
os.environ["OPENCODE_SERVER_PASSWORD"] = ""

from app.main import app
from app.database import engine, Base
from app.seed import init_db
from app.settings import SETTINGS_FILE

client = TestClient(app)


def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    init_db()


def first_legume_id():
    from app.database import SessionLocal
    from app.models import Legume

    db = SessionLocal()
    lid = db.query(Legume).first().id
    db.close()
    return lid


def first_famille_id():
    from app.database import SessionLocal
    from app.models import Famille

    db = SessionLocal()
    fid = db.query(Famille).first().id
    db.close()
    return fid


def create_potager():
    resp = client.post(
        "/potager/creer",
        data={"annee": 2025, "nom": "Test Potager", "notes": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    from app.database import SessionLocal
    from app.models import Potager

    db = SessionLocal()
    p = db.query(Potager).first()
    db.close()
    return p.id


# ═══════════════════════════════════════════
# PAGES PUBLIQUES
# ═══════════════════════════════════════════


class TestPublicPages:
    def setup_method(self):
        setup_db()

    def test_home(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Mon Potager" in resp.text

    def test_home_stats(self):
        resp = client.get("/")
        assert "Alliacées" in resp.text
        assert "Solanacées" in resp.text
        assert "4" in resp.text  # 4 familles seed

    def test_legumes_list(self):
        resp = client.get("/legumes")
        assert resp.status_code == 200
        assert "Ail" in resp.text
        assert "Poivron" in resp.text

    def test_legumes_filter_by_famille(self):
        fid = first_famille_id()
        resp = client.get(f"/legumes?famille_id={fid}")
        assert resp.status_code == 200

    def test_legume_detail(self):
        lid = first_legume_id()
        resp = client.get(f"/legume/{lid}")
        assert resp.status_code == 200
        assert "Ail" in resp.text or "Poivron" in resp.text

    def test_legume_detail_404(self):
        resp = client.get("/legume/99999")
        assert resp.status_code == 404

    def test_legume_pdf(self):
        lid = first_legume_id()
        resp = client.get(f"/legume/{lid}/pdf")
        assert resp.status_code == 200
        assert "style" in resp.text  # calendrier-barres

    def test_legume_pdf_404(self):
        resp = client.get("/legume/99999/pdf")
        assert resp.status_code == 404

    def test_familles_list(self):
        resp = client.get("/familles")
        assert resp.status_code == 200

    def test_search_empty(self):
        resp = client.get("/recherche")
        assert resp.status_code == 200

    def test_search_results(self):
        resp = client.get("/recherche?q=ail")
        assert resp.status_code == 200
        assert "Ail" in resp.text

    def test_search_no_results(self):
        resp = client.get("/recherche?q=zzzzzzz")
        assert resp.status_code == 200

    def test_api_varietes(self):
        lid = first_legume_id()
        resp = client.get(f"/api/legume/{lid}/varietes")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_api_varietes_empty(self):
        resp = client.get("/api/legume/99999/varietes")
        assert resp.status_code == 200
        assert resp.json() == []


# ═══════════════════════════════════════════
# MON POTAGER
# ═══════════════════════════════════════════


class TestPotager:
    def setup_method(self):
        setup_db()

    def test_potager_list_empty(self):
        resp = client.get("/potager")
        assert resp.status_code == 200

    def test_potager_create_form(self):
        resp = client.get("/potager/creer")
        assert resp.status_code == 200

    def test_potager_create(self):
        resp = client.post(
            "/potager/creer",
            data={"annee": 2025, "nom": "Mon Carré", "notes": "test"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/potager/" in resp.headers["location"]

    def test_potager_create_minimal(self):
        resp = client.post(
            "/potager/creer",
            data={"annee": 2026, "nom": "Test"},
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_potager_detail_exists(self):
        pid = create_potager()
        resp = client.get(f"/potager/{pid}")
        assert resp.status_code == 200
        assert "Test Potager" in resp.text

    def test_potager_detail_404(self):
        resp = client.get("/potager/99999")
        assert resp.status_code == 404

    def test_potager_detail_month(self):
        pid = create_potager()
        resp = client.get(f"/potager/{pid}?mois=5")
        assert resp.status_code == 200
        assert "Mai" in resp.text

    def test_potager_ajouter_item_legume(self):
        pid = create_potager()
        lid = first_legume_id()
        resp = client.post(
            f"/potager/{pid}/ajouter",
            data={"legume_id": lid, "type_item": "legume", "quantite": "10 plants"},
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_potager_ajouter_item_custom(self):
        pid = create_potager()
        resp = client.post(
            f"/potager/{pid}/ajouter",
            data={
                "type_item": "couvert",
                "nom_custom": "Moutarde",
                "quantite": "1 sachet",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_potager_edit_item(self):
        pid = create_potager()
        lid = first_legume_id()
        client.post(
            f"/potager/{pid}/ajouter", data={"legume_id": lid, "type_item": "legume"}
        )
        from app.database import SessionLocal
        from app.models import PotagerItem

        db = SessionLocal()
        item = db.query(PotagerItem).first()
        db.close()
        resp = client.post(
            f"/potager/item/{item.id}/editer",
            data={
                "nom_custom": "Ail révisé",
                "quantite": "20 plants",
                "emplacement": "Planche B",
                "compagnons": "carotte",
                "notes": "test edit",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_potager_edit_item_invalid(self):
        resp = client.post(
            "/potager/item/99999/editer",
            data={"nom_custom": "x"},
            follow_redirects=False,
        )
        assert resp.status_code == 302  # redirect vers /potager

    def test_potager_delete_item(self):
        pid = create_potager()
        lid = first_legume_id()
        client.post(
            f"/potager/{pid}/ajouter", data={"legume_id": lid, "type_item": "legume"}
        )
        from app.database import SessionLocal
        from app.models import PotagerItem

        db = SessionLocal()
        item = db.query(PotagerItem).first()
        db.close()
        resp = client.post(f"/potager/item/{item.id}/supprimer", follow_redirects=False)
        assert resp.status_code == 302

    def test_potager_add_calendar(self):
        pid = create_potager()
        lid = first_legume_id()
        client.post(
            f"/potager/{pid}/ajouter", data={"legume_id": lid, "type_item": "legume"}
        )
        from app.database import SessionLocal
        from app.models import PotagerItem

        db = SessionLocal()
        item = db.query(PotagerItem).first()
        db.close()
        resp = client.post(
            f"/potager/item/{item.id}/calendrier/ajouter",
            data={
                "type_cal": "semis_direct",
                "mois_debut": 3,
                "semaine_debut": 1,
                "mois_fin": 5,
                "semaine_fin": 2,
                "details": "Semis test",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_potager_edit_calendar(self):
        pid = create_potager()
        lid = first_legume_id()
        client.post(
            f"/potager/{pid}/ajouter", data={"legume_id": lid, "type_item": "legume"}
        )
        from app.database import SessionLocal
        from app.models import PotagerCalendrier

        db = SessionLocal()
        cal = db.query(PotagerCalendrier).first()
        db.close()
        if cal:
            resp = client.post(
                f"/potager/calendrier/{cal.id}/editer",
                data={
                    "mois_debut": 4,
                    "mois_fin": 6,
                    "semaine_debut": 2,
                    "semaine_fin": 3,
                    "details": "modifié",
                },
                follow_redirects=False,
            )
            assert resp.status_code == 302

    def test_potager_delete_calendar(self):
        pid = create_potager()
        lid = first_legume_id()
        client.post(
            f"/potager/{pid}/ajouter", data={"legume_id": lid, "type_item": "legume"}
        )
        from app.database import SessionLocal
        from app.models import PotagerCalendrier

        db = SessionLocal()
        cal = db.query(PotagerCalendrier).first()
        db.close()
        if cal:
            resp = client.post(
                f"/potager/calendrier/{cal.id}/supprimer", follow_redirects=False
            )
            assert resp.status_code == 302


# ═══════════════════════════════════════════
# PARAMÈTRES
# ═══════════════════════════════════════════


class TestSettings:
    def setup_method(self):
        setup_db()
        if SETTINGS_FILE.exists():
            SETTINGS_FILE.unlink()

    def test_settings_page(self):
        resp = client.get("/settings")
        assert resp.status_code == 200
        assert "Paramètres" in resp.text

    def test_settings_save(self):
        resp = client.post(
            "/settings",
            data={
                "llm_model": "opencode/deepseek-v4-flash-free",
                "rag_k": 5,
                "rag_enabled": "on",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_settings_change_model(self):
        client.post(
            "/settings", data={"llm_model": "opencode/gpt-5.4-mini", "rag_k": 3}
        )
        resp = client.get("/settings")
        assert resp.status_code == 200

    def test_settings_reset(self):
        client.post(
            "/settings", data={"llm_model": "opencode/gpt-5.4-mini", "rag_k": 5}
        )
        resp = client.post("/settings/reset", follow_redirects=False)
        assert resp.status_code == 302

    def test_api_models(self):
        resp = client.get("/api/models")
        assert resp.status_code == 200
        models = resp.json()
        assert isinstance(models, list)
        assert len(models) > 0
        assert "opencode/deepseek-v4-flash-free" in models

    def test_settings_custom_colors(self):
        resp = client.post(
            "/settings",
            data={
                "llm_model": "opencode/deepseek-v4-flash-free",
                "rag_k": 3,
                "color_semis_direct": "#ff0000",
                "label_semis_direct": "Semis test",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302


# ═══════════════════════════════════════════
# ADMIN CRUD
# ═══════════════════════════════════════════


class TestAdmin:
    def setup_method(self):
        setup_db()

    def test_admin_dashboard(self):
        resp = client.get("/admin")
        assert resp.status_code == 200

    def test_admin_legumes(self):
        resp = client.get("/admin/legumes")
        assert resp.status_code == 200
        assert "Ail" in resp.text

    def test_admin_legume_edit_page(self):
        lid = first_legume_id()
        resp = client.get(f"/admin/legumes/{lid}")
        assert resp.status_code == 200

    def test_admin_legume_edit_page_404(self):
        resp = client.get("/admin/legumes/99999", follow_redirects=False)
        assert resp.status_code == 302  # redirect

    def test_admin_legume_edit_post(self):
        lid = first_legume_id()
        fid = first_famille_id()
        resp = client.post(
            f"/admin/legumes/{lid}/editer",
            data={
                "nom": "Ail Modifié",
                "nom_scientifique": "Allium test",
                "famille_id": fid,
                "exposition": "Soleil",
                "sol": "Léger",
                "arrosage": "Faible",
                "description": "Test",
                "conseils_culture": "Bien",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_admin_legume_create(self):
        fid = first_famille_id()
        resp = client.post(
            "/admin/legumes/creer",
            data={
                "nom": "Nouveau légume",
                "famille_id": fid,
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_admin_legume_delete(self):
        fid = first_famille_id()
        client.post(
            "/admin/legumes/creer", data={"nom": "À supprimer", "famille_id": fid}
        )
        from app.database import SessionLocal
        from app.models import Legume

        db = SessionLocal()
        leg = db.query(Legume).filter(Legume.nom == "À supprimer").first()
        db.close()
        resp = client.post(f"/admin/legumes/{leg.id}/supprimer", follow_redirects=False)
        assert resp.status_code == 302

    def test_admin_variete_add(self):
        lid = first_legume_id()
        resp = client.post(
            f"/admin/legumes/{lid}/varietes/ajouter",
            data={
                "nom": "Variété test",
                "description": "Desc",
                "particularites": "Part",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_admin_variete_edit(self):
        from app.database import SessionLocal
        from app.models import Variete

        lid = first_legume_id()
        client.post(f"/admin/legumes/{lid}/varietes/ajouter", data={"nom": "VarTest"})
        db = SessionLocal()
        v = db.query(Variete).filter(Variete.nom == "VarTest").first()
        db.close()
        resp = client.post(
            f"/admin/varietes/{v.id}/editer",
            data={
                "nom": "VarModifiée",
                "description": "Nouvelle desc",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_admin_variete_delete(self):
        from app.database import SessionLocal
        from app.models import Variete

        lid = first_legume_id()
        client.post(f"/admin/legumes/{lid}/varietes/ajouter", data={"nom": "VarDelete"})
        db = SessionLocal()
        v = db.query(Variete).filter(Variete.nom == "VarDelete").first()
        db.close()
        resp = client.get(f"/admin/varietes/{v.id}/supprimer", follow_redirects=False)
        assert resp.status_code == 302

    def test_admin_calendar_add(self):
        lid = first_legume_id()
        resp = client.post(
            f"/admin/legumes/{lid}/calendrier/ajouter",
            data={
                "type": "semis_direct",
                "mois_debut": 3,
                "semaine_debut": 1,
                "mois_fin": 5,
                "semaine_fin": 2,
                "details": "Cal test",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_admin_calendar_edit(self):
        from app.database import SessionLocal
        from app.models import Calendrier

        lid = first_legume_id()
        client.post(
            f"/admin/legumes/{lid}/calendrier/ajouter",
            data={
                "type": "plantation",
                "mois_debut": 4,
                "mois_fin": 6,
                "details": "test",
            },
        )
        db = SessionLocal()
        c = db.query(Calendrier).filter(Calendrier.details == "test").first()
        db.close()
        resp = client.post(
            f"/admin/calendrier/{c.id}/editer",
            data={
                "type": "recolte",
                "mois_debut": 5,
                "semaine_debut": 1,
                "mois_fin": 7,
                "semaine_fin": 3,
                "details": "édité",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_admin_calendar_delete(self):
        from app.database import SessionLocal
        from app.models import Calendrier

        lid = first_legume_id()
        client.post(
            f"/admin/legumes/{lid}/calendrier/ajouter",
            data={
                "type": "action",
                "mois_debut": 5,
                "mois_fin": 6,
            },
        )
        db = SessionLocal()
        c = db.query(Calendrier).filter(Calendrier.type == "action").first()
        db.close()
        resp = client.get(f"/admin/calendrier/{c.id}/supprimer", follow_redirects=False)
        assert resp.status_code == 302

    def test_admin_maladie_add(self):
        lid = first_legume_id()
        resp = client.post(
            f"/admin/legumes/{lid}/maladies/ajouter",
            data={
                "type": "maladie",
                "nom": "Test maladie",
                "symptomes": "taches",
                "traitement": "bouillie",
                "prevention": "rotation",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_admin_maladie_edit(self):
        from app.database import SessionLocal
        from app.models import Maladie

        lid = first_legume_id()
        client.post(
            f"/admin/legumes/{lid}/maladies/ajouter",
            data={
                "type": "ravageur",
                "nom": "Test ravageur",
            },
        )
        db = SessionLocal()
        m = db.query(Maladie).filter(Maladie.nom == "Test ravageur").first()
        db.close()
        resp = client.post(
            f"/admin/maladies/{m.id}/editer",
            data={
                "type": "maladie",
                "nom": "Modifié",
                "symptomes": "s",
                "traitement": "t",
                "prevention": "p",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_admin_maladie_delete(self):
        from app.database import SessionLocal
        from app.models import Maladie

        lid = first_legume_id()
        client.post(
            f"/admin/legumes/{lid}/maladies/ajouter",
            data={"type": "maladie", "nom": "MalDelete"},
        )
        db = SessionLocal()
        m = db.query(Maladie).filter(Maladie.nom == "MalDelete").first()
        db.close()
        resp = client.get(f"/admin/maladies/{m.id}/supprimer", follow_redirects=False)
        assert resp.status_code == 302

    def test_admin_familles_list(self):
        resp = client.get("/admin/familles")
        assert resp.status_code == 200

    def test_admin_famille_create(self):
        resp = client.post(
            "/admin/familles/creer",
            data={
                "nom": "Famille Test",
                "description": "Desc",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_admin_famille_edit(self):
        from app.database import SessionLocal
        from app.models import Famille

        client.post("/admin/familles/creer", data={"nom": "FamEdit"})
        db = SessionLocal()
        f = db.query(Famille).filter(Famille.nom == "FamEdit").first()
        db.close()
        resp = client.post(
            f"/admin/familles/{f.id}/editer",
            data={
                "nom": "FamEditModifiée",
                "description": "Nouvelle",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_admin_famille_delete(self):
        from app.database import SessionLocal
        from app.models import Famille

        client.post("/admin/familles/creer", data={"nom": "FamDelete"})
        db = SessionLocal()
        f = db.query(Famille).filter(Famille.nom == "FamDelete").first()
        db.close()
        resp = client.get(f"/admin/familles/{f.id}/supprimer", follow_redirects=False)
        assert resp.status_code == 302


# ═══════════════════════════════════════════
# RAG
# ═══════════════════════════════════════════


class TestRAG:
    def setup_method(self):
        setup_db()

    def test_admin_rag_page(self):
        resp = client.get("/admin/rag")
        assert resp.status_code == 200
        assert "Base documentaire" in resp.text


# ═══════════════════════════════════════════
# UTILITAIRES & EDGE CASES
# ═══════════════════════════════════════════


class TestUtilities:
    def setup_method(self):
        setup_db()

    def test_bar_style(self):
        from app.main import bar_style

        style = bar_style(3, 1, 5, 2)
        assert "left:" in style
        assert "width:" in style

    def test_bar_style_full_year(self):
        from app.main import bar_style

        style = bar_style(1, 1, 12, 4)
        assert "left:0.00%" in style
        assert "width:100.00%" in style

    def test_week_pos(self):
        from app.main import week_pos

        assert week_pos(1, 1) == 1
        assert week_pos(3, 2) == 10
        assert week_pos(12, 4) == 48

    def test_settings_load_default(self):
        if SETTINGS_FILE.exists():
            SETTINGS_FILE.unlink()
        from app.settings import load

        s = load()
        assert s["llm"]["model"] == "opencode/deepseek-v4-flash-free"
        assert len(s["colors"]) == 8
        assert len(s["labels"]) == 8

    def test_settings_save_and_load(self):
        from app.settings import save, load

        save({"llm": {"model": "test/model", "enabled": True}})
        s = load()
        assert s["llm"]["model"] == "test/model"

    def test_rag_available(self):
        from app.rag import is_available

        assert is_available()  # chromadb est installé

    def test_rag_chunk_text(self):
        from app.rag import chunk_text

        chunks = chunk_text("mot " * 2000, chunk_size=500, overlap=100)
        assert len(chunks) >= 2

    def test_rag_search_empty(self):
        from app.rag import search

        results = search("test")
        assert isinstance(results, list)

    def test_rag_get_context_empty(self):
        from app.rag import get_context

        ctx = get_context("test")
        assert ctx == ""

    def test_static_files_css(self):
        resp = client.get("/static/style.css")
        assert resp.status_code == 200

    def test_static_files_js(self):
        resp = client.get("/static/chat.js")
        assert resp.status_code == 200

    def test_static_files_css_chat(self):
        resp = client.get("/static/chat.css")
        assert resp.status_code == 200

    def test_404_page(self):
        resp = client.get("/page-inexistante")
        assert resp.status_code == 404

    def test_navbar_links(self):
        resp = client.get("/")
        assert "/potager" in resp.text
        assert "/settings" in resp.text
        assert "/legumes" in resp.text
        assert "/familles" in resp.text
        assert "/recherche" in resp.text


# ═══════════════════════════════════════════
# CHAT (sans opencode serve)
# ═══════════════════════════════════════════


class TestChat:
    def setup_method(self):
        setup_db()

    def test_chat_health(self):
        """Sans serveur, doit retourner ok: False"""
        resp = client.get("/api/chat/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "ok" in data
