// Browser inference shares the exported Python feature order and transforms.
// Project type supplies comparable evidence; it is never a fitted feature.
function projectEstimate(model, inputs) {
  const result = {status: 'unsupported', estimate: null, errors: {}, nearest_cases: [],
    empirical_error: null, similarity: null, notes: [], model_id: model && model.selected_model};
  if (!model || !model.candidates || !model.candidates[model.selected_model]) {
    result.errors.model = 'The fitted model is unavailable.';
    return result;
  }
  inputs = inputs || {};
  const candidate = model.candidates[model.selected_model];
  const names = candidate.feature_names;
  if (model.selected_model === 'advanced_text' && (!model.advanced_text ||
      inputs.topic_basis_version !== model.advanced_text.basis_version)) {
    result.errors.topic_basis_version = 'Advanced topic inputs must use this fitted model’s exact topic basis; descriptive topic values cannot be substituted.';
  }
  const transform = (field, value) => model.feature_schema[field].transform === 'log1p' ? Math.log1p(value) : value;
  for (const field of names) {
    const spec = model.feature_schema[field];
    const value = inputs[field];
    if (typeof value !== 'number' || !Number.isFinite(value)) {
      result.errors[field] = 'Enter a measured value or an explicit numeric assumption.';
    } else if (field === 'baseline_reviewed' && (!Number.isInteger(value) || value < 20)) {
      result.errors[field] = 'At least 20 baseline-reviewed businesses are required; use a whole number.';
    } else if (value < spec.min || value > spec.max) {
      result.errors[field] = `Outside observed support (${spec.min.toLocaleString()}–${spec.max.toLocaleString()}).`;
    }
  }
  if (Object.keys(result.errors).length) return result;
  const z = names.map((field, i) => (transform(field, inputs[field]) - candidate.feature_means[i]) / candidate.feature_scales[i]);
  const ranked = model.training_rows.map(row => {
    const distance = Math.sqrt(names.reduce((sum, field, i) => {
      const rz = (transform(field, row.inputs[field]) - candidate.feature_means[i]) / candidate.feature_scales[i];
      return sum + (z[i] - rz) ** 2;
    }, 0) / names.length);
    return {id: row.id, project: row.project, city: row.city, project_type: row.project_type,
      cost_millions: row.cost_millions, observed_ce: row.observed_ce, distance,
      same_type: Boolean(inputs.project_type && inputs.project_type === row.project_type)};
  }).sort((a, b) => a.distance - b.distance);
  const closest = ranked[0].distance;
  result.similarity = {distance: closest, threshold: candidate.similarity_threshold,
    supported: closest <= candidate.similarity_threshold + 1e-12};
  // Type preference changes only evidence ordering, never prediction/support.
  result.nearest_cases = ranked.slice().sort((a, b) => Number(b.same_type) - Number(a.same_type) || a.distance - b.distance).slice(0, 3);
  result.notes = [model.uncertainty,
    'Project type selects comparable evidence only; changing type does not change the fitted estimate.',
    'Cost is on the nominal reported historical basis; no causal budget response or inflation conversion is implied.'];
  if (Object.values(model.sensitivities || {}).some(check => check.candidates && check.mean_baseline &&
      check.candidates[model.selected_model] && check.candidates[model.selected_model].city_metrics.mae >= check.mean_baseline.city_metrics.mae)) {
    result.notes.push('The model does not outperform the mean-only comparator in every timing-exclusion sensitivity; its apparent advantage is not robust.');
  }
  if (model.selected_model === 'advanced_text') result.notes.push('Advanced text remains an exploratory challenger; reduced-case timing sensitivity has not been evaluated.');
  if (!result.similarity.supported) {
    result.errors.combination = 'Each input is in range, but this combination is farther from observed cases than the training support permits.';
    return result;
  }
  const ce = candidate.intercept + z.reduce((sum, value, i) => sum + candidate.coefficients[i] * value, 0);
  result.status = 'ok';
  result.estimate = {ce, net_reviews: ce * inputs.cost_millions};
  result.empirical_error = {low: ce - candidate.empirical_error_radius, high: ce + candidate.empirical_error_radius,
    mae: candidate.city_metrics.mae, n: candidate.city_metrics.n,
    label: 'Historical city-holdout error envelope · not a confidence interval'};
  return result;
}

if (typeof module !== 'undefined' && module.exports) module.exports = {projectEstimate};
