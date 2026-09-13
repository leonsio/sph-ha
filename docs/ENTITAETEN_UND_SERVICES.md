# Entitäten, Sensoren und Services

Diese Seite beschreibt die von SPH-HA bereitgestellten Home-Assistant-Entitäten und die integrationsspezifischen Services. Die allgemeine Projektbeschreibung befindet sich in der [README](../README.md).

## Namensschema

Für jeden Integrationseintrag wird aus **Name des Kindes** und **Kürzel des Kindes** ein Suffix gebildet. Aus `Maxim` und `Mk` wird beispielsweise `maxim_mk`.

Die folgenden Namen zeigen die standardmäßig von der Integration verwendeten Entity-IDs. Home Assistant kann Entity-IDs bei Namenskonflikten abweichend vergeben; außerdem können sie vom Benutzer nachträglich umbenannt werden.

In den Beispielen steht `NAME_KUERZEL` für dieses normalisierte Suffix.

## Sensoren

### Stundenplan

#### `sensor.stundenplan_NAME_KUERZEL`

Strukturierter persönlicher Stundenplan.

**Zustand**

- `verfügbar`, wenn Stundenplandaten vorhanden sind
- `unbekannt`, solange noch keine verwendbaren Daten vorliegen

**Wichtige Attribute**

| Attribut | Inhalt |
|---|---|
| `kind` | Name des Kindes |
| `kind_kürzel` | Kürzel des Kindes |
| `klasse` | vom SPH erkannte Klasse |
| `wochenkennung` | aktuelle A-/B-Wochenkennung |
| `wochenbeginn` | Referenzdatum der vom SPH gelieferten Woche |
| `eigener_grundplan` | persönlicher Grundstundenplan ohne Maskierung aktueller freier Tage |
| `eigener_plan` | persönlicher Stundenplan unter Berücksichtigung erkannter freier Tage |
| `tage` | vollständiger SPH-Stundenplan, wenn in den Optionen die vollständige Stundenplan-Ausgabe aktiviert ist; sonst leere Tageslisten |
| `freie_tage` | erkannte schulfreie Datumswerte |
| `freie_tage_kalender` | verwendete Kalenderquelle für schulfreie Tage |

Unterrichtseinträge enthalten unter anderem Wochentag, Fach/Kürzel, aufgelösten Fachnamen, Lehrkraft, Raum, Beginn, Ende, Stundenindex, Dauer und gegebenenfalls A-/B-Kennzeichnungen.

#### `sensor.stundenplan_NAME_KUERZEL_json`

Enthält denselben logischen Stundenplan als kompaktes JSON für ESPHome, Displays und andere externe Verbraucher.

Attribute:

- `json` – kompletter Payload als JSON-String
- `format` – `application/json`
- `bytes` – Größe des JSON-Strings in Bytes

---

### Schulkalender

#### `sensor.schulkalender_NAME_KUERZEL`

Strukturierte Übersicht der aus dem SPH-Schulkalender übernommenen Termine.

**Zustand**

Anzahl der aktuell berücksichtigten Termine.

**Wichtige Attribute**

| Attribut | Inhalt |
|---|---|
| `kind`, `kind_kürzel`, `klasse` | Zuordnung zum Kind |
| `kalenderarten` | aktuell ausgewählte Kalenderarten |
| `termine` | Vorschau der nächsten bzw. relevanten Termine, begrenzt auf 50 Einträge |
| `termine_gesamt` | Gesamtzahl der berücksichtigten Termine |
| `termine_weitere` | Zahl der Termine außerhalb der 50 Einträge der Vorschau |
| `arten` | Anzahl der Termine je Kalenderart |
| `verantwortliche` | Anzahl der Termine je Verantwortlichem |

Ein Termin enthält unter anderem Start, Ende, Ganztagskennzeichnung, Titel, Art, Verantwortlichen, Ort und UID.

#### `sensor.schulkalender_NAME_KUERZEL_json`

Vollständige konfigurierte Schulkalenderdaten als kompaktes JSON. Anders als die Vorschau des normalen Sensors ist die JSON-Ausgabe nicht auf 50 Termine begrenzt.

Attribute: `json`, `format`, `bytes`.

---

### Mein Unterricht

#### `sensor.mein_unterricht_NAME_KUERZEL`

Hausaufgaben und Aufgaben aus **Mein Unterricht**, ergänzt um lokal angelegte Einträge.

**Zustand**

Anzahl der aktuell vorhandenen Aufgaben.

**Wichtige Attribute**

| Attribut | Inhalt |
|---|---|
| `aufgaben` | vollständige Aufgabenliste |
| `anzahl` | Gesamtzahl der Aufgaben |
| `unerledigt` | Zahl der offenen Aufgaben |
| `erledigt` | Zahl der erledigten Aufgaben |
| `faecher` | zusammengefasste Fachübersicht |
| `faecher_gesamt` | Anzahl unterschiedlicher Fächer |
| `faecher_offen` | Anzahl der Fächer mit offenen Aufgaben |

Kursbezeichnungen werden für die Fachübersicht normalisiert; der ursprüngliche Kurs bleibt in den jeweiligen Aufgabendaten erhalten.

#### `sensor.mein_unterricht_NAME_KUERZEL_json`

Derselbe logische Inhalt als kompaktes JSON.

Attribute: `json`, `format`, `bytes`.

---

### Lerngruppen

#### `sensor.lerngruppen_NAME_KUERZEL`

Leistungskontrollen aus den SPH-Lerngruppen sowie lokal ergänzte Termine.

**Zustand**

Anzahl der vorhandenen Leistungskontrollen.

**Wichtige Attribute**

- `kind`
- `kind_kürzel`
- `anzahl`
- `leistungskontrollen`

Leistungskontrollen können unter anderem Datum, Art, Fach/Kurs, Dauer, Schulstunden, Lehrkraft, Quelle und – soweit aus dem Stundenplan ableitbar – konkrete Start-/Endzeiten enthalten.

#### `sensor.lerngruppen_NAME_KUERZEL_json`

Lerngruppendaten als kompaktes JSON.

Attribute: `json`, `format`, `bytes`.

---

### Vertretungsplan

#### `sensor.vertretungsplan_NAME_KUERZEL`

Strukturierter interner SPH-Vertretungsplan.

**Zustand**

Gesamtzahl der Einträge in den aktuell veröffentlichten Plantagen.

**Wichtige Attribute**

| Attribut | Inhalt |
|---|---|
| `tage` | veröffentlichte Plantage mit Einträgen und Hinweisen |
| `heute` | Einträge für heute |
| `morgen` | Einträge für morgen |
| `anzahl_heute`, `anzahl_morgen` | Anzahl der Einträge |
| `entfaelle_heute`, `entfaelle_morgen` | Zahl erkannter Entfälle |
| `hinweise` | zusammengefasste Hinweise der veröffentlichten Tage |
| `aktualisiert` | vom SPH gelieferter Aktualisierungsstand |
| `wird_aktualisiert` | Kennzeichnung eines laufenden Portalupdates |
| `geplante_tage` | Datumswerte der veröffentlichten Plantage |

Ein Vertretungseintrag kann unter anderem Datum, Stunde/Stundenbereich, Klasse, Fach, ursprüngliches Fach, Vertretungslehrkraft, Raum, Vertretungsart, Hinweis und Entfallkennzeichnung enthalten. Zusätzlich wird ein aufgelöster Fachname bereitgestellt.

#### `sensor.vertretungsplan_NAME_KUERZEL_json`

Derselbe Vertretungsplan als kompaktes JSON.

Attribute: `json`, `format`, `bytes`.

## Binärsensoren für Entfälle

### `binary_sensor.erste_stunde_entfaellt_heute_NAME_KUERZEL`

Prüft, ob die in den Integrationsoptionen konfigurierte **Bezugsstunde** heute vollständig als Entfall gemeldet ist.

### `binary_sensor.erste_stunde_entfaellt_morgen_NAME_KUERZEL`

Dieselbe Prüfung für morgen.

Die Bezeichnung enthält aus Kompatibilitätsgründen weiterhin `erste_stunde`, auch wenn als Bezugsstunde beispielsweise Stunde 2 oder 3 gewählt wurde.

**Zustände**

- `on` – die konfigurierte Bezugsstunde fällt aus
- `off` – ein Plan für den Tag liegt vor, aber die Bezugsstunde fällt nicht aus
- `unavailable` – für den betreffenden Tag liegt noch kein veröffentlichter Vertretungsplan vor oder das Modul ist deaktiviert

**Attribute**

- `bezugstag`
- `wochentag`
- `stunde`
- `plan_veröffentlicht`
- `betroffene_eintraege`

## Kalender-Entitäten

Welche Kalender sichtbar sind, hängt von der Option **Gemeinsamen SPH-Kalender verwenden** ab.

### Gemeinsamer Kalender

#### `calendar.sph_NAME_KUERZEL`

Wird verwendet, wenn der gemeinsame SPH-Kalender aktiviert ist. Er führt die aktivierten Quellen für Stundenplan, Schulkalender und Lerngruppen in einer Kalenderansicht zusammen.

Wenn der Schulkalender aktiv ist, können über den gemeinsamen Kalender auch lokale eigene Schulkalendertermine angelegt und wieder gelöscht werden.

### Getrennte Kalender

Wenn der gemeinsame SPH-Kalender deaktiviert ist, werden die jeweiligen Kalender getrennt bereitgestellt:

| Entity | Inhalt |
|---|---|
| `calendar.stundenplan_NAME_KUERZEL` | persönlicher Stundenplan als Kalender |
| `calendar.schulkalender_NAME_KUERZEL` | SPH-Schulkalender und lokale eigene Termine |
| `calendar.lerngruppen_NAME_KUERZEL` | Leistungskontrollen aus Lerngruppen |

Der Stundenplankalender erzeugt ein rollierendes Fenster von zwei Wochen Vergangenheit bis acht Wochen Zukunft. Er berücksichtigt A-/B-Wochen, schulfreie Tage und den internen SPH-Vertretungsplan. Vertretungen ändern vorhandene Unterrichtstermine, statt für dieselbe Stunde einen zusätzlichen unabhängigen Termin anzulegen.

### Bewegliche Ferientage

#### `calendar.bewegliche_ferientage_NAME_KUERZEL`

Wird angelegt, wenn ein Schulamtsbezirk konfiguriert ist. Der Kalender enthält die für das aktuelle hessische Schuljahr veröffentlichten beweglichen Ferientage des ausgewählten Bezirks.

Dieser Kalender bleibt unabhängig von der Einstellung für den gemeinsamen SPH-Kalender separat, da er zusätzlich als technische Quelle für schulfreie Tage des Stundenplans verwendet wird.

## Integrationsspezifische Services

SPH-HA registriert vier eigene Services im Domain-Namensraum `sph`.

### `sph.lerngruppen_termin_hinzufuegen`

Legt einen lokalen Leistungskontrolltermin an. Der Eintrag wird persistent gespeichert und mit den aus SPH geladenen Terminen zusammengeführt.

| Feld | Pflicht | Beschreibung |
|---|---:|---|
| `entity_id` | ja | zugehöriger Lerngruppen-Sensor |
| `datum` | ja | Datum der Leistungskontrolle |
| `art` | ja | z. B. `Arbeit` oder `Lernkontrolle` |
| `kurs` | ja | Fach/Kurs |
| `dauer_minuten` | nein | Dauer in Minuten, 1–1440 |
| `stunden` | nein | Schulstunden, z. B. `3,4` oder `3-4` |
| `lehrkraft` | nein | Lehrkraft |

Beispiel:

```yaml
action: sph.lerngruppen_termin_hinzufuegen
data:
  entity_id: sensor.lerngruppen_maxim_mk
  datum: "2026-09-30"
  art: Lernkontrolle
  kurs: Politik und Wirtschaft
  dauer_minuten: 30
  stunden: "3,4"
```

### `sph.lerngruppen_termin_loeschen`

Löscht ausschließlich einen lokal angelegten Leistungskontrolltermin. Aus SPH importierte Termine sind schreibgeschützt.

Pflichtfelder:

- `entity_id` – zugehöriger Lerngruppen-Sensor
- `id` – ID des lokal angelegten Termins

### `sph.meinunterricht_hausaufgabe_hinzufuegen`

Legt eine lokale Hausaufgabe an. Lokale Hausaufgaben bleiben unabhängig von SPH-Aktualisierungen gespeichert und werden sieben Tage nach dem eingetragenen Datum automatisch bereinigt.

| Feld | Pflicht | Beschreibung |
|---|---:|---|
| `entity_id` | ja | zugehöriger Mein-Unterricht-Sensor |
| `datum` | ja | Datum |
| `fach` | ja | Fach |
| `kurs` | nein | ursprüngliche/konkrete Kursbezeichnung |
| `thema` | nein | Thema |
| `aufgabe` | ja | Aufgabentext |
| `lehrer` | nein | Lehrkraft |
| `erledigt` | nein | Erledigt-Status, Standard `false` |

Beispiel:

```yaml
action: sph.meinunterricht_hausaufgabe_hinzufuegen
data:
  entity_id: sensor.mein_unterricht_maxim_mk
  datum: "2026-09-15"
  fach: Englisch
  thema: Unit 2
  aufgabe: Vokabeln lernen
  erledigt: false
```

### `sph.meinunterricht_hausaufgabe_loeschen`

Löscht ausschließlich eine lokal angelegte Hausaufgabe. Aus SPH importierte Aufgaben können nicht über diesen Service gelöscht werden.

Pflichtfelder:

- `entity_id` – zugehöriger Mein-Unterricht-Sensor
- `id` – ID der lokal angelegten Hausaufgabe

## JSON-Sensoren

Alle `*_json`-Sensoren sind vor allem für externe Verbraucher gedacht, die mit einem einzelnen JSON-String einfacher arbeiten können als mit verschachtelten Home-Assistant-Attributen.

Sie enthalten immer:

```text
json
format: application/json
bytes
```

Der logische Inhalt entspricht jeweils dem strukturierten Sensor des gleichen Moduls.

## Weitere technische Dokumentation

- [Architektur](ARCHITEKTUR.md)
- [Lovelace-Karten](lovelace/README.md)
- [School Hacks](lovelace/school-hacks.md)
- [Schulspezifische Profile](schools/README.md)
