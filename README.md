# Projet de gestion de consommation énergétique

## 1. Objectif

Développer une application permettant de :
- Calculer la consommation énergétique d’une maison
- Analyser cette consommation selon différents critères
- Déterminer les besoins en énergie (panneaux solaires et batteries)
- Fournir un bilan énergétique global

---

## 2. Calcul de la consommation énergétique

### 2.1 Par matériel
- Basé sur :
  - La puissance de l’appareil
  - Le temps d’utilisation

### 2.2 Par tranche horaire
- Journée : 6h - 17h
- Soir : 17h - 19h
- Nuit : 19h - 6h

---

## 3. Affichage des résultats

### 3.1 Par matériel
- Consommation totale
- Consommation par appareil selon l’usage

### 3.2 Par tranche horaire
- Consommation totale
- Consommation par période (jour / soir / nuit)

---

## 4. Bilan des besoins énergétiques

### 4.1 Énergie totale nécessaire
- Correspond à la consommation totale de la maison

### 4.2 Panneaux solaires
- Hypothèse :
  - 1 panneau produit 40% de l’énergie qu’il fournit
- Exemple :
  - Besoin : 1000W
  - Nécessaire : 2500W de panneaux solaires

#### Répartition de la production
- Journée (6h - 17h) :
  - Alimentation des appareils
  - Stockage dans la batterie
- Soir (17h - 19h) :
  - Production réduite à 50%

#### Question / hypothèse
- Production horaire :
  - Production totale journalière = production par heure × nombre d’heures
  - Exemple :
    - 2500W / 11h = 227W par heure

---

### 4.3 Batterie de stockage
- Utilisation :
  - Nuit
  - Journées nuageuses

- Capacité :
  - Consommation nocturne majorée de 50%
- Exemple :
  - Consommation nuit : 500W
  - Capacité batterie : 750W

#### Fonctionnement
- Journée :
  - Recharge continue par les panneaux
- Problème :
  - Si batterie pleine → perte d’énergie produite

---

## 5. Résultats du bilan énergétique

- Consommation totale de la maison
- Puissance totale des panneaux solaires nécessaires
- Capacité de batterie requise pour la nuit (avec marge de 50%)

---

## 6. Technologies utilisées

- Python (application desktop)
- SQL Server

---

## 7. Structure de la base de données (Branche Dev)

### 7.1 Tables de configuration

#### TimeSlot
- Définition des créneaux horaires :
  - Jour (6h - 17h)
  - Soir (17h - 19h)
  - Nuit (19h - 6h)

#### SystemConfiguration
- GridVoltageV : 230V (par défaut)
- SolarPanelEfficiencyPct : 40%
- BatteryOvercapacityPct : 50%

---

### 7.2 Tables matériels

#### DeviceType
- Catégories d’appareils (chauffage, éclairage, etc.)

#### Device
- Liste des appareils
- PowerW : puissance
- Statut : ACTIF, INACTIF, MAINTENANCE
- Date d’installation

#### DeviceUsageSchedule
- Programme d’utilisation quotidien
- DailyUsageHours par tranche horaire
- Sert au calcul de consommation

---

### 7.3 Tables consommation et production

#### EnergyConsumption
- Historique des consommations
- EnergyConsumedWh
- DurationHours
- Lié à Device et TimeSlot

#### SolarPanelProduction
- Production journalière
- TotalPanelCapacityW
- ProductionPercentage
- EnergyProducedWh (calculée)

#### BatteryStorage
- Configuration des batteries
- TotalCapacityWh
- CurrentChargeWh
- ChargingEfficiencyPct : 95%
- Statut : ACTIF, MAINTENANCE, DEFAUT

#### BatteryMovement
- Historique des charges/décharges
- MovementType : CHARGE / DECHARGE
- ChargeBeforeWh / ChargeAfterWh

---

### 7.4 Vues de calcul

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

## 8. CI/CD (Desktop Python + SQL Server Docker)

Pipeline GitHub Actions ajouté pour la branche dev et main :

- CI :
  - Lance SQL Server avec Docker Compose
  - Attend le healthcheck du conteneur
  - Vérifie la connexion Python vers SQL Server
  - Vérifie la présence des données d'initialisation

- CD :
  - Build de l'application desktop Python en exécutable Windows
  - Publication de l'exécutable en artifact GitHub Actions

Fichiers CI/CD :

- .github/workflows/ci-cd.yml
- ci/check_db_connection.py
- requirements-dev.txt

Déclenchement :

- Push / Pull Request sur dev et main
- Publication d'une release (pour le build CD)
- Exécution manuelle (workflow_dispatch)