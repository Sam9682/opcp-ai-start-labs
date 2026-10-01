# Modèle de menaces d'agent IA

> **Livrable d'atelier.** Remplissez chaque section. Ce modèle de menaces
> identifie comment un agent opérant sur opcp-explorer pourrait être détourné ou
> échouer, et mappe chaque mesure d'atténuation à l'une des cinq couches de
> garde-fous. Remplacez les _invites en italique_.

- **Auteur :** _votre nom_
- **Date :** _AAAA-MM-JJ_
- **Agent analysé :** _p. ex. opcp-deploy-agent_
- **Plateforme cible :** opcp-explorer (AI-Powered-Store)

---

## 1. Vue d'ensemble du système

_Décrivez brièvement l'agent, son objectif, ses outils et son niveau
d'autonomie. Que peut-il toucher sur opcp-explorer ?_

## 2. Frontières de confiance

_Où entre l'entrée non fiable ? (invites utilisateur, sorties d'outils, contenu
web, autres agents) Où sont les frontières de privilège ?_

- _..._

## 3. Menaces

_Pour chaque menace, décrivez l'attaque/la défaillance, son impact et sa
probabilité. Couvrez au moins les trois menaces spécifiques aux agents
ci-dessous ; ajoutez-en d'autres au besoin._

### 3.1 Détournement d'outil
_L'agent appelle un outil d'une manière nuisible ou non prévue (p. ex. déploie
en production, supprime une app, épuise le quota)._

- **Impact :** _..._
- **Probabilité :** _..._

### 3.2 Injection d'invite
_Un contenu non fiable (sortie d'outil, données utilisateur, fichier de dépôt)
glisse des instructions qui redirigent l'agent._

- **Impact :** _..._
- **Probabilité :** _..._

### 3.3 Boucles emballées
_L'agent ne s'arrête pas : oscillation, échecs identiques répétés ou absence de
convergence — consommant le budget et saturant la plateforme._

- **Impact :** _..._
- **Probabilité :** _..._

### 3.4 Autres menaces
_p. ex. exfiltration de données, permissions excessives, fuite de secrets, déni
de service. Ajoutez des lignes au besoin._

- _..._

## 4. Atténuations mappées aux cinq couches de garde-fous

_Pour chaque menace ci-dessus, précisez le contrôle d'atténuation et la couche de
garde-fou à laquelle il appartient. Chacune des cinq couches doit apparaître au
moins une fois._

| Menace | Atténuation | Couche de garde-fou |
|--------|-------------|---------------------|
| Détournement d'outil | _..._ | Permissions |
| Boucles emballées | _..._ | Limites opérationnelles |
| Action à fort impact | _..._ | Approbation humaine |
| Défaillance non détectée | _..._ | Observabilité |
| Incident actif | _..._ | Kill switch |

### Liste de couverture des couches de garde-fous
_Confirmez que chaque couche est traitée par au moins une atténuation._

- [ ] Permissions
- [ ] Limites opérationnelles
- [ ] Approbation humaine
- [ ] Observabilité
- [ ] Kill switch

## 5. Risque résiduel

_Quel risque subsiste après atténuation ? Est-il acceptable ? Qui l'approuve ?_

- _..._

## 6. Note IA responsable (politique IA OVHcloud)

_Comment ces atténuations s'alignent-elles sur les principes d'IA responsable
(transparence, responsabilité humaine, sécurité, contrôlabilité) ? Vérifiez par
rapport à la politique IA OVHcloud canonique._

- _..._
