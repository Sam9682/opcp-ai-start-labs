# Document de conception d'agent IA

> **Livrable final.** Remplissez chaque section. Ce document est la conception
> finale, entièrement documentée, d'un agent IA fonctionnel, fiable et
> contrôlable opérant sur la plateforme opcp-explorer. Remplacez les _invites en
> italique_ par votre propre contenu.

- **Auteur :** _votre nom_
- **Date :** _AAAA-MM-JJ_
- **Nom de l'agent :** _p. ex. opcp-deploy-agent_
- **Plateforme cible :** opcp-explorer (AI-Powered-Store)

---

## 1. Objectif et périmètre

_Quel objectif unique cet agent poursuit-il ? Qu'est-ce qui est explicitement
hors périmètre ?_

- **Objectif :** _..._
- **Hors périmètre :** _..._
- **Critères de réussite :** _comment savez-vous que l'agent a réussi ?_

## 2. Niveau d'autonomie

_Où se situe cet agent sur le spectre d'autonomie, et pourquoi ? (suggérer /
confirmer chaque étape / agir avec points de contrôle / agir et rendre compte /
entièrement autonome)_

- **Niveau choisi :** _..._
- **Justification :** _pourquoi est-ce la plus faible autonomie qui atteint encore l'objectif ?_

## 3. Les sept composants essentiels

_Décrivez chaque composant pour votre agent._

### 3.1 Cerveau (LLM)
_Quel modèle, et quel rôle de raisonnement ?_

### 3.2 Mémoire à court terme
_Quel contexte de travail conserve-t-il pendant une exécution ?_

### 3.3 Mémoire à long terme
_Qu'est-ce qui persiste entre les exécutions, et où est-ce stocké ?_

### 3.4 Outils
_Quels outils opcp-explorer (API/CLI/MCP) appelle-t-il ? Listez-les._

### 3.5 Planificateur
_Comment décompose-t-il l'objectif en étapes ?_

### 3.6 Boucle d'exécution
_Comment la boucle pilote-t-elle l'agent ? (référez-vous à votre variante choisie ci-dessous)_

### 3.7 Garde-fous
_Résumez ; détaillé en section 6._

## 4. Variante de boucle

_Quelle variante de boucle utilisez-vous et pourquoi ? (ReAct / Plan-and-Execute
/ Reflexion, ou une combinaison)_

- **Variante choisie :** _..._
- **Justification :** _..._

## 5. Critères d'arrêt

_Listez les critères d'arrêt explicites et appliqués. Associez une condition
d'objectif à au moins une limite stricte._

| Critère | Type (objectif / limite / erreur / humain) | Valeur |
|---------|---------------------------------------------|--------|
| _..._ | _..._ | _..._ |

- **À l'arrêt, l'agent indique :** _quel critère s'est déclenché + état final_

## 6. Garde-fous (cinq couches)

_Renseignez un contrôle concret pour chacune des cinq couches. Les cinq lignes
sont obligatoires._

| Couche | Contrôle pour cet agent |
|--------|-------------------------|
| Permissions | _jeton restreint, liste d'outils, frontière d'environnement_ |
| Limites opérationnelles | _plafonds itérations / reprises / budget / délai_ |
| Approbation humaine | _quelles actions exigent un oui humain_ |
| Observabilité | _ce qui est journalisé / tracé / alerté_ |
| Kill switch | _comment l'agent est arrêté immédiatement_ |

## 7. Décision multi-agents

_Est-ce un agent unique ou plusieurs agents ? Justifiez avec la liste de décision._

- **Décision :** agent unique | multi-agents
- **Si multi-agents :** quel patron (superviseur / pipeline / parallèle / réseau)
  et comment les agents communiquent-ils ?
- **Justification :** _pourquoi est-ce l'architecture la plus simple répondant au besoin_

## 8. Alignement IA responsable (politique IA OVHcloud)

_Comment la conception respecte-t-elle les principes d'IA responsable ? Mappez au
moins transparence, responsabilité humaine, protection des données, sécurité et
contrôlabilité à des choix concrets ci-dessus._

| Principe | Comment la conception le respecte |
|----------|-----------------------------------|
| Transparence | _..._ |
| Responsabilité humaine | _..._ |
| Protection des données et vie privée | _..._ |
| Sécurité | _..._ |
| Contrôlabilité | _..._ |

## 9. Référence au modèle de menaces

_Lien vers le modèle de menaces complété pour cet agent (voir
threat-model-template.fr.md)._

- **Modèle de menaces :** _..._

## 10. Questions ouvertes et risques

_Qu'est-ce qui reste non résolu, risqué ou reporté ?_

- _..._
