# Schulportal Hessen – Architektur

Diese Datei beschreibt die technische Struktur von SPH-HA ab **Version 0.5.0**.

## Grundprinzipien

- Eine Home-Assistant-Integration bedient mehrere fachlich getrennte Module.
- Alle SPH-Module teilen sich Authentifizierung und Session.
- Fachlogik bleibt im jeweiligen Modul.
- Modulübergreifende Normalisierung liegt unter `api/`.
- Lovelace-Karten sind allgemeine `sph-*` Karten; schulspezifische Abweichungen werden über **School Hacks** injiziert.
- School Hacks ändern keine Backend-Sensordaten.
- Native Kalender verwenden ausschließlich Backend-Daten der SPH-Integration und keine Frontend-School-Hacks.

## Quelltextstruktur

```text
custom_components/sph/
├── __init__.py
├── binary_sensor.py
├── calendar.py
├── config_flow.py
├── const.py
├── coordinator.py
├── sensor.py
├── services.yaml
├── api/
│   ├── auth_client.py
│   ├── client.py
│   └── subjects.py
├── module/
│   ├── stundenplan/
│   │   ├── client.py
│   │   ├── coordinator.py
│   │   ├── calendar.py
│   │   ├── movable_holidays.py
│   │   └── sensor.py
│   ├── kalender/
│   │   ├── client.py
│   │   ├── coordinator.py
│   │   ├── sensor.py
│   │   └── storage.py
│   ├── meinunterricht/
│   │   ├── client.py
│   │   ├── coordinator.py
│   │   ├── helpers.py
│   │   ├── sensor.py
│   │   ├── services.py
│   │   └── storage.py
│   ├── lerngruppen/
│   │   ├── client.py
│   │   ├── coordinator.py
│   │   ├── calendar.py
│   │   ├── sensor.py
│   │   ├── services.py
│   │   └── storage.py
│   └── vertretung/
│       ├── apply.py
│       ├── binary_sensor.py
│       ├── client.py
│       ├── coordinator.py
│       ├── helpers.py
│       └── sensor.py
├── static/
│   ├── sph-stundenplan-card.js
│   ├── sph-stundenplan-tag-card.js
│   ├── sph-stundenplan-grid-card.js
│   ├── sph-meinunterricht-card.js
│   ├── sph-lerngruppen-card.js
│   ├── sph-kalender-card.js
│   ├── sph-vertretungsplan-card.js
│   ├── school-hacks.js
│   ├── substitution-adapter.js
│   └── school-hacks/
│       └── kfg.js
└── translations/
```

## Integrationsebene

### `__init__.py`

Verantwortlich für:

- Aufbau der gemeinsamen `SphAuthClient`-Instanz,
- Initialisierung der Modul-Coordinatoren,
- Modulaktivierung,
- Entity-ID-Migrationen,
- automatische Lovelace-Ressourcenregistrierung,
- Start/Stop zusätzlicher Hintergrundlogik.

### `sensor.py`

Dispatcher für die Sensoren der Module. Die Module liefern strukturierte Sensoren und – soweit vorgesehen – JSON-Sensoren.

### `binary_sensor.py`

Dispatcher für die Vertretungsplan-Binärsensoren.

### `calendar.py`

Erzeugt bzw. kombiniert native Home-Assistant-Kalender:

- Stundenplan,
- Schulkalender,
- Lerngruppen,
- zusammengefasster SPH-Kalender,
- bewegliche Ferientage.

Je nach Konfiguration werden die fachlichen Kalender getrennt oder über `calendar.sph_*` zusammengefasst.

## Gemeinsame API-Schicht

### Authentifizierung

Die gemeinsame Client-Schicht verwaltet Login, Session und erneute Anmeldung bei abgelaufener Session. Ein temporärer Fehler eines einzelnen Moduls soll andere Module nicht unbrauchbar machen.

### Fachnormalisierung

`api/subjects.py` enthält gemeinsame Fach-/Kursnormalisierung für mehrere Module. Ziel ist, bekannte Kürzel und Schreibvarianten zentral aufzulösen, statt Mappinglogik mehrfach zu implementieren.

## Modulaktivierung

Aktuell existieren fünf Module:

- Stundenplan
- Schulkalender
- Mein Unterricht
- Lerngruppen
- Vertretungsplan

Ein deaktiviertes Modul soll keine unnötigen SPH-Abrufe durchführen. Nicht mehr benötigte Entities werden abhängig vom Modul aus der Entity Registry entfernt oder inaktiv gehalten.

## Stundenplan

Quelle: `stundenplan.php`.

Wichtige Attribute:

- `eigener_plan`
- `eigener_grundplan`
- optional `tage`
- `wochenkennung`
- `wochenbeginn`
- `klasse`
- `freie_tage`

Der JSON-Sensor enthält denselben logischen Payload im Attribut `json`.

### A/B-Wochen

`wochenbeginn` verankert die aktuell gemeldete A/B-Woche. Vorschauansichten und Kalender schreiben daraus die Wochenkennung fort.

`eigener_grundplan` bleibt von der aktuellen Freie-Tage-Maskierung unberührt und dient deshalb als Basis für zukünftige Wochenansichten.

### Freie Tage

Berücksichtigt werden insbesondere:

- `calendar.deutschland_he`, falls vorhanden,
- bewegliche Ferientage des konfigurierten Schulamtsbezirks.

Freie Tage wirken auf Stundenplan-Sensoren, Lovelace-Auswahl und den nativen Stundenplan-Kalender.

### Stundenplan-Kalender

`module/stundenplan/calendar.py` erzeugt dynamisch Unterrichtstermine in einem rollierenden Fenster von zwei Wochen Vergangenheit bis acht Wochen Zukunft.

Seit 0.5.0 erhält der Kalender zusätzlich den Vertretungs-Coordinator und wendet interne SPH-Vertretungsdaten auf die regulären Unterrichtstermine an.

## Vertretungsplan

Quelle: `vertretungsplan.php`.

### Abruf und Normalisierung

`module/vertretung/client.py` liest die veröffentlichten Tagesbereiche und ordnet Tabellenfelder über die SPH-`data-field`-Kennzeichnungen zu. Hilfsfunktionen für Stundenbereiche und Vertretungsarten liegen in `helpers.py`.

Normalisierte Felder umfassen unter anderem:

- `datum`
- `wochentag`
- `woche`
- `stunde`
- `stunden`
- `von_stunde`
- `bis_stunde`
- `klasse`
- `fach`
- `fach_alt`
- `vertreter`
- `lehrer`
- `raum`
- `art`
- `art_lang`
- `entfall`
- `hinweis`

### Sensoren

- `sensor.vertretungsplan_<kind>_<kürzel>`
- `sensor.vertretungsplan_<kind>_<kürzel>_json`

Der JSON-Sensor enthält denselben vollständigen logischen Payload im Attribut `json`.

### Binärsensoren

`module/vertretung/binary_sensor.py` stellt Entfall-Sensoren für heute und morgen bereit. Die geprüfte Bezugsstunde ist konfigurierbar. Ist für einen Tag noch kein Plan veröffentlicht, bleibt die Entity `unavailable`.

### Anwendung auf Stunden

`module/vertretung/apply.py` ordnet einen internen Vertretungseintrag einer regulären Stundenplanstunde zu.

Matching-Kriterien:

- Datum
- Klasse
- Fach/Originalfach
- Schulstunde bzw. Stundenbereich

Angewendet werden unter anderem:

- Entfall,
- Vertretungsart,
- neues und ursprüngliches Fach,
- Vertretungslehrkraft,
- Raumänderung.

Diese Logik wird serverseitig bei der Kalendergenerierung verwendet.

## Frontend-Vertretungsadapter

`static/substitution-adapter.js` verbindet Stundenplankarten mit Vertretungsdaten.

### Ohne School Hack

Die Karte sucht den zum Kind passenden internen `sensor.vertretungsplan_*` und wendet dessen Einträge auf die dargestellten Stunden an.

### Mit School Hack

Reihenfolge pro Stunde:

1. explizit in der Karte gesetzte Quelle (`vertretungsplan_sensor`, `vertretungsplan`, `substitution_sensor`),
2. bevorzugte Quelle des aktiven Schulprofils,
3. interner SPH-Vertretungsplan als Fallback, wenn die bevorzugte Quelle keinen Treffer liefert.

Eine explizit gesetzte Quelle bleibt autoritativ; auch ein absichtlich fehlender expliziter Sensor führt nicht zu einem stillen Quellenwechsel.

## School Hacks

`static/school-hacks.js` enthält die gemeinsame Profil-Logik. Schuldateien unter `static/school-hacks/<name>.js` enthalten nur schulbezogene Einstellungen.

Aktuell vorhanden:

- `kfg.js` – Kaiserin-Friedrich-Gymnasium Bad Homburg

Ein Profil kann unter anderem definieren:

- A/B-Wochenregeln,
- Badge-Verhalten,
- automatische Wochenumschaltung,
- Lehrerquelle,
- bevorzugte Vertretungssensoren,
- Bezeichnungen von Vertretungsarten,
- Nachricht-des-Tages-Verarbeitung.

Neue Schulen erhalten keine Kartenkopien, sondern eine neue Profildatei und eine eigene README unter `docs/schools/<name>/README.md`.

Allgemeine Anleitung: [`lovelace/school-hacks.md`](lovelace/school-hacks.md).

Schulspezifische Dokumentation: [`schools/README.md`](schools/README.md).

## Mein Unterricht

Quelle: `meinunterricht.php`.

Kursnamen werden auf gemeinsame Fachnamen normalisiert. Klassenbestandteile werden entfernt, bekannte Kürzel ausgeschrieben und der ursprüngliche Kurswert bleibt erhalten.

Normaler Sensor und JSON-Sensor liefern zusätzlich:

- `faecher`
- `faecher_gesamt`
- `faecher_offen`

Lokale Hausaufgaben werden persistent gespeichert, mit SPH-Daten zusammengeführt und nach sieben Tagen relativ zum Aufgabendatum bereinigt.

## Lerngruppen

Quelle: `lerngruppen.php`.

Leistungskontrollen werden mit Lerngruppen und persönlichem Stundenplan verknüpft. Schulstunden werden nach Möglichkeit in konkrete Uhrzeiten umgerechnet. Lokale Termine werden persistent gespeichert und konservativ mit SPH-Terminen dedupliziert.

## Schulkalender

Der Schulkalender bevorzugt CSV und verwendet iCal als Fallback. Daten werden auf das relevante hessische Schuljahr begrenzt. Optional können Kalenderarten gefiltert werden. Lokale eigene Kalendertermine werden separat gespeichert.

## Lovelace-Ressourcen

Die Integration registriert ihre JavaScript-Ressourcen selbst und verwendet versionierte URLs.

Aktuelle Karten:

- `sph-stundenplan-card`
- `sph-stundenplan-tag-card`
- `sph-stundenplan-grid-card`
- `sph-meinunterricht-card`
- `sph-lerngruppen-card`
- `sph-kalender-card`
- `sph-vertretungsplan-card`

## Robustheit

- Erfolgreiche Daten sollen bei temporären Abruffehlern erhalten bleiben.
- Lokale Einträge werden unabhängig von SPH gespeichert.
- Frontend-Karten vermeiden unnötigen vollständigen Shadow-DOM-Neuaufbau, damit Scrollposition und Dialogzustand stabil bleiben.
- School Hacks dürfen Home-Assistant-State-Objekte nicht verändern.

## Tests

Die Tests decken unter anderem ab:

- A/B-Wochenlogik,
- School-Hack-Profilladen,
- Vertretungsquellen-Priorität,
- internen SPH-Vertretungsadapter,
- Vertretungsplan-Normalisierung und JSON-Payload,
- Kursnormalisierung,
- serverseitige Vertretungsanwendung,
- Lovelace-Ressourcenregistrierung.
