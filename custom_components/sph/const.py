DOMAIN = "sph"
CONF_SCHOOL_ID = "school_id"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_CHILD_NAME = "child_name"
CONF_CHILD_SHORTCUT = "child_shortcut"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_CALENDAR_EVENT_TYPES = "calendar_event_types"
CONF_ACTIVE_MODULES = "active_modules"
CONF_TIMETABLE_OUTPUT = "timetable_output"
CONF_SCHOOL_DISTRICT = "school_district"
CONF_MODULE_STUNDENPLAN = "module_stundenplan"
CONF_MODULE_KALENDER = "module_kalender"
CONF_MODULE_MEINUNTERRICHT = "module_meinunterricht"
CONF_MODULE_LERNGRUPPEN = "module_lerngruppen"
DEFAULT_UPDATE_INTERVAL = 60
# Empty means: do not filter calendar event types, keep all entries.
DEFAULT_CALENDAR_EVENT_TYPES = []
DEFAULT_MODULE_ENABLED = True
# The personal timetable is always exposed. "all" additionally fills the
# legacy "tage" block with the complete timetable returned by SPH.
TIMETABLE_OUTPUT_OWN = "own"
TIMETABLE_OUTPUT_ALL = "all"
DEFAULT_TIMETABLE_OUTPUT = TIMETABLE_OUTPUT_OWN
# Existing installations default to no district until explicitly selected.
SCHOOL_DISTRICT_NONE = "none"

# Authentication is hosted separately from the legacy school portal.
SPH_BASE = "https://start.schulportal.hessen.de"
SPH_LOGIN = "https://login.schulportal.hessen.de/"
SPH_CONNECT = "https://connect.schulportal.hessen.de/"
