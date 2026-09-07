# Entrepôt de données — VenteRapide

## Contexte
Entrepôt de données e-commerce fourni dans le cadre de l'épreuve **E6**
de la certification RNCP 37638 Data Engineer.

La société fictive **VenteRapide** exploite une boutique en ligne généraliste.
Cet entrepôt centralise les données de commandes, produits, clients, visites et retours.

## Stack technique
| Composant | Technologie |
|-----------|-------------|
| Base de données | PostgreSQL 16 |
| Transformation | dbt 1.11 |
| Modélisation | Schéma en étoile (Kimball) |
| Environnement | Linux / WSL2 |

## Prérequis
- PostgreSQL installé et démarré
- dbt installé : `pip install dbt-postgres`

## Installation

### 1. Dézipper le projet
```bash
unzip datawarehouse_e6.zip
cd datawarehouse_e6
```

### 2. Créer la base de données PostgreSQL

```bash
sudo -u postgres psql -c "CREATE DATABASE datawarehouse_e6;"
sudo -u postgres psql -c "CREATE USER dbt_user WITH PASSWORD 'dbt_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE datawarehouse_e6 TO dbt_user;"
sudo -u postgres psql -d datawarehouse_e6 -c "GRANT ALL ON SCHEMA public TO dbt_user;"
sudo -u postgres psql -d datawarehouse_e6 -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO dbt_user;"
```

### 3. Configurer le profil dbt
Éditez le fichier `~/.dbt/profiles.yml` et ajoutez :

```yaml
datawarehouse_e6:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5432
      user: dbt_user
      password: dbt_password
      dbname: datawarehouse_e6
      schema: public
      threads: 4
```

### 4. Vérifier la connexion
```bash
dbt debug
```

### 5. Lancer l'entrepôt
```bash
dbt seed        # charge les 5 tables brutes
dbt run         # construit les 12 modèles
dbt snapshot    # initialise le SCD type 2
dbt test        # lance les 66 tests
```

## Structure du projet

seeds/  
raw_clients.csv  
raw_produits.csv  
raw_commandes.csv  
raw_lignes_commande.csv  
raw_visites.csv  
models/
staging/                 ← nettoyage et typage des données brutes  
dimensions/              ← dim_client, dim_produit, dim_date, dim_canal, dim_statut_commande  
facts/                   ← fact_commandes, fact_visites  
snapshots/  
scd_client.sql           ← SCD type 2 sur dim_client (ville, code_postal, segment)  

## Utilisateurs PostgreSQL
| Utilisateur | Droits | Usage |
|-------------|--------|-------|
| postgres | Superadmin | Administration |
| dbt_user | Lecture/écriture | Pipeline dbt |

## Documentation interactive
```bash
dbt docs generate
dbt docs serve --port 8080
```
Ouvrez ensuite http://localhost:8080 pour accéder au lineage graph (icône en bas à droite sur l'interface web dbt).

## Restauration depuis un backup
```bash
pg_restore -d datawarehouse_e6 fichier.dump
```
