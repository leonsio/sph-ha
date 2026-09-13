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
│   │   └── sensor.py
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
│       ├── client.py
│       ├── coordinator.py
│       ├── parser.py
│       ├── sensor.py
│       └── apply.py
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

Dispatcher für die Sensoren der Module. Die Module liefern jeweils einen strukturierten Sensor und – sofern vorgesehen – einen JSON-Sensor.

### `binary_sensor.py`

Stellt die Entfall-Binärsensoren des Vertretungsplan-Moduls bereit.

### `calendar.py`

Erzeugt die nativen Kalender:

- Stundenplan,
- Schulkalender,
- Lerngruppen,
- zusammengefasster SPH-Kalender,
- bewegliche Ferientage.

Der kombinierte Kalender aggregiert die aktivierten Kalenderquellen eines Kindes.

## Gemeinsame API-Schicht

### Authentifizierung

`api/auth_client.py` bzw. die gemeinsame Client-Schicht verwaltet Login, Session und erneute Anmeldung bei abgelaufener Session. Ein temporärer Fehler eines einzelnen Moduls soll andere Module nicht unbrauchbar machen.

### Fachnormalisierung

`api/subjects.py` enthält die gemeinsame Fach-/Kursnormalisierung. Sie wird unter anderem von Stundenplan, Mein Unterricht und Vertretungsplan verwendet.

Ziele:

- bekannte Kürzel auflösen,
- fachgleiche Kursvarianten zusammenführen,
- Normalisierung nicht mehrfach in einzelnen Modulen implementieren.

## Modulaktivierung

Aktuell existieren fünf Module:

- Stundenplan
- Schulkalender
- Mein Unterricht
- Lerngruppen
- Vertretungsplan

Ein deaktiviertes Modul soll keine unnötigen SPH-Abrufe durchführen. Entities werden abhängig vom Modul bereinigt oder inaktiv gehalten.

## Stundenplan

Quelle: `stundenplan.php`.

Wichtige Sensorattribute:

- `eigener_plan`
- `eigener_grundplan`
- optional `tage`
- `wochenkennung`
- `wochenbeginn`
- `klasse`
- `freie_tage`

Der JSON-Sensor enthält denselben logischen Payload im Attribut `json`.

### A/B-Wochen

`wochenbeginn` dient als Anker für die aktuelle SPH-Wochenkennung. Vorschauansichten und Kalender können daraus zukünftige A/B-Wochen fortschreiben.

`eigener_grundplan` bleibt unverändert von aktuell ausgeblendeten freien Tagen und ist deshalb für Vorschauen geeignet.

### Freie Tage

Freie Tage werden aus mehreren Quellen zusammengeführt:

- `calendar.deutschland_he`, falls vorhanden,
- bewegliche Ferientage des konfigurierten Schulamtsbezirks.

Sie beeinflussen Sensoransicht, Lovelace-Auswahl und Stundenplan-Kalender.

### Stundenplan-Kalender

`module/stundenplan/calendar.py` erzeugt dynamisch ein rollierendes Fenster:

- 2 Wochen Vergangenheit
- 8 Wochen Zukunft

Neben Unterrichtsterminen können A/B-Wochenmarker erzeugt werden.

Seit 0.5.0 wird der interne SPH-Vertretungsplan beim Generieren der Unterrichtstermine berücksichtigt. Dafür erhält `SphTimetableCalendar` zusätzlich den Vertretungs-Coordinator.

## Vertretungsplan

Quelle: `vertretungsplan.php`.

### Parser

Der Parser ordnet Spalten über SPH-`data-field`-Kennzeichnungen zu und ist dadurch nicht von einer festen Tabellenreihenfolge abhängig.

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

Der JSON-Sensor enthält denselben vollständigen Payload wie der normale Sensor.

### Binärsensoren

- Entfall der konfigurierten Bezugsstunde heute
- Entfall der konfigurierten Bezugsstunde morgen

Ist für den jeweiligen Tag noch kein Plan veröffentlicht, ist der Sensor `unavailable`.

### Anwendung auf Stunden

`module/vertretung/apply.py` enthält die serverseitige Zuordnung zwischen regulärer Unterrichtsstunde und Vertretungsplan-Eintrag.

Matching-Kriterien:

- Datum
- Klasse
- Fach/Originalfach
- Schulstunde bzw. Stundenbereich

Angewendet werden unter anderem:

- Entfall,
- Vertretungsart,
- neues Fach,
- ursprüngliches Fach,
- Vertretungslehrkraft,
- Raumänderung.

Diese Logik wird bei der nativen Kalendergenerierung verwendet.

## Frontend-Vertretungsadapter

`static/substitution-adapter.js` verbindet Stundenplankarten mit Vertretungsdaten.

### Ohne School Hack

Die Karte sucht den zum Kind passenden internen SPH-Sensor `sensor.vertretungsplan_*` und wendet dessen Einträge auf die dargestellten Stunden an.

### Mit School Hack

Reihenfolge pro Stunde:

1. explizit in der Karte gesetzte Quelle (`vertretungsplan_sensor`, `vertretungsplan`, `substitution_sensor`),
2. bevorzugte Quelle des aktiven Schulprofils,
3. interner SPH-Vertretungsplan als Fallback, wenn die bevorzugte Quelle keinen Treffer liefert.

Eine explizit gesetzte Quelle bleibt autoritativ; auch ein absichtlich fehlender expliziter Sensor löst keinen automatischen Wechsel auf eine andere Quelle aus.

Damit kann jede Schule ihre eigene primäre Vertretungsquelle definieren, während das allgemeine SPH-Modul als kompatibler Fallback verfügbar bleibt.

## School Hacks

`static/school-hacks.js` enthält die gemeinsame Profil-Logik. Schuldateien unter `static/school-hacks/<name>.js` enthalten nur schulbezogene Einstellungen.

Aktuell vorhanden:

- `kfg.js` – Kaiserin-Friedrich-Gymnasium Bad Homburg

Ein Profil kann unter anderem definieren:

- A/B-Wochenregeln,
- Badge-Verhalten,
- Umschalten der Wochenansicht,
- Lehrerquelle,
- bevorzugte Vertretungssensoren,
- Bezeichnungen von Vertretungsarten,
- Nachricht-des-Tages-Verarbeitung.

Neue Schulen sollen **keine Kartenkopien** erhalten. Stattdessen wird eine neue Profildatei plus eigene Schulspezifische README angelegt.

Allgemeine Anleitung: [`lovelace/school-hacks.md`](lovelace/school-hacks.md).

Schulspezifische Dokumentation: [`schools/README.md`](schools/README.md).

## Mein Unterricht

Quelle: `meinunterricht.php`.

### Kursnormalisierung

Kursnamen wie `D 05cG`, `Deutsch 7n` oder `Biologie 05cg` werden auf ein Fach normalisiert. Klassenbestandteile werden entfernt, bekannte Kürzel ausgeschrieben und der ursprüngliche Kurswert bleibt erhalten.

### Fachübersicht

Normaler Sensor und JSON-Sensor liefern zusätzlich:

- `faecher`
- `faecher_gesamt`
- `faecher_offen`

### Manuelle Hausaufgaben

Lokale Hausaufgaben werden persistent gespeichert, mit SPH-Daten zusammengeführt und nach sieben Tagen relativ zum Aufgabendatum automatisch bereinigt.

## Lerngruppen

Quelle: `lerngruppen.php`.

Leistungskontrollen werden mit Lerngruppen und persönlichem Stundenplan verknüpft. Schulstunden werden nach Möglichkeit in konkrete Uhrzeiten umgerechnet.

Manuelle Termine werden persistent gespeichert und konservativ mit SPH-Terminen dedupliziert.

## Schulkalender

Der Schulkalender bevorzugt den CSV-Export und verwendet iCal als Fallback. Die Daten werden auf das relevante hessische Schuljahr begrenzt. Optional können Kalenderarten gefiltert werden.

## Lovelace-Ressourcen

Die Integration registriert ihre JavaScript-Ressourcen selbst und verwendet versionierte URLs. Nutzer müssen bei aktuellen Home-Assistant-Versionen keine manuellen `/local/...`-Ressourcen anlegen.

Aktuelle Karten:

- `sph-stundenplan-card`
- `sph-stundenplan-tag-card`
- `sph-stundenplan-grid-card`
- `sph-meinunterricht-card`
- `sph-lerngruppen-card`
- `sph-kalender-card`
- `sph-vertretungsplan-card`

## Robustheit und Cache-Verhalten

- Erfolgreiche Daten sollen bei temporären Abruffehlern erhalten bleiben.
- Lokale Einträge werden unabhängig von SPH gespeichert.
- Frontend-Karten vermeiden unnötigen vollständigen Shadow-DOM-Neuaufbau, damit Scrollposition und Dialogzustand stabil bleiben.
- School-Hacks dürfen die ursprünglichen Home-Assistant-State-Objekte nicht verändern.

## Tests

Die vorhandenen Tests decken unter anderem ab:

- A/B-Wochenlogik,
- School-Hack-Profilladen,
- Vertretungsquellen-Priorität,
- internen SPH-Vertretungsadapter,
- Vertretungsplan-Parser,
- JSON-Payload,
- Kursnormalisierung,
- serverseitige Vertretungsanwendung,
- Lovelace-Ressourcenregistrierung.
