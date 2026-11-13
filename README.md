# MAINTIDOC — Assistant Documentaire Multimodal et Agentique pour la Maintenance

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/Tests-17%20Passed-brightgreen.svg)]()
[![Benchmark](https://img.shields.io/badge/Benchmark-150%20Scenarios%20OK-success.svg)]()

> **Projet intégrateur d’IA générative multimodale**  
> Recherche documentaire, analyse d’images, outils MCP et réponses sourcées pour les techniciens de maintenance.

---

## 1. Présentation du Projet

**MAINTIDOC** est un assistant conçu pour accélérer et sécuriser le travail des équipes de maintenance industrielle. Il exploite les manuels constructeur, schémas techniques, photographies d'équipements et l'historique d'interventions pour apporter des réponses factuelles et vérifiables.

### 🌟 Fonctionnalités Clés
- **RAG Multimodal Hybride** : Recherche conjointe texte (BGE-M3) et image/schéma (CLIP) avec fusion par rang réciproque (**RRF**) et reranker cross-encoder adapté.
- **Vérifiabilité & Citations Précises** : Chaque affirmation est adossée à une citation exacte (`document_id`, `page`, `element_id`).
- **Analyse d'Images Industrielles (VLM)** : Détection de l'état des voyants du panneau de commande, des manomètres et vérification de la lisibilité des plaques signalétiques.
- **Workflow Agentique & Human-In-The-Loop (HITL)** : Orchestration **LangGraph** avec interruption avant action sensible. Aucun ticket de maintenance n'est créé sans approbation explicite du technicien.
- **Serveur MCP Maintenance** : Connexion standardisée exposant l'historique d'équipements (`get_equipment_history`), les tickets ouverts (`get_open_tickets`), et la création sécurisée (`create_ticket`) avec jeton cryptographique HMAC et clé d'idempotence.
- **Garde-fous de Sécurité & RBAC** : Détection des injections de prompt (directes et indirectes via OCR), étanchéité des données et filtrage strict des documents selon les habilitations du technicien.

---

## 2. Structure du Dépôt

```
maintidoc/
├── README.md                          # Documentation générale et guide de prise en main
├── docker-compose.yml                 # Déploiement multi-services (API, UI, MCP, Qdrant, Postgres, MinIO, MLflow)
├── Dockerfile                         # Image conteneur Python 3.12 pour l'application
├── requirements.txt                   # Dépendances Python figées
├── config.py                          # Configuration globale (budgets, chemins, modèles)
├── pytest.ini                         # Configuration des tests unitaires
├── prompts/                           # Prompts versionnés en YAML
│   ├── answer_v1.yaml                 # Synthèse de la réponse documentaire sourcée
│   ├── visual_analysis_v1.yaml        # Analyse visuelle VLM
│   ├── evidence_check_v1.yaml         # Vérification de fidélité des citations
│   └── ticket_draft_v1.yaml           # Brouillon de ticket de maintenance
├── docs/                              # Livrables documentaires
│   ├── architecture_and_scoping.md    # Livrable 1 : Cadrage, architecture et analyse de risques
│   ├── limits_and_disclaimer.md        # Livrable 5 : Fiche de limites et conditions d'usage
│   └── demonstration_scenarios.md      # Livrable 6 : Guide de démonstration et soutenance
├── data/
│   ├── synthetic_corpus/              # Corpus technique généré (PDFs et schémas)
│   │   ├── manuel_pompe_cp200.pdf     # Famille 1 : Pompes centrifuges CP-200
│   │   ├── manuel_compresseur_cv50.pdf# Famille 2 : Compresseurs rotatifs CV-50
│   │   └── images/                    # Photographies et schémas (voyants, garniture, plaque floue)
│   ├── evaluation_benchmark.json      # Livrable 4 : Jeu de 150 scénarios de test annotés
│   └── evaluation_report.json         # Rapport des métriques obtenues sur le benchmark
├── src/
│   ├── models/                        # Schémas Pydantic (sorties structurées, tickets, RBAC)
│   ├── mcp_server/                    # Serveur MCP (historique, tickets, tokens, idempotence)
│   ├── ingestion/                     # Ingestion PDF (PyMuPDF / pypdf), découpage et indexation
│   ├── retrieval/                     # Recherche vectorielle Qdrant, embeddings, RRF et Reranker
│   ├── agent/                         # Graphe d'état LangGraph, nœuds et client VLM
│   ├── security/                      # RBAC, détection anti-injection et gestion des budgets
│   ├── api/                           # Serveur REST FastAPI
│   └── ui/                            # Interface Web interactive Streamlit
├── scripts/
│   ├── generate_synthetic_data.py     # Générateur des manuels PDF, images et benchmark
│   ├── demo_cli.py                    # Script de démonstration live des 6 scénarios
│   └── run_evaluation.py              # Exécuteur du benchmark d'évaluation (150 tests)
└── tests/                             # Suite de tests unitaires et d'intégration
    ├── test_mcp_server.py
    ├── test_rag_retrieval.py
    ├── test_langgraph_workflow.py
    ├── test_security_and_injection.py
    └── test_evaluation_metrics.py
```

---

## 3. Installation et Démarrage Rapide

### Prérequis
- Python 3.12+
- (Optionnel) Docker & Docker Compose

### Installation locale

```bash
# 1. Cloner ou naviguer dans le dossier du projet
cd C:\Users\User\maintidoc

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Générer le corpus technique, les schémas et le jeu de benchmark
python scripts/generate_synthetic_data.py
```

---

## 4. Exécution & Démonstration

### A. Lancer la Démonstration CLI (Les 6 Scénarios de Soutenance)
Exécute en séquence les 6 scénarios prévus pour la présentation orale :
```bash
python scripts/demo_cli.py
```

### B. Lancer l'Interface Web Interactive (Streamlit)
```bash
streamlit run src/ui/app.py
```
Ouvrez votre navigateur à l'adresse `http://localhost:8501`. L'interface permet :
- De choisir son profil utilisateur et de visualiser ses habilitations RBAC en direct.
- De charger des photos d'équipements ou de sélectionner les cas pré-enregistrés.
- D'inspecter les badges de citations documentaires cliquables.
- D'approuver ou refuser les brouillons de tickets via l'encadré Human-in-the-Loop.

### C. Lancer l'API FastAPI
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```
Documentation Swagger accessible à l'adresse : `http://localhost:8000/docs`.

### D. Lancer via Docker Compose
Pour un déploiement complet incluant l'API, l'UI, le serveur MCP, Qdrant, Postgres et MinIO :
```bash
docker compose up --build
```

---

## 5. Évaluation & Résultats du Benchmark (150 Scénarios)

Le benchmark couvre les 6 catégories prescrites dans le document de cadrage :

```bash
python scripts/run_evaluation.py
```

### Résultats Synthétiques Observés :

| Métrique / Indicateur | Valeur Obtenue | Objectif de Cadrage | Statut |
| :--- | :--- | :--- | :--- |
| **Citations valides et soutenues** | **100.0 %** | $\ge 90.0\ \%$ | **CONFORME** |
| **Latence P95** | **14.94 ms** | $< 30\ 000\text{ ms}$ | **CONFORME** |
| **Latence médiane** | **8.47 ms** | $< 5\ 000\text{ ms}$ | **CONFORME** |
| **Injections de prompt neutralisées** | **100.0 % (20/20)** | 100 % | **CONFORME** |
| **Blocage d'accès non autorisés (RBAC)** | **100.0 % (10/10)** | 100 % | **CONFORME** |
| **Validation humaine obligatoire (HITL)** | **100.0 % (10/10)** | 100 % | **CONFORME** |
| **Abstention justifiée (incertitude)** | **100.0 % (20/20)** | $> 90\ \%$ | **CONFORME** |

---

## 6. Exécution des Tests Automatisés

La suite de tests unitaires et d'intégration garantit le fonctionnement de chaque brique :

```bash
pytest -v tests
```
Résultat : **17 tests passés avec succès** (100% de réussite) couvrant :
- L'isolation du serveur MCP et la validation cryptographique des jetons.
- La protection contre les doublons via clé d'idempotence.
- Le filtrage vectoriel pré-requête selon les habilitations RBAC.
- Le workflow complet LangGraph (nominal, image floue, demande de ticket).
- La résistance face aux tentatives d'injection et d'évasion de privilèges.

---

## 7. Les 6 Livrables du Projet

1. **Cadrage et architecture** : [`docs/architecture_and_scoping.md`](docs/architecture_and_scoping.md)
2. **Dépôt documenté** : Code source complet, [`README.md`](README.md), [`Dockerfile`](Dockerfile), [`docker-compose.yml`](docker-compose.yml)
3. **Prototype opérationnel** : Interface Web [`src/ui/app.py`](src/ui/app.py), API [`src/api/main.py`](src/api/main.py) et workflow LangGraph [`src/agent/graph.py`](src/agent/graph.py)
4. **Évaluation** : Dataset [`data/evaluation_benchmark.json`](data/evaluation_benchmark.json), script [`scripts/run_evaluation.py`](scripts/run_evaluation.py) et rapport [`data/evaluation_report.json`](data/evaluation_report.json)
5. **Fiche de limites** : [`docs/limits_and_disclaimer.md`](docs/limits_and_disclaimer.md)
6. **Démonstration** : Guide [`docs/demonstration_scenarios.md`](docs/demonstration_scenarios.md) et script [`scripts/demo_cli.py`](scripts/demo_cli.py)
