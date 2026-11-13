# LIVRABLE 5 : FICHE DE LIMITES, CONDITIONS D'UTILISATION ET SÉCURITÉ
## MAINTIDOC — Assistant Documentaire Multimodal

---

### 1. Statut Juridique et Rôle du Système

> [!CAUTION]
> **MAINTIDOC EST EXCLUSIVEMENT UN OUTIL D'AIDE DOCUMENTAIRE.**
> Il ne constitue en aucun cas un automate de commande, un système de contrôle-commande, ni un dispositif de sécurité certifié.
> Les réponses générées par le système **ne constituent pas une garantie technique ou contractuelle de diagnostic**.

### 2. Usages Autorisés vs. Usages Proscrits

#### Usages Autorisés (In-Scope)
- Recherche rapide et contextualisée dans la documentation technique officielle (manuels d'atelier, éclatés, schémas).
- Localisation précise de références de pièces détachées (ex: joints, garnitures, cartouches filtrantes) avec indication des pages et figures.
- Consultation de l'historique des pannes antérieures via le serveur MCP.
- Pré-remplissage assisté de brouillons de tickets d'intervention pour soumission à un superviseur ou technicien habilité.
- Décryptage d'alarmes visuelles et voyants lumineux à partir de photographies nettes.

#### Usages Strictement Proscrits (Out-of-Scope)
- **Pilotage ou téléopération d'équipements** : MAINTIDOC n'a aucune interface de contrôle directe sur les automates programmables (API/PLC).
- **Substitution aux consignations de sécurité** : Aucune intervention sur machine ne doit être entreprise sans application préalable des procédures réglementaires (consignation électrique NFC 18-510, consignation fluidique, port des EPI).
- **Intervention sur machines hors périmètre** : Ne pas interroger MAINTIDOC pour des machines dont les manuels n'ont pas été formellement validés et indexés dans le système.
- **Création de ticket automatisée sans revue humaine** : Le système interdit la création autonome sans approbation préalable.

---

### 3. Gestion de l'Incertitude & Déontologie de l'Assistant

Conformément à la section 8 du document de cadrage :
1. **Photographie floue ou plaque illisible** : Le système s'interdit d'émettre une conjecture hasardée. Il bascule immédiatement en statut `needs_clarification` et sollicite une prise de vue nette.
2. **Absence de pourcentage de confiance arbitraire** : MAINTIDOC n'affiche pas de taux de confiance factice inventé par le modèle (ex: "sûr à 87%"). Il liste de manière factuelle les **preuves documentaires disponibles** et les **informations manquantes**.
3. **Contradiction documentaire** : En cas de divergence entre deux révisions de documents, l'assistant signale explicitement la contradiction et préconise l'arbitrage du responsable de maintenance.

---

### 4. Responsabilités de l'Utilisateur Technicien

Le technicien utilisateur demeure le seul responsable opérationnel de l'intervention :
- Il doit vérifier visuellement la concordance physique entre la pièce démontée et la référence citée.
- Il doit inspecter le couple de serrage et s'assurer de l'étalonnage de sa clé dynamométrique.
- Avant de valider un ticket d'intervention via le bouton d'approbation HITL, il doit en relire le titre, la criticité et la description.
