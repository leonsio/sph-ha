# Schul-Profile entwickeln

Diese Dokumentation beschreibt die aktuelle Entwickler-API für **Schul-Profile** in SPH-HA.

Schul-Profile sind kleine, pro Kind auswählbare Erweiterungen für Besonderheiten einer Schule. Sie dürfen Werte aus SPH schulspezifisch aufbereiten, ohne die allgemeine SPH-Logik oder die öffentlichen Sensorstrukturen für alle Schulen zu verändern.

## Ziele

Ein Schul-Profil kann unter anderem:

- Lehrerkürzel in Namen auflösen,
- schulspezifische Fachbezeichnungen anpassen,
- Vertretungsarten anders benennen,
- Werte in Sensor- und JSON-Ausgaben aufbereiten,
- Werte in nativen Home-Assistant-Kalendern aufbereiten,
- zusätzliche, ausschließlich für dieses Profil benötigte HA-Entities beobachten,
- UI-spezifische Regeln für die mitgelieferten Lovelace-Karten definieren.

Ein Schul-Profil soll **nicht**:

- die vom Benutzer konfigurierte Stundenplanquelle ändern,
- `eigener_grundplan` als Ersatz für den persönlichen Stundenplan verwenden,
- allgemeine SPH-Funktionen duplizieren,
- neue schulspezifische Sensorvarianten erzeugen,
- bestehende Sensor-/JSON-Strukturen unnötig verändern.

Grundsatz: **Was schulübergreifend funktioniert, gehört in den Core. Nur echte Abweichungen gehören in ein Schul-Profil.**

---

## Architektur

Die Verarbeitung ist in zwei Ebenen getrennt:

```text
SPH
 │
 ▼
Parser / Coordinator
 │
 ▼
allgemeine Normalisierung
 │
 ▼
konfigurierte Ausgabe des Kindes
 │
 ▼
serverseitiges Schul-Profil (Python)
 │
 ├── Sensoren
 ├── JSON-Sensoren
 ├── native Kalender
 └── weitere serverseitige Verbraucher

Lovelace
 │
 ▼
optionales Präsentationsprofil (JavaScript)
```

Das Python-Profil ist für **Daten** zuständig. Das JavaScript-Profil enthält nur Regeln, die tatsächlich Darstellung oder zeitabhängige UI-Auswahl betreffen.

Ein Lehrerkürzel, das schulspezifisch aufgelöst werden muss, gehört daher in das Python-Profil. Ein ausgeblendetes A/B-Badge oder eine zusätzliche Grid-Überschrift gehört in das Frontend-Profil.

---

## Konfiguration pro Kind

Der Config-Entry enthält:

```text
school_profile
```

Standardwert:

```text
none
```

Beispiel:

```text
kfg
```

Die Auswahl erfolgt bei der Einrichtung und in den Optionen pro Kind. Das ausgewählte Profil wird in veröffentlichten Payloads zusätzlich als Metadatum ausgegeben:

```yaml
school_profile: kfg
```

Dieses Feld ist additiv. Bestehende Schlüssel und Verschachtelungen bleiben erhalten.

---

## Verzeichnisstruktur

Serverseitige Profile:

```text
custom_components/sph/school_profiles/
├── __init__.py
├── base.py
└── kfg.py
```

Frontend-Profile:

```text
custom_components/sph/static/
├── school-profile.js
└── school-profiles/
    └── kfg.js
```

Schuldokumentation:

```text
docs/schools/
└── kfg/
    └── README.md
```

---

# Python-API

Die Basisklasse befindet sich in:

```python
custom_components/sph/school_profiles/base.py
```

Neue Profile erben von:

```python
from .base import SchoolProfile
```

Minimalbeispiel:

```python
class ExampleProfile(SchoolProfile):
    id = "example"
    name = "Beispielschule"
```

Anschließend wird das Profil in `school_profiles/__init__.py` registriert.

---

## Grundlegende Eigenschaften

### `id`

Technischer Profilname. Der Wert wird in Konfiguration, Payloads und Frontend verwendet.

```python
id = "example"
```

Empfohlen sind Kleinbuchstaben, Ziffern, `-` und `_` ohne Leerzeichen.

### `name`

Anzeigename im Config-Flow.

```python
name = "Beispiel-Gymnasium"
```

### `subject_names`

Optionale exakte Fachnamens-Zuordnungen.

```python
subject_names = {
    "PoWi": "Politik und Wirtschaft",
    "Reli": "Religion",
}
```

Die Zuordnung erfolgt case-insensitiv über `resolve_subject()`.

Allgemeine Fachnormalisierung, die für mehrere Schulen gilt, gehört in `api/subjects.py` und nicht in ein Schul-Profil.

### `substitution_labels`

Schulspezifische Bezeichnungen für Vertretungsarten.

```python
substitution_labels = {
    "Vertr": "Vertretung",
    "Entf": "Entfall",
}
```

Der Rohcode `art` bleibt erhalten. Die lesbare Bezeichnung wird über `art_lang` beziehungsweise datumsbezogene Anzeigen bereitgestellt.

### `description_teacher_labels`

Kennzeichnet Zeilen in mehrzeiligen Beschreibungen, deren Wert als Lehrerwert behandelt werden darf.

```python
description_teacher_labels = (
    "lehrer",
    "lehrkraft",
)
```

Beispiel:

```text
Lehrkraft: FRA
Raum: 123
```

Nur die Zeile `Lehrkraft:` wird dabei über `resolve_teacher()` verarbeitet.

### `teacher_fields`

Menge der Dictionary-Felder, die `transform_data()` automatisch als Lehrerwerte behandelt.

Standard:

```text
teacher
lehrer
lehrkraft
vertreter
lehrer_nach
verantwortlich
```

Ein Profil kann `teacher_fields` überschreiben, wenn seine Daten eine andere Semantik verwenden.

### `subject_fields`

Menge der Dictionary-Felder, die automatisch über `resolve_subject()` verarbeitet werden.

Standard:

```text
fach
fach_lang
displaySubject
```

---

# Verfügbare Hooks

## `state_entities`

```python
@property
def state_entities(self) -> tuple[str, ...]:
    return ()
```

Ein Profil kann Home-Assistant-Entities angeben, von denen seine Transformation abhängt. Wenn sich eine dieser Entities ändert, veröffentlicht SPH-HA die betroffenen Profildaten erneut.

Beispiel:

```python
@property
def state_entities(self):
    return ("sensor.meine_schule_lehrerliste",)
```

Solche Entity-Namen gehören ausschließlich in das konkrete Profil. Der Core kennt keine schulspezifischen Datenquellen.

---

## `resolve_teacher(value, hass=None)`

```python
def resolve_teacher(self, value, hass=None):
    return value
```

Die Basisklasse verändert den Wert nicht. Ein Profil kann hier beispielsweise:

- eine statische Mapping-Tabelle verwenden,
- eine profil-eigene HA-Entity auslesen,
- Kürzel normalisieren,
- unbekannte Werte unverändert zurückgeben.

Beispiel:

```python
def resolve_teacher(self, value, hass=None):
    if not isinstance(value, str):
        return value
    return self.TEACHERS.get(value.strip(), value)
```

Kürzel-Felder, die ausdrücklich Kürzel bleiben sollen, sollten nicht in `teacher_fields` aufgenommen werden.

---

## `resolve_subject(value)`

```python
def resolve_subject(self, value):
    ...
```

Die Basisklasse verwendet `subject_names`. Für komplexere Regeln kann der Hook überschrieben werden.

```python
def resolve_subject(self, value):
    value = super().resolve_subject(value)
    if value == "Religion ev.":
        return "Evangelische Religion"
    return value
```

---

## `resolve_substitution_label(value)`

Löst einen schulspezifischen Vertretungscode über `substitution_labels` auf.

```python
def resolve_substitution_label(self, value):
    return self.substitution_labels.get(value, value)
```

---

## `transform_description(value, hass=None)`

Verarbeitet mehrzeilige Beschreibungstexte. Die Basisklasse ändert nur Zeilen, deren Prefix in `description_teacher_labels` enthalten ist.

---

## `transform_data(value, hass=None)`

Generischer rekursiver Transformer für Listen, Tupel und Dictionaries.

Die Basisklasse verarbeitet:

- Felder aus `teacher_fields` über `resolve_teacher()`
- Felder aus `subject_fields` über `resolve_subject()`
- `description` über `transform_description()`

Andere Werte werden rekursiv verarbeitet. Die Datenstruktur bleibt erhalten.

Für modulbezogene Besonderheiten sollten die spezifischen Hooks verwendet werden.

---

# Modulbezogene Transformations-Hooks

## `transform_timetable_payload(payload, hass=None, substitution_data=None)`

Wird vor Veröffentlichung von Stundenplan-Sensor und Stundenplan-JSON angewandt.

Die Basisklasse:

- verarbeitet `eigener_plan`,
- verarbeitet `tage`, wenn dieser Bereich durch die Konfiguration ausgegeben wird,
- fügt `school_profile` hinzu,
- verändert `eigener_grundplan` nicht.

### Stundenplanquelle

Das Profil darf niemals selbst zwischen persönlichem und vollständigem Stundenplan umschalten.

```text
SPH own/all
  ↓
Benutzerkonfiguration timetable_output
  ↓
veröffentlichte Planbereiche
  ↓
Schul-Profil
```

Bei `timetable_output = all` werden `eigener_plan` und `tage` jeweils profiliert. `eigener_grundplan` wird weder als Profilquelle verwendet noch durch die Profiltransformation umgeschrieben.

### Datumsbezogene Vertretungen

Konkrete Vertretungen gelten für ein bestimmtes Datum. Sie werden deshalb nicht dauerhaft in einen wiederverwendeten Wochenplan geschrieben. Die Anwendung erfolgt in datumsbewussten Kontexten, insbesondere Kalendern und Stundenplan-Karten.

---

## `transform_calendar_payload(payload, hass=None)`

Wird auf den strukturierten Schulkalender-Sensor und dessen JSON-Ausgabe angewandt.

Geeignet für Lehrer-, Fach- und Beschreibungswerte sowie andere schemaerhaltende Anpassungen.

---

## `transform_meinunterricht_payload(payload, hass=None)`

Wird auf Sensor und JSON-Sensor von **Mein Unterricht** angewandt.

---

## `transform_learning_groups_payload(payload, hass=None)`

Wird auf Lerngruppen-/Leistungskontroll-Sensor und JSON-Sensor angewandt.

---

## `transform_substitution_payload(payload, hass=None)`

Wird auf Vertretungsplan-Sensor und JSON-Sensor angewandt.

Die Basisklasse:

1. führt `transform_data()` aus,
2. löst bekannte `art`-Codes über `resolve_substitution_label()` auf,
3. setzt `art_lang`,
4. ergänzt `school_profile`.

---

## `transform_calendar_item(item, hass=None)`

Verarbeitet einen einzelnen Quelldatensatz des nativen Schulkalenders, bevor daraus ein `CalendarEvent` erzeugt wird.

---

## `transform_timetable_display(display, hass=None, substitution=None)`

Verarbeitet einen datumsbezogenen Stundenplan-/Kalendereintrag. Hier ist eine konkrete Vertretung bereits dem Unterrichtstermin zugeordnet.

Die Basisklasse bereitet auf:

- `subject` über `resolve_subject()`
- `teacher` über `resolve_teacher()`
- `label` bei vorhandener Vertretung über `resolve_substitution_label()`

---

# Sensor- und JSON-Kompatibilität

Schul-Profile sollen bestehende Verbraucher nicht unnötig brechen.

Regeln:

1. Vorhandene Top-Level-Strukturen bleiben erhalten.
2. Listen und Dictionaries werden nicht ohne zwingenden Grund verschoben.
3. Werte dürfen schulspezifisch korrigiert werden.
4. Neue Felder sollen additiv sein.
5. `school_profile` ist ein zusätzliches Metadatenfeld.
6. JSON-Sensoren verwenden dieselben transformierten Payloads wie die strukturierten Sensoren.

Beispiel:

```json
{
  "fach": "Deutsch",
  "teacher": "FRA"
}
```

kann durch ein Profil zu

```json
{
  "fach": "Deutsch",
  "teacher": "Franziska Beispiel"
}
```

werden. Die Struktur bleibt identisch.

---

# Profil-eigene Home-Assistant-Daten

Ein Profil darf andere HA-Entities auslesen, wenn die Schule diese Information tatsächlich benötigt. Diese Abhängigkeit wird im Profil selbst gekapselt.

Beispiel:

```python
teacher_entity = "sensor.meine_schule_kollegium"

@property
def state_entities(self):
    return (self.teacher_entity,)
```

Empfehlungen:

- fehlende optionale Datenquellen dürfen das Profil nicht unbrauchbar machen,
- unbekannte Lehrer-/Fachwerte sollten unverändert bleiben,
- der Core darf keine Profil-spezifischen Entity-Namen enthalten,
- `state_entities` sollte nur tatsächlich benötigte Entities melden.

---

# Registrierung eines neuen Profils

Beispiel `custom_components/sph/school_profiles/example.py`:

```python
from .base import SchoolProfile


class ExampleProfile(SchoolProfile):
    id = "example"
    name = "Beispielschule"

    subject_names = {
        "PoWi": "Politik und Wirtschaft",
    }

    substitution_labels = {
        "V": "Vertretung",
        "E": "Entfall",
    }
```

Registrierung in `school_profiles/__init__.py`:

```python
from .example import ExampleProfile

_PROFILES = {
    SCHOOL_PROFILE_NONE: SchoolProfile(),
    KFGProfile.id: KFGProfile(),
    ExampleProfile.id: ExampleProfile(),
}
```

`school_profile_options()` erzeugt aus dieser Registry die Auswahl für den Config-Flow.

---

# Frontend-Profil

Ein Frontend-Profil ist nur erforderlich, wenn eine Schule zusätzliche Darstellungsregeln benötigt.

Datei:

```text
custom_components/sph/static/school-profiles/example.js
```

Beispiel:

```javascript
export default {
  weekBadges: ["A", "B"],
  unbadgedFallback: true,
  hideWeekBadges: true,
  gridWeekHeading: true,
  advanceWeekAfterFriday: true,
  teachers: {
    entity: "sensor.meine_schule_kollegium",
    attribute: "lehrer",
    descriptionLabels: ["lehrer", "lehrkraft"]
  },
  substitution: {
    classPrefix: "sensor.vertretungsplan_",
    fallback: "sensor.vertretungsplan",
    news: true,
    labels: {
      V: "Vertretung",
      E: "Entfall"
    }
  }
};
```

Verfügbare Präsentationseinstellungen hängen von `static/school-profile.js` ab. Aktuell verwendet die gemeinsame Kartenlogik insbesondere:

| Einstellung | Bedeutung |
|---|---|
| `weekBadges` | gültige Wochenkennungen für die UI-Filterung |
| `unbadgedFallback` | blendet unmarkierte Gegenstücke aus, wenn derselbe Slot ein passendes Wochen-Badge besitzt |
| `hideWeekBadges` | versteckt Wochen-Badges an einzelnen Unterrichtseinträgen |
| `gridWeekHeading` | zeigt die Schulwoche einmal oberhalb der Grid-Ansicht |
| `advanceWeekAfterFriday` | schaltet nach Ende der letzten Freitagsstunde auf die nächste Woche |
| `teachers` | optionale Lehrerauflösung für reine UI-Texte |
| `substitution` | bevorzugte Vertretungsquelle, Labels und Nachrichtenanzeige |

Die Karten erkennen das Profil normalerweise über das Sensorattribut `school_profile`.

Für Tests oder einen gezielten Override kann eine Karte verwenden:

```yaml
school-profile: example
```

Mit

```yaml
school-profile: false
```

wird die Profil-Darstellung für diese Karte deaktiviert.

---

# Vertretungsquellen im Frontend

Für Stundenplan-Karten gilt folgende Priorität:

1. explizit in der Karte konfigurierte Quelle über `vertretungsplan_sensor`, `vertretungsplan` oder `substitution_sensor`,
2. bevorzugte Quelle des aktiven Frontend-Profils,
3. interner SPH-Vertretungsplan des Kindes als Fallback.

Eine explizit konfigurierte Quelle ist autoritativ. Wenn sie nicht existiert, wird nicht automatisch auf eine andere Quelle gewechselt.

Das Matching eines Eintrags berücksichtigt unter anderem Datum, Klasse, Stunde/Stundenbereich und Fach beziehungsweise Originalfach.

---

# Dokumentation eines Profils

Für jedes Profil sollte eine Datei angelegt werden:

```text
docs/schools/<profil>/README.md
```

Sie sollte nur den aktuellen Funktionsumfang beschreiben:

- Schule und Profil-ID
- Aktivierung
- serverseitige Anpassungen
- zusätzliche HA-Abhängigkeiten
- Vertretungslabels
- Frontend-Regeln
- besondere Einschränkungen

---

# Tests

Ein neues Profil sollte mindestens folgende Fälle abdecken:

- Registry und Config-Flow-Auswahl
- Verhalten ohne Profil
- Lehrerauflösung einschließlich unbekannter Werte
- Fachauflösung
- Vertretungslabels
- Sensor- und JSON-Strukturerhalt
- `eigener_plan` und `tage` bei vollständiger Stundenplan-Ausgabe
- unverändertes `eigener_grundplan`
- Frontend-Profilladen und `school-profile: false`
- profil-eigene Vertretungsquelle und Fallback
- optionale `state_entities`

Python-Tests liegen unter `tests/test_*.py`, Frontend-Tests unter `tests/*.test.mjs`.

---

# Referenz: KFG

Das KFG-Profil zeigt die vollständige aktuelle Struktur eines Profils:

```text
custom_components/sph/school_profiles/kfg.py
custom_components/sph/static/school-profiles/kfg.js
docs/schools/kfg/README.md
```

`sensor.kfg_kollegium` ist ausschließlich Bestandteil dieses Profils. Die allgemeine Profil-Engine kennt diese Entity nicht.
