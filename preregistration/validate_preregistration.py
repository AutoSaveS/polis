#!/usr/bin/env python3
"""Validate structure and optional freeze readiness of the POLIS preregistration."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_csv(relative_path: str) -> list[dict[str, str]]:
    with (ROOT / relative_path).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def csv_fields(relative_path: str) -> list[str]:
    with (ROOT / relative_path).open(newline="", encoding="utf-8") as stream:
        return csv.DictReader(stream).fieldnames or []


params_text = (ROOT / "parameters.yaml").read_text(encoding="utf-8")


def yaml_section(name: str) -> str:
    lines = params_text.splitlines()
    start = next((i for i, line in enumerate(lines) if line == f"{name}:"), None)
    require(start is not None, f"Missing YAML section: {name}")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i] and not lines[i].startswith(" "):
            end = i
            break
    return "\n".join(lines[start + 1 : end])


def section_scalar(section: str, key: str) -> str:
    text = yaml_section(section)
    match = re.search(rf"^  {re.escape(key)}:\s*([^#\n]+)$", text, re.MULTILINE)
    require(match is not None, f"Missing YAML key: {section}.{key}")
    return match.group(1).strip().strip('"')


def as_bool(value: str) -> bool:
    require(value in {"true", "false"}, f"Expected YAML boolean, got {value}")
    return value == "true"


scenarios = read_csv("scenarios.csv")
sources = read_csv("inputs/source_inventory.csv")
need_profiles = read_csv("inputs/need_profiles.csv")
need_predicates = read_csv("inputs/need_predicates.csv")
site_constraints = read_csv("constraints/site_constraints.csv")
real_project_confirmation_log = read_csv("constraints/real_project_confirmation_log.template.csv")
tolerances = read_csv("constraints/design_parameter_tolerances.csv")
human_template = read_csv("inputs/human_need_profile_collection_template.csv")
resident_session_template = read_csv("inputs/resident_session_collection_template.csv")
expert_instrument = read_csv("protocols/expert_rating_instrument.csv")
resident_instrument = read_csv("protocols/resident_instrument.csv")
resident_randomisation = read_csv("protocols/resident_randomisation.csv")
operator_roles = read_csv("protocols/operator_roles.csv")
operator_assignment_plan = read_csv("protocols/operator_assignment_plan.csv")
operator_training_log = read_csv("protocols/operator_training_log.template.csv")
expert_timing_pilot_log = read_csv("protocols/expert_timing_pilot_log.template.csv")
author_threshold_inventory = read_csv("protocols/author_threshold_inventory.csv")
seeds = read_csv("seeds.csv")
model_manifest_text = (ROOT / "software/model_manifest.yaml").read_text(encoding="utf-8")
model_config = json.loads((ROOT / "software/openai_responses_config.json").read_text(encoding="utf-8"))
prompt_schema_manifest = read_csv("software/prompt_schema_manifest.csv")
api_preflight_result = json.loads((ROOT / "software/api_preflight_result.json").read_text(encoding="utf-8"))
smoke_result = json.loads((ROOT / "analysis/synthetic_smoke_test_result.json").read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_strict_schema(node: object, location: str) -> None:
    require(isinstance(node, dict), f"Schema node must be an object: {location}")
    if node.get("type") == "object":
        properties = node.get("properties")
        require(isinstance(properties, dict), f"Object schema lacks properties: {location}")
        require(node.get("additionalProperties") is False, f"Object schema must set additionalProperties=false: {location}")
        required = node.get("required")
        require(isinstance(required, list) and set(required) == set(properties), f"Every object property must be required: {location}")
        for key, child in properties.items():
            validate_strict_schema(child, f"{location}.properties.{key}")
    if "items" in node:
        validate_strict_schema(node["items"], f"{location}.items")
    for combinator in ("anyOf", "allOf", "oneOf"):
        if combinator in node:
            require(isinstance(node[combinator], list), f"{combinator} must be an array: {location}")
            for index, child in enumerate(node[combinator]):
                validate_strict_schema(child, f"{location}.{combinator}[{index}]")


# Protocol and ethics boundaries.
require(section_scalar("protocol", "status") == "NOT_YET_REGISTERED", "Unexpected protocol status")
require(section_scalar("protocol", "study_structure") == "3_experiments_2_case_studies", "Study structure mismatch")
require(section_scalar("expert_ethics_approval", "status") == "APPROVED", "Expert ethics approval missing")
require(section_scalar("expert_ethics_approval", "application_number") == "11000110520260706104327", "Wrong expert ethics application")
require(section_scalar("expert_ethics_approval", "approval_date") == "2026-07-06", "Wrong expert approval date")
require(int(section_scalar("expert_ethics_approval", "approved_participant_min")) == 8, "Expert minimum must be 8")
require(int(section_scalar("expert_ethics_approval", "approved_participant_max")) == 12, "Expert maximum must be 12")
require(section_scalar("expert_ethics_approval", "public_or_resident_participants") == "none", "Expert approval must not be extended to residents")
resident_ethics_status = section_scalar("resident_ethics", "status")
require(resident_ethics_status in {"PENDING_NEW_APPLICATION", "APPROVED"}, "Invalid resident ethics status")
if resident_ethics_status == "PENDING_NEW_APPLICATION":
    require(int(section_scalar("resident_ethics", "approved_participant_count")) == 0, "Do not assert approved residents before approval")
    require(int(section_scalar("resident_ethics", "approved_participant_max")) == 0, "Do not assert an approved resident maximum before approval")
    require(not as_bool(section_scalar("resident_ethics", "recruitment_allowed")), "Resident recruitment must be disabled")
    require(not as_bool(section_scalar("resident_ethics", "data_collection_allowed")), "Resident data collection must be disabled")
else:
    require(section_scalar("resident_ethics", "application_number") != "TO_BE_ASSIGNED", "Approved resident ethics requires an application number")
    require(section_scalar("resident_ethics", "approval_date") != "TO_BE_ASSIGNED", "Approved resident ethics requires an approval date")
    require(int(section_scalar("resident_ethics", "approved_participant_max")) >= 60, "Resident approval must cover the prespecified consent cap")
    require(as_bool(section_scalar("resident_ethics", "recruitment_allowed")), "Approved resident study must explicitly enable recruitment")
    require(as_bool(section_scalar("resident_ethics", "data_collection_allowed")), "Approved resident study must explicitly enable data collection")

require(int(section_scalar("design", "total_scenarios")) == 36, "Expected 36 scenarios")
require(int(section_scalar("design", "exp2_scenarios")) == 12, "Expected 12 Experiment 2 scenarios")
require(int(section_scalar("design", "exp2_configurations")) == 6, "Expected six Experiment 2 configurations")
require(int(section_scalar("design", "exp2_total_runs")) == 72, "Expected 72 Experiment 2 runs")
require(int(section_scalar("design", "exp3_target_experts")) == 12, "Expert target must be 12")
require(int(section_scalar("design", "exp3_scenarios_per_expert")) == 9, "Each expert must receive nine scenarios")
require(int(section_scalar("design", "exp3_outputs_per_expert")) == 27, "Each expert must receive 27 outputs")
require(int(section_scalar("design", "exp3_experts_per_output")) == 3, "Each output must be allocated to three expert slots")
require(int(section_scalar("design", "minimum_real_operators")) == 3, "At least three real operators are required")
require(int(section_scalar("design", "active_workflow_assignments")) == 108, "Expected 108 active workflow assignments")
require(section_scalar("analysis_execution_readiness", "registered_runtime") == "R 4.3.3", "Registered analysis runtime must be R 4.3.3")
require(as_bool(section_scalar("analysis_execution_readiness", "python_structural_smoke_test_passed")), "Python structural smoke test must be recorded as passed")
require(int(section_scalar("llm_configuration", "api_preflight_live_schema_requests")) == 4, "API preflight must contain four live schema requests")
require(int(section_scalar("llm_configuration", "api_preflight_local_refusal_fixtures")) == 1, "API preflight must contain one local refusal fixture")

require(as_bool(section_scalar("case_studies", "case2_online_only")), "Resident case must be fully online")
require(int(section_scalar("case_studies", "case2_target_analysable_per_city")) == 15, "Resident target must be 15 per city")
require(int(section_scalar("case_studies", "case2_max_consent_per_city")) == 20, "Resident consent cap must be 20 per city")
require(int(section_scalar("case_studies", "case2_target_total_analysable")) == 45, "Resident total target must be 45")
require(int(section_scalar("case_studies", "case2_max_consent_total")) == 60, "Resident total consent cap must be 60")
require(int(section_scalar("case_studies", "case2_fidelity_scale_min")) == 1, "Fidelity minimum must be 1")
require(int(section_scalar("case_studies", "case2_fidelity_scale_max")) == 7, "Fidelity maximum must be 7")
require(int(section_scalar("case_studies", "case2_trace_comprehension_items")) == 4, "Expected four comprehension items")
require(not as_bool(section_scalar("case_studies", "case2_exact_address_collection")), "Exact address collection must be disabled")
require(section_scalar("case_studies", "case2_population_representativeness") == "prohibited", "Population representativeness disclaimer missing")


# Scenario frame and deterministic seeds.
require(len(scenarios) == 36, "Expected 36 scenario rows")
require(len({row["scenario_id"] for row in scenarios}) == 36, "Scenario IDs must be unique")
site_counts = Counter(row["site"] for row in scenarios)
decision_counts = Counter(row["decision_type"] for row in scenarios)
variant_counts = Counter(row["variant"] for row in scenarios)
require(site_counts == {"Suzhou": 12, "London": 12, "Chicago": 12}, f"Site imbalance: {site_counts}")
require(set(decision_counts.values()) == {6}, f"Decision imbalance: {decision_counts}")
require(variant_counts == {"B": 18, "S": 18}, f"Variant imbalance: {variant_counts}")
require("exp3_seed" not in csv_fields("scenarios.csv"), "Old efficiency Experiment 3 seed must be removed")

exp2 = [row for row in scenarios if row["exp2_included"] == "yes"]
require(len(exp2) == 12, "Experiment 2 must contain 12 scenarios")
require(Counter(row["site"] for row in exp2) == {"Suzhou": 4, "London": 4, "Chicago": 4}, "Experiment 2 site imbalance")
require({row["decision_type"] for row in exp2} == {"GE", "AR", "EA", "IP"}, "Wrong Experiment 2 subset")
require({row["variant"] for row in exp2} == {"B"}, "Experiment 2 must use base variants")

exp1_seeds = [int(row["exp1_seed"]) for row in scenarios]
require(len(exp1_seeds) == len(set(exp1_seeds)), "Duplicate Experiment 1 seeds")
exp2_seeds = [int(row["exp2_seed"]) for row in exp2]
require(len(exp2_seeds) == len(set(exp2_seeds)), "Duplicate Experiment 2 seeds")
for row in scenarios:
    site_index = int(row["site_index"])
    decision_index = int(row["decision_index"])
    variant_index = 1 if row["variant"] == "B" else 2
    require(int(row["exp1_seed"]) == 100000 + site_index * 10000 + decision_index * 100 + variant_index, f"Wrong Experiment 1 seed for {row['scenario_id']}")
    if row["exp2_included"] == "yes":
        require(int(row["exp2_seed"]) == 200000 + site_index * 10000 + decision_index * 100 + 1, f"Wrong Experiment 2 seed for {row['scenario_id']}")
    else:
        require(row["exp2_seed"] == "", f"Unexpected Experiment 2 seed for {row['scenario_id']}")
    expected = ("8", "2", "2", "1.00") if row["variant"] == "B" else ("10", "3", "4", "0.80")
    actual = (row["need_count"], row["critical_need_count"], row["conflict_count"], row["budget_multiplier"])
    require(actual == expected, f"Wrong scenario settings for {row['scenario_id']}")

seed_purposes = {row["purpose"] for row in seeds}
require("exp3_process" not in seed_purposes, "Old quality-resource efficiency seed remains")
require({"exp1_scenario", "exp2_ablation", "exp3_expert_allocation", "exp3_expert_output_order", "case1_deviation", "case2_resident_order"} <= seed_purposes, "Required seed purposes missing")


# Analytical need profiles and conflicts.
source_ids = {row["source_id"] for row in sources}
require(len(sources) == len(source_ids), "Source IDs must be unique")
require("INT-PREREG" in source_ids, "Missing internal preregistration source")
require(len(need_profiles) == 60 and len(need_predicates) == 60, "Expected 60 needs and 60 predicates")
require(len({row["need_id"] for row in need_profiles}) == 60, "Need IDs must be unique")
require(len({row["predicate_id"] for row in need_predicates}) == 60, "Predicate IDs must be unique")
require({row["need_id"] for row in need_profiles} == {row["need_id"] for row in need_predicates}, "Every need must have one predicate")

expected_base = {"access_mobility": 2, "shade_comfort": 2, "ecology": 1, "activity_use": 1, "maintenance_budget": 1, "vulnerable_group_priority": 1}
site_codes = {"Suzhou": "SUZ", "London": "LON", "Chicago": "CHI"}
for site, code in site_codes.items():
    site_needs = [row for row in need_profiles if row["site"] == site]
    core = [row for row in site_needs if row["stress_only"] == "no"]
    stress = [row for row in site_needs if row["stress_only"] == "yes"]
    require(len(core) == 8 and len(stress) == 12, f"Wrong need counts for {site}")
    require(Counter(row["need_class"] for row in core) == expected_base, f"Wrong base composition for {site}")
    require(sum(row["criticality"] == "critical" for row in core) == 2, f"Wrong critical core count for {site}")
    require(all(row["scenario_applicability"] == f"{code}-ALL" for row in core), f"Wrong core applicability for {site}")
    for decision_type in ("GE", "AR", "CU", "RR", "EA", "IP"):
        additions = [row for row in stress if row["decision_type"] == decision_type]
        require(len(additions) == 2, f"{site} {decision_type} must have two additions")
        require(sum(row["criticality"] == "critical" for row in additions) == 1, f"{site} {decision_type} critical addition mismatch")
        require(sum(row["priority"] == "high" and row["criticality"] != "critical" for row in additions) == 1, f"{site} {decision_type} high-priority addition mismatch")

for need in need_profiles:
    require(need["source_id"] in source_ids, f"Unknown source for need {need['need_id']}")
    require("Not elicited from residents" in need["interpretation_note"], f"Need {need['need_id']} lacks participant disclaimer")
for predicate in need_predicates:
    require(predicate["source_id"] in source_ids and predicate["pass_logic"], f"Invalid predicate {predicate['predicate_id']}")

for scenario in scenarios:
    code = {1: "SUZ", 2: "LON", 3: "CHI"}[int(scenario["site_index"])]
    applicable = [row for row in need_profiles if row["scenario_applicability"] in {f"{code}-ALL", scenario["scenario_id"]}]
    require(len(applicable) == int(scenario["need_count"]), f"Wrong need count for {scenario['scenario_id']}")
    require(sum(row["criticality"] == "critical" for row in applicable) == int(scenario["critical_need_count"]), f"Wrong critical count for {scenario['scenario_id']}")
    ids = {row["need_id"] for row in applicable}
    edges: set[tuple[str, str]] = set()
    for need in applicable:
        for linked in filter(None, need["conflict_links"].split("|")):
            require(linked in ids, f"Unavailable conflict target {linked} in {scenario['scenario_id']}")
            edges.add(tuple(sorted((need["need_id"], linked))))
    require(len(edges) == int(scenario["conflict_count"]), f"Wrong conflict count for {scenario['scenario_id']}")


# Official-source constraints and thresholds.
require(len(site_constraints) == len({row["constraint_id"] for row in site_constraints}), "Constraint IDs must be unique")
require(Counter(row["site"] for row in site_constraints).keys() == {"Suzhou", "London", "Chicago"}, "Constraints must cover all sites")
allowed_classes = {"binding_regulation", "binding_standard", "binding_federal_standard", "planning_policy", "official_guidance", "official_site_record"}
for row in site_constraints:
    cid = row["constraint_id"]
    require(row["source_id"] in source_ids and row["source_id"] != "INT-PREREG", f"Invalid source for {cid}")
    for field in ("database_name", "instrument_title", "issuing_authority", "section", "effective_date_or_version", "official_url", "verbatim_rule_summary", "applicability_condition", "source_text_status", "study_evaluator_applicability", "study_applicability_basis", "real_project_applicability_status", "real_project_confirmation_required", "confirmation_authority", "predicate", "verification_status", "hard_or_soft"):
        require(row[field], f"Constraint {cid} lacks {field}")
    require(row["instrument_class"] in allowed_classes, f"Invalid instrument class for {cid}")
    require(row["official_url"].startswith("https://"), f"Constraint {cid} lacks an official HTTPS URL")
    if row["operator"] in {"review", "qualitative"}:
        require(row["threshold"] == "", f"Non-numeric constraint {cid} must not assert a threshold")
    else:
        require(row["threshold"] != "", f"Numeric constraint {cid} lacks a threshold")
    if row["instrument_class"] in {"planning_policy", "official_guidance", "official_site_record"}:
        require(not row["hard_or_soft"].startswith("binding"), f"Non-regulatory instrument marked binding: {cid}")
    require(row["study_evaluator_applicability"] in {"conditional_screening_rule_frozen", "reference_only_not_scored"}, f"Invalid study applicability state for {cid}")
    require("pending" not in row["study_evaluator_applicability"], f"Study applicability is not frozen for {cid}")
    require(row["real_project_confirmation_required"] in {"yes", "no"}, f"Invalid real-project confirmation flag for {cid}")
    if row["real_project_confirmation_required"] == "yes":
        require(row["confirmation_authority"], f"Constraint {cid} lacks a confirmation authority")

by_constraint = {row["constraint_id"]: row for row in site_constraints}
require(by_constraint["SUZ-C04"]["section"] == "Article 41(3)", "Suzhou square-land citation mismatch")
require(by_constraint["SUZ-C10"]["threshold"] == "", "Unverified GB 55019 number must remain blank")
require(by_constraint["SUZ-C10"]["study_evaluator_applicability"] == "reference_only_not_scored", "Unverified GB 55019 clauses must not be scored")
require(by_constraint["CHI-C09"]["threshold"] == "1" and by_constraint["CHI-C09"]["unit"] == "tree per 125 ft2", "Chicago interior-tree density mismatch")
require(by_constraint["CHI-C11"]["threshold"] == "15000" and by_constraint["CHI-C12"]["threshold"] == "7500", "Chicago stormwater trigger mismatch")
require(by_constraint["LON-C03"]["instrument_class"] == "binding_regulation", "BNG classification mismatch")

pending_real_project_ids = {
    row["constraint_id"]
    for row in site_constraints
    if "pending" in row["real_project_applicability_status"].lower()
    or "pending" in row["verification_status"].lower()
}
require(len(pending_real_project_ids) == 34, "Expected 34 unresolved real-project constraint records")
require({row["constraint_id"] for row in real_project_confirmation_log} == pending_real_project_ids, "Real-project confirmation log does not match the pending constraint set")
require(len(real_project_confirmation_log) == len({row["constraint_id"] for row in real_project_confirmation_log}), "Duplicate real-project confirmation log IDs")
for row in real_project_confirmation_log:
    require(row["confirmed_status"] in {"pending", "confirmed_applicable", "confirmed_not_applicable", "superseded"}, f"Invalid project confirmation state for {row['constraint_id']}")
    require(row["confirmation_question"] and row["required_authority"], f"Incomplete project confirmation question for {row['constraint_id']}")

expected_targets = {"A_green_min": 0.80, "E_equity_min": 0.80, "C_comfort_min": 0.60, "P_ret_min": 0.80, "critical_need_retention_min": 1.00, "I_impl_min": 0.95}
quality_text = yaml_section("quality_target")
for key, expected in expected_targets.items():
    match = re.search(rf"^  {key}:\s*([^\n]+)$", quality_text, re.MULTILINE)
    require(match is not None and float(match.group(1)) == expected, f"Unexpected target {key}")
require(float(section_scalar("shared_hard_constraints", "wheelchair_turning_diameter_m_min")) == 1.525, "Common circular turning diameter must be 1.525 m")
for code in site_codes.values():
    predicate = next(row for row in need_predicates if row["predicate_id"] == f"{code}-N08-P")
    require(predicate["target_value"] == "1.525;0.75", f"Wrong turning threshold in {code}-N08-P")
require(len(tolerances) >= 8 and all(row["source_id"] in source_ids for row in tolerances), "Tolerance table incomplete")


# Human-participant instruments, templates, and randomisation.
require(human_template == [], "Resident mode-level template must contain no fabricated participant rows")
require(resident_session_template == [], "Resident session-level template must contain no fabricated participant rows")
human_fields = set(csv_fields("inputs/human_need_profile_collection_template.csv"))
for field in ("record_id", "participant_id", "need_statement_verbatim", "mode_order", "mode", "fidelity_rating_1_7", "material_correction_count", "consent_confirmed", "exclusion_reason"):
    require(field in human_fields, f"Resident data template lacks {field}")
require(not any("address" in field.lower() or "postcode" in field.lower() or "zip" in field.lower() for field in human_fields), "Resident template must not collect exact address or postcode")
session_fields = set(csv_fields("inputs/resident_session_collection_template.csv"))
for field in ("participant_id", "comprehension_source_correct", "comprehension_decision_correct", "comprehension_parameter_correct", "comprehension_trigger_correct", "voice_rating_1_7", "fairness_rating_1_7", "trust_rating_1_7", "usability_rating_1_7", "burden_rating_1_7", "exclusion_reason"):
    require(field in session_fields, f"Resident session template lacks {field}")
require(not any("address" in field.lower() or "postcode" in field.lower() or "zip" in field.lower() for field in session_fields), "Resident session template must not collect exact address or postcode")

expert_ratings = [row for row in expert_instrument if row["item_type"] == "rating"]
require({row["construct"] for row in expert_ratings} == {"stakeholder_responsiveness", "spatial_coherence", "constructability", "equity_sensitivity", "overall_integration"}, "Expert dimensions mismatch")
require(all((row["scale_min"], row["scale_max"]) == ("1", "7") for row in expert_ratings), "Expert ratings must use seven points")
require(all(row["item_id"].startswith("EXP3-") for row in expert_instrument), "Expert instrument must be labelled Experiment 3")

resident_primary = [row for row in resident_instrument if row["analysis_role"] == "primary"]
require(len(resident_primary) == 1 and resident_primary[0]["construct"] == "participant_confirmed_need_fidelity", "Resident primary outcome mismatch")
require((resident_primary[0]["scale_min"], resident_primary[0]["scale_max"]) == ("1", "7"), "Resident fidelity must use seven points")
comprehension = [row for row in resident_instrument if row["construct"] in {"source_need", "design_decision", "affected_parameter", "review_trigger"}]
require(len(comprehension) == 4, "Resident instrument must contain four comprehension items")
for construct in ("perceived_voice", "procedural_fairness", "trust", "usability", "burden"):
    rows = [row for row in resident_instrument if row["construct"] == construct]
    require(len(rows) == 1 and (rows[0]["scale_min"], rows[0]["scale_max"]) == ("1", "7"), f"Resident {construct} item missing or wrong")

require(len(resident_randomisation) == 60, "Expected 60 resident consent slots")
require(len({row["allocation_id"] for row in resident_randomisation}) == 60, "Resident allocation IDs must be unique")
for city, city_index in (("SUZ", 1), ("LON", 2), ("CHI", 3)):
    rows = [row for row in resident_randomisation if row["city"] == city]
    require(len(rows) == 20, f"{city} must have 20 consent slots")
    require({int(row["consent_slot"]) for row in rows} == set(range(1, 21)), f"{city} slot numbers mismatch")
    require(Counter(row["mode_order"] for row in rows) == {"TEXT_THEN_SPATIAL": 10, "SPATIAL_THEN_TEXT": 10}, f"{city} mode order is not balanced")
    seed = 800000 + city_index
    ranked = sorted(range(1, 21), key=lambda slot: hashlib.sha256(f"{seed}:{slot}".encode()).hexdigest())
    text_first = set(ranked[:10])
    expected_order = {slot: ("TEXT_THEN_SPATIAL" if slot in text_first else "SPATIAL_THEN_TEXT") for slot in range(1, 21)}
    for row in rows:
        slot = int(row["consent_slot"])
        require(int(row["city_seed"]) == seed and row["mode_order"] == expected_order[slot], f"Wrong frozen resident order for {row['allocation_id']}")

require(len(operator_assignment_plan) == 108, "Expected 108 planned active-workflow assignments")
require(len({row["assignment_id"] for row in operator_assignment_plan}) == 108, "Operator assignment IDs must be unique")
for scenario in scenarios:
    rows = [row for row in operator_assignment_plan if row["scenario_id"] == scenario["scenario_id"]]
    require({row["workflow"] for row in rows} == {"CONVENTIONAL", "DIGITAL", "POLIS"}, f"Wrong operator workflows for {scenario['scenario_id']}")
    require(len({row["planned_operator_slot"] for row in rows}) == 3, f"Operator slots repeat within {scenario['scenario_id']}")
for slot in ("OP_SLOT01", "OP_SLOT02", "OP_SLOT03"):
    rows = [row for row in operator_assignment_plan if row["planned_operator_slot"] == slot]
    require(Counter(row["workflow"] for row in rows) == {"CONVENTIONAL": 12, "DIGITAL": 12, "POLIS": 12}, f"Unbalanced workflow allocation for {slot}")
for row in operator_training_log:
    require(re.fullmatch(r"OP\d{2,}", row["operator_id"]) is not None, "Operator training log must use coded IDs")
    require(float(row["active_training_minutes"]) >= 120, f"Insufficient training time for {row['operator_id']}")
    require(row["completed_all_modules"].lower() == "yes" and row["pi_verified"].lower() == "yes", f"Incomplete training verification for {row['operator_id']}")
for row in expert_timing_pilot_log:
    require(re.fullmatch(r"PILOT\d{2,}", row["pilot_id"]) is not None, "Timing pilot must use coded IDs")
    require(row["completed_all_items"].lower() == "yes", f"Incomplete timing task for {row['pilot_id']}")
    require(30 <= float(row["elapsed_minutes"]) <= 60, f"Timing pilot outside approved range for {row['pilot_id']}")

require(len(author_threshold_inventory) >= 100, "Author threshold inventory is incomplete")
require(len({row["yaml_path"] for row in author_threshold_inventory}) == len(author_threshold_inventory), "Duplicate threshold inventory paths")
require(all(row["decision"] in {"pending_author_and_pi_approval", "approved_unchanged", "approved_with_amendment"} for row in author_threshold_inventory), "Invalid threshold approval decision")
require("manifest_status: FROZEN_FOR_PREREGISTRATION_API_PREFLIGHT_PENDING" in model_manifest_text, "Model manifest must be frozen with API preflight pending")
require(model_config == {
    "provider": "OpenAI",
    "endpoint": "/v1/responses",
    "primary_model": "gpt-5.6-terra",
    "reasoning": {"effort": "medium", "context": "current_turn"},
    "store": False,
    "max_output_tokens": 8192,
    "structured_outputs": "strict_json_schema",
    "logical_agents": ["demand_capture", "conflict_detection", "equity_guardian", "orchestrator"],
    "same_model_for_all_agents": True,
    "hosted_tools_enabled": False,
    "web_search_enabled": False,
    "file_search_enabled": False,
    "provider_multi_agent_beta_enabled": False,
    "participant_data_allowed": False,
    "primary_response_rule": "first_schema_valid_non_refusal_response",
    "schema_invalid_retry_limit": 1,
    "sampling_seed_claimed": False,
    "temperature_or_top_p_sent": False,
    "sensitivity_model": "gpt-5.6-sol",
    "sensitivity_scope": "same 12 Experiment 2 base scenarios; Full POLIS only; descriptive appendix",
}, "OpenAI Responses configuration differs from the frozen Terra registration")
require("model_id: gpt-5.6-terra" in model_manifest_text, "Primary Terra model is missing from model manifest")
require("model_id: gpt-5.6-sol" in model_manifest_text, "Sol sensitivity model is missing from model manifest")
require("descriptive_appendix_only" in model_manifest_text and "inferential_tests: prohibited" in model_manifest_text, "Sol sensitivity must remain descriptive and non-inferential")
require("one retry with the identical frozen input plus the schema-validation error" in model_manifest_text, "Model retry policy is not frozen correctly")

expected_artifacts = {
    "software/openai_responses_config.json",
    "software/prompts/demand_capture.txt",
    "software/prompts/conflict_detection.txt",
    "software/prompts/equity_guardian.txt",
    "software/prompts/orchestrator.txt",
    "software/schemas/demand_capture.schema.json",
    "software/schemas/conflict_detection.schema.json",
    "software/schemas/equity_guardian.schema.json",
    "software/schemas/orchestrator.schema.json",
}
require({row["relative_path"] for row in prompt_schema_manifest} == expected_artifacts, "Prompt/schema artifact manifest has the wrong file set")
for row in prompt_schema_manifest:
    artifact_path = ROOT / row["relative_path"]
    require(artifact_path.is_file(), f"Frozen model artifact is missing: {row['relative_path']}")
    require(sha256_file(artifact_path) == row["sha256"], f"Frozen model artifact hash mismatch: {row['relative_path']}")
require(sha256_file(ROOT / "software/prompt_schema_manifest.csv") == "130116b72570e9c488750bdb45be0911a3433097390151297d26883f78dc269d", "Prompt/schema manifest hash mismatch")
for schema_path in sorted((ROOT / "software/schemas").glob("*.schema.json")):
    validate_strict_schema(json.loads(schema_path.read_text(encoding="utf-8")), schema_path.name)
require(api_preflight_result["status"] in {
    "OFFLINE_CONTRACT_CHECK_ONLY",
    "BLOCKED_NO_OPENAI_API_KEY",
    "FAILED_LIVE_PREFLIGHT",
    "PASSED_LIVE_SCHEMAS_AND_LOCAL_REFUSAL_HANDLER",
}, "Unknown API preflight status")
require(api_preflight_result["model"] == "gpt-5.6-terra", "API preflight uses the wrong model")
require(api_preflight_result["endpoint"] == "/v1/responses", "API preflight uses the wrong endpoint")
require(api_preflight_result["synthetic_input_only"] is True, "API preflight must use synthetic inputs only")
require(api_preflight_result["participant_data_used"] is False, "API preflight must not use participant data")
require(set(api_preflight_result["schema_request_contracts_passed"]) == {"demand_capture", "conflict_detection", "equity_guardian", "orchestrator"}, "Offline API schema contracts are incomplete")
require(api_preflight_result["local_refusal_handler_passed"] is True, "Local API refusal handler did not pass")
if api_preflight_result["status"] == "PASSED_LIVE_SCHEMAS_AND_LOCAL_REFUSAL_HANDLER":
    expected_live_requests = int(section_scalar("llm_configuration", "api_preflight_live_schema_requests"))
    require(api_preflight_result["network_requests_sent"] == expected_live_requests, "Live API preflight has the wrong request count")
    require(len(api_preflight_result["live_results"]) == expected_live_requests, "Live API preflight lacks result records")
require(smoke_result["status"] == "PASSED_STRUCTURAL_SMOKE_ONLY" and smoke_result["seed"] == 700001, "Synthetic structural smoke test did not pass")
require(smoke_result["exp1_rows"] == 720 and smoke_result["exp2_rows"] == 72, "Synthetic smoke-test row counts mismatch")

for relative_path, phrases in {
    "protocols/resident_eligibility.md": ["18 years", "1-km", "once per month", "Exact home"],
    "protocols/resident_online_SOP.md": ["fully online", "before approval", "fidelity", "four comprehension"],
    "protocols/resident_data_SOP.md": ["Never request an exact address", "generative-AI", "No missing primary fidelity value is imputed"],
}.items():
    text = (ROOT / relative_path).read_text(encoding="utf-8")
    for phrase in phrases:
        require(phrase in text, f"{relative_path} lacks required rule: {phrase}")

protocol_text = (ROOT / "POLIS_preregistration.md").read_text(encoding="utf-8")
for phrase in ("Experiment 1", "Experiment 2", "Experiment 3", "Case Study 1", "Case Study 2", "Scenario generation rules", "Outcomes and fixed thresholds", "Stopping rules", "Statistical models", "Exclusion, failure, and missing-data rules", "fidelity ~ mode * city + order + (1 | participant_id)"):
    require(phrase in protocol_text, f"Main protocol lacks: {phrase}")
require("Experiment 4" not in protocol_text, "Old Experiment 4 label remains")
require("quality-resource efficiency" not in protocol_text.lower(), "Old efficiency experiment remains")
require("descriptive reproducibility information" in protocol_text, "Resource reporting must be descriptive only")
require("gpt-5.6-terra" in protocol_text and "gpt-5.6-sol" in protocol_text, "Protocol lacks the registered primary or sensitivity model")
require("same-model single-agent baseline" in protocol_text, "Protocol lacks the A4 same-model single-agent definition")
require("seventh Experiment 2 configuration" in protocol_text, "Protocol must keep Sol outside the Experiment 2 configuration family")


def freeze_blockers() -> list[str]:
    blockers: list[str] = []
    readiness_text = yaml_section("readiness")
    for match in re.finditer(r"^  ([a-z0-9_]+):\s*(true|false)$", readiness_text, re.MULTILINE):
        if match.group(2) != "true":
            blockers.append(f"readiness flag is false: {match.group(1)}")

    if section_scalar("resident_ethics", "status") != "APPROVED":
        blockers.append("resident ethics approval has not been obtained")
    if not operator_roles:
        blockers.append("operator_roles.csv has no real operator assignments")
    else:
        if len(operator_roles) < 3:
            blockers.append("fewer than three real coded operators are registered")
        required_operator_fields = ("operator_id", "workflow_authorisation", "relevant_experience_years", "qualification_basis", "training_completed_utc", "practice_task_id", "practice_task_passed", "scenario_assignment_file", "conflict_check_complete", "verified_by", "verification_date_utc")
        for index, row in enumerate(operator_roles, start=2):
            if any(not row[field] for field in required_operator_fields):
                blockers.append(f"operator_roles.csv row {index} is incomplete")
                continue
            if not re.fullmatch(r"OP\d{2,}", row["operator_id"]):
                blockers.append(f"operator_roles.csv row {index} must use a coded ID such as OP01")
            try:
                if float(row["relevant_experience_years"]) < 1:
                    blockers.append(f"operator_roles.csv row {index} has less than one year of relevant experience")
            except ValueError:
                blockers.append(f"operator_roles.csv row {index} has a non-numeric experience value")
            if row["practice_task_passed"].lower() != "yes" or row["conflict_check_complete"].lower() != "yes":
                blockers.append(f"operator_roles.csv row {index} lacks a passed practice task or completed conflict check")
            public_row_text = " ".join(row.values())
            if "@" in public_row_text:
                blockers.append(f"operator_roles.csv row {index} contains an email address; keep direct identifiers in the restricted linkage table")

    unmapped_assignments = [row for row in operator_assignment_plan if not row["real_operator_id"] or row["assignment_status"] != "verified_real_assignment" or row["pi_verified"].lower() != "yes"]
    if unmapped_assignments:
        blockers.append(f"{len(unmapped_assignments)} planned workflow assignments are not mapped to PI-verified real operator IDs")
    if len({row["operator_id"] for row in operator_training_log}) < 3:
        blockers.append("fewer than three real operators have PI-verified training records")
    if len(expert_timing_pilot_log) < 3 or any(row["pass_status"].lower() != "pass" for row in expert_timing_pilot_log):
        blockers.append("the real non-study expert timing pilot lacks three complete passing records")

    if api_preflight_result["status"] != "PASSED_LIVE_SCHEMAS_AND_LOCAL_REFUSAL_HANDLER":
        blockers.append(f"live four-schema Terra API preflight has not passed: {api_preflight_result['status']}")

    pending_thresholds = [row for row in author_threshold_inventory if row["decision"].startswith("pending")]
    if pending_thresholds:
        blockers.append(f"{len(pending_thresholds)} numeric settings await author and PI approval")
    unfrozen_study_constraints = [row["constraint_id"] for row in site_constraints if "pending" in row["study_evaluator_applicability"].lower()]
    if unfrozen_study_constraints:
        blockers.append(f"{len(unfrozen_study_constraints)} constraint rows still lack a frozen study-evaluator applicability rule")

    pending_expert_items = [row["item_id"] for row in expert_instrument if row["approved_wording_status"].startswith("pending")]
    if pending_expert_items:
        blockers.append("exact approved expert rubric wording has not been imported")
    pending_resident_items = [row["item_id"] for row in resident_instrument if row["ethics_status"] != "approved"]
    if pending_resident_items:
        blockers.append("resident instrument wording has not been ethics approved")

    required_paths = re.findall(r"^  - ([^\n]+)$", yaml_section("required_before_freeze"), re.MULTILINE)
    for relative_path in required_paths:
        path = ROOT / relative_path
        if not path.is_file() or path.stat().st_size == 0:
            blockers.append(f"required freeze file missing or empty: {relative_path}")
    return blockers


def stage1_blockers() -> list[str]:
    blockers: list[str] = []
    scope_path = ROOT / "STAGE1_REGISTRATION_SCOPE.md"
    if not scope_path.is_file():
        blockers.append("Stage 1 scope document is missing")
    else:
        scope_text = scope_path.read_text(encoding="utf-8")
        for phrase in (
            "READY_FOR_EXTERNAL_DEPOSIT_NOT_YET_REGISTERED",
            "139 numerical settings",
            "three real coded operators",
            "four benign synthetic Terra API schema preflights",
            "Resident recruitment and data collection remain prohibited",
            "34 unresolved project-level regulatory records",
        ):
            if phrase not in scope_text:
                blockers.append(f"Stage 1 scope lacks required boundary: {phrase}")

    if len(author_threshold_inventory) != 139:
        blockers.append("Stage 1 numerical inventory must contain 139 settings")
    expected_inventory_hash = "fbda6e09f123bc03ae0d69b567e4a9b9d969432b40da6f891fa2ebfdbf882704"
    if sha256_file(ROOT / "protocols/author_threshold_inventory.csv") != expected_inventory_hash:
        blockers.append("Stage 1 numerical inventory hash has changed")
    if section_scalar("protocol", "status") != "NOT_YET_REGISTERED":
        blockers.append("Local Stage 1 package must not claim registration before external deposit")
    if not as_bool(section_scalar("readiness", "model_manifest_frozen")):
        blockers.append("Stage 1 model manifest is not frozen")
    if not as_bool(section_scalar("readiness", "study_constraint_applicability_frozen")):
        blockers.append("Stage 1 study constraint rules are not frozen")
    if not as_bool(section_scalar("readiness", "synthetic_pipeline_structural_smoke_tested")):
        blockers.append("Stage 1 structural smoke test is incomplete")
    if not as_bool(section_scalar("readiness", "confirmatory_analysis_specification_frozen")):
        blockers.append("Stage 1 confirmatory analysis specification is not frozen")
    if human_template or resident_session_template:
        blockers.append("Stage 1 archive contains resident observations")
    if operator_roles:
        blockers.append("Stage 1 archive unexpectedly claims completed real operators")
    if api_preflight_result["status"] not in {
        "OFFLINE_CONTRACT_CHECK_ONLY",
        "PASSED_LIVE_SCHEMAS_AND_LOCAL_REFUSAL_HANDLER",
    }:
        blockers.append(f"Stage 1 API contract status is unsuitable: {api_preflight_result['status']}")
    return blockers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-ready", action="store_true", help="Fail unless every registration freeze gate is satisfied")
    parser.add_argument("--stage1-ready", action="store_true", help="Fail unless the bounded Stage 1 protocol archive is ready for external deposit")
    args = parser.parse_args()

    blockers = freeze_blockers()
    print("POLIS preregistration structural validation passed")
    print("design=3_experiments+2_case_studies scenarios=36 exp2_runs=72")
    print("expert_target=12 resident_target=45 resident_consent_cap=60 resident_mode_rows=0 resident_session_rows=0")
    print(f"sources={len(sources)} needs={len(need_profiles)} predicates={len(need_predicates)}")
    pending_real_project = sum(
        "pending" in row["real_project_applicability_status"].lower()
        or "pending" in row["verification_status"].lower()
        for row in site_constraints
    )
    print(f"constraints={dict(Counter(row['site'] for row in site_constraints))} study_rules_frozen={sum(row['study_evaluator_applicability'] in {'conditional_screening_rule_frozen', 'reference_only_not_scored'} for row in site_constraints)} pending_real_project_rows={pending_real_project}")
    if args.stage1_ready:
        first_stage_blockers = stage1_blockers()
        if first_stage_blockers:
            print(f"stage1_deposit_readiness=BLOCKED blockers={len(first_stage_blockers)}")
            for blocker in first_stage_blockers:
                print(f"- {blocker}")
            return 1
        print("stage1_deposit_readiness=READY_FOR_EXTERNAL_DEPOSIT")
        print("stage1_execution_authorisation=NOT_GRANTED_EXECUTION_GATES_REMAIN")
        return 0
    if blockers:
        print(f"freeze_readiness=BLOCKED blockers={len(blockers)}")
        for blocker in blockers:
            print(f"- {blocker}")
        return 1 if args.freeze_ready else 0
    print("freeze_readiness=READY")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"STRUCTURAL VALIDATION FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2)
