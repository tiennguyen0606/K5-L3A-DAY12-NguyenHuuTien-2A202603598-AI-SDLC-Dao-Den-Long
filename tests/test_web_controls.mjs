import test from 'node:test';
import assert from 'node:assert/strict';

import { nextMouseYaw } from '../web/controls.mjs';

test('mouse look rotates while movement keys are held and pointer lock is active', () => {
  const yaw = nextMouseYaw(0, 40, {
    running: true,
    paused: false,
    pointerLocked: true,
    pointerOnCanvas: false,
    pressedKeys: new Set(['w', 'd']),
  });
  assert.equal(yaw, -0.1);
});

test('canvas hover is a fallback when pointer lock is unavailable', () => {
  const yaw = nextMouseYaw(0, -20, {
    running: true,
    paused: false,
    pointerLocked: false,
    pointerOnCanvas: true,
    pressedKeys: new Set(['a']),
  });
  assert.equal(yaw, 0.05);
});

test('mouse look is frozen while paused', () => {
  const yaw = nextMouseYaw(1, 50, {
    running: true,
    paused: true,
    pointerLocked: true,
    pointerOnCanvas: true,
    pressedKeys: new Set(['w']),
  });
  assert.equal(yaw, 1);
});
