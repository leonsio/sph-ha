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

Die Module **Stundenplan**, **Schulkalender**, **Mein Unterricht** und **Lerngruppen** können in der Konfiguration einzeln aktiviert oder deaktiviert werden. Für den Stundenplan kann zusätzlich die gewünschte Ausgabe gewählt werden. Beim Schulkalender ist ein optionaler Filter nach Kalenderarten möglich; ein leerer Filter übernimmt alle Einträge.

Für bewegliche Ferientage kann ein Schulamtsbezirk ausgewählt werden. Die Integration berücksichtigt dabei das jeweilige Schuljahr und stellt die Termine zusätzlich über einen eigenen Kalender bereit.

Die Zugangsdaten werden von den Modulen gemeinsam verwendet. Mehrere Kinder können als separate Einträge eingerichtet werden.

## Sensoren und Kalender

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
calendar.stundenplan_maxim_mk
calendar.schulkalender_maxim_mk
calendar.lerngruppen_maxim_mk
calendar.bewegliche_ferientage_maxim_mk
```

### Stundenplan

Der Stundenplan enthält unter anderem persönliche Stunden, Fach, Lehrkraft, Raum, Uhrzeit und Badge. Badges wie `A` oder `B` kennzeichnen wochenabhängige Stunden.

Der persönliche Plan bleibt im Block `eigener_plan` erhalten. Abhängig von der Konfiguration kann der vollständige SPH-Stundenplan zusätzlich ausgegeben werden; die bisherige Sensorstruktur bleibt aus Kompatibilitätsgründen erhalten.

Zusätzlich wird ein rollierender Stundenplan-Kalender für zwei Wochen rückwirkend und acht Wochen im Voraus erzeugt. A/B-Wochen werden automatisch fortgeschrieben.

#### Freie Tage

Wenn `calendar.deutschland_he` vorhanden ist, werden Tage mit Kalendereinträgen als schulfrei behandelt. An diesen Tagen werden Unterrichtsstunden und der Marker `Schulwoche A/B` im Stundenplan-Kalender unterdrückt. Die freien Tage werden ebenfalls bei der Sensor-Ausgabe berücksichtigt.

Zusätzlich können die **beweglichen Ferientage** des ausgewählten hessischen Schulamtsbezirks berücksichtigt werden. Die Daten werden nach Schuljahr gefiltert, lokal zwischengespeichert und höchstens einmal täglich aus der Quelle aktualisiert. Bei einem fehlgeschlagenen Abruf bleiben die zuletzt erfolgreich gespeicherten Daten erhalten.

### Schulkalender

Der Kalender verwendet automatisch das aktuelle **hessische Schuljahr** und bevorzugt den CSV-Export des Schulportals. iCal wird als Fallback verwendet. Die anzuzeigenden Kalenderarten können in den Integrationseinstellungen festgelegt werden. Ist das Feld für Kalenderarten leer, werden alle Arten übernommen.

### Mein Unterricht

Das Modul stellt aktuelle Hausaufgaben aus **„Mein Unterricht“** bereit. Zu den Daten gehören unter anderem:

- Datum und Wochentag
- Fach/Kurs
- Thema
- Aufgabe
- Lehrkraft
- Erledigt-Status
- Quelle (`sph` oder `manuell`)

Fehlende Hausaufgaben können lokal ergänzt werden, wenn sie beispielsweise vom Lehrer nicht im Schulportal eingetragen wurden. Diese Einträge werden persistent in Home Assistant gespeichert und bei SPH-Aktualisierungen nicht überschrieben.

Manuelle Hausaufgaben werden **eine Woche nach ihrem Aufgabendatum automatisch gelöscht**. Sie können vorher auch direkt über die Lovelace-Karte entfernt werden. SPH-Einträge bleiben schreibgeschützt.

Intern verwendet die Funktion die Home-Assistant-Dienste:

```text
sph.meinunterricht_hausaufgabe_hinzufuegen
sph.meinunterricht_hausaufgabe_loeschen
```

### Lerngruppen

Das Modul liest die **Leistungskontrollen** aus `lerngruppen.php`. Der Kursname wird ohne die technische Kennung in Klammern gespeichert. Wenn der Kursname die Klasse des Kindes enthält, wird diese für die kompakte Darstellung entfernt. Die Lehrkraft wird über die zugehörige Lerngruppe ermittelt.

Für Kalendertermine werden die angegebenen Schulstunden mit dem persönlichen Stundenplan abgeglichen. Beginn und Ende richten sich nach der ersten bzw. letzten angegebenen Schulstunde. Art und angegebene Prüfungsdauer bleiben als eigene Felder erhalten.

Beispiel:

```text
Arbeit: Englisch (60 Min)
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
- `quelle` (`sph` oder `manuell`)

Manuell ergänzte Leistungskontrollen werden persistent in Home Assistant gespeichert und bei SPH-Aktualisierungen nicht überschrieben. Sensor und Kalender enthalten immer die zusammengeführten Daten. Wenn später ein gleichartiger SPH-Termin mit gleichem Datum, Art, Kurs und Stunden vorhanden ist, hat der SPH-Eintrag in der Anzeige Vorrang; der lokale Eintrag bleibt gespeichert.

## Lovelace-Karten

### Stundenplan

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

### Mein Unterricht / Hausaufgaben

```yaml
type: custom:sph-meinunterricht-card
entity: sensor.mein_unterricht_maxim_mk
title: Hausaufgaben Maxim
```

Die Karte zeigt alle Hausaufgaben tabellarisch mit Datum, Fach, Thema, Aufgabe, Lehrkraft, Status und Quelle. Über **+ Hausaufgabe hinzufügen** können lokale Aufgaben ergänzt werden. Nur manuell hinzugefügte Aufgaben können über die Tabelle gelöscht werden.

Die Karte berücksichtigt die bei Custom Cards relevante Shadow-DOM-Problematik: Unabhängige Home-Assistant-State-Updates führen nicht zu einem vollständigen Neuaufbau des Shadow DOM. Bei einem tatsächlichen Update des Mein-Unterricht-Sensors werden horizontale Scrollposition, geöffneter Dialog, Formularwerte und Fokus wiederhergestellt. Dadurch bleiben horizontales Scrollen und der Eingabedialog stabil.

### Lerngruppen / Leistungskontrollen

```yaml
type: custom:sph-lerngruppen-card
entity: sensor.lerngruppen_maxim_mk
title: Leistungskontrollen Maxim
```

Die Lerngruppen-Karte zeigt alle Termine tabellarisch. Über **+ Termin hinzufügen** können lokale Termine mit Datum, Art, Fach/Kurs, Dauer, Schulstunden und optionaler Lehrkraft ergänzt werden. Manuelle Einträge können direkt in der Tabelle wieder gelöscht werden. Aus dem Schulportal geladene Termine sind schreibgeschützt und können über die Karte nicht gelöscht werden.

Intern verwendet die Karte die Home-Assistant-Dienste:

```text
sph.lerngruppen_termin_hinzufuegen
sph.lerngruppen_termin_loeschen
```

Auch die Lerngruppen-Karte erhält beim Rendern Scrollposition, Dialogzustand, Formularwerte und Fokus, damit Home-Assistant-Updates den Dialog nicht schließen und die Tabelle nicht nach links zurückspringen lassen.

Die Karten werden von der Integration automatisch als Lovelace-Ressourcen registriert. Für Home Assistant 2026.2+ ist keine manuelle `/local/...`-Ressource erforderlich.

## Verhalten bei Verbindungsproblemen

Bei einem fehlgeschlagenen Abruf bleiben die zuletzt erfolgreich geladenen Daten erhalten, soweit das jeweilige Modul bereits Daten geladen hat. Lokal gespeicherte Lerngruppen-Termine und Hausaufgaben bleiben unabhängig von der Erreichbarkeit des Schulportals erhalten. Sobald das Schulportal wieder erreichbar ist, werden die Daten beim nächsten erfolgreichen Aktualisierungsversuch aktualisiert und erneut mit den lokalen Daten zusammengeführt.

Auch die zwischengespeicherten beweglichen Ferientage werden bei einem fehlgeschlagenen Abruf nicht durch leere Daten ersetzt.

## Hinweis

Dieses Projekt ist ein unabhängiges Community-Projekt und steht nicht in offizieller Verbindung mit dem Schulportal Hessen.

Weitere Informationen zur Quelltextstruktur befinden sich unter [`docs/ARCHITEKTUR.md`](docs/ARCHITEKTUR.md).
