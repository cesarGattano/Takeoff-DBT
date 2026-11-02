# Contexte du projet

## Contexte et stack technique fournie
L'entrepôt de données mis à votre disposition repose sur la stack suivante :
* Base de données : PostgreSQL 16
* Transformation : dbt (Data Build Tool) 1.11
* Modélisation Schéma en étoile (Kimball)
* Versioning : Git
* Environnement : Linux / WSL2

L'entrepôt contient les tables suivantes :
* 5 tables brutes (seeds) : rawclients, rawproduits, rawcommandes, rawlignescommande, rawvisites
* 5 vues de staging : stgclients, stgproduits, stgcommandes, stglignescommande, stgvisites
* 5 tables de dimensions : dimclient, dimproduit, dimdate, dimstatutcommande, dimcanal
* 2 tables de faits : factcommandes, factvisites
* 1 snapshot SCD : scd_client
* 66 tests dbt configurés
* 2 utilisateurs PostgreSQL : postgres (admin), dbt_user (lecture/écriture)
* 1 procédure de backup via pg_dump + cron
  
# Modalités pédagogiques

## Tâches à réaliser

Votre rapport professionnel devra couvrir l'ensemble des tâches suivantes. Chaque tâche doit être documentée avec la méthodologie employée, les commandes exécutées, les résultats obtenus et les éventuelles difficultés rencontrées

1. Organisation de la maintenance (C16)

* Présenter la méthodologie de répartition et de priorisation des tâches de maintenance (ex : ticketing, ITIL, Kanban)
* Définir les indicateurs de suivi du service (SLA, disponibilité, temps de traitement)
* Proposer un tableau de bord de suivi de la maintenance

2. Journalisation des alertes (C16)

* Configurer la journalisation des erreurs et des alertes dans PostgreSQL (fichiers de logs, niveau de sévérité)
* Mettre en place une stratégie de monitoring des pipelines dbt (logs dbt, alertes en cas d'échec)
* Documenter la procédure de consultation et d'analyse des logs

3. Sauvegarde de l'entrepôt (C16)

* Décrire et justifier la procédure de backup complet mise en place (pg_dump, fréquence, rétention)
* Mettre en place et planifier via cron le backup complet et le backup partiel
* Documenter la procédure de restauration (pg_restore) et la tester

4. Intégration d'une nouvelle source de données (C16)

* Intégrer la nouvelle source de données fournie : le fichier raw_retours.csv (retours produits) à l'entrepôt existant en la chargeant comme seed dbt.
* Créer le modèle staging correspondant (stg_retours)
* Créer la table de faits fact_retours en jointure avec les dimensions existantes
* Ajouter les tests dbt appropriés sur les nouveaux modèles
* Mettre à jour la documentation dbt

5. Gestion des accès (C16)

* Créer un nouvel utilisateur PostgreSQL 'reporting' avec accès en lecture seule
* Documenter la procédure d'ajout d'un accès (création, droits, tests)
* Décrire la stratégie de gestion des accès dans le respect du RGPD
* Rédiger un registre des traitements de données personnelles recensant chaque traitement de l'entrepôt (finalité, données concernées, base légale, durée de conservation, destinataires)
* Rédiger une procédure de tri/purge des données personnelles (ex : anonymisation des comptes clients inactifs depuis N mois) précisant la fréquence d'exécution et si elle est automatisée ou manuelle

6. Variations de dimensions — SCD (C17)

* Expliquer les 3 types de SCD de Ralph Kimball (type 1, 2 et 3) avec leurs cas d'usage respectifs
* Analyser le snapshot scdclient existant (SCD type 2 sur les colonnes ville, codepostal, segment)
* Simuler un changement de ville pour un client et vérifier l'historisation dans scd_client
* Illustrer par une requête SQL la jointure entre factcommandes et scdclient (sur les bornes dbtvalidfrom / dbtvalidto) permettant de retrouver le segment ou la ville du client au moment de sa commande, et non son état courant
* Implémenter un SCD type 1 sur la dimension dim_produit (mise à jour du prix sans historique)
* Mettre à jour les modèles ETL (dbt) impactés par les variations
* Documenter les variations et mettre à jour les modèles logiques et physiques

7. Documentation et scalabilité (C16)

* Documenter la procédure d'ajout d'un nouveau datamart
* Documenter la procédure d'augmentation de l'espace de stockage PostgreSQL
* Mettre à jour la documentation dbt (schema.yml) pour les nouveaux modèles créés
* Générer et consulter le lineage graph dbt après les évolutions

## Nouvelle source de données à intégrer

Dans le cadre de l'évolution de l'activité, VenteRapide souhaite analyser les retours produits. Vous devez intégrer le fichier suivant à l'entrepôt :

| Colonne           | Description                                           |
| ----------------- | ----------------------------------------------------- |
| retour_id         | Identifiant unique du retour                          |
| commande_id       | Référence vers la commande   concernée                |
| produit_id        | Référence vers le produit   retourné                  |
| client_id         | Référence vers le client                              |
| date_retour       | Date du retour                                        |
| motif             | Motif du retour (Défaut, Erreur,   Changement d'avis) |
| montant_rembourse | Montant remboursé au client                           |

Le fichier raw_retours.csv vous sera fourni séparément. Vous devrez l'intégrer comme seed dbt, puis construire les modèles staging et fact associés.