from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, Text, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime

Base = declarative_base()

# Routine fixe (config globale)
class RoutineTemplate(Base):
    __tablename__ = "routine_template"
    
    id = Column(Integer, primary_key=True)
    item_name = Column(String, nullable=False)
    order = Column(Integer, default=0)

# Routine du jour (state)
class RoutineDaily(Base):
    __tablename__ = "routine_daily"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    item_name = Column(String, nullable=False)
    done = Column(Boolean, default=False)

# Raisons personnelles
class Reason(Base):
    __tablename__ = "reasons"
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

# Tâches planifiées
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    title = Column(String, nullable=False)
    time = Column(String, nullable=True)
    done = Column(Boolean, default=False)

# Substances (sobriété)
class Substance(Base):
    __tablename__ = "substances"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

# Consommations
class Consumption(Base):
    __tablename__ = "consumptions"
    
    id = Column(Integer, primary_key=True)
    substance_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    quantity = Column(String, nullable=True)
    note = Column(Text, nullable=True)

# Productivité quotidienne
class Productivity(Base):
    __tablename__ = "productivity"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, nullable=False)
    score = Column(Float, nullable=True)
    note = Column(Text, nullable=True)

# Objectifs
class Objectives(Base):
    __tablename__ = "objectives"
    
    id = Column(Integer, primary_key=True)
    studies_progress = Column(Integer, default=0)
    studies_notes = Column(Text, nullable=True)
    current_weight = Column(Float, default=87.0)
    sleep_hours = Column(Float, nullable=True)
    food_satisfaction = Column(Integer, default=5)

class ImmigrationStep(Base):
    __tablename__ = "immigration_steps"
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    done = Column(Boolean, default=False)
    order = Column(Integer, default=0)

# Configuration DB
engine = create_engine("sqlite:///productivity.db")
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    
    db = SessionLocal()
    
    # Routine template
    if db.query(RoutineTemplate).count() == 0:
        default_routine = [
            "Douche",
            "Brossage de dents",
            "Ranger ma chambre",
            "Vérifier mes ongles",
            "Mettre du parfum"
        ]
        for i, item in enumerate(default_routine):
            db.add(RoutineTemplate(item_name=item, order=i))
    
    # Objectifs par défaut
    if db.query(Objectives).count() == 0:
        db.add(Objectives())
    
    # Étapes immigration par défaut
    if db.query(ImmigrationStep).count() == 0:
        default_steps = [
            "Évaluation profil Express Entry",
            "Test de langue (IELTS/TEF)",
            "Équivalence diplômes (ECA)",
            "Créer profil Express Entry",
            "Recevoir ITA (Invitation)",
            "Soumettre demande résidence permanente"
        ]
        for i, step in enumerate(default_steps):
            db.add(ImmigrationStep(title=step, order=i))
    
    db.commit()
    db.close()