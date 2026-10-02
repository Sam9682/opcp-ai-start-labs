#!/usr/bin/env python3
"""Generate a marketing-style PDF from the OPCP AI Start Labs SkillHub content."""

from weasyprint import HTML

html_content = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<style>
@page {
    size: A4;
    margin: 0;
}

body {
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    margin: 0;
    padding: 0;
    color: #2c3e50;
    line-height: 1.6;
}

/* Cover Page */
.cover {
    height: 297mm;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    color: white;
    padding: 60px;
    page-break-after: always;
}

.cover h1 {
    font-size: 42px;
    font-weight: 700;
    margin-bottom: 20px;
    letter-spacing: -0.5px;
}

.cover .subtitle {
    font-size: 22px;
    font-weight: 300;
    opacity: 0.9;
    margin-bottom: 40px;
}

.cover .tagline {
    font-size: 16px;
    font-weight: 300;
    opacity: 0.7;
    border-top: 1px solid rgba(255,255,255,0.3);
    padding-top: 30px;
    margin-top: 40px;
}

.cover .brand {
    font-size: 18px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 60px;
    opacity: 0.8;
}

/* Content Pages */
.page {
    padding: 50px 60px;
    page-break-after: always;
}

.page:last-child {
    page-break-after: avoid;
}

h2 {
    font-size: 28px;
    color: #0f3460;
    font-weight: 700;
    margin-bottom: 25px;
    padding-bottom: 10px;
    border-bottom: 3px solid #e94560;
}

h3 {
    font-size: 20px;
    color: #16213e;
    font-weight: 600;
    margin-top: 30px;
    margin-bottom: 15px;
}

p {
    font-size: 14px;
    margin-bottom: 15px;
    color: #444;
}

.intro-text {
    font-size: 16px;
    color: #555;
    line-height: 1.8;
    margin-bottom: 30px;
}

/* Feature Cards */
.features {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    margin: 30px 0;
}

.feature-card {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 25px;
    width: 45%;
    border-left: 4px solid #e94560;
}

.feature-card h4 {
    font-size: 16px;
    color: #0f3460;
    margin: 0 0 10px 0;
    font-weight: 600;
}

.feature-card p {
    font-size: 13px;
    color: #666;
    margin: 0;
}

/* Benefits List */
.benefits {
    list-style: none;
    padding: 0;
}

.benefits li {
    font-size: 15px;
    padding: 12px 0 12px 35px;
    position: relative;
    border-bottom: 1px solid #eee;
}

.benefits li::before {
    content: "✓";
    position: absolute;
    left: 0;
    color: #e94560;
    font-weight: 700;
    font-size: 18px;
}

/* Timeline */
.timeline {
    margin: 30px 0;
}

.timeline-item {
    display: flex;
    align-items: flex-start;
    margin-bottom: 20px;
}

.timeline-badge {
    background: #0f3460;
    color: white;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 14px;
    margin-right: 20px;
    flex-shrink: 0;
}

.timeline-badge.beginner {
    background: #27ae60;
}

.timeline-badge.intermediate {
    background: #f39c12;
}

.timeline-badge.advanced {
    background: #e94560;
}

.timeline-content {
    flex: 1;
}

.timeline-content h4 {
    margin: 0 0 5px 0;
    font-size: 16px;
    color: #16213e;
}

.timeline-content p {
    margin: 0;
    font-size: 13px;
    color: #666;
}

/* Modules Grid */
.modules-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    margin: 25px 0;
}

.module-card {
    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
    border-radius: 10px;
    padding: 20px;
    width: 44%;
    text-align: center;
}

.module-card .module-number {
    background: #e94560;
    color: white;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 14px;
    margin-bottom: 10px;
}

.module-card .module-number.beginner {
    background: #27ae60;
}

.module-card .module-number.intermediate {
    background: #f39c12;
}

.module-card .module-number.advanced {
    background: #e94560;
}

.module-card h4 {
    font-size: 15px;
    color: #0f3460;
    margin: 8px 0;
}

.module-card p {
    font-size: 12px;
    color: #666;
    margin: 0;
}

.module-card .duration {
    font-size: 11px;
    color: #999;
    margin-top: 5px;
}

/* CTA Section */
.cta {
    background: linear-gradient(135deg, #0f3460, #16213e);
    border-radius: 15px;
    padding: 40px;
    text-align: center;
    color: white;
    margin-top: 40px;
}

.cta h3 {
    color: white;
    font-size: 24px;
    margin: 0 0 15px 0;
}

.cta p {
    color: rgba(255,255,255,0.8);
    font-size: 15px;
    margin-bottom: 25px;
}

.cta .contact {
    font-size: 18px;
    font-weight: 600;
    color: #e94560;
}

/* Highlight Box */
.highlight-box {
    background: linear-gradient(135deg, #fff3f5, #ffeef0);
    border: 1px solid #e94560;
    border-radius: 12px;
    padding: 25px;
    margin: 25px 0;
}

.highlight-box h4 {
    color: #e94560;
    margin: 0 0 10px 0;
    font-size: 16px;
}

/* Environment section */
.env-cards {
    display: flex;
    gap: 20px;
    margin: 25px 0;
}

.env-card {
    flex: 1;
    background: white;
    border: 2px solid #e9ecef;
    border-radius: 12px;
    padding: 25px;
    text-align: center;
}

.env-card h4 {
    color: #0f3460;
    font-size: 16px;
    margin: 0 0 15px 0;
}

.env-card ul {
    text-align: left;
    padding-left: 20px;
    font-size: 13px;
    color: #666;
}

.env-card ul li {
    margin-bottom: 8px;
}

/* Level badges */
.level-badge {
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 12px;
    color: white;
    margin-left: 8px;
}

.level-badge.beginner { background: #27ae60; }
.level-badge.intermediate { background: #f39c12; }
.level-badge.advanced { background: #e94560; }

/* Footer */
.footer {
    text-align: center;
    padding: 20px;
    font-size: 11px;
    color: #999;
    margin-top: 40px;
}
</style>
</head>
<body>

<!-- COVER PAGE -->
<div class="cover">
    <h1>OPCP-Explorer<br>AI Powered Platform Labs</h1>
    <div class="subtitle">Plateforme de formation interactive<br>OPCP-AI-Powered-Platform</div>
    <div class="tagline">Maîtrisez le déploiement, la gestion et l'exploitation<br>d'applications conteneurisées avec GPU et IA</div>
    <div class="brand">PSMC OVHcloud</div>
</div>

<!-- PAGE 2: INTRODUCTION & VALUE PROPOSITION -->
<div class="page">
    <h2>Maîtrisez la plateforme OPCP-Explorer</h2>
    <p class="intro-text">
        Découvrez et maîtrisez la plateforme AI-Powered-Platform (OPCP) à travers un parcours interactif
        structuré en 9 modules progressifs. Du déploiement bare-metal à l'exploitation avancée
        des GPUs NVIDIA et de l'exécution serverless — accompagné d'exercices hands-on à chaque étape.
    </p>

    <h3>Ce que vous allez accomplir</h3>
    <ul class="benefits">
        <li>Installer et configurer la plateforme OPCP-Explorer sur un serveur bare-metal Ubuntu</li>
        <li>Gérer le cycle de vie complet des applications (ajout, démarrage, arrêt)</li>
        <li>Maîtriser les sauvegardes et la restauration vers OVH Object Storage (S3)</li>
        <li>Utiliser l'IA (SHAI OVH CLI) pour modifier et personnaliser les applications</li>
        <li>Exploiter les GPUs NVIDIA avec la technologie MIG (Multi-Instance GPU)</li>
        <li>Configurer l'exécution serverless et le suivi des coûts</li>
    </ul>

    <div class="highlight-box">
        <h4>⏱ Format optimisé : ~1 journée (10 heures)</h4>
        <p style="margin:0; font-size: 14px; color: #555;">
            Un programme intensif et progressif organisé en 3 niveaux de difficulté,
            conçu pour vous rendre opérationnel sur la plateforme complète.
        </p>
    </div>
</div>

<!-- PAGE 3: PROGRAMME BEGINNER & INTERMEDIATE -->
<div class="page">
    <h2>Un parcours structuré en 3 niveaux</h2>

    <h3>Niveau Débutant <span class="level-badge beginner">Beginner</span></h3>
    <div class="timeline">
        <div class="timeline-item">
            <div class="timeline-badge beginner">1</div>
            <div class="timeline-content">
                <h4>Installation sur Bare-Metal Ubuntu — ~20 min</h4>
                <p>Déploiement complet : dépendances système, CLI tools (Shai, OVH S3, Terraform, Tofu), Docker, drivers NVIDIA, configuration réseau et S3.</p>
            </div>
        </div>
        <div class="timeline-item">
            <div class="timeline-badge beginner">2</div>
            <div class="timeline-content">
                <h4>Ajout de Nouvelles Applications — ~20 min</h4>
                <p>Enregistrement d'applications via l'interface web, le CLI ou l'API REST. Gestion des métadonnées et du cycle CRUD.</p>
            </div>
        </div>
    </div>

    <h3>Niveau Intermédiaire <span class="level-badge intermediate">Intermediate</span></h3>
    <div class="timeline">
        <div class="timeline-item">
            <div class="timeline-badge intermediate">3</div>
            <div class="timeline-content">
                <h4>Démarrage des Applications — ~5 min</h4>
                <p>Utilisation de deployApp.sh, orchestration Docker, surveillance des logs et vérification de la connectivité.</p>
            </div>
        </div>
        <div class="timeline-item">
            <div class="timeline-badge intermediate">4</div>
            <div class="timeline-content">
                <h4>Arrêt des Applications — ~5 min</h4>
                <p>Arrêt gracieux, nettoyage des ressources Docker, hooks d'arrêt et persistance des données.</p>
            </div>
        </div>
        <div class="timeline-item">
            <div class="timeline-badge intermediate">5</div>
            <div class="timeline-content">
                <h4>Réalisation de Sauvegardes — ~20 min</h4>
                <p>Dump PostgreSQL, sync vers OVH S3, restauration, planification automatique et vérification d'intégrité.</p>
            </div>
        </div>
        <div class="timeline-item">
            <div class="timeline-badge intermediate">6</div>
            <div class="timeline-content">
                <h4>Modification d'Applications avec l'IA — ~20 min</h4>
                <p>Workflow SHAI CLI pour modifier le code, tester en isolation et déployer les changements validés.</p>
            </div>
        </div>
    </div>
</div>

<!-- PAGE 4: ADVANCED MODULES & ENVIRONMENT -->
<div class="page">
    <h3>Niveau Avancé <span class="level-badge advanced">Advanced</span></h3>
    <div class="timeline">
        <div class="timeline-item">
            <div class="timeline-badge advanced">7</div>
            <div class="timeline-content">
                <h4>Docker avec MIG GPU — ~10 min</h4>
                <p>Partitionnement NVIDIA MIG, création d'instances GPU, attribution de slices à des conteneurs Docker et monitoring.</p>
            </div>
        </div>
        <div class="timeline-item">
            <div class="timeline-badge advanced">8</div>
            <div class="timeline-content">
                <h4>Exécution Serverless Docker — ~75 min</h4>
                <p>Activation à la demande, timeout d'inactivité, optimisation du cold-start et auto-scaling.</p>
            </div>
        </div>
        <div class="timeline-item">
            <div class="timeline-badge advanced">9</div>
            <div class="timeline-content">
                <h4>Facturation et Suivi des Coûts — ~20 min</h4>
                <p>Modèle de coûts (CPU, RAM, GPU, stockage, réseau), rapports par application, alertes et optimisation.</p>
            </div>
        </div>
    </div>

    <h3>Votre environnement de formation</h3>
    <div class="env-cards">
        <div class="env-card">
            <h4>🌐 SkillHub</h4>
            <ul>
                <li>Interface web interactive multilingue (FR/EN)</li>
                <li>9 modules progressifs avec navigation par sidebar</li>
                <li>Barre de progression globale</li>
                <li>Suivi d'avancement par leçon</li>
            </ul>
        </div>
        <div class="env-card">
            <h4>🔬 Labs Pratiques</h4>
            <ul>
                <li>Environnement isolé par module</li>
                <li>Exercices hands-on guidés</li>
                <li>Serveur bare-metal réel ou simulé</li>
                <li>Validation automatique des exercices</li>
            </ul>
        </div>
    </div>
</div>

<!-- PAGE 5: AUDIENCE, PREREQS & CTA -->
<div class="page">
    <h2>À qui s'adresse ce programme ?</h2>

    <div class="features">
        <div class="feature-card">
            <h4>👨‍💻 Administrateurs Système</h4>
            <p>Vous gérez des infrastructures Linux et souhaitez maîtriser le déploiement de plateformes conteneurisées avec GPU.</p>
        </div>
        <div class="feature-card">
            <h4>🚀 Ingénieurs DevOps</h4>
            <p>Vous travaillez avec Docker et le cloud, et souhaitez explorer les architectures serverless et GPU.</p>
        </div>
        <div class="feature-card">
            <h4>📊 Développeurs</h4>
            <p>Vous voulez comprendre comment déployer et gérer des applications sur une plateforme IA complète.</p>
        </div>
        <div class="feature-card">
            <h4>🎓 Professionnels IT</h4>
            <p>Vous souhaitez découvrir la gestion d'applications et la facturation sur infrastructure GPU.</p>
        </div>
    </div>

    <div class="highlight-box">
        <h4>🎯 Prérequis</h4>
        <p style="margin:0; font-size: 14px; color: #555;">
            Connaissance de base de Linux (Ubuntu) et du terminal. Familiarité avec Docker et docker-compose.
            Notions de base en réseau. Nous fournissons l'environnement, les outils CLI et la documentation complète.
        </p>
    </div>

    <h3>Vos acquis à l'issue de la formation</h3>
    <ul class="benefits">
        <li>Déploiement complet de la plateforme OPCP-Explorer sur bare-metal</li>
        <li>Gestion du cycle de vie des applications (CRUD, démarrage, arrêt)</li>
        <li>Maîtrise des sauvegardes vers le stockage objet S3 OVH</li>
        <li>Modification de code assistée par IA avec SHAI CLI</li>
        <li>Configuration et exploitation de GPUs NVIDIA en mode MIG</li>
        <li>Mise en place d'architectures serverless optimisées en coûts</li>
    </ul>

    <div class="cta">
        <h3>Prêt à démarrer ?</h3>
        <p>Contactez notre équipe pour planifier votre session de formation Agentic AI OPCP Labs.</p>
        <div class="contact">psmc@ovhcloud.com</div>
    </div>

    <div class="footer">
        <p>© PSMC OVHcloud — Programme OPCP Agentic AI OPCP Labs</p>
    </div>
</div>

</body>
</html>
"""

output_path = "/home/slepetre/workspace/forgejo/opcp-ai-start-labs/docs/OPCP-AI-Start-Labs-Marketing.pdf"
HTML(string=html_content).write_pdf(output_path)
print(f"PDF generated: {output_path}")
