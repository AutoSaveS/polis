#!/usr/bin/env Rscript

# Confirmatory analysis entry point. This script is intentionally not marked as
# executed until the declared R 4.3 environment and package lock are available.

required <- c("clubSandwich", "ordinal", "BradleyTerry2", "irr", "exact2x2")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) {
  stop("Missing declared analysis packages: ", paste(missing, collapse = ", "))
}

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) {
  stop("Usage: confirmatory_analysis.R <analysis_input_directory>")
}
input_dir <- normalizePath(args[[1]], mustWork = TRUE)

holm <- function(p) p.adjust(p, method = "holm")

fit_exp1 <- function(data, outcome) {
  formula <- stats::as.formula(paste0(outcome, " ~ workflow + site + decision_type + variant"))
  model <- stats::lm(formula, data = data)
  robust <- clubSandwich::vcovCR(model, cluster = data$scenario_id, type = "CR2")
  list(model = model, robust = robust, coefficient_test = clubSandwich::coef_test(model, vcov = robust))
}

fit_exp3 <- function(data, outcome = "overall_integration") {
  ordinal::clmm(
    stats::as.formula(paste0(outcome, " ~ workflow + (1|expert_id) + (1|scenario_id)")),
    data = data, link = "logit", Hess = TRUE, nAGQ = 1
  )
}

fit_resident <- function(data) {
  ordinal::clmm(
    fidelity ~ mode * city + order + (1|participant_id),
    data = data, link = "logit", Hess = TRUE, nAGQ = 1
  )
}

message("Analysis entry point validated syntactically only; no participant or study outcome data are read by this package.")

