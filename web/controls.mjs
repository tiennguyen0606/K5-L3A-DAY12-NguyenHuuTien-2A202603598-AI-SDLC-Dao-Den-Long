const DEFAULT_SENSITIVITY = 0.0025;

export function nextMouseYaw(currentYaw, movementX, state, sensitivity = DEFAULT_SENSITIVITY) {
  const canRotate = state.running
    && !state.paused
    && (state.pointerLocked || state.pointerOnCanvas);
  if (!canRotate) return currentYaw;
  return currentYaw - movementX * sensitivity;
}
