# Schulportal Hessen

Home-Assistant-Custom-Integration für Daten aus dem **Schulportal Hessen (SPH)**.

Aktueller Stand: **0.6.0**.

## Module

Für jedes Kind können folgende Module einzeln aktiviert werden:

- Stundenplan
- Schulkalender
- Mein Unterricht
- Lerngruppen
- Vertretungsplan

Zu den Modulen gehören normale Sensoren, JSON-Sensoren und – je nach Funktion – native Home-Assistant-Kalender, Binärsensoren und Lovelace-Karten.

## Installation

Über HACS als **Integration** installieren:

```text
https://github.com/leonsio/sph-ha
```

Danach unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach **Schulportal Hessen** suchen.

## Wichtige Funktionen

- persönlicher Stundenplan mit A/B-Wochen
- freie Tage und bewegliche Ferientage
- SPH-Schulkalender
- Hausaufgaben aus „Mein Unterricht“ inklusive Kurs-/Fachnormalisierung
- Leistungskontrollen aus Lerngruppen
- Vertretungsplan mit Entfall-, Raum-, Lehrer- und Fachänderungen
- JSON-Sensoren für externe Clients
- automatische Lovelace-Ressourcenregistrierung
- zusammengefasster oder getrennter SPH-Kalender
- lokale Hausaufgaben, Leistungskontrollen und eigene Kalendertermine
- pro Kind auswählbare Schul-Profile

## Schul-Profile

Ab 0.6.0 können schulspezifische Besonderheiten direkt im Integrationseintrag des Kindes über **Schul-Profil** ausgewählt werden.

Ein Profil kann Werte serverseitig in Sensoren, JSON und Kalendern aufbereiten und zusätzlich notwendige Darstellungsregeln für die SPH-Lovelace-Karten bereitstellen.

Das derzeit vorhandene Profil `kfg` ist für das **Kaiserin-Friedrich-Gymnasium Bad Homburg** vorgesehen.

Die Karten erkennen das Profil automatisch. Ein zusätzlicher Kartenparameter ist normalerweise nicht erforderlich.

Der alte Parameter `school-hacks: kfg` bleibt in 0.6.0 als Legacy-Alias erhalten.

## Beispiel-Entities

```text
sensor.stundenplan_maxim_mk
sensor.stundenplan_maxim_mk_json
sensor.schulkalender_maxim_mk
sensor.mein_unterricht_maxim_mk
sensor.lerngruppen_maxim_mk
sensor.vertretungsplan_maxim_mk
sensor.vertretungsplan_maxim_mk_json
calendar.stundenplan_maxim_mk
calendar.schulkalender_maxim_mk
```

## Dokumentation

Die vollständige Dokumentation befindet sich in der Repository-README und unter `docs/`.

Für Entwickler eigener Profile: `docs/SCHOOL_PROFILES_DEVELOPMENT.md`.

Dieses Projekt ist ein unabhängiges Community-Projekt und steht nicht in offizieller Verbindung mit dem Schulportal Hessen.
