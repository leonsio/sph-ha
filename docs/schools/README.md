# Schulspezifische Schul-Profile

Dieser Ordner enthält die Dokumentation zu den vorhandenen schulspezifischen Profilen.

Die allgemeine Benutzer-Dokumentation befindet sich unter [`../SCHOOL_PROFILES.md`](../SCHOOL_PROFILES.md). Die Entwickler-API und Anleitung für neue Profile ist unter [`../SCHOOL_PROFILES_DEVELOPMENT.md`](../SCHOOL_PROFILES_DEVELOPMENT.md) beschrieben.

## Vorhandene Profile

| Profil | Schule | Dokumentation |
|---|---|---|
| `kfg` | Kaiserin-Friedrich-Gymnasium Bad Homburg | [KFG](kfg/README.md) |

## Struktur

Jede Schule besitzt einen eigenen Profilordner:

```text
custom_components/sph/school_profiles/<name>/
├── __init__.py
├── profile.py
├── ... optionale Python-Helfer ...
└── frontend/
    ├── lovelace.js
    └── ... optionale Frontend-Dateien ...
```

`profile.py` enthält Metadaten und serverseitige Datenlogik. Die Dateien unter `frontend/` enthalten die schulspezifischen Darstellungsregeln für die mitgelieferten Lovelace-Karten.

Die Integration entdeckt Profilordner automatisch. Neue Profile werden deshalb nicht in einer zentralen Registry oder im Config-Flow eingetragen.

Für jedes Profil wird zusätzlich eine Schuldokumentation angelegt:

```text
docs/schools/<name>/README.md
```

## Grundregel

Profile sollen möglichst klein bleiben. Sobald eine Regel schulübergreifend sinnvoll ist, gehört sie in die allgemeine Integration.

Schulspezifische externe Entities gehören ausschließlich in das jeweilige Profil. Beispielsweise ist `sensor.kfg_kollegium` nur Bestandteil des KFG-Profils und keine allgemeine Abhängigkeit von SPH-HA.
