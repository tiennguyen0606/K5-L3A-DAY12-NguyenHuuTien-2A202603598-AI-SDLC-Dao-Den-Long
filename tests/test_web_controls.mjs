import test from 'node:test';
import assert from 'node:assert/strict';

import {
  DEFAULT_BINDINGS, DEFAULT_SENSITIVITY, DEFAULT_VOLUME,
  clampSensitivity, clampVolume, duplicateBindings, nextMouseYaw,
} from '../web/controls.mjs';

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

test('mouse look remains active before pointer lock is granted', () => {
  const yaw = nextMouseYaw(0, 12, {
    running: true,
    paused: false,
    pointerLocked: false,
    pointerOnCanvas: false,
    pressedKeys: new Set(['w']),
  });
  assert.equal(yaw, -0.03);
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

test('default accessibility bindings cover every required action without conflicts', () => {
  assert.deepEqual(Object.keys(DEFAULT_BINDINGS).sort(), ['backward','dash','forward','interact','jump','left','pause','pulse','right']);
  assert.deepEqual(duplicateBindings(DEFAULT_BINDINGS), []);
});

test('duplicate bindings identify both conflicting actions', () => {
  const bindings = {...DEFAULT_BINDINGS, interact: 'w'};
  assert.deepEqual(duplicateBindings(bindings), ['forward', 'interact']);
});

test('volume and sensitivity clamps keep saved settings in range', () => {
  assert.equal(clampVolume(-1), 0);
  assert.equal(clampVolume(2), 1);
  assert.equal(clampVolume('nope'), DEFAULT_VOLUME);
  assert.equal(clampSensitivity(0), DEFAULT_SENSITIVITY);
  assert.equal(clampSensitivity(0.02), 0.01);
  assert.equal(clampSensitivity(0.001), 0.001);
});
