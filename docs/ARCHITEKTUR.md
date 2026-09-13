# Schulportal Hessen – Architektur

Diese Datei beschreibt die aktuelle technische Struktur von SPH-HA.

## Grundprinzipien

- Eine Home-Assistant-Integration bedient mehrere fachlich getrennte Module.
- Alle SPH-Module teilen sich Authentifizierung und Session.
- Fachlogik bleibt im jeweiligen Modul.
- Modulübergreifende Normalisierung liegt unter `api/`.
- Schulspezifische Datenanpassungen werden über serverseitige **Schul-Profile** gekapselt.
- Jede Schule besitzt ein eigenes dynamisch entdecktes Profilpaket.
- Schulspezifische Darstellungsregeln liegen im `frontend/`-Unterordner des jeweiligen Profils.
- Sensoren, JSON-Sensoren und native Kalender verwenden dieselben serverseitig profilierten Datenregeln.
- Datumsbezogene Vertretungen werden nur in datumsbewussten Kontexten auf einen Stundenplaneintrag angewandt.

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
├── school_profiles/
│   ├── __init__.py
│   ├── base.py
│   └── kfg/
│       ├── __init__.py
│       ├── profile.py
│       └── frontend/
│           └── lovelace.js
├── module/
│   ├── stundenplan/
│   ├── kalender/
│   ├── meinunterricht/
│   ├── lerngruppen/
│   └── vertretung/
├── static/
│   ├── school-profile.js
│   ├── substitution-adapter.js
│   ├── sph-stundenplan-card.js
│   ├── sph-stundenplan-tag-card.js
│   ├── sph-stundenplan-grid-card.js
│   ├── sph-meinunterricht-card.js
│   ├── sph-lerngruppen-card.js
│   ├── sph-kalender-card.js
│   └── sph-vertretungsplan-card.js
└── translations/
```

## Integrationsebene

### `__init__.py`

Verantwortlich für:

- Aufbau der gemeinsamen `SphAuthClient`-Instanz,
- Initialisierung der Modul-Coordinatoren,
- Modulaktivierung,
- Entity-ID-Verwaltung,
- automatische Lovelace-Ressourcenregistrierung,
- dynamische Registrierung der Frontend-Verzeichnisse gefundener Schul-Profile,
- Beobachtung profil-eigener Home-Assistant-Entities,
- Start und Stop integrationsweiter Hilfslogik.

Das pro Kind konfigurierte Schul-Profil wird über `get_school_profile(entry)` geladen und im Laufzeitkontext des Integrationseintrags gespeichert.

Wenn ein Profil `state_entities` definiert, beobachtet die Integration diese Entities. Änderungen lösen eine erneute Veröffentlichung der betroffenen SPH-Daten aus.

### `sensor.py`

Dispatcher für die Sensoren der Module. Die Module liefern strukturierte Sensoren und – soweit vorgesehen – JSON-Sensoren.

### `binary_sensor.py`

Dispatcher für die Vertretungsplan-Binärsensoren.

### `calendar.py`

Erzeugt beziehungsweise kombiniert native Home-Assistant-Kalender:

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

`api/subjects.py` enthält schulübergreifende Fach-/Kursnormalisierung. Bekannte Kürzel und Schreibvarianten werden zentral aufgelöst.

Schulspezifische Ausnahmen gehören dagegen in das jeweilige Schul-Profil.

## Schul-Profile

### Dynamische Discovery

`school_profiles/__init__.py` durchsucht direkte Unterordner von `school_profiles/`. Ein Profilpaket wird erkannt, wenn es eine `profile.py` enthält.

Beispiel:

```text
school_profiles/example/
├── __init__.py
├── profile.py
└── frontend/
    └── lovelace.js
```

`profile.py` exportiert ein `PROFILE`-Objekt auf Basis von `SchoolProfile`. Die Profil-ID muss dem Ordnernamen entsprechen.

Die Registry enthält keine statische Liste konkreter Schulen. Neue Profilpakete werden automatisch gefunden und aus ihren eigenen Metadaten in Config-Flow und Laufzeit eingebunden.

Der Standardwert ist:

```text
none
```

### Profilmetadaten

Jedes Profil liefert selbst:

- `id`
- `name`
- `description`
- `frontend_module`

`school_profile_options()` erzeugt die Auswahl für Config-Flow und Options-Flow aus `profile.config_option()`.

`school_profile_metadata()` stellt die Metadaten generischen Komponenten zur Verfügung.

### Serverprofil

`school_profiles/base.py` definiert `SchoolProfile` und die gemeinsamen Hooks für:

- Lehrerauflösung,
- Fachauflösung,
- Vertretungsbezeichnungen,
- rekursive Daten-Transformation,
- Stundenplan-Payloads,
- Schulkalender-Payloads,
- Mein-Unterricht-Payloads,
- Lerngruppen-Payloads,
- Vertretungsplan-Payloads,
- native Kalenderdatensätze,
- datumsbezogene Stundenplananzeigen.

Die Basisklasse erhält bereits vom Core ausgewählte und normalisierte Daten. Ein Profil entscheidet nicht selbst zwischen persönlichem und vollständigem Stundenplan.

Bei vollständiger Stundenplan-Ausgabe werden `eigener_plan` und `tage` jeweils profiliert. `eigener_grundplan` wird nicht als Profilquelle verwendet und nicht durch die Profiltransformation umgeschrieben.

### Profil-eigene Python-Dateien

Zusätzliche Hilfsdateien können im jeweiligen Profilordner liegen und von `profile.py` relativ importiert werden. Nur `profile.py` dient als Discovery-Einstiegspunkt; dadurch werden beliebige Dateien nicht automatisch ausgeführt.

### Frontendprofil

`static/school-profile.js` enthält die gemeinsame Darstellungsschicht. Profil-spezifische Frontend-Dateien liegen innerhalb des jeweiligen Profilpakets:

```text
school_profiles/<profil>/frontend/
```

Der Profilordner wird von `school_profile_frontend_paths()` ermittelt. `async_setup()` registriert ausschließlich diesen `frontend/`-Ordner als statischen Pfad:

```text
/api/sph/school_profiles/<profil>/frontend/
```

Python-Dateien des Profils werden dadurch nicht als statische Ressourcen veröffentlicht.

Das Frontend erkennt das aktive Profil über das Sensorattribut:

```yaml
school_profile: <profil>
```

Ein Karten-Override kann über `school-profile` gesetzt werden.

## Modulaktivierung

Aktuell existieren fünf Module:

- Stundenplan
- Schulkalender
- Mein Unterricht
- Lerngruppen
- Vertretungsplan

Ein deaktiviertes Modul soll keine unnötigen SPH-Abrufe durchführen. Nicht benötigte Entities werden abhängig vom Modul entfernt oder nicht angelegt.

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
- `school_profile`

Der JSON-Sensor enthält denselben logischen Payload im Attribut `json`.

### A/B-Wochen

`wochenbeginn` verankert die gemeldete A/B-Woche. Datumsbezogene Ansichten schreiben daraus die Wochenkennung fort.

### Freie Tage

Berücksichtigt werden insbesondere:

- `calendar.deutschland_he`, falls vorhanden,
- bewegliche Ferientage des konfigurierten Schulamtsbezirks.

Freie Tage wirken auf Stundenplan-Sensoren, Lovelace-Auswahl und den nativen Stundenplan-Kalender.

### Stundenplan-Kalender

`module/stundenplan/calendar.py` erzeugt dynamisch Unterrichtstermine in einem rollierenden Zeitfenster. Der Kalender erhält den Vertretungs-Coordinator und wendet passende SPH-Vertretungen auf konkrete Unterrichtstermine an.

Vor der Ausgabe können serverseitige Profil-Hooks Fach-, Lehrer- und Vertretungsbezeichnungen aufbereiten.

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

Das aktive Schul-Profil wird vor Veröffentlichung auf den Payload angewandt. Dadurch können beispielsweise schulspezifische `art_lang`-Bezeichnungen oder Lehrernamen serverseitig aufbereitet werden.

### Binärsensoren

`module/vertretung/binary_sensor.py` stellt Entfall-Sensoren für heute und morgen bereit. Die geprüfte Bezugsstunde ist konfigurierbar. Ist für einen Tag noch kein Plan veröffentlicht, bleibt die Entity `unavailable`.

### Anwendung auf Stunden

`module/vertretung/apply.py` ordnet einen Vertretungseintrag einer regulären Stundenplanstunde zu.

Matching-Kriterien umfassen:

- Datum
- Klasse
- Fach/Originalfach
- Schulstunde beziehungsweise Stundenbereich

Angewendet werden unter anderem:

- Entfall,
- Vertretungsart,
- neues und ursprüngliches Fach,
- Vertretungslehrkraft,
- Raumänderung.

## Frontend-Vertretungsadapter

`static/substitution-adapter.js` verbindet Stundenplankarten mit Vertretungsdaten.

Reihenfolge pro Stunde:

1. explizit in der Karte gesetzte Quelle (`vertretungsplan_sensor`, `vertretungsplan`, `substitution_sensor`),
2. bevorzugte Quelle des aktiven Schul-Profils,
3. interner SPH-Vertretungsplan als Fallback, wenn die Profilquelle keinen Treffer liefert.

Eine explizit gesetzte Quelle bleibt autoritativ.

## Mein Unterricht

Quelle: `meinunterricht.php`.

Kursnamen werden auf gemeinsame Fachnamen normalisiert. Klassenbestandteile werden entfernt, bekannte Kürzel ausgeschrieben und der ursprüngliche Kurswert bleibt erhalten.

Normaler Sensor und JSON-Sensor liefern zusätzlich:

- `faecher`
- `faecher_gesamt`
- `faecher_offen`

Das aktive Schul-Profil wird auf den veröffentlichten Payload angewandt.

## Lerngruppen

Quelle: `lerngruppen.php`.

Leistungskontrollen werden mit Lerngruppen und persönlichem Stundenplan verknüpft. Schulstunden werden nach Möglichkeit in konkrete Uhrzeiten umgerechnet. Lokale Termine werden persistent gespeichert und mit SPH-Terminen zusammengeführt.

Das aktive Schul-Profil wird auf Sensor-, JSON- und Kalenderdaten angewandt.

## Schulkalender

Der Schulkalender bevorzugt CSV und verwendet iCal als Fallback. Daten werden auf das relevante hessische Schuljahr begrenzt. Optional können Kalenderarten gefiltert werden. Lokale eigene Kalendertermine werden separat gespeichert.

Profil-Hooks können einzelne Kalenderdatensätze sowie strukturierte Sensor-/JSON-Payloads aufbereiten.

## Lovelace-Ressourcen

Die Integration registriert ihre allgemeinen JavaScript-Ressourcen selbst und verwendet versionierte URLs. Profil-eigene Frontend-Verzeichnisse werden zusätzlich dynamisch aus den entdeckten Profilpaketen registriert.

Aktuelle Karten:

- `sph-stundenplan-card`
- `sph-stundenplan-tag-card`
- `sph-stundenplan-grid-card`
- `sph-meinunterricht-card`
- `sph-lerngruppen-card`
- `sph-kalender-card`
- `sph-vertretungsplan-card`

## Robustheit

- Erfolgreiche Daten bleiben bei temporären Abruffehlern soweit möglich erhalten.
- Lokale Einträge werden unabhängig von SPH gespeichert.
- Profile sollen unbekannte Werte unverändert lassen, wenn eine optionale schulspezifische Datenquelle fehlt.
- Fehlerhafte Profilpakete werden bei der Discovery isoliert und nicht in der Auswahl angeboten.
- Frontend-Karten verändern keine Home-Assistant-State-Objekte.

## Tests

Die Tests decken unter anderem ab:

- dynamische Profil-Discovery,
- profil-eigene Metadaten und Config-Optionen,
- Frontend-Pfade aus Profilpaketen,
- A/B-Wochenlogik,
- serverseitige Profiltransformationen,
- Vertretungsquellen-Priorität,
- internen SPH-Vertretungsadapter,
- Vertretungsplan-Normalisierung und JSON-Payload,
- Kursnormalisierung,
- serverseitige Vertretungsanwendung,
- Lovelace-Ressourcenregistrierung.
