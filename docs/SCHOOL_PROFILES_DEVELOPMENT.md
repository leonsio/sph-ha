# Schul-Profile entwickeln

Diese Dokumentation beschreibt die Entwickler-API für **School Profiles** ab SPH-HA 0.6.0.

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

Der langfristige Grundsatz lautet: **Was für mehrere Schulen gleich funktioniert, gehört in den Core. Nur tatsächliche Abweichungen gehören in ein Schul-Profil.**

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
serverseitiges School Profile (Python)
 │
 ├── Sensoren
 ├── JSON-Sensoren
 ├── native Kalender
 └── Services/weitere Verbraucher

Lovelace
 │
 ▼
optionales Präsentationsprofil (JavaScript)
```

Das Python-Profil ist für **Daten** zuständig. Das JavaScript-Profil enthält nur Regeln, die tatsächlich Darstellung oder zeitabhängige UI-Auswahl betreffen.

### Warum zwei Ebenen?

Ein Lehrerkürzel soll nicht nur in einer Lovelace-Karte korrekt erscheinen. Wenn eine Schule dafür eine schulspezifische Zuordnung benötigt, soll derselbe Wert auch in Sensoren, JSON und Kalendern verfügbar sein.

Andererseits sind Dinge wie das Ausblenden eines A/B-Badges oder eine zusätzliche Überschrift im Grid reine Darstellung und gehören nicht in Sensorwerte.

---

## Konfiguration pro Kind

Der Config-Entry enthält ab 0.6.0:

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

Die Auswahl erfolgt bei der Einrichtung und in den Optionen **pro Kind**. Dadurch können mehrere Kinder an verschiedenen Schulen in derselben Home-Assistant-Installation unterschiedliche Profile verwenden.

Das ausgewählte Profil wird in veröffentlichten Payloads zusätzlich als

```yaml
school_profile: kfg
```

angegeben. Das Feld ist additiv; bestehende Schlüssel und Verschachtelungen bleiben erhalten.

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

Danach muss das Profil in `school_profiles/__init__.py` registriert werden.

---

## Grundlegende Eigenschaften

### `id`

Technischer Profilname. Muss stabil und für Konfiguration/Frontend geeignet sein.

```python
id = "example"
```

Empfohlen:

- Kleinbuchstaben
- Ziffern
- `-` oder `_`
- keine Leerzeichen

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

Die Zuordnung erfolgt case-insensitiv.

Allgemeine Fachnormalisierung, die für mehrere Schulen gilt, gehört dagegen in `api/subjects.py`, nicht in ein Schul-Profil.

### `substitution_labels`

Schulspezifische Bezeichnungen für Vertretungsarten.

```python
substitution_labels = {
    "Vertr": "Vertretung",
    "Entf": "Entfall",
}
```

Der Rohcode bleibt in den ursprünglichen Feldern erhalten. Das Profil kann einen lesbaren Wert in `art_lang` bzw. in datumsbezogenen Kalenderdarstellungen bereitstellen.

### `description_teacher_labels`

Kennzeichnet Zeilen in mehrzeiligen Beschreibungen, deren Wert mit `resolve_teacher()` verarbeitet werden darf.

```python
description_teacher_labels = (
    "lehrer",
    "lehrkraft",
)
```

---

# Verfügbare Hooks

## `state_entities`

```python
@property
def state_entities(self) -> tuple[str, ...]:
    return ()
```

Ein Profil kann eigene Home-Assistant-Entities angeben, von denen seine Transformation abhängt.

Wenn sich eine dieser Entities ändert, werden die betroffenen SPH-Ausgaben erneut veröffentlicht.

Beispiel:

```python
@property
def state_entities(self):
    return ("sensor.meine_schule_lehrerliste",)
```

**Wichtig:** Solche Entities gehören ausschließlich in das konkrete Profil. Der Core kennt keine schulabhängigen Entity-Namen.

Beim KFG ist daher `sensor.kfg_kollegium` ausschließlich in `KFGProfile` definiert.

---

## `resolve_teacher(value, hass=None)`

```python
def resolve_teacher(self, value, hass=None):
    return value
```

Wird für bekannte Lehrerfelder verwendet.

Die Basisklasse verändert nichts. Ein Profil kann z. B.:

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

### Welche Felder werden standardmäßig als Lehrerfelder behandelt?

Die Basisklasse verarbeitet aktuell rekursiv:

```text
teacher
lehrer
lehrkraft
vertreter
lehrer_nach
verantwortlich
```

Ein Profil kann `teacher_fields` überschreiben, wenn eine Schule andere Semantik benötigt.

`lehrkraft_kürzel` wird bewusst nicht automatisch durch einen Langnamen ersetzt, damit Kürzel-Felder Kürzel bleiben.

---

## `resolve_subject(value)`

```python
def resolve_subject(self, value):
    ...
```

Standardmäßig werden Einträge aus `subject_names` angewandt.

Bekannte Felder:

```text
fach
fach_lang
displaySubject
```

Für komplexere Regeln kann der Hook überschrieben werden.

Beispiel:

```python
def resolve_subject(self, value):
    value = super().resolve_subject(value)
    if value == "Religion ev.":
        return "Evangelische Religion"
    return value
```

---

## `resolve_substitution_label(value)`

Löst einen schulspezifischen Vertretungscode auf.

```python
def resolve_substitution_label(self, value):
    return self.substitution_labels.get(value, value)
```

---

## `transform_description(value, hass=None)`

Verarbeitet mehrzeilige Beschreibungstexte. Standardmäßig werden nur Zeilen mit einem Prefix aus `description_teacher_labels` verändert.

Beispiel:

```text
Lehrkraft: FRA
Raum: 123
```

kann zu

```text
Lehrkraft: Vorname Nachname
Raum: 123
```

werden, wenn das Profil `FRA` auflösen kann.

---

## `transform_data(value, hass=None)`

Generischer rekursiver Transformer für Listen und Dictionaries.

Er verarbeitet standardmäßig:

- Lehrerfelder über `resolve_teacher()`
- Fachfelder über `resolve_subject()`
- `description` über `transform_description()`

Die Struktur des Objekts bleibt erhalten.

Dieser Hook ist für kleine, schemaerhaltende Anpassungen gedacht. Für modulbezogene Sonderfälle sollten die spezifischen Hooks verwendet werden.

---

# Modulbezogene Transformations-Hooks

## `transform_timetable_payload(payload, hass=None, substitution_data=None)`

Wird vor Veröffentlichung von Stundenplan-Sensor und Stundenplan-JSON angewandt.

Standardverhalten:

- verarbeitet `eigener_plan`
- verarbeitet `tage`, falls diese durch die Konfiguration ausgegeben werden
- fügt `school_profile` hinzu
- verändert `eigener_grundplan` nicht

### Wichtige Regel zur Stundenplanquelle

Das Profil darf niemals selbst entscheiden, ob `own` oder `all` verwendet wird.

Die Reihenfolge ist:

```text
SPH own/all
  ↓
Benutzerkonfiguration timetable_output
  ↓
veröffentlichte Planbereiche
  ↓
School Profile
```

Insbesondere darf ein Profil **nicht `eigener_grundplan` als Quelle verwenden**.

Warum: An manchen Schulen enthält ein umfangreicher Plan gleichzeitig mehrere alternative Gruppen, z. B. katholische Religion, evangelische Religion und Ethik. Für ein Kind darf das Profil nicht aus einer anderen Quelle zusätzliche Unterrichtseinträge hineinmischen.

### Datumsbezogene Vertretungen

Eine Vertretung gilt für ein konkretes Datum. Der Wochenplan wird jedoch auch zur Berechnung anderer Wochen verwendet.

Daher werden datumsbezogene Vertretungen nicht dauerhaft in den wiederverwendeten `eigener_plan` geschrieben. Sie werden dort angewandt, wo das Datum bekannt ist, z. B. im Stundenplan-Kalender oder in der Lovelace-Darstellung.

---

## `transform_calendar_payload(payload, hass=None)`

Wird für den Schulkalender-Sensor und dessen JSON-Ausgabe verwendet.

Geeignet für:

- Lehrernamen
- Fachnamen
- schulspezifische Verantwortlichen-Bezeichnungen
- Beschreibungen
- weitere schemaerhaltende Werte

---

## `transform_meinunterricht_payload(payload, hass=None)`

Wird auf den Sensor und JSON-Sensor von **Mein Unterricht** angewandt.

Damit können beispielsweise schulspezifische Lehrer- und Fachbezeichnungen auch außerhalb der Lovelace-Karte korrigiert werden.

---

## `transform_learning_groups_payload(payload, hass=None)`

Wird auf Lerngruppen-/Leistungskontroll-Sensor und JSON-Sensor angewandt.

---

## `transform_substitution_payload(payload, hass=None)`

Wird auf Vertretungsplan-Sensor und JSON-Sensor angewandt.

Die Basisklasse:

1. führt die normale Daten-Transformation aus,
2. ergänzt für bekannte `art`-Codes die profilabhängige `art_lang`-Bezeichnung,
3. fügt `school_profile` hinzu.

---

## `transform_calendar_item(item, hass=None)`

Verarbeitet einen einzelnen nativen Kalender-Quelldatensatz, bevor daraus ein `CalendarEvent` erzeugt wird.

Dadurch werden schulspezifische Daten nicht nur im Sensor, sondern auch in Home Assistants Kalender-Entities sichtbar.

---

## `transform_timetable_display(display, hass=None, substitution=None)`

Wird für einen **datumsbezogenen** Stundenplan-Kalendereintrag aufgerufen.

Hier ist das konkrete Datum bereits bekannt und die passende Vertretung wurde gefunden. Deshalb ist dieser Hook für Änderungen geeignet, die nur zusammen mit einem konkreten Vertretungseintrag korrekt sind.

Standardmäßig werden:

- Fachname
- Lehrkraft
- Vertretungsbezeichnung

über das Profil aufbereitet.

---

# Sensor- und JSON-Kompatibilität

School Profiles sollen bestehende Verbraucher nicht unnötig brechen.

Grundregeln:

1. Vorhandene Top-Level-Strukturen bleiben erhalten.
2. Vorhandene Listen/Dictionaries werden nicht ohne zwingenden Grund verschoben.
3. Werte dürfen schulspezifisch korrigiert werden.
4. Neue Felder sollen additiv sein.
5. `school_profile` ist ein zusätzliches Metadatenfeld.
6. JSON-Sensoren verwenden dieselben transformierten Payloads wie normale Sensoren.

Beispiel:

Vorher:

```json
{
  "fach": "Deutsch",
  "teacher": "FRA"
}
```

Mit einem Profil, das Lehrerkürzel auflöst:

```json
{
  "fach": "Deutsch",
  "teacher": "Franziska Beispiel"
}
```

Die Struktur bleibt gleich.

---

# Profil-eigene externe Home-Assistant-Daten

Ein Profil darf auf andere HA-Entities zugreifen, wenn die Schule diese Information tatsächlich benötigt.

Das ist **keine allgemeine SPH-Abhängigkeit**.

Beispiel KFG:

```python
teacher_entity = "sensor.kfg_kollegium"
```

Diese Entity ist nur relevant, wenn `school_profile: kfg` gewählt ist.

Ein anderes Profil kann:

- gar keine externe Entity benötigen,
- eine eigene Lehrerliste verwenden,
- eine statische Mapping-Tabelle enthalten,
- andere Datenquellen verwenden.

Profile sollten bei fehlenden optionalen Datenquellen möglichst auf die unveränderten SPH-Werte zurückfallen.

---

# Registrierung eines neuen Profils

Beispiel `example.py`:

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

Dann in `school_profiles/__init__.py`:

```python
from .example import ExampleProfile

_PROFILES = {
    SCHOOL_PROFILE_NONE: SchoolProfile(),
    KFGProfile.id: KFGProfile(),
    ExampleProfile.id: ExampleProfile(),
}
```

Das Profil erscheint danach automatisch in der Profil-Auswahl des Config-Flows.

---

# Frontend-Profil

Nur wenn die Schule tatsächlich eine besondere Darstellung benötigt, wird zusätzlich eine Datei angelegt:

```text
custom_components/sph/static/school-profiles/example.js
```

Minimal:

```javascript
export default {};
```

Mögliche aktuelle UI-Eigenschaften:

```javascript
export default {
  weekBadges: ["A", "B"],
  unbadgedFallback: true,
  hideWeekBadges: true,
  gridWeekHeading: true,
  advanceWeekAfterFriday: true,
};
```

## `weekBadges`

Welche Badge-Werte als Wochenkennung behandelt werden.

## `unbadgedFallback`

Steuert die Auswahl unmarkierter paralleler Stunden bei A/B-Gruppen.

## `hideWeekBadges`

Blendet A/B-Badges an einzelnen Unterrichtseinträgen aus, wenn die Woche bereits an anderer Stelle dargestellt wird.

## `gridWeekHeading`

Zeigt die Schulwoche einmal oberhalb der Grid-Ansicht statt an jedem Tag.

## `advanceWeekAfterFriday`

Die Wochenansicht wechselt nach Ende der letzten Freitagsstunde auf die folgende Schulwoche.

---

# Optionale Frontend-Lehrerquelle

Für Legacy-/UI-Fallbacks kann ein Frontend-Profil weiterhin einen `teachers`-Block definieren:

```javascript
teachers: {
  entity: "sensor.example_teachers",
  attribute: "lehrer",
  descriptionLabels: ["lehrer", "lehrkraft"]
}
```

Neue serverseitige Profile sollten Lehrernamen jedoch bevorzugt bereits im Python-Profil auflösen. Dann bekommen Sensoren, JSON und Kalender dieselben Werte.

Beim KFG ist der Block nur wegen der bestehenden KFG-Funktionalität und als Fallback vorhanden.

---

# Vertretungsdarstellung im Frontend

Ein Profil kann für die Lovelace-Darstellung aktuell definieren:

```javascript
substitution: {
  classPrefix: "sensor.vertretungsplan_",
  fallback: "sensor.vertretungsplan",
  news: true,
  labels: {
    Vertr: "Vertretung",
    Entf: "Entfall"
  }
}
```

Die allgemeinen SPH-Vertretungssensoren werden bevorzugt automatisch dem Kind zugeordnet. `classPrefix`/`fallback` dienen hauptsächlich als Kompatibilitäts-/Sonderfallmechanismus.

Langfristig sollten solche Angaben aus einem Profil entfernt werden, sobald die allgemeine Integration die betreffende Schule ohne Sonderregel korrekt bedienen kann.

---

# Automatische Profil-Erkennung in Lovelace

Die SPH-Sensoren tragen das Feld:

```yaml
school_profile: kfg
```

Die mitgelieferten Lovelace-Karten erkennen das Profil darüber automatisch.

Damit genügt normalerweise:

```yaml
type: custom:sph-stundenplan-grid-card
entity: sensor.stundenplan_maxim_mk
```

Eine zusätzliche Kartenkonfiguration ist nicht erforderlich.

Für Tests oder explizite Overrides kann weiterhin verwendet werden:

```yaml
school-profile: kfg
```

Der alte Parameter

```yaml
school-hacks: kfg
```

bleibt in 0.6.0 als Legacy-Alias erhalten, sollte für neue Konfigurationen aber nicht mehr verwendet werden.

---

# KFG als Referenzprofil

Server:

```text
custom_components/sph/school_profiles/kfg.py
```

Frontend:

```text
custom_components/sph/static/school-profiles/kfg.js
```

Das KFG-Profil übernimmt die vorherige `school-hacks/kfg.js`-Funktionalität, trennt sie aber nun nach Verantwortlichkeit.

Serverseitig gehören dazu insbesondere:

- Lehrernamen über die KFG-eigene Kollegiums-Entity,
- KFG-Bezeichnungen für Vertretungsarten,
- Transformation derselben Werte in Sensoren, JSON und Kalendern.

Frontendseitig bleiben insbesondere:

- A/B-Badge-Darstellung,
- Grid-Wochenüberschrift,
- Wechsel auf die Folgewoche nach der letzten Freitagsstunde,
- visuelle Vertretungskennzeichnung und Tageshinweise.

`sensor.kfg_kollegium` ist **keine allgemeine Abhängigkeit von SPH-HA**. Er wird ausschließlich vom KFG-Profil verwendet.

---

# Wann gehört etwas in den Core?

Vor dem Hinzufügen eines Profil-Hooks sollte geprüft werden:

**Core**, wenn:

- SPH dieselbe Semantik schulübergreifend liefert,
- mehrere Schulen dieselbe Regel benötigen,
- es sich um Normalisierung eines allgemeinen SPH-Formats handelt,
- es sich um allgemeine Vertretungs-/Kalenderlogik handelt.

**Profil**, wenn:

- eine Schule eigene Codes verwendet,
- eine Schule eine zusätzliche lokale Mapping-Quelle benötigt,
- dieselben SPH-Daten an dieser Schule anders interpretiert werden müssen,
- eine Darstellung wirklich schulabhängig ist.

Beispiele:

| Funktion | Ort |
|---|---|
| `Deutsch 7n` → `Deutsch` allgemeingültig normalisieren | Core |
| SPH-Vertretung nach Datum und Stunde zuordnen | Core |
| KFG-Kürzel über `sensor.kfg_kollegium` auflösen | KFG-Profil |
| KFG-Code `Betr` als `Betreuung` anzeigen | KFG-Profil |
| Kalendertermine aus Stundenplan erzeugen | Core |
| Grid-Ansicht am KFG nach Freitag auf Folgewoche schalten, solange nicht verallgemeinert | KFG-Frontendprofil |

---

# Empfehlungen für neue Profile

1. Mit möglichst wenigen Overrides beginnen.
2. Allgemeine Parser- oder Normalisierungsfehler zuerst im Core beheben.
3. Sensorschlüssel nicht umbenennen.
4. Rohwerte nur dann ersetzen, wenn der veröffentlichte Wert dadurch fachlich korrekter wird.
5. Bei optionalen externen Entities einen sicheren Fallback vorsehen.
6. Datumsabhängige Änderungen nur in einem datumsbewussten Kontext anwenden.
7. Für jedes Profil eine eigene Dokumentation unter `docs/schools/<profil>/README.md` anlegen.
8. Python-Tests für Daten-Hooks und JavaScript-Tests für reine UI-Regeln ergänzen.
9. Das Profil regelmäßig verkleinern, wenn frühere Sonderfälle in den Core übernommen wurden.

---

# Checkliste für ein neues Profil

- [ ] `school_profiles/<name>.py` angelegt
- [ ] eindeutige `id` und `name` gesetzt
- [ ] Profil in `school_profiles/__init__.py` registriert
- [ ] nur tatsächlich schulspezifische Hooks überschrieben
- [ ] externe Entities ausschließlich im Profil definiert
- [ ] vorhandene Sensorstruktur erhalten
- [ ] Stundenplan-Auswahl nicht verändert
- [ ] `eigener_grundplan` nicht als alternative Profilquelle verwendet
- [ ] falls nötig `static/school-profiles/<name>.js` angelegt
- [ ] Entwickler-/Schuldokumentation ergänzt
- [ ] Tests für Transformationsregeln ergänzt

