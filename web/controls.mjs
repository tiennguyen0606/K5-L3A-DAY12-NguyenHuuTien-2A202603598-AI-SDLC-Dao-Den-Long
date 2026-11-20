export const DEFAULT_SENSITIVITY = 0.0025;
export const DEFAULT_VOLUME = 0.55;

export const DEFAULT_BINDINGS = Object.freeze({
  forward: 'w', backward: 's', left: 'a', right: 'd', jump: ' ',
  dash: 'shift', interact: 'e', pulse: 'q', pause: 'p',
});

export function duplicateBindings(bindings) {
  const grouped = new Map();
  for (const [action, key] of Object.entries(bindings)) {
    const normalized = String(key).toLowerCase();
    grouped.set(normalized, [...(grouped.get(normalized) || []), action]);
  }
  return [...grouped.values()].filter(actions => actions.length > 1).flat().sort();
}

export function nextMouseYaw(currentYaw, movementX, state, sensitivity = DEFAULT_SENSITIVITY) {
  const canRotate = state.running && !state.paused;
  if (!canRotate) return currentYaw;
  return currentYaw - movementX * sensitivity;
}

export function clampVolume(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return DEFAULT_VOLUME;
  return Math.min(1, Math.max(0, number));
}

export function clampSensitivity(value) {
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) return DEFAULT_SENSITIVITY;
  return Math.min(0.01, Math.max(0.0005, number));
}
