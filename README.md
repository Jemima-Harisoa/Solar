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