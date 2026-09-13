# Schulportal Hessen

Home-Assistant-Custom-Integration für Daten aus dem **Schulportal Hessen (SPH)**.

Aktueller Stand: **0.5.0**.

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

Seit 0.5.0 werden interne SPH-Vertretungsdaten auch in den allgemeinen Stundenplankarten und bei der Generierung des nativen Stundenplan-Kalenders berücksichtigt.

## School Hacks

Schulspezifische Anpassungen werden über normale SPH-Karten aktiviert:

```yaml
type: custom:sph-stundenplan-grid-card
entity: sensor.stundenplan_maxim_mk
school-hacks: kfg
```

Das derzeit vorhandene Profil `kfg` ist für das **Kaiserin-Friedrich-Gymnasium Bad Homburg** vorgesehen. Weitere Schulen können eigene Profile erhalten, ohne separate Kartenkopien anzulegen.

Bei aktivem School Hack wird die schulische Vertretungsquelle bevorzugt; der interne SPH-Vertretungsplan kann als Fallback dienen. Ohne School Hack wird der interne SPH-Vertretungsplan direkt verwendet.

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

Dieses Projekt ist ein unabhängiges Community-Projekt und steht nicht in offizieller Verbindung mit dem Schulportal Hessen.