# Schul-Profile entwickeln

Diese Dokumentation beschreibt die aktuelle Entwickler-API für **Schul-Profile** in SPH-HA.

Schul-Profile kapseln ausschließlich Besonderheiten einer einzelnen Schule. Allgemeine SPH-Logik bleibt im Core. Ein Profil kann serverseitige Daten für Sensoren, JSON-Sensoren und Kalender aufbereiten und zusätzlich eigene Darstellungsregeln für die SPH-Lovelace-Karten bereitstellen.

## Grundprinzip

Ein neues Schul-Profil wird als eigener Ordner unter `custom_components/sph/school_profiles/` angelegt. Die Integration durchsucht diese Ordner automatisch. Eine zentrale Liste mit Profilnamen oder Klassen muss nicht gepflegt werden.

Beispiel:

```text
custom_components/sph/school_profiles/
├── __init__.py
├── base.py
└── beispielschule/
    ├── __init__.py
    ├── profile.py
    ├── helpers.py              # optional
    └── frontend/
        ├── lovelace.js
        └── weitere-datei.js    # optional
```

Der Ordnername ist gleichzeitig die technische Profil-ID. Für `beispielschule/` muss das Profil deshalb `id = "beispielschule"` verwenden.

## Discovery

`school_profiles/__init__.py` durchsucht beim Laden alle direkten Unterordner von `school_profiles/`.

Ein Ordner wird als Profil behandelt, wenn er enthält:

```text
<profil>/profile.py
```

Die Datei muss ein `PROFILE`-Objekt exportieren, das von `SchoolProfile` abgeleitet ist.

Beispiel:

```python
from ..base import SchoolProfile


class BeispielProfil(SchoolProfile):
    id = "beispielschule"
    name = "Beispielschule"
    description = "Schulprofil für die Beispielschule."
    frontend_module = "lovelace.js"


PROFILE = BeispielProfil()
```

Die Registry importiert die Profilordner dynamisch. Es ist **keine Änderung** an `school_profiles/__init__.py`, `config_flow.py` oder einer anderen zentralen Profilliste erforderlich.

### Validierung bei der Discovery

Ein Profil wird nur registriert, wenn:

1. `profile.py` vorhanden ist,
2. `PROFILE` ein gültiges `SchoolProfile`-Objekt bzw. eine passende Unterklasse ist,
3. `id` nur Kleinbuchstaben, Ziffern, `-` und `_` verwendet,
4. `id` exakt dem Ordnernamen entspricht,
5. die Profil-ID noch nicht vergeben ist,
6. ein angegebenes `frontend_module` im eigenen `frontend/`-Ordner vorhanden ist.

Ein fehlerhaftes Profil wird protokolliert und nicht in der Konfigurationsauswahl angeboten. Andere Profile bleiben davon unabhängig.

## Metadaten des Profils

Die Profildatei ist die maßgebliche Quelle für profilbezogene Metadaten.

### `id`

Technischer Name des Profils.

```python
id = "beispielschule"
```

Der Wert wird verwendet für:

- den gespeicherten Config-Entry-Wert `school_profile`,
- das Sensorattribut `school_profile`,
- die dynamische Profil-Registry,
- die Zuordnung des Frontend-Pakets.

### `name`

Anzeigename in der Home-Assistant-Konfiguration.

```python
name = "Beispiel-Gymnasium Musterstadt"
```

`school_profile_options()` erzeugt die Auswahl des Config- und Options-Flows direkt aus den entdeckten Profilobjekten.

### `description`

Beschreibung des Profils für generische Verbraucher, Diagnose und zukünftige Konfigurationsoberflächen.

```python
description = "Anpassungen für das Beispiel-Gymnasium Musterstadt."
```

### `frontend_module`

Dateiname des Frontend-Einstiegspunkts im Unterordner `frontend/`.

```python
frontend_module = "lovelace.js"
```

Für Profile mit Lovelace-Anpassungen liegt die Datei unter:

```text
school_profiles/<id>/frontend/lovelace.js
```

Die Integration registriert den jeweiligen Frontend-Ordner automatisch als statischen Pfad. Zusätzliche JS-Dateien, CSS-Dateien oder andere Frontend-Ressourcen können im selben `frontend/`-Ordner liegen und vom Einstiegspunkt importiert werden.

## `metadata()`

Die Basisklasse liefert die profil-eigenen Metadaten über:

```python
profile.metadata()
```

Aktuell enthalten:

```python
{
    "id": profile.id,
    "name": profile.name,
    "description": profile.description,
    "frontend_module": profile.frontend_module,
}
```

Generische Komponenten sollen diese Metadaten verwenden, statt einzelne Schulen im Core zu kennen.

## `config_option()`

Für die Home-Assistant-Auswahl liefert jedes Profil:

```python
profile.config_option()
```

Beispiel:

```python
{
    "value": "beispielschule",
    "label": "Beispiel-Gymnasium Musterstadt",
}
```

Die Konfigurationsseite wird damit vollständig aus den dynamisch gefundenen Profilen aufgebaut.

---

# Python-Profil

Die Basisklasse befindet sich in:

```text
custom_components/sph/school_profiles/base.py
```

Import innerhalb eines Profilordners:

```python
from ..base import SchoolProfile
```

## Allgemeine Regeln

Ein Profil darf:

- Lehrerkürzel auflösen,
- schulspezifische Fachbezeichnungen anpassen,
- schulspezifische Vertretungscodes aufbereiten,
- profil-eigene Home-Assistant-Entities auslesen,
- Werte in Sensor-, JSON- und Kalenderdaten verändern,
- eigene Hilfsdateien im Profilordner verwenden.

Ein Profil soll nicht:

- die konfigurierte Stundenplanquelle wechseln,
- `eigener_grundplan` als Ersatzquelle verwenden,
- allgemeine Parser- oder Matchinglogik duplizieren,
- schulspezifische Sonderfälle in den Core verschieben,
- unnötig neue Sensorstrukturen oder Entity-IDs erzeugen.

Grundregel: **Was für mehrere Schulen sinnvoll ist, gehört in den Core. Was nur eine Schule benötigt, gehört in ihren Profilordner.**

## `subject_names`

Exakte schulspezifische Fachzuordnung:

```python
subject_names = {
    "Reli ev.": "Evangelische Religion",
    "PoWi": "Politik und Wirtschaft",
}
```

Die Basisklasse verwendet diese Tabelle in `resolve_subject()` case-insensitiv.

## `substitution_labels`

Schulspezifische Vertretungscodes:

```python
substitution_labels = {
    "V": "Vertretung",
    "E": "Entfall",
}
```

Der Rohwert `art` bleibt erhalten. Die lesbare Bezeichnung wird über `art_lang` bzw. datumsbezogene Anzeigeobjekte bereitgestellt.

## `description_teacher_labels`

Zeilenbezeichnungen in mehrzeiligen Beschreibungen, deren Inhalt als Lehrkraft behandelt werden soll:

```python
description_teacher_labels = (
    "lehrer",
    "lehrkraft",
    "verantwortlich",
)
```

## `teacher_fields`

Die Basisklasse transformiert standardmäßig folgende Dictionary-Felder über `resolve_teacher()`:

```text
teacher
lehrer
lehrkraft
vertreter
lehrer_nach
verantwortlich
```

Ein Profil kann die Menge überschreiben, wenn seine Daten eine andere Semantik haben.

## `subject_fields`

Standardmäßig werden diese Felder über `resolve_subject()` verarbeitet:

```text
fach
fach_lang
displaySubject
```

---

# Profil-eigene Home-Assistant-Entities

## `state_entities`

Ein Profil kann angeben, von welchen Home-Assistant-Entities seine Transformation abhängt:

```python
@property
def state_entities(self) -> tuple[str, ...]:
    return ("sensor.beispielschule_kollegium",)
```

Ändert sich eine dieser Entities, veröffentlicht SPH-HA die betroffenen profilierten Daten erneut.

Schulspezifische Entity-Namen gehören ausschließlich in das konkrete Profil. Der Core kennt diese Namen nicht.

Beispiel:

```python
teacher_entity = "sensor.beispielschule_kollegium"
teacher_attribute = "lehrer"

@property
def state_entities(self):
    return (self.teacher_entity,)
```

---

# Transformations-Hooks

## `resolve_teacher(value, hass=None)`

Standardmäßig ein No-op. Ein Profil kann hier Lehrerkürzel über eine eigene Tabelle, eine HA-Entity oder eine andere schulspezifische Quelle auflösen.

```python
def resolve_teacher(self, value, hass=None):
    if not isinstance(value, str) or not value.strip():
        return value
    return self.TEACHERS.get(value.strip(), value)
```

Unbekannte Werte sollten möglichst unverändert bleiben.

## `resolve_subject(value)`

Verwendet standardmäßig `subject_names`. Für komplexere Regeln kann die Methode überschrieben werden.

## `resolve_substitution_label(value)`

Löst einen schulspezifischen Vertretungscode über `substitution_labels` auf.

## `transform_description(value, hass=None)`

Verarbeitet mehrzeilige Beschreibungen. Nur Prefixe aus `description_teacher_labels` werden als Lehrerwerte behandelt.

## `transform_data(value, hass=None)`

Rekursiver Transformer für Dictionaries, Listen und Tupel. Die Basisklasse wendet Lehrer-, Fach- und Beschreibungs-Hooks an und erhält die Datenstruktur.

---

# Modulbezogene Hooks

## `transform_timetable_payload(...)`

Wird vor Veröffentlichung von Stundenplan-Sensor und Stundenplan-JSON angewandt.

Die Basisklasse verarbeitet:

- `eigener_plan`,
- `tage`, wenn die vollständige Ausgabe aktiviert ist,
- das zusätzliche Metadatum `school_profile`.

`eigener_grundplan` wird nicht als Profilquelle verwendet und nicht durch die Profiltransformation verändert.

Die Stundenplan-Auswahl erfolgt vorher im Core:

```text
SPH own/all
  ↓
Benutzerkonfiguration timetable_output
  ↓
veröffentlichte Planbereiche
  ↓
Schul-Profil
```

Bei vollständiger Stundenplan-Ausgabe werden `eigener_plan` und `tage` unabhängig voneinander profiliert.

Datumsabhängige Vertretungen werden nicht dauerhaft in den wiederverwendeten Wochenplan geschrieben.

## `transform_calendar_payload(payload, hass=None)`

Verarbeitet den strukturierten Schulkalender-Sensor und dessen JSON-Ausgabe.

## `transform_meinunterricht_payload(payload, hass=None)`

Verarbeitet Sensor und JSON-Sensor von **Mein Unterricht**.

## `transform_learning_groups_payload(payload, hass=None)`

Verarbeitet Lerngruppen-/Leistungskontroll-Sensor und JSON-Sensor.

## `transform_substitution_payload(payload, hass=None)`

Verarbeitet Vertretungsplan-Sensor und JSON-Sensor. Die Basisklasse setzt für bekannte `art`-Codes zusätzlich `art_lang`.

## `transform_calendar_item(item, hass=None)`

Verarbeitet einen einzelnen Quelldatensatz des nativen Schulkalenders.

## `transform_timetable_display(display, hass=None, substitution=None)`

Verarbeitet einen datumsbezogenen Stundenplan-/Kalendereintrag, wenn eine konkrete Vertretung bereits einer Unterrichtsstunde zugeordnet ist.

---

# Frontend-Profil

Jedes Profil mit UI-Anpassungen besitzt seinen Frontend-Einstiegspunkt im eigenen Profilordner:

```text
custom_components/sph/school_profiles/<id>/frontend/lovelace.js
```

Minimalbeispiel:

```javascript
export default {};
```

Beispiel mit Darstellungsregeln:

```javascript
export default {
  weekBadges: ["A", "B"],
  unbadgedFallback: true,
  hideWeekBadges: true,
  gridWeekHeading: true,
  advanceWeekAfterFriday: true,
  teachers: {
    entity: "sensor.beispielschule_kollegium",
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

## Dynamisches Laden

`static/school-profile.js` kennt keine Liste konkreter Schulen. Es verwendet die Profil-ID aus dem Sensor bzw. aus `school-profile` und lädt den Frontend-Einstiegspunkt aus dem passenden Profilordner.

Browserpfad:

```text
/api/sph/school_profiles/<id>/frontend/lovelace.js
```

Die statischen Pfade werden aus `school_profile_frontend_paths()` erzeugt. Es wird nur der jeweilige `frontend/`-Ordner veröffentlicht; Python-Dateien des Profils werden nicht als statische Ressourcen freigegeben.

## Weitere Frontend-Dateien

`lovelace.js` kann weitere Dateien aus dem eigenen `frontend/`-Ordner importieren:

```javascript
import { labels } from "./labels.js";
```

Dadurch können größere Profile ihre Darstellung auf mehrere Dateien verteilen, ohne zentrale Dateien der Integration anzupassen.

---

# Eigene Python-Hilfsdateien

Ein Profil kann beliebige interne Python-Helfer im eigenen Ordner ablegen:

```text
beispielschule/
├── profile.py
├── teachers.py
├── subjects.py
└── frontend/
    └── lovelace.js
```

In `profile.py`:

```python
from .teachers import resolve_teacher_name
from .subjects import SUBJECTS
```

Nur `profile.py` ist der Discovery-Einstiegspunkt. Zusätzliche Dateien werden durch das Profil selbst importiert. Dadurch werden nicht versehentlich beliebige Dateien automatisch ausgeführt.

---

# Vollständiges Minimalprofil

```text
custom_components/sph/school_profiles/beispielschule/
├── __init__.py
├── profile.py
└── frontend/
    └── lovelace.js
```

`__init__.py`:

```python
"""Beispielschule school profile package."""
```

`profile.py`:

```python
from ..base import SchoolProfile


class BeispielProfil(SchoolProfile):
    id = "beispielschule"
    name = "Beispielschule Musterstadt"
    description = "Schulprofil für die Beispielschule Musterstadt."
    frontend_module = "lovelace.js"

    subject_names = {
        "Reli ev.": "Evangelische Religion",
    }

    substitution_labels = {
        "V": "Vertretung",
        "E": "Entfall",
    }


PROFILE = BeispielProfil()
```

`frontend/lovelace.js`:

```javascript
export default {};
```

Nach Installation bzw. Neustart wird `beispielschule` automatisch entdeckt und erscheint in der Auswahl **Schul-Profil**. Es sind keine Änderungen an einer zentralen Registry erforderlich.

---

# Sensor- und JSON-Kompatibilität

Profile sollen bestehende Verbraucher nicht unnötig brechen.

Regeln:

1. Vorhandene Top-Level-Strukturen bleiben erhalten.
2. Listen und Dictionaries werden nicht ohne zwingenden Grund verschoben.
3. Werte dürfen schulspezifisch korrigiert werden.
4. Neue Felder werden additiv ergänzt.
5. `school_profile` ist ein zusätzliches Metadatenfeld.
6. JSON-Sensoren verwenden dieselben transformierten Payloads wie die strukturierten Sensoren.
7. `eigener_grundplan` ist keine Profilquelle.
8. Bei vollständiger Stundenplan-Ausgabe werden `eigener_plan` und `tage` beide profiliert.

---

# Tests für ein neues Profil

Mindestens prüfen:

- Profilordner wird dynamisch entdeckt,
- `id` entspricht dem Ordnernamen,
- `name` erscheint über `config_option()`,
- `frontend_module` existiert,
- profil-eigene `state_entities` sind korrekt,
- Lehrer-/Fachauflösung lässt unbekannte Werte stabil,
- Sensorstruktur bleibt erhalten,
- `eigener_plan` und gegebenenfalls `tage` werden profiliert,
- `eigener_grundplan` bleibt unverändert,
- Vertretungscodes behalten `art` und erhalten die gewünschte Langform,
- Frontend-Modul lässt sich importieren.

Die bestehenden Regressionstests unter `tests/test_school_profiles.py` und `tests/*.test.mjs` dienen als Referenz.

---

# Checkliste für neue Profile

1. Ordner `school_profiles/<id>/` anlegen.
2. `__init__.py` anlegen.
3. `profile.py` mit `PROFILE` erstellen.
4. `id`, `name`, `description` und `frontend_module` im Profil definieren.
5. Bei UI-Anpassungen `frontend/lovelace.js` anlegen.
6. Schulspezifische Python-Helfer nur innerhalb des Profilordners ablegen.
7. Profil-spezifische HA-Entities nur über `state_entities` referenzieren.
8. Keine zentrale Registry oder ConfigFlow-Liste erweitern.
9. Tests ergänzen.
10. Schuldokumentation unter `docs/schools/<id>/README.md` ergänzen.
