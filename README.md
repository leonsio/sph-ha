# Schulportal Hessen für Home Assistant

Home-Assistant-Custom-Integration für Daten aus dem **Schulportal Hessen (SPH)**.

Die Installation erfolgt einmalig als Integration **Schulportal Hessen**. Sie umfasst aktuell die Module **Stundenplan**, **Schulkalender**, **Mein Unterricht** und **Lerngruppen**.

## Installation über HACS

In HACS das Repository hinzufügen:

```text
https://github.com/leonsio/sph-ha
```

Kategorie: **Integration**.

Anschließend unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach **Schulportal Hessen** suchen.

## Einrichtung

Für jedes Kind wird ein eigener Eintrag der Integration angelegt. Benötigt werden:

- Schulnummer
- SPH-Benutzername
- SPH-Passwort
- Name des Kindes
- Kürzel des Kindes
- Aktualisierungsintervall

Das Standard-Aktualisierungsintervall beträgt **60 Minuten** und kann nach der Einrichtung geändert werden. Auch Zugangsdaten, Schulnummer, Name und Kürzel können über die Konfiguration angepasst werden.

Die Zugangsdaten werden von den Modulen gemeinsam verwendet. Mehrere Kinder können als separate Einträge eingerichtet werden.

## Sensoren

Für ein Kind mit Name `Maxim` und Kürzel `Mk` entstehen beispielsweise:

```text
sensor.stundenplan_maxim_mk
sensor.stundenplan_maxim_mk_json
sensor.schulkalender_maxim_mk
sensor.schulkalender_maxim_mk_json
sensor.mein_unterricht_maxim_mk
sensor.mein_unterricht_maxim_mk_json
sensor.lerngruppen_maxim_mk
sensor.lerngruppen_maxim_mk_json
calendar.schulkalender_maxim_mk
calendar.lerngruppen_maxim_mk
```

### Stundenplan

Der Stundenplan enthält unter anderem persönliche Stunden, Fach, Lehrkraft, Raum, Uhrzeit und Badge. Badges wie `A` oder `B` kennzeichnen wochenabhängige Stunden.

### Schulkalender

Der Kalender verwendet automatisch das aktuelle **hessische Schuljahr** und bevorzugt den CSV-Export des Schulportals. iCal wird als Fallback verwendet. Die anzuzeigenden Kalenderarten können in den Integrationseinstellungen festgelegt werden.

### Mein Unterricht

Das Modul stellt aktuelle Aufgaben aus „Mein Unterricht“ mit Kurs, Thema, Aufgabe und Erledigt-Status bereit.

### Lerngruppen

Das Modul liest die **Leistungskontrollen** aus `lerngruppen.php`. Der Kursname wird ohne die technische Kennung in Klammern gespeichert. Die Lehrkraft wird über die zugehörige Lerngruppe ermittelt.

Für Kalendertermine werden die angegebenen Schulstunden mit dem persönlichen Stundenplan abgeglichen. Beginn und Ende richten sich nach der ersten bzw. letzten angegebenen Schulstunde. Art und angegebene Prüfungsdauer bleiben als eigene Felder erhalten.

Beispiel:

```text
Arbeit: Englisch 7n
```

Gespeichert werden unter anderem:

- `datum`
- `kurs`
- `art`
- `stunden`
- `stunden_text`
- `dauer_minuten`
- `lehrkraft`
- `lehrkraft_kürzel`
- `start`
- `end`
- `summary`
- `uid`

## Lovelace-Karten

Stundenplan:

```yaml
type: custom:sph-stundenplan-card
entity: sensor.stundenplan_maxim_mk
title: Stundenplan Maxim
```

Tagesansicht:

```yaml
type: custom:sph-stundenplan-tag-card
entity: sensor.stundenplan_maxim_mk
title: Heute – Maxim
```

Die Karten werden von der Integration automatisch als Lovelace-Ressourcen registriert. Für Home Assistant 2026.2+ ist keine manuelle `/local/...`-Ressource erforderlich.

## Verhalten bei Verbindungsproblemen

Bei einem fehlgeschlagenen Abruf bleiben die zuletzt erfolgreich geladenen Daten erhalten, soweit das jeweilige Modul bereits Daten geladen hat. Sobald das Schulportal wieder erreichbar ist, werden die Daten beim nächsten erfolgreichen Aktualisierungsversuch aktualisiert.

## Hinweis

Dieses Projekt ist ein unabhängiges Community-Projekt und steht nicht in offizieller Verbindung mit dem Schulportal Hessen.

Weitere Informationen zur Quelltextstruktur befinden sich unter [`docs/ARCHITEKTUR.md`](docs/ARCHITEKTUR.md).
