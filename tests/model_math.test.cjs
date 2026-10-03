const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const context = vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(__dirname, '../src/model_math.js'), 'utf8'), context);
const { scenarioScore, scenarioScoreWithAssumptions, trainedCeScore } = context;
const trained = JSON.parse(fs.readFileSync(path.join(__dirname, '../data/derived/ce_trained_model.json'), 'utf8'));
const learned = trainedCeScore(trained, 278, 3807 / 278, 196.5);
assert.ok(learned && Number.isFinite(learned.ce), 'Fitted coefficients score a supported full-route case');
const xs = [3807 / 278, 196.5, 278].map(Math.log1p);
const expectedCe = trained.intercept + xs.reduce((sum, x, i) =>
  sum + trained.coefficients[i] * (x - trained.feature_means[i]) / trained.feature_scales[i], 0);
assert.ok(Math.abs(learned.ce - expectedCe) < 1e-9);
assert.equal(trainedCeScore(trained, 6, 8, 196.5), null, 'Low baseline support is withheld');
assert.equal(trainedCeScore(trained, 278, 3807 / 278, 10000), null, 'Unsupported cost extrapolation is withheld');
const matched = {did_per_pair: 7.496, pairs: 498, low_support: false};
const reference = scenarioScore(matched, 498, 55);
assert.ok(reference);
assert.ok(Math.abs(reference.ce - 67.8765) < .01, 'Reference inputs reproduce the Dilworth CE benchmark');
assert.ok(Math.abs(scenarioScore(matched, 100, 20).ce - 37.48) < 1e-9,
  'Cost and local business count change the score');
const sunLinkCorridor = {did_per_pair: -2207.3422717686044 / 717, pairs: 717, low_support: false};
assert.ok(Math.abs(scenarioScore(sunLinkCorridor, 717, 196.5).ce - (-11.233294)) < .001,
  'Full-route scenario reproduces the unmatched Sun Link corridor result');
assert.equal(scenarioScore({did_per_pair: -52.5, pairs: 2, low_support: true}, 50, 10), null,
  'Two matched pairs cannot support a scenario score');
assert.equal(scenarioScore(matched, 100, 0), null);
assert.equal(scenarioScore(matched, 0, 20), null);
assert.equal(scenarioScore(matched, 2.5, 20), null);
const matchedEvidence = {
  ...matched, near_pre_mean: 30, near_post_mean: 42,
  control_pre_mean: 28, control_post_mean: 32.504,
};
const observedWhatIf = scenarioScoreWithAssumptions(matchedEvidence, 498, 55, 12, 4.504, false);
assert.ok(Math.abs(observedWhatIf.ce - reference.ce) < 1e-9,
  'Editable matched near and control changes reproduce the source difference');
assert.ok(Math.abs(scenarioScoreWithAssumptions(matchedEvidence, 498, 55, 14, 4.504, false).ce - observedWhatIf.ce - 498 * 2 / 55) < 1e-9,
  'A higher near trend increases CE by the expected amount');
assert.equal(scenarioScoreWithAssumptions(matchedEvidence, 498, 55, -31, 4, false), null,
  'Impossible negative post-period counts are rejected');
const sunEvidence = {...sunLinkCorridor, near_pre_reviews: 3807};
const sunNearGrowth = (10943 / 3807 - 1) * 100;
const sunFarGrowth = (34394 / 9957 - 1) * 100;
const sunWhatIf = scenarioScoreWithAssumptions(sunEvidence, 717, 196.5, sunNearGrowth, sunFarGrowth, true);
assert.ok(Math.abs(sunWhatIf.ce - scenarioScore(sunLinkCorridor, 717, 196.5).ce) < 1e-8,
  'Sun Link assumptions preserve the proportional full-route reference');
assert.equal(scenarioScoreWithAssumptions(sunEvidence, 717, 196.5, -101, 20, true), null,
  'Growth below minus 100 percent is rejected');
console.log('PASS: scenario arithmetic, source benchmark, support guard and invalid inputs');
