# LIVRABLE 1 : CADRAGE, ARCHITECTURE TECHNIQUE & ANALYSE DES RISQUES
## Projet Intégrateur d'IA Générative Multimodale — MAINTIDOC

---

### 1. Objectifs & Vision du Projet

**MAINTIDOC** est un assistant documentaire multimodal et agentique conçu pour les techniciens et responsables de maintenance industrielle. Son objectif central est d'accélérer et fiabiliser la résolution des pannes sur site en exploitant de manière unifiée :
- Les manuels d'utilisation, notices techniques d'atelier et procédures constructeur.
- Les schémas de coupe mécanique, plans de câblage et figures techniques.
- Les photographies prises sur le terrain par les techniciens (panneaux d'alarme, voyants, manomètres, étiquettes).
- L'historique des interventions et tickets de maintenance accessible via un serveur standardisé **MCP (Model Context Protocol)**.

### 2. Note de Cadrage Opérationnel

| Élément | Périmètre Retenu | Hors Périmètre (Exclusions Strictes) |
| :--- | :--- | :--- |
| **Utilisateurs** | Techniciens de maintenance habilités, chefs d'équipe, auditeurs. | Opérateurs non formés sans habilitation sécurité. |
| **Corpus** | 30 à 50 documents techniques autorisés, couvrant deux familles de machines : **Pompes centrifuges haute pression (Série CP-200)** et **Compresseurs rotatifs à vis lubrifiée (Modèle CV-50)**. | Documentation tierce non validée, machines non répertoriées. |
| **Entrées** | Requêtes textuelles en français, photographies haute résolution, plans et manuels PDF. | Flux vidéo temps réel, commandes vocales brutes. |
| **Sorties** | Réponses techniques sourcées (citations exactes page + élément), demandes de clarification, brouillons de tickets. | Diagnostic garanti absolu, exécution autonome sur les automates. |
| **Actions Sensibles** | Préparation de brouillon de ticket avec jeton cryptographique et approbation explicite (**Human-In-The-Loop**). | Création de ticket en aveugle, modification de paramètres machine. |

---

### 3. Architecture Technique & Flux de Données

```
                               ┌──────────────────────────────────────────────┐
                               │     INTERFACE UTILISATEUR TECHNICIEN         │
                               │  - Application Web Streamlit                │
                               │  - Question en français + Photo de terrain   │
                               └──────────────────────┬───────────────────────┘
                                                      │ HTTPS / REST
                                                      ▼
                               ┌──────────────────────────────────────────────┐
                               │         COUCHE API & SÉCURITÉ FASTAPI        │
                               │  - Authentification & vérification des rôles │
                               │  - Détection anti-injection de prompt        │
                               │  - Contrôle budgétaire (appels, temps, ctx)  │
                               └──────────────────────┬───────────────────────┘
                                                      │
                                                      ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
 │                                   WORKFLOW AGENTIQUE LANGGRAPH                                         │
 │                                                                                                        │
 │  [1. Verify Access] ──► [2. Analyze Image VLM] ──► [3. Search Sources] ──► [4. Consult MCP Server]     │
 │        │                       │                           │                       │                   │
 │   Échec sécurité         Détection voyants/         Recherche hybride        get_equipment_history     │
 │        ▼                 plaque signalétique        Texte + Image (CLIP)     get_open_tickets          │
 │   Fin (Rejet)                  │                           │                       │                   │
 │                                └─────────────┬─────────────┘                       │                   │
 │                                              ▼                                     │                   │
 │                                     [Reciprocal Rank Fusion]                       │                   │
 │                                              ▼                                     │                   │
 │                                     [Reranker Adapté BGE]                          │                   │
 │                                              ▼                                     │                   │
 │                               [5. Evidence Check & Synthesis] ◄────────────────────┘                   │
 │                                              │                                                         │
 │                       ┌──────────────────────┴──────────────────────┐                                  │
 │                       ▼                                             ▼                                  │
 │             [Incertitude détectée]                        [Demande de Ticket ?]                        │
 │                       │                                             │                                  │
 │                       ▼                                     Non ◄───┴───► Oui                          │
 │            status="needs_clarification"                      │             │                           │
 │            (Question ciblée au technicien)                   ▼             ▼                           │
 │                                                      status="answered"   [6. Prepare Ticket Draft]     │
 │                                                      (Citations page/fig)          │                   │
 └────────────────────────────────────────────────────────────────────────────────────┼───────────────────┘
                                                                                      │
                                                                                      ▼
                                                                        ┌───────────────────────────┐
                                                                        │  INTERRUPTION HUMAINE     │
                                                                        │  (Human-in-the-Loop)      │
                                                                        │  Validation du technicien │
                                                                        └─────────────┬─────────────┘
                                                                                      │ Accord explicite
                                                                                      ▼
                                                                        ┌───────────────────────────┐
                                                                        │   SERVEUR MCP MAINTENANCE │
                                                                        │   - create_ticket(...)    │
                                                                        │   - Vérification token    │
                                                                        │   - Clé d'idempotence     │
                                                                        └───────────────────────────┘
```

---

### 4. Composants & Choix Technologiques

| Composant | Solution Retenue | Justification |
| :--- | :--- | :--- |
| **Vision-Language Model (VLM)** | **Qwen2.5-VL-7B-Instruct** | Modèle multilingue à poids ouverts de pointe, capable de lire le français technique, d'inspecter les détails visuels (LEDs, jauges) et de respecter des schémas JSON stricts. |
| **Orchestration Agentique** | **LangGraph & LangChain** | Gestion fine du graphe d'état cyclique, mémoire conversationnelle, et primitives natives d'interruption pour validation humaine (`interrupt`). |
| **Moteur Vectoriel** | **Qdrant** (avec fallback FAISS local) | Indexation dense multimodale, filtrage pré-requête strict par payload (RBAC par groupe), performance et support Docker standardisé. |
| **Embeddings Textuels** | **BGE-M3** | Modèle dense/hybride multilingue adapté au vocabulaire technique industriel. |
| **Embeddings Visuels** | **CLIP ViT (OpenAI)** | Projection conjointe texte-image permettant la recherche par similarité visuelle de schémas. |
| **Reranker Adapté** | **BGE-Reranker-Base fine-tuné** | Cross-encoder spécialisé sur les triplets industriels (question, passage positif, faux positif inter-équipements). |
| **Connexion Outils** | **Serveur MCP (Model Context Protocol)** | Protocole standardisé assurant le découplage des outils externes (historique, tickets) avec contrôle serveur strict. |
| **Conteneurisation & Suivi** | **Docker Compose & MLflow** | Déploiement reproductible et traçabilité des métriques d'évaluation et versions de prompts. |

---

### 5. Analyse des Risques & Stratégie d'Atténuation

| Risque Identifié | Impact | Mesure de Mitigé / Garde-fou Implémenté |
| :--- | :--- | :--- |
| **Hallucination / Mauvais couple de serrage** | Critique (Casse mécanique ou fuite sous pression). | **Evidence Checking systématique** : chaque affirmation doit être soutenue par une citation page/figure exacte. Statut `needs_clarification` si information manquante. |
| **Injection de Prompt (Directe ou via OCR)** | Élevé (Détournement des consignes, exfiltration de données). | **PromptInjectionGuard** : Analyse lexicale et sémantique regex/embeddings de toutes les entrées utilisateur, extraits OCR et sorties d'outils. Étanchéité via balises `<UNTRUSTED_DOCUMENT_DATA>`. |
| **Fuite documentaire entre habilitations (RBAC)** | Moyen (Accès non autorisé à des équipements sensibles). | **Double filtrage RBAC** : Pré-filtrage strict dans la requête vectorielle Qdrant, et post-filtrage avant affichage. |
| **Création intempestive ou doublon de tickets** | Moyen (Saturation des équipes de maintenance). | **Jeton d'approbation cryptographique HMAC-SHA256** lié au contenu exact et à l'utilisateur, associé à une clé d'idempotence unique. |
| **Dépassement de budget / Boucle infinie** | Faible (Consommation GPU / CPU). | **RequestBudgetTracker** : Plafond strict à 3 appels MCP, 6 appels VLM, et 60 secondes d'exécution automatique par requête. |
