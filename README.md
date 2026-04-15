Projet de développement d'une application de gestion de consomation energétique
- Calculer la comsommation énergétique d'une maison 
1. par rapport au materiel : puissance et temps d'utilisation
2. par rapport au moment de la journée : tranche horaire (journe 6-17h , soir 17-19h, nuit 19-6h)

- Afficher les résultats de la consommation énergétique
1. par rapport au materiel : consommation totale et par appareil selon usage
2. par rapport au moment de la journée : consommation totale et par tranche horaire

- Etablir un bilan des besoin en énergie de la maison
1. Energie totale pour couvrir les besoins de la maison -> consommation totale => Panneaux solaires (sachant que 1 panneau solaire produit 40% de l'energie qu'il fournit ex: 1000W de besoin => 2500W de panneaux solaires)
1.1 En soire fin d'après-midi (17-19h) => 50% d'energie produite par les panneaux solaires => le soleil se couche
1.2 En journée (6-17h) => les panneaux solaires alimente les materiels branches et stocke l'energie dans la batterie de stockage
Q : est ce que les panneaux solaires produise une quantite d'enerigie par heure ? D'ou le total produit en journée = quantite d'energie produite par heure * nombre d'heure de production (ex: 1000W de besoin => 2500W de panneaux solaires => 2500W / 11h = 227W par heure)

2. Batterie de stockage pour stocker l'énergie produite par les panneaux solaires => usage lorsque les panneaux solaires ne produisent pas d'énergie (nuit, jours nuageux) => capacité de la batterie = consommation totale de la maison pour la nuit majoree de 50% (ex: consommation totale de la maison pour la nuit = 500W => capacité de la batterie = 750W)
2.1 En journée (6-17h) => les batteries de stockage sont rechargées par les panneaux solaires dans l'ensemble de la journée => evite les perte d'energie (si la batterie de stockage est pleine a midi on perds l'energie produite par les panneaux le reste de la journée)

- Afficher les résultats du bilan énergétique
=> consommation totale de la maison 
=> puissance totale des panneaux solaires nécessaires pour couvrir les besoins de la maison (40% besoin de la maison => 100% besoin de panneaux solaires)
=> capacité de la batterie de stockage nécessaire pour couvrir les besoins de la maison pendant la nuit (majoree de 50%)

# Technologies utilisées
- Python => desktop application
- SqlServer 

# Structure de la base de données (Branche Dev)

La structuration des données suit une architecture modulaire organisée autour de la gestion énergétique :

## Tables de Configuration

### TimeSlot
- Définit les créneaux horaires d'une journée (jour 6-17h, soir 17-19h, nuit 19-6h)
- Utilisée pour segmenter les consommations et productions d'énergie

### SystemConfiguration
- Tension secteur (GridVoltageV : 230V par défaut)
- Rendement des panneaux solaires (SolarPanelEfficiencyPct : 40% par défaut)
- Surcapacité batterie (BatteryOvercapacityPct : 50% par défaut)

## Tables Matériels

### DeviceType
- Catégories d'appareils électriques (ex: Chauffage, Éclairage, etc.)

### Device
- Liste des appareils présents dans la maison
- Puissance nominale (PowerW)
- Statut (ACTIF, INACTIF, MAINTEN)
- Date d'installation

### DeviceUsageSchedule
- Programme d'utilisation quotidien par appareil
- DailyUsageHours par créneau horaire (jour/soir/nuit)
- Permet de calculer la consommation énergétique estimée

## Tables Consommations & Production

### EnergyConsumption
- Historique détaillé de consommation énergétique
- EnergyConsumedWh : énergie consommée en Wh
- DurationHours : durée réelle d'utilisation
- Lié à Device et TimeSlot

### SolarPanelProduction
- Production d'énergie quotidienne des panneaux solaires
- TotalPanelCapacityW : capacité installée
- ProductionPercentage : rendement journalier
- EnergyProducedWh : calculée automatiquement

### BatteryStorage
- Configuration des batteries de stockage
- TotalCapacityWh : capacité totale
- CurrentChargeWh : charge actuelle
- ChargingEfficiencyPct : 95% par défaut
- Statut (ACTIF, MAINTENANCE, DEFAUT)

### BatteryMovement
- Historique des mouvements charge/décharge
- MovementType : CHARGE ou DECHARGE
- Traçabilité complète : ChargeBeforeWh et ChargeAfterWh

## Vues Calculs

### vw_DeviceUsageSchedule
- Agrège appareils + programme d'utilisation + créneaux horaires
- DailyEnergyConsumptionWh calculée automatiquement (PowerW × DailyUsageHours)

### vw_EnergyBalance
- Bilan énergétique quotidien complet
- TotalConsumptionWh vs TotalProductionWh
- Calcul automatique : panneaux solaires nécessaires et batterie requise
- EnergyBalanceWh : différence production - consommation