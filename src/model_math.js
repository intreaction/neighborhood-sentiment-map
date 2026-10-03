// Arithmetic for illustrative project scenarios. A reference row is one observed case.
function scenarioScore(row, businesses, costMillions) {
  if (!row || row.low_support || !Number.isFinite(row.did_per_pair) ||
      !Number.isFinite(row.pairs) || row.pairs < 20 ||
      !Number.isInteger(businesses) || businesses < 1 || businesses > 100000 ||
      !Number.isFinite(costMillions) || costMillions <= 0) return null;
  const netReviews = businesses * row.did_per_pair;
  return {netReviews, ce: netReviews / costMillions};
}

// A what-if result uses editable review changes while retaining the reference
// cohort's baseline. Sun Link uses proportional growth; matched cases use
// absolute per-business changes. Neither calculation is a fitted prediction.
function scenarioScoreWithAssumptions(row, businesses, costMillions, nearChange, comparisonChange, corridor) {
  if (!row || row.low_support || !Number.isFinite(row.pairs) || row.pairs < 20 ||
      !Number.isInteger(businesses) || businesses < 1 || businesses > 100000 ||
      !Number.isFinite(costMillions) || costMillions <= 0 ||
      !Number.isFinite(nearChange) || !Number.isFinite(comparisonChange)) return null;
  let perListing;
  if (corridor) {
    if (!Number.isFinite(row.near_pre_reviews) || row.near_pre_reviews <= 0 ||
        nearChange < -100 || comparisonChange < -100) return null;
    perListing = row.near_pre_reviews / row.pairs * (nearChange - comparisonChange) / 100;
  } else {
    if (!Number.isFinite(row.near_pre_mean) || !Number.isFinite(row.near_post_mean) ||
        !Number.isFinite(row.control_pre_mean) || !Number.isFinite(row.control_post_mean) ||
        row.near_pre_mean + nearChange < 0 || row.control_pre_mean + comparisonChange < 0) return null;
    perListing = nearChange - comparisonChange;
  }
  const netReviews = businesses * perListing;
  return {netReviews, ce: netReviews / costMillions, perListing};
}

// Coefficients are fitted in Python on project outcomes; this is inference only.
// The three inputs match the training features and the historical 500 m cohort.
function trainedCeScore(model, baselineReviewed, preReviewsPerActive, costMillions) {
  if (!model || !Number.isInteger(baselineReviewed) || baselineReviewed < 20 || baselineReviewed > 100000 ||
      !Number.isFinite(preReviewsPerActive) || preReviewsPerActive < 0 ||
      !Number.isFinite(costMillions) || costMillions <= 0) return null;
  const features = [Math.log1p(preReviewsPerActive), Math.log1p(costMillions), Math.log1p(baselineReviewed)];
  if (features.some((value, i) => value < model.training_feature_min[i] || value > model.training_feature_max[i])) return null;
  const ce = model.intercept + features.reduce((sum, value, i) =>
    sum + model.coefficients[i] * (value - model.feature_means[i]) / model.feature_scales[i], 0);
  return {ce, netReviews: ce * costMillions};
}
