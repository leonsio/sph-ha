// Compatibility and shared selection logic for KFG timetable cards.
//
// KFG A/B week rules:
// - A/B badges describe the week in which that lesson is active.
// - An unbadged lesson is the counterpart/fallback for the other week when
//   it shares a time slot with an explicitly badged lesson.
// - A lesson with a non-matching badge is never shown.
//
// Vertretungsplan sensor selection:
// - `vertretungsplan_sensor` in the card config explicitly selects the sensor.
// - Without an explicit setting, `sensor.vertretungsplan_<klasse>` is used
//   when that entity exists, e.g. `sensor.vertretungsplan_7n`.
// - For backwards compatibility `sensor.vertretungsplan` remains the fallback.
(() => {
  const CARD_TAGS = [
    "kfg-stundenplan-card",
    "kfg-stundenplan-tag-card",
    "kfg-stundenplan-grid-card",
  ];

  const badgeValues = (badge) => {
    if (badge === null || badge === undefined || badge === "") return [];
    const values = Array.isArray(badge)
      ? badge
      : String(badge).split(/[,;/|]+/);
    return values
      .map((value) => String(value).trim().replace(/[()]/g, "").toUpperCase())
      .filter(Boolean);
  };

  const slotKey = (lesson) => {
    const start = String(lesson?.start || "").trim();
    const end = String(lesson?.end || "").trim();
    if (start || end) return `${start}|${end}`;
    return `${lesson?.index ?? ""}|${lesson?.duration ?? 1}`;
  };

  const filterDayForWeek = (day, week) => {
    const lessons = Array.isArray(day) ? day : [];
    const wanted = String(week || "").trim().toUpperCase();
    if (!wanted) return lessons.slice();

    const groups = new Map();
    const order = [];

    for (const lesson of lessons) {
      const key = slotKey(lesson);
      if (!groups.has(key)) {
        groups.set(key, []);
        order.push(key);
      }
      groups.get(key).push(lesson);
    }

    const result = [];
    for (const key of order) {
      const group = groups.get(key) || [];
      const matching = group.filter((lesson) => badgeValues(lesson?.badge).includes(wanted));
      const unbadged = group.filter((lesson) => badgeValues(lesson?.badge).length === 0);
      const hasExplicitBadges = group.some((lesson) => badgeValues(lesson?.badge).length > 0);

      if (matching.length) {
        result.push(...matching);
      } else if (hasExplicitBadges) {
        result.push(...unbadged);
      } else {
        result.push(...unbadged);
      }
    }

    return result;
  };

  const filterDaysForWeek = (days, week) =>
    (Array.isArray(days) ? days : []).map((day) => filterDayForWeek(day, week));

  const findTimetableEntity = (card, hass) => {
    const configured = card?.config?.sensor || card?.config?.entity;
    if (configured && hass?.states?.[configured]) return hass.states[configured];

    const child = String(card?.config?.child || "").trim().toLowerCase();
    if (child) {
      const byChild = Object.values(hass?.states || {}).find((state) =>
        state?.entity_id?.startsWith("sensor.") &&
        String(state?.attributes?.kind_kürzel || "").trim().toLowerCase() === child
      );
      if (byChild) return byChild;
    }

    return Object.values(hass?.states || {}).find((state) =>
      state?.entity_id?.startsWith("sensor.stundenplan") &&
      Array.isArray(state?.attributes?.eigener_plan)
    );
  };

  const entitySuffix = (value) =>
    String(value || "")
      .trim()
      .toLowerCase()
      .replace(/ä/g, "a")
      .replace(/ö/g, "o")
      .replace(/ü/g, "u")
      .replace(/ß/g, "ss")
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/^_+|_+$/g, "");

  const configuredSubstitutionSensor = (card) => {
    const value =
      card?.config?.vertretungsplan_sensor ??
      card?.config?.vertretungsplan ??
      card?.config?.substitution_sensor;
    return String(value || "").trim();
  };

  const findSubstitutionSensor = (card, hass, timetableEntity) => {
    const configured = configuredSubstitutionSensor(card);
    if (configured) {
      // Explicit configuration always wins, even if the configured entity is
      // currently unavailable. This prevents silently switching to another
      // class' Vertretungsplan.
      return hass?.states?.[configured] || null;
    }

    const childClass = String(timetableEntity?.attributes?.klasse || "").trim();
    const classSuffix = entitySuffix(childClass);
    if (classSuffix) {
      const classEntity = hass?.states?.[`sensor.vertretungsplan_${classSuffix}`];
      if (classEntity) return classEntity;
    }

    return hass?.states?.["sensor.vertretungsplan"] || null;
  };

  const hassForCard = (card, hass) => {
    const timetableEntity = findTimetableEntity(card, hass);
    if (!timetableEntity) return hass;

    const attrs = timetableEntity.attributes || {};
    const days = attrs.eigener_plan;
    const week = attrs.wochenkennung;
    const states = { ...(hass.states || {}) };
    let changed = false;

    if (Array.isArray(days) && week) {
      states[timetableEntity.entity_id] = {
        ...timetableEntity,
        attributes: {
          ...attrs,
          eigener_plan: filterDaysForWeek(days, week),
        },
      };
      changed = true;
    }

    const substitution = findSubstitutionSensor(card, hass, timetableEntity);
    if (substitution) {
      // The existing KFG cards internally read sensor.vertretungsplan. Alias
      // the selected per-class/configured entity to that legacy name so all
      // substitution and "Nachricht des Tages" logic uses the same source.
      states["sensor.vertretungsplan"] = substitution;
      changed = true;
    } else if (configuredSubstitutionSensor(card)) {
      // An explicit but unavailable entity must not fall back to a different
      // Vertretungsplan that may happen to exist in hass.states.
      delete states["sensor.vertretungsplan"];
      changed = true;
    }

    if (!changed) return hass;

    const patchedHass = Object.create(Object.getPrototypeOf(hass));
    Object.assign(patchedHass, hass);
    patchedHass.states = states;
    return patchedHass;
  };

  const patchCard = (tagName) => {
    const apply = () => {
      const Card = customElements.get(tagName);
      if (!Card || Card.prototype.__kfgWeekSelectionPatched) return;

      // Keep the old alias required by kfg-stundenplan-card.
      if (
        tagName === "kfg-stundenplan-card" &&
        !Card.prototype._entity &&
        typeof Card.prototype._findEntity === "function"
      ) {
        Card.prototype._entity = Card.prototype._findEntity;
      }

      const descriptor = Object.getOwnPropertyDescriptor(Card.prototype, "hass");
      const originalSetter = descriptor?.set;
      if (typeof originalSetter !== "function") return;

      Object.defineProperty(Card.prototype, "hass", {
        configurable: descriptor.configurable !== false,
        enumerable: descriptor.enumerable === true,
        get: descriptor.get,
        set(hass) {
          originalSetter.call(this, hassForCard(this, hass));
        },
      });

      Card.prototype.__kfgWeekSelectionPatched = true;
    };

    if (customElements.get(tagName)) {
      apply();
    } else {
      customElements.whenDefined(tagName).then(apply);
    }
  };

  CARD_TAGS.forEach(patchCard);
})();
