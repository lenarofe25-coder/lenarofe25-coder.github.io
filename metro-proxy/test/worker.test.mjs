import { test } from 'node:test';
import assert from 'node:assert/strict';
import { routeFor } from '../src/worker.js';

test('routes PRIM autorisées', () => {
  assert.ok(routeFor('stop-monitoring'));
  assert.ok(routeFor('v2/navitia/journeys'));
  assert.ok(routeFor('v2/navitia/places'));
  assert.ok(routeFor('v2/navitia/stop_areas/stop_area:IDFM:71517/departures'));
  assert.ok(routeFor('v2/navitia/stop_areas/stop_area:IDFM:71517/lines'));
});

test('routes refusées', () => {
  assert.equal(routeFor('v2/navitia/stop_areas/../../admin'), null);
  assert.equal(routeFor('autre-api'), null);
  assert.equal(routeFor('stop-monitoringX'), null);
  assert.equal(routeFor('v2/navitia//journeys'), null);
});
