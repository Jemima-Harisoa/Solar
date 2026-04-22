# Projet Solar - Gestion energetique domestique

## 1. Objectif

Developper une application desktop Python permettant de:
- calculer la consommation energetique d'une maison,
- analyser la consommation par tranche horaire,
- dimensionner les besoins en panneaux solaires et en batterie,
- proposer le type de panneau le plus pertinent selon le ratio prix/energie.

## 2. Fonctionnalites principales

### 2.1 Gestion des donnees metier

- Gestion des types d'appareils et des appareils (code, nom, puissance, statut, date d'installation).
- Gestion des creneaux horaires (avec support des creneaux traversant minuit).
- Gestion des programmes d'usage par appareil et par creneau.
- Historique de consommation energetique.

### 2.2 Gestion des configurations systeme

- Creation, mise a jour, suppression de configurations systeme.
- Une seule configuration active a la fois (`IsActive = 1`).
- Parametres utilises pour les calculs:
  - `GridVoltageV`
  - `SolarPanelEfficiencyPct` (information globale)
  - `BatteryOvercapacityPct`

### 2.3 Gestion des types de panneaux

- CRUD des types de panneaux (`PanelType`).
- Chaque type contient:
  - energie unitaire (`UnitEnergyW`),
  - capacite exploitable (`ExploitablePct`),
  - energie utile calculee (`UsableEnergyW`),
  - prix unitaire (`UnitPriceAr`).
- Comparaison automatique des options pour un besoin donne avec recommandation du meilleur ratio `Ar/W`.

### 2.4 Bilan energetique

Le bilan prend en compte les tranches:
- JOUR (6h-17h)
- SOIR (17h-19h)
- NUIT (19h-6h)

Regles metier appliquees:
- la tranche SOIR est couverte a 50% par le solaire et 50% par la batterie,
- la batterie couvre la nuit + part batterie du soir,
- une marge batterie est appliquee via `BatteryOvercapacityPct`,
- la puissance panneau requise est calculee sur la fenetre de recharge JOUR.

## 3. Interface utilisateur (Tkinter)

L'application expose 7 onglets:
1. Materiels
2. Creneaux
3. Usage
4. Historique
5. Bilan
6. Configurations
7. Types panneaux

Points notables:
- verrouillage progressif de certaines etapes selon l'etat des donnees,
- generation du bilan energetique avec details par tranche,
- recommandation automatique de type de panneau (cout total, nombre de panneaux, ratio prix/energie),
- gestion des erreurs avec rollback SQL automatique.

## 4. Architecture du projet

- `main.py`: point d'entree, chargement environnement, normalisation host SQL local, lancement UI.
- `app/config.py`: chargement `.env` et adaptation host Docker local.
- `connection/server_connection.py`: wrapper de connexion SQL Server (`ServerConnect`) avec `commit`, `rollback`, `Disconnect`.
- `app/crud/`: acces donnees SQL Server (Device, TimeSlot, Usage, History, Config, PanelType, etc.).
- `app/services/energy_spec_service.py`: calculs de dimensionnement energetique et comparaison des panneaux.
- `app/ui/solar_app.py`: UI Tkinter et orchestration metier.

## 5. Base de donnees SQL Server

### 5.1 Tables principales

- `TimeSlot`
- `SystemConfiguration`
- `DeviceType`
- `Device`
- `DeviceUsageSchedule`
- `EnergyConsumption`
- `SolarPanelProduction`
- `BatteryStorage`
- `BatteryMovement`
- `PanelType`

### 5.2 Vues

- `vw_DeviceUsageSchedule`
- `vw_EnergyBalance`

### 5.3 Scripts d'initialisation

Ordre d'execution dans `database/init/`:
1. `00-reset-base.sql`: reset des donnees metier (conserve `PanelType` et `SystemConfiguration`).
2. `01-schema.sql`: creation schema principal (tables, vues, indexes).
3. `02-data.sql`: seed de base (config, creneaux, appareils, usages, historique, production, batterie).
4. `03-alea.sql`: creation/seed de `PanelType` (si absent).
5. `04-data_import.sql`: jeu de donnees de test/import.
6. `05-panel_types.sql`: reinitialisation + insertion de types de panneaux personnalises.

## 6. Environnement et connexion SQL

Variables supportees (`.env`):

```env
SQL_SERVER_HOST=sqlserver
SQL_SERVER_PORT=1433
SQL_USER=sa
SQL_PASSWORD=SolarDev!2026
SA_PASSWORD=SolarDev!2026
DATABASE_NAME=solar
```

Comportement local:
- si `SQL_SERVER_HOST=sqlserver`, l'application le normalise en `127.0.0.1` pour l'execution locale hors conteneur.

## 7. Lancement local

### 7.1 Prerequis

- Python 3.8+
- Docker + Docker Compose
- SQL Server (via conteneur)

### 7.2 Installation

```bash
git clone <repo-url>
cd Solar
pip install -r requirements-dev.txt
```

### 7.3 Demarrage SQL Server

```bash
docker compose up -d sqlserver
```

### 7.4 Verification connexion

```bash
python ci/check_db_connection.py
```

### 7.5 Lancement application

```bash
python main.py
```

## 8. CI/CD

Workflow GitHub Actions: `.github/workflows/ci-cd.yml`

### 8.1 CI

- Demarrage SQL Server Docker.
- Verification healthcheck.
- Initialisation SQL (`01-schema.sql`, `02-data.sql`).
- Verification de connexion et des donnees via `ci/check_db_connection.py`.

### 8.2 CD

- Build Windows de l'application desktop via PyInstaller.
- Publication de l'executable en artifact.

### 8.3 Triggers

- Push/Pull Request sur `main` et `dev`
- `workflow_dispatch`
- `release` (publication)

## 9. Dependances de dev

- `pymssql==2.3.5`
- `pytest==8.3.5`
- `pyinstaller==6.13.0`
