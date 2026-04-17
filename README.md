# Projet de gestion de consommation énergétique

## 1. Objectif

Développer une application permettant de :
- Calculer la consommation énergétique d’une maison
- Analyser cette consommation selon différents critères
- Déterminer les besoins en énergie (panneaux solaires et batteries)
- Fournir un bilan énergétique global

---

## 2. Fonctionnalités principales

### 2.1 Calcul de la consommation énergétique

#### Par matériel
- Basé sur :
  - La puissance de l’appareil
  - Le temps d’utilisation

#### Par tranche horaire
- Journée : 6h - 17h
- Soir : 17h - 19h
- Nuit : 19h - 6h

---

### 2.2 Affichage des résultats

#### Par matériel
- Consommation totale
- Consommation par appareil selon l’usage

#### Par tranche horaire
- Consommation totale
- Consommation par période (jour / soir / nuit)

---

## 3. Bilan des besoins énergétiques

### 3.1 Énergie totale nécessaire
- Correspond à la consommation totale de la maison

---

### 3.2 Panneaux solaires

#### Hypothèse
- 1 panneau produit 40% de l’énergie qu’il fournit

#### Exemple
- Besoin : 1000W  
- Nécessaire : 2500W de panneaux solaires

#### Répartition de la production
- Journée (6h - 17h) :
  - Alimentation des appareils
  - Stockage dans la batterie
- Soir (17h - 19h) :
  - Production réduite à 50%

#### Hypothèse de production horaire
- Production totale journalière = production horaire × nombre d’heures
- Exemple :
  - 2500W / 11h = 227W par heure

---

### 3.3 Batterie de stockage

#### Utilisation
- Nuit
- Journées nuageuses

#### Capacité
- Consommation nocturne majorée de 50%
- Exemple :
  - Consommation nuit : 500W  
  - Capacité batterie : 750W

#### Fonctionnement
- Journée :
  - Recharge continue par les panneaux
- Limite :
  - Batterie pleine → perte d’énergie produite

---

### 3.4 Résultats attendus

- Consommation totale de la maison
- Puissance totale des panneaux solaires nécessaires
- Capacité de batterie requise pour la nuit (avec marge de 50%)

---

## 4. Technologies utilisées

- Python (application desktop)
- SQL Server

---

## 5. Structure de la base de données (Branche Dev)

### 5.1 Tables de configuration

#### TimeSlot
- Créneaux horaires :
  - Jour (6h - 17h)
  - Soir (17h - 19h)
  - Nuit (19h - 6h)

#### SystemConfiguration
- GridVoltageV : 230V
- SolarPanelEfficiencyPct : 40%
- BatteryOvercapacityPct : 50%

---

### 5.2 Tables matériels

#### DeviceType
- Catégories d’appareils

#### Device
- Appareils de la maison
- PowerW
- Statut : ACTIF, INACTIF, MAINTENANCE
- Date d’installation

#### DeviceUsageSchedule
- Programme d’utilisation quotidien
- DailyUsageHours par tranche horaire

---

### 5.3 Tables consommation et production

#### EnergyConsumption
- Historique de consommation
- EnergyConsumedWh
- DurationHours
- Lié à Device et TimeSlot

#### SolarPanelProduction
- Production journalière
- TotalPanelCapacityW
- ProductionPercentage
- EnergyProducedWh (calculée)

#### BatteryStorage
- Batteries
- TotalCapacityWh
- CurrentChargeWh
- ChargingEfficiencyPct : 95%
- Statut : ACTIF, MAINTENANCE, DEFAUT

#### BatteryMovement
- Historique des charges/décharges
- MovementType : CHARGE / DECHARGE
- ChargeBeforeWh / ChargeAfterWh

---

### 5.4 Vues de calcul

#### vw_DeviceUsageSchedule
- Agrégation :
  - Appareils
  - Utilisation
  - Créneaux horaires
- Calcul :
  - DailyEnergyConsumptionWh = PowerW × DailyUsageHours

#### vw_EnergyBalance
- Bilan énergétique global
- TotalConsumptionWh vs TotalProductionWh
- Calcul automatique :
  - Besoin en panneaux solaires
  - Capacité batterie
- EnergyBalanceWh :
  - Production - consommation

---

## 6. CI/CD (Desktop Python + SQL Server Docker)

### 6.1 Objectif

Automatiser :
- Les vérifications de connexion à la base
- Le build de l’application

---

### 6.2 CI

- Lancement de SQL Server avec Docker Compose
- Attente du healthcheck du conteneur
- Vérification de la connexion Python vers SQL Server
- Vérification des données d’initialisation

---

### 6.3 CD

- Build de l’application desktop Python (exécutable Windows)
- Publication en artifact GitHub Actions

---

### 6.4 Fichiers

- `.github/workflows/ci-cd.yml`
- `ci/check_db_connection.py`
- `requirements-dev.txt`

---

### 6.5 Déclenchement

- Push / Pull Request sur `dev` et `main`
- Release (pour le build CD)
- Exécution manuelle (`workflow_dispatch`)

---

## 7. Gestion de la connexion SQL

### 7.1 Module de connexion

- Fichier : `connection/server_connection.py`
- Classe : `ServerConnect`

Méthodes :
- `getConnection()`
- `commit()`
- `rollback()`
- `Disconnect()`

Import :
```python
from connection import ServerConnect
```

### 7.3.2 Variables d'environnement (.env)

Le fichier `.env` charge automatiquement les paramètres de connexion :

```env
SQL_SERVER_HOST=sqlserver           # Hostname du service SQL Server Docker
SQL_SERVER_PORT=1433                # Port SQL Server (défaut 1433)
SQL_USER=sa                         # Utilisateur SQL Server
SQL_PASSWORD=Dev12345               # Mot de passe SQL
SA_PASSWORD=SolarDev!2026           # Fallback si SQL_PASSWORD absent
DATABASE_NAME=SolarDB               # Nom de la base de données
```

**Comportement** :
- Normalisé au démarrage : `sqlserver` → `127.0.0.1` pour Docker local
- Chargé via `app.config.load_dotenv_file()` dans `main.py`

### 7.3.3 Gestion des transactions

Chaque opération CRUD encapsule les transactions :
```python
def execute(self, sql: str, params: tuple = ()) -> None:
    conn = self.connector.getConnection()
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
    self.connector.commit()
```

En cas d'erreur, la méthode `_safe()` dans `SolarApp` effectue un `rollback()` auto.

---

## 8. Historique de refactorisation (Branche actuelle)

### 8.1 Renommage des fichiers CRUD

Les fichiers CRUD ont été renommés pour simplifier la convention de nommage :

- ❌ `base_crud.py` → ✅ `base.py`
- ❌ `device_crud.py` → ✅ `device.py`
- ❌ `device_type_crud.py` → ✅ `device_type.py`
- ❌ `timeslot_crud.py` → ✅ `timeslot.py`
- ❌ `device_usage_schedule_crud.py` → ✅ `device_usage_schedule.py`
- ❌ `energy_consumption_crud.py` → ✅ `energy_consumption.py`
- ❌ `system_configuration_crud.py` → ✅ `system_configuration.py`

**Bénéfices** :
- Noms plus courts et lisibles
- Import simplifié
- Cohérence avec les bonnes pratiques Python

### 8.2 Commits de refactorisation

5 commits groupés par fonctionnalité :

1. **feat: Connection module and configuration**
   - Module `ServerConnect` avec gestion des transactions
   - Configuration du chargement d'environnement
   - Normalisation du hostname Docker

2. **feat: Data access layer (CRUD)**
   - Classes de base et modèles CRUD pour tous les domaines
   - Opérations de lecture/écriture SQL Server
   - Requêtes conformes aux contraintes d'agrégation SQL Server

3. **feat: Business logic layer (Services)**
   - `EnergySpecService` pour les calculs d'énergie
   - Formule de calcul panneau solaire (rendement)
   - Formule de batterie (surcharge)

4. **feat: User interface layer (UI)**
   - SolarApp Tkinter à 5 onglets
   - Liaison entre UI et CRUD
   - Verrouillage progressif des fonctionnalités
   - Gestion des erreurs avec rollback

5. **chore: Application orchestration and entry point**
   - Orchestrateur `main.py` minimal
   - Separation of Concerns complète

### 8.3 Validation

Tous les fichiers compilent sans erreur :
```bash
python -m py_compile main.py app/ui/solar_app.py app/services/energy_spec_service.py app/crud/base.py
```

---

## 9. Guide de démarrage

### 9.1 Prérequis

- Python 3.8+
- SQL Server 2019+ (Docker recommandé)
- `pymssql>=2.3.5`

### 9.2 Installation

```bash
# Cloner le repo
git clone <repo-url>
cd Solar

# Installer les dépendances
pip install -r requirements-dev.txt

# Démarrer SQL Server Docker
docker compose up -d

# Vérifier la connexion
python ci/check_db_connection.py
```

### 9.3 Lancement

```bash
python main.py
```

La fenêtre Tkinter s'ouvre alors avec les 5 onglets de gestion énergétique.

### 9.4 Workflow type

1. **Ajouter des appareils** (onglet Matériels)
2. **Paramétrer les créneaux horaires** (onglet Créneaux) — pré-remplis
3. **Définir l'usage quotidien** (onglet Usage) — durée par créneau
4. **Consulter l'historique** (onglet Historique) — données passées
5. **Générer le bilan** (onglet Bilan) — panneaux et batterie nécessaires

---

## 10. Réinitialisation des données depuis l'interface

Des boutons de réinitialisation sont disponibles dans les onglets pour éviter un script manuel à chaque purge.

### 10.1 Onglet Matériels

- Bouton : `Reinitialiser`
- Supprime : `Device`
- Supprime aussi les dépendances : `DeviceUsageSchedule`, `EnergyConsumption`
- Conserve : `DeviceType`

### 10.2 Onglet Créneaux

- Bouton : `Reinitialiser`
- Supprime : `TimeSlot`
- Supprime aussi les dépendances : `DeviceUsageSchedule`, `EnergyConsumption`, `SolarPanelProduction`, `BatteryMovement`

### 10.3 Onglet Usage

- Bouton : `Reinitialiser`
- Supprime : `DeviceUsageSchedule`

### 10.4 Onglet Historique

- Bouton : `Reinitialiser`
- Supprime : `EnergyConsumption`

### 10.5 Onglet Bilan

- Bouton : `Reinitialiser tout`
- Effet : reset global des données fonctionnelles des onglets (hors `DeviceType`)

Toutes les actions sont protégées par une confirmation utilisateur.

---

## 11. Exécuter un script SQL à chaud (sans redémarrer SQL Server)

Runner inclus : `database/scripts/run-sql-script.ps1`

Exemple d'exécution :

```powershell
$env:SA_PASSWORD = "SolarDev!2026"
.\database\scripts\run-sql-script.ps1 -SqlFile ".\database\scripts\truncate-usage-and-device-insert-3-tv.sql" -Database "solar"
```

Script de seed ciblé : `database/scripts/truncate-usage-and-device-insert-3-tv.sql`

Ce script :
- vide `EnergyConsumption`, `DeviceUsageSchedule`, `Device`
- insère 3 TV : 23W, 20W, 10W
- configure les créneaux :
  - TV001 -> NUIT (2h)
  - TV002 -> SOIR (2h)
  - TV003 -> JOUR (1h)

Résultat attendu :
- JOUR = 10
- SOIR = 40
- NUIT = 46