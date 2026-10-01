# AI Store Labs - Présentation pour les Clients

## Introduction

Bienvenue dans la plateforme de formation AI Store Labs (SkillHub). Ce programme interactif vous permet de découvrir et maîtriser la plateforme AI-Powered-Store (OPCP) dans un environnement structuré et pratique, avec des leçons progressives accompagnées d'exercices hands-on.

## Objectif de l'Offre

Cette formation vous permet de :
- Installer et configurer la plateforme AI-Powered-Store sur un serveur bare-metal
- Gérer le cycle de vie complet des applications (ajout, démarrage, arrêt)
- Maîtriser les sauvegardes et la restauration de données vers OVH S3
- Utiliser l'IA pour modifier et personnaliser les applications déployées
- Exploiter les GPUs NVIDIA avec la technologie MIG (Multi-Instance GPU)
- Configurer l'exécution serverless et le suivi des coûts

## Public Cible et Profil

### Public Cible
- Administrateurs système souhaitant déployer et gérer la plateforme AI-Powered-Store
- Développeurs et ingénieurs DevOps travaillant avec Docker et l'infrastructure cloud
- Professionnels souhaitant comprendre la gestion d'applications conteneurisées avec GPU

### Profil Attendu
- Connaissance de base de Linux (Ubuntu) et du terminal
- Familiarité avec Docker et docker-compose
- Capacité à utiliser un terminal/command line
- Notions de base en réseau et configuration serveur

## Durée Estimée

### Temps Total : ~1 journée (environ 10 heures)
- **Module 1 : Installation sur Bare-Metal Ubuntu** (~120 min)
- **Module 2 : Ajout de Nouvelles Applications** (~60 min)
- **Module 3 : Démarrage des Applications** (~45 min)
- **Module 4 : Arrêt des Applications** (~30 min)
- **Module 5 : Réalisation de Sauvegardes** (~60 min)
- **Module 6 : Modification d'Applications avec l'IA** (~90 min)
- **Module 7 : Docker avec MIG GPU** (~90 min)
- **Module 8 : Exécution Serverless Docker** (~75 min)
- **Module 9 : Facturation et Suivi des Coûts** (~60 min)

## Prérequis Techniques

Avant de commencer, assurez-vous de disposer des éléments suivants :

### Environnement Serveur
- **Ubuntu 22.04 ou 24.04 LTS** (installation propre)
- **Accès root ou sudo**
- **4 Go de RAM minimum** et 20 Go d'espace disque
- **Connectivité Internet** pour le téléchargement des paquets
- **GPU NVIDIA compatible** (optionnel, pour le support MIG : A100, A30, H100)

### Outils Installés (via le script d'installation)
- Python 3 + pip + venv
- Docker (version 20.10+) et docker-compose
- AWS CLI (pour le stockage S3 OVH)
- Terraform
- Amazon Kiro CLI
- OVH CLI (shai)

### Configuration Réseau et Stockage
- Configuration Netplan pour la priorisation des interfaces réseau
- Identifiants AWS configurés pour OVH Object Storage (S3 GRA)
- Certificat SSL pour le HTTPS (nginx)

## Structure de la Formation SkillHub

### Interface Web Interactive
- Interface web multilingue (Français / English)
- Navigation par sidebar avec les leçons organisées par niveau
- Barre de progression globale
- Bouton "Mark as Complete" pour suivre l'avancement
- Labs pratiques accompagnant chaque leçon

### Organisation par Niveaux

Les leçons sont organisées en trois niveaux de difficulté :
- **Débutant** — Installation de la plateforme et opérations de base
- **Intermédiaire** — Cycle de vie des applications et gestion des données
- **Avancé** — Workloads GPU, serverless et facturation

## Modules de Formation

### Module 1 : Installation sur Bare-Metal Ubuntu (Débutant, ~120 min)

Déploiement complet de la plateforme AI-Powered-Store sur un serveur Ubuntu :
- Installation des dépendances système (python3, pip, venv, net-tools, unzip)
- Installation des outils CLI (Kiro CLI, OVH shai, AWS CLI, Terraform)
- Configuration réseau Netplan (priorisation interfaces publique/privée)
- Installation de Docker et docker-compose
- Installation des drivers NVIDIA et support GPU (optionnel)
- Configuration AWS pour le stockage S3 OVH
- Clonage du dépôt et configuration de l'environnement Python
- Configuration finale (deploy.ini, certificats SSL, identifiants S3)

**Script automatisé** : `init_pltf.sh` pour exécuter toutes les étapes automatiquement.

### Module 2 : Ajout de Nouvelles Applications (Débutant, ~60 min)

Enregistrement et gestion des applications sur la plateforme :
- **Via l'interface web** : formulaire d'ajout dans le panneau d'administration
- **Via le CLI** : commande `python aipoweredstore_cli.py add-app`
- **Via l'API REST** : endpoint POST `/api/applications`
- Gestion des métadonnées (nom, description, URL, dépôt Git)
- Modification et suppression d'applications existantes
- Export de la liste des applications en PDF

### Module 3 : Démarrage des Applications (Intermédiaire, ~45 min)

Lancement et vérification des applications déployées :
- Utilisation du script `deployApp.sh` pour démarrer une application
- Orchestration des conteneurs Docker
- Surveillance des logs de démarrage
- Vérification de la santé et de la connectivité
- Résolution des problèmes courants de démarrage

### Module 4 : Arrêt des Applications (Intermédiaire, ~30 min)

Procédures d'arrêt gracieux et gestion des ressources :
- Arrêt d'une application individuelle (`docker-compose down`)
- Arrêt de la plateforme entière
- Nettoyage des ressources Docker (volumes, réseaux)
- Compréhension des hooks d'arrêt et de la persistance des données

### Module 5 : Réalisation de Sauvegardes (Intermédiaire, ~60 min)

Sauvegarde et restauration des données applicatives :
- Dump de bases de données PostgreSQL
- Synchronisation vers OVH Object Storage (S3) via AWS CLI
- Restauration depuis une sauvegarde
- Planification de sauvegardes automatiques
- Vérification de l'intégrité des sauvegardes

### Module 6 : Modification d'Applications avec l'IA (Intermédiaire, ~90 min)

Utilisation d'outils IA pour personnaliser les applications :
- Workflow de modification assistée par IA avec Kiro CLI
- Application des changements aux applications en production
- Tests des modifications dans des environnements isolés
- Rollback des changements si nécessaire
- Bonnes pratiques pour le développement assisté par IA

### Module 7 : Docker avec MIG GPU (Avancé, ~90 min)

Partitionnement GPU avec la technologie NVIDIA MIG :
- Architecture MIG et partitionnement GPU
- Activation et configuration du mode MIG
- Création d'instances GPU et d'instances de calcul
- Attribution de slices MIG à des conteneurs Docker
- Supervision de l'utilisation GPU par instance

### Module 8 : Exécution Serverless Docker (Avancé, ~75 min)

Configuration du mode d'exécution serverless :
- Modèle d'exécution serverless (démarrage à la demande, arrêt sur inactivité)
- Configuration du timeout d'inactivité et des paramètres d'auto-scaling
- Activation de conteneurs basée sur les requêtes
- Suivi des performances de démarrage à froid (cold-start)
- Optimisation des images Docker pour un démarrage rapide

### Module 9 : Facturation et Suivi des Coûts (Avancé, ~60 min)

Monitoring de la consommation de ressources et gestion des coûts :
- Modèle de coûts : CPU (core-heures), RAM (GB-heures), GPU (GPU-heures), Stockage (GB-mois), Réseau (GB transférés)
- Rapports d'utilisation par application
- Configuration d'alertes de facturation et de seuils
- Export des données d'utilisation
- Optimisation des coûts avec le serverless et l'auto-scaling

## Résultats Attendus

### Compétences Acquises
- Déploiement complet de la plateforme AI-Powered-Store sur bare-metal
- Gestion du cycle de vie des applications (CRUD, démarrage, arrêt)
- Maîtrise des sauvegardes et restaurations vers le stockage objet S3
- Utilisation d'outils IA pour la modification de code
- Configuration et exploitation de GPUs NVIDIA en mode MIG
- Mise en place d'architectures serverless optimisées en coûts

### Produits Finis
- Plateforme AI-Powered-Store opérationnelle
- Applications déployées et fonctionnelles
- Sauvegardes automatisées configurées
- Exercices validés pour chaque module

## Support et Assistance

### Ressources Disponibles
- Documentation complète via le SkillHub (interface web)
- Labs pratiques accompagnant chaque module
- Support technique dédié

### Contact
Pour toute question ou assistance, contactez notre équipe technique PSMC OVH psmc@ovhcloud.com.

---

*PS : Pour plus d'informations techniques, consultez le dépôt Git officiel du projet.*
