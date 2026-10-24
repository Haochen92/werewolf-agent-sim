"""The shapes of the admission pipeline: the admission config, the vote scores and the gate's verdict.

The config (``AdmissionConfig``) is what one candidate's admission is run from
(``python -m evaluation.src.cli_runner.admit --config <file>``); the criteria in it are written before the
run. The vote-score and verdict models are what ``vote_scoring.py`` and ``gate.py`` return and what the
runner writes to ``admission_verdict.json``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

# --- the admission config -------------------------------------------------------------------------


class ReferenceModel(BaseModel):
    """The model the candidate is compared with: the one doing the job today."""

    model: str
    """Catalogue id, e.g. "anthropic/claude-haiku-5-5"."""
    thinking_level: str
    """The thinking level it does the job at today, e.g. "low"."""
    structured_mode: str | None = None
    """The calling mode its replay arms run on (the bench's ``LLM_STRUCTURED_MODE``), e.g.
    "json_mode"; None leaves the model factory's choice for that model."""


class CandidateModel(BaseModel):
    """The model being admitted, tried at one or more thinking levels."""

    model: str
    """Catalogue id, e.g. "openai/gpt-6-luna"."""
    thinking_levels: list[str]
    """Every level to try, e.g. ["low", "medium"]; each becomes one probe run and one arm per case set."""
    structured_mode: str | None = None
    """The calling mode its replay arms run on, e.g. "json_mode"; None leaves the factory's choice.
    The probe run tries every mode regardless and records which one it recommends."""


class CaseSet(BaseModel):
    """One set of frozen cases to replay, as one bench run."""

    name: str
    """Short name used in file and arm paths, e.g. "discussion" or "votes"."""
    kind: Literal["discussion", "vote", "resummarize"]
    """"discussion": judged turns only. "vote": judged notes, and every vote scored by its target.
    "resummarize": the arms rewrite earlier days' summaries first (the bench's ``resummarize``), so the
    set tests the summariser; the summary runs on the arm's own model and level, as in a game."""
    dataset: str
    """The frozen cases file, relative to the repo root, e.g.
    "evidence/game_play_enhancement/data/phase3_turn_replay/cases.jsonl"."""
    slices: list[str] | None = None
    """Only cases in these slices (the bench's ``slices``), e.g. ["pinned", "control"]; None = all."""
    n: int | None = None
    """Samples per case for this set; None uses the config's ``n``."""
    right_target_overrides: dict[str, list[str]] = Field(default_factory=dict)
    """Vote sets only: case id → the targets that count as right on that case, replacing the role
    lookup, e.g. {"9b827b695a61ece9": ["player_6", "player_10", "abstain"]}. "abstain" may be listed.
    A case record can carry the same list itself as ``right_vote_targets``; this mapping wins."""
    speed: SpeedCriteria | None = None
    """This set's own latency limits, replacing ``criteria.speed`` for it; None uses the shared ones.
    The stage gives each phase a different room (``frontend/docs/stage_fit/README.md``), so a
    discussion set and a vote set can carry different limits."""


class IntegrationCriteria(BaseModel):
    """What the probe run must show for a level to pass integration."""

    require_recommended_mode: bool = True
    """The run must recommend a calling mode, i.e. one mode passed every probe call."""
    max_real_turn_failures: int = 0
    """Most real game turns the recommended mode may fail in the probe run."""
    require_reasoning_when_thinking: bool = True
    """When a thinking level other than "minimal" is asked for, the recommended mode must actually
    report reasoning tokens (a forced tool call can turn thinking off without an error)."""


class QualityCriteria(BaseModel):
    """How much worse than the reference the candidate's judged samples may be, per case set."""

    max_bad_rate_gap: float
    """Points the candidate's bad-sample rate may sit above the reference arm's, e.g. 6.0."""
    worse_p_threshold: float = 0.05
    """The candidate fails when it is worse on more cases than better and the bench's per-case sign
    test gives p below this."""


class VoteCriteria(BaseModel):
    """How much worse than the reference the candidate's votes may be, per vote case set."""

    max_vote_gap: float
    """Points the candidate's votes-right rate may sit below the reference arm's, e.g. 10.0."""
    worse_p_threshold: float = 0.05
    """The candidate fails when it is right less often on more cases than more often and the per-case
    sign test gives p below this."""


class SpeedCriteria(BaseModel):
    """Seconds per replayed sample, from the timings each sample records. None skips the check."""

    max_p50_seconds: float | None = None
    """Highest median seconds per sample allowed, e.g. 5.5."""
    max_p95_seconds: float | None = None
    """Highest 95th-percentile seconds per sample allowed, e.g. 30.0."""


class CostCriteria(BaseModel):
    """Tokens per replayed sample, from the usage each sample records. None skips the check."""

    max_output_tokens_per_sample: float | None = None
    """Highest mean output tokens per sample (output already includes reasoning tokens)."""
    max_reasoning_tokens_per_sample: float | None = None
    """Highest mean reasoning tokens per sample."""


class AdmissionCriteria(BaseModel):
    """Every pass criterion, fixed in the config before the run."""

    integration: IntegrationCriteria = Field(default_factory=IntegrationCriteria)
    """Probe-run checks, per thinking level."""
    quality: QualityCriteria
    """Judged-sample checks, per case set."""
    votes: VoteCriteria | None = None
    """Vote-target checks, per vote case set; None skips them."""
    speed: SpeedCriteria = Field(default_factory=SpeedCriteria)
    """Latency checks, per case set."""
    cost: CostCriteria = Field(default_factory=CostCriteria)
    """Token checks, per case set."""
    quality_rejects: bool = False
    """Whether a failed quality or vote criterion rejects the candidate. False while the project is
    experimental (owner, 2026-10-24): a model is dropped only for cost, latency or integration, and its
    quality results are reported beside the verdict. True for a commercial release."""


class ProbeSettings(BaseModel):
    """Settings passed through to the probe run (``eval-model-admission``)."""

    samples_per_schema: int = 3
    """Calls per seat schema per calling mode."""
    workers: int = 4
    """Parallel probe calls."""
    modes: list[str] | None = None
    """Calling modes to try, e.g. ["json_schema", "json_mode"]; None tries every mode the model allows."""
    floor_sizes: list[int] = Field(default_factory=lambda: [256, 512, 1024, 2048, 4096, 8192])
    """Prompt sizes (tokens) the cache-floor probe tries, smallest first."""
    wait_s: float = 8
    """Seconds between the cache probe's sends."""
    real_turn_dataset: str | None = None
    """Frozen cases the real-turn probe replays; None uses the first discussion case set's dataset."""
    real_turn_cases: int = 2
    """How many of its discussion cases are replayed (three calls each)."""


class JudgeModels(BaseModel):
    """The bench's judges; None keeps the bench's default for that judge."""

    recall_model: str | None = None
    """The fact-sheet census reader."""
    precision_model: str | None = None
    """The reader that re-reads the census reader's positives."""
    golden_model: str | None = None
    """The judge of cases with a hand-written expectation."""


class AdmissionConfig(BaseModel):
    """One candidate's admission: what to run, against what, and what counts as passing."""

    label: str
    """Names the output folder ``evaluation/eval_results/model_admission/<label>/``."""
    candidate: CandidateModel
    """The model being admitted."""
    reference: ReferenceModel
    """The model doing the job today; its arm is first in every bench run."""
    case_sets: list[CaseSet]
    """The frozen cases to replay, one bench run each."""
    n: int = 5
    """Samples per case, unless a case set sets its own."""
    workers: int = 3
    """The bench's parallel generations per arm."""
    probe: ProbeSettings = Field(default_factory=ProbeSettings)
    """Settings for the probe run."""
    judges: JudgeModels = Field(default_factory=JudgeModels)
    """The bench's judge models."""
    criteria: AdmissionCriteria
    """The pass criteria."""
    note: str = ""
    """Free text: why the run, and where each criterion's value comes from."""

    @model_validator(mode="after")
    def _case_set_names_are_unique(self) -> AdmissionConfig:
        """Check that no two case sets share a name, since the name picks each set's output folder.

        Returns:
            The config, unchanged. Raises ValueError when two case sets share a name.
        """
        names = [case_set.name for case_set in self.case_sets]
        if len(names) != len(set(names)):
            raise ValueError(f"case set names must be unique, got {names}")
        return self


class PlannedStep(BaseModel):
    """One step of an admission run, as the plan prints it."""

    title: str
    """What the step does, e.g. "bench: votes (3 arms)"."""
    config_path: str | None = None
    """The generated config the step runs, or None for a step that runs no config."""
    model_calls: int = 0
    """The most model calls the step makes (0 for a step that calls no model)."""
    calls_note: str = ""
    """How the count was reached, e.g. "16 cases × 10 samples × 3 arms"."""


# --- vote scores -----------------------------------------------------------------------------------

VoteOutcomeLabel = Literal["right", "wrong", "unscorable"]


class VoteSampleScore(BaseModel):
    """One generated vote sample, scored."""

    case_id: str
    """The frozen case the sample answers."""
    sample: int
    """The sample's index within its case."""
    vote_target: str | None
    """The vote as written, e.g. "player_6" or "abstain"; None when the reply had none."""
    outcome: VoteOutcomeLabel
    """"right" or "wrong" against the case's right targets; "unscorable" when it cannot be scored."""
    is_abstain: bool = False
    """The vote was "abstain" (scored: wrong unless the case lists "abstain" as right)."""
    unscorable_reason: str | None = None
    """Why the sample was not scored, e.g. "invalid sample (generation failed)"."""


class VoteCaseRow(BaseModel):
    """One case's votes in one arm."""

    case_id: str
    """The frozen case."""
    game_id: str
    """The game the case was cut from, e.g. "403f4dbc"."""
    day: int
    """The game day of the vote."""
    voter: str
    """The seat voting, e.g. "player_2"."""
    voter_role: str
    """The voter's true role."""
    right_targets: list[str]
    """The targets that count as right on this case."""
    right_source: Literal["roles", "case_record", "override"]
    """Where the right targets came from: the true roles, the case's own ``right_vote_targets``, or the
    config's ``right_target_overrides``."""
    right: int
    """Samples voting a right target."""
    scored: int
    """Samples scored (abstains included)."""
    abstains: int
    """Scored samples that abstained."""
    unscorable: int
    """Samples that could not be scored."""
    vote_counts: dict[str, int]
    """Every vote target written and how often, e.g. {"player_6": 9, "abstain": 1}."""


class ArmVoteScore(BaseModel):
    """One arm's votes over a case set."""

    arm_label: str
    """The bench arm, e.g. "candidate_low"."""
    right: int
    """Scored samples voting a right target."""
    scored: int
    """Samples scored (abstains included)."""
    abstains: int
    """Scored samples that abstained."""
    unscorable: list[VoteSampleScore]
    """Every sample that could not be scored, with its reason."""
    per_case: list[VoteCaseRow]
    """One row per case, in the case set's order."""

    @property
    def right_rate(self) -> float | None:
        """The share of scored samples that were right.

        Returns:
            right / scored, e.g. 0.406; None when nothing was scored.
        """
        return self.right / self.scored if self.scored else None


class VoteComparison(BaseModel):
    """Two arms' votes compared case by case."""

    reference_arm: str
    """The arm compared against."""
    candidate_arm: str
    """The arm compared."""
    cases: int
    """Cases scored in both arms."""
    better: int
    """Cases where the candidate was right more often than the reference."""
    worse: int
    """Cases where the candidate was right less often."""
    two_sided_sign_p: float
    """Exact two-sided sign test over the cases that differ (1.0 when none differ)."""


# --- the gate's verdict ------------------------------------------------------------------------------

CriterionStatus = Literal["passed", "failed", "not_measured"]


class ArmSampleStats(BaseModel):
    """One bench arm's samples on one case set, summed for the gate and the report."""

    arm_label: str
    """The bench arm, e.g. "reference_low"."""
    valid: int
    """Valid samples (a reply the game could act on)."""
    invalid: int
    """Samples whose generation failed."""
    judged: bool
    """True when the arm's ``judged_<arm>.jsonl`` was read, so ``bad`` is known."""
    bad: int | None
    """Valid samples the judges marked bad; None when the arm is not judged."""
    samples_timed: int
    """Valid samples that recorded their generation seconds."""
    seconds_p50: float | None
    """Median seconds per sample; None when no sample was timed."""
    seconds_p95: float | None
    """95th-percentile seconds per sample (linear interpolation); None when no sample was timed."""
    samples_with_usage: int
    """Valid samples that recorded their token usage."""
    output_tokens_per_sample: float | None
    """Mean output tokens over those samples (reasoning included); None when none recorded usage."""
    reasoning_tokens_per_sample: float | None
    """Mean reasoning tokens over those samples; None when none recorded usage."""

    @property
    def bad_rate(self) -> float | None:
        """The share of valid samples marked bad.

        Returns:
            bad / valid, e.g. 0.071; None when the arm is not judged or has no valid sample.
        """
        if self.bad is None or not self.valid:
            return None
        return self.bad / self.valid


class CriterionResult(BaseModel):
    """One criterion applied to one candidate arm."""

    name: str
    """Which check, e.g. "bad_rate_gap" or "p95_seconds"."""
    area: Literal["integration", "quality", "votes", "speed", "cost"]
    """The report section it belongs to."""
    case_set: str | None = None
    """The case set it was measured on; None for probe-run checks."""
    value: str
    """What was measured, in words and numbers, e.g. "+3.4 points (7.1% against 3.7%)"."""
    limit: str
    """The criterion, e.g. "at most +6.0 points"."""
    status: CriterionStatus
    """Passed, failed, or not measured (the outputs needed are missing)."""
    blocking: bool = True
    """Whether this criterion decides the verdict. Quality and vote criteria are advisory (False) unless
    the config's ``quality_rejects`` is set; an advisory failure is reported, never a rejection."""


class ArmVerdict(BaseModel):
    """The verdict on the candidate at one thinking level."""

    thinking_level: str
    """The level, e.g. "low"."""
    arm_label: str
    """Its arm label in every bench run, e.g. "candidate_low"."""
    verdict: Literal["admit", "reject", "incomplete"]
    """"reject" when a blocking criterion failed, else "incomplete" when a blocking one was not measured,
    else "admit". Advisory criteria never change it."""
    criteria: list[CriterionResult]
    """Every criterion applied."""
    output_tokens_per_sample: float | None
    """Mean output tokens per replayed sample over every case set (output includes reasoning); the
    cheapness measure. None when no sample recorded usage."""


class AdmissionVerdict(BaseModel):
    """The whole admission's result, as written to ``admission_verdict.json``."""

    label: str
    """The admission's label."""
    candidate_model: str
    """The candidate's catalogue id."""
    reference_model: str
    """The reference's catalogue id."""
    reference_arm: str
    """The reference's arm label, e.g. "reference_low"."""
    arms: list[ArmVerdict]
    """One verdict per thinking level tried, in the config's order."""
    cheapest_passing_level: str | None
    """The admitted level with the fewest output tokens per sample; None when no level was admitted
    or no admitted level recorded usage."""
    cheapest_basis: str
    """How the cheapest level was chosen, in words."""
    sample_stats: dict[str, dict[str, ArmSampleStats]] = Field(default_factory=dict)
    """Case set name → arm label → that arm's sample totals, for every arm whose outputs exist."""
    probe_records: dict[str, str | None] = Field(default_factory=dict)
    """Thinking level → the path of the probe record read for it, or None when it was missing."""
    vote_scores: dict[str, dict[str, ArmVoteScore]] = Field(default_factory=dict)
    """Vote case set name → arm label → that arm's vote score."""
    vote_comparisons: dict[str, dict[str, VoteComparison]] = Field(default_factory=dict)
    """Vote case set name → candidate arm label → its comparison with the reference arm."""


# CaseSet refers to SpeedCriteria, defined after it.
CaseSet.model_rebuild()
