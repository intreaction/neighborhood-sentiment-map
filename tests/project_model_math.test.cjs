const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {projectEstimate} = require('../src/project_model_math.js');
const model = JSON.parse(fs.readFileSync(path.join(__dirname, '../data/derived/project_model.json'), 'utf8'));

// Verify every exported Python fitted prediction in every predefined candidate.
for (const [id, candidate] of Object.entries(model.candidates)) {
  const configured = {...model, selected_model: id};
  for (const parity of candidate.parity_cases) {
    const result = projectEstimate(configured, parity.inputs);
    assert.equal(result.status, 'ok');
    assert.ok(Math.abs(result.estimate.ce - parity.ce) < 1e-9, `${id}/${parity.id} Python/browser parity`);
    assert.ok(result.empirical_error.low <= result.estimate.ce);
    assert.ok(result.empirical_error.high >= result.estimate.ce);
    assert.equal(result.nearest_cases[0].id, parity.id);
  }
}
const inputs = {...model.training_rows[0].inputs};
assert.equal(projectEstimate(model, {...inputs, cost_millions: 0}).status, 'unsupported');
assert.equal(projectEstimate(model, {...inputs, baseline_reviewed: 19}).status, 'unsupported');
assert.equal(projectEstimate(model, {...inputs, baseline_reviewed: 20.5}).status, 'unsupported');
assert.equal(projectEstimate(model, {...inputs, cost_millions: NaN}).status, 'unsupported');
assert.equal(projectEstimate(model, {...inputs, cost_millions: ''}).status, 'unsupported');
assert.equal(projectEstimate(model, {...inputs, cost_millions: Infinity}).status, 'unsupported');
assert.equal(projectEstimate(null, inputs).status, 'unsupported');
const original = projectEstimate(model, inputs);
const advancedModel = {...model, selected_model: 'advanced_text'};
assert.equal(projectEstimate(advancedModel, {...inputs, topic_basis_version: 'descriptive-other-basis'}).status, 'unsupported', 'Topic bases cannot be substituted');
const anotherType = projectEstimate(model, {...inputs, project_type: 'Unseen project type'});
assert.equal(anotherType.estimate.ce, original.estimate.ce, 'Type only changes evidence, not fitted response');
assert.match(original.empirical_error.label, /not a confidence interval/);
// Force a strict support boundary to test composite support independently of ranges.
const strict = JSON.parse(JSON.stringify(model));
strict.candidates[strict.selected_model].similarity_threshold = 0;
const mixed = {...inputs, cost_millions: inputs.cost_millions + 0.0001};
assert.ok(mixed.cost_millions < strict.feature_schema.cost_millions.max);
const unsupported = projectEstimate(strict, mixed);
assert.equal(unsupported.status, 'unsupported');
assert.ok(unsupported.errors.combination);
console.log('Project model: Python parity, inputs, type semantics and combination support passed.');
