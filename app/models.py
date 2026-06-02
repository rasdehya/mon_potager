from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base


class Famille(Base):
    __tablename__ = "familles"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    legumes = relationship(
        "Legume", back_populates="famille", cascade="all, delete-orphan"
    )


class Legume(Base):
    __tablename__ = "legumes"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), unique=True, nullable=False)
    nom_scientifique = Column(String(200))
    famille_id = Column(Integer, ForeignKey("familles.id"), nullable=False)
    description = Column(Text)
    conseils_culture = Column(Text)
    exposition = Column(String(200))
    sol = Column(String(200))
    arrosage = Column(String(200))
    famille = relationship("Famille", back_populates="legumes")
    varietes = relationship(
        "Variete", back_populates="legume", cascade="all, delete-orphan"
    )
    calendrier = relationship(
        "Calendrier", back_populates="legume", cascade="all, delete-orphan"
    )
    maladies = relationship(
        "Maladie", back_populates="legume", cascade="all, delete-orphan"
    )


class Variete(Base):
    __tablename__ = "varietes"
    id = Column(Integer, primary_key=True, index=True)
    legume_id = Column(Integer, ForeignKey("legumes.id"), nullable=False)
    nom = Column(String(200), nullable=False)
    description = Column(Text)
    particularites = Column(Text)
    legume = relationship("Legume", back_populates="varietes")


class Calendrier(Base):
    __tablename__ = "calendrier"
    id = Column(Integer, primary_key=True, index=True)
    legume_id = Column(Integer, ForeignKey("legumes.id"), nullable=False)
    type = Column(String(50), nullable=False)
    mois_debut = Column(Integer, nullable=False)
    semaine_debut = Column(Integer, default=1)
    mois_fin = Column(Integer, nullable=False)
    semaine_fin = Column(Integer, default=4)
    details = Column(Text)
    legume = relationship("Legume", back_populates="calendrier")


class Maladie(Base):
    __tablename__ = "maladies"
    id = Column(Integer, primary_key=True, index=True)
    legume_id = Column(Integer, ForeignKey("legumes.id"), nullable=False)
    nom = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)
    symptomes = Column(Text)
    traitement = Column(Text)
    prevention = Column(Text)
    legume = relationship("Legume", back_populates="maladies")


class Potager(Base):
    __tablename__ = "potagers"
    id = Column(Integer, primary_key=True, index=True)
    annee = Column(Integer, nullable=False)
    nom = Column(String(200), nullable=False)
    active = Column(Integer, default=1)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    items = relationship(
        "PotagerItem", back_populates="potager", cascade="all, delete-orphan"
    )


class PotagerItem(Base):
    __tablename__ = "potager_items"
    id = Column(Integer, primary_key=True, index=True)
    potager_id = Column(Integer, ForeignKey("potagers.id"), nullable=False)
    legume_id = Column(Integer, ForeignKey("legumes.id"), nullable=True)
    variete_id = Column(Integer, ForeignKey("varietes.id"), nullable=True)
    type = Column(String(50), default="legume")
    nom_custom = Column(String(200))
    quantite = Column(String(100))
    emplacement = Column(String(200))
    compagnons = Column(String(200))
    notes = Column(Text)
    ordre = Column(Integer, default=0)
    potager = relationship("Potager", back_populates="items")
    legume = relationship("Legume")
    variete = relationship("Variete")
    calendrier = relationship(
        "PotagerCalendrier", back_populates="item", cascade="all, delete-orphan"
    )


class PotagerCalendrier(Base):
    __tablename__ = "potager_calendrier"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("potager_items.id"), nullable=False)
    type = Column(String(50), nullable=False)
    mois_debut = Column(Integer, nullable=False)
    semaine_debut = Column(Integer, default=1)
    mois_fin = Column(Integer, nullable=False)
    semaine_fin = Column(Integer, default=4)
    details = Column(Text)
    item = relationship("PotagerItem", back_populates="calendrier")
