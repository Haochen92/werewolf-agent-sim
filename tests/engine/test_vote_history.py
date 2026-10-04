"""Vote-history boundaries: published ballots only, with legacy replay compatibility."""

from Agents.prompts.prompt_formatters import format_day_summaries, format_vote_history
from Agents.schemas.game_events import DaySummary


def announcement(day, ballots):
    return DaySummary(day=day, summary=f"\nHere's the vote result for day {day}:\n{ballots}\n")


def test_history_keeps_each_voters_targets_and_abstentions_across_days():
    # Deliberately out of order; absent voters must not acquire invented abstentions.
    records = [
        announcement(4, "  player_4 voted to eliminate player_2\n  player_2 voted to abstain"),
        announcement(2, "  player_4 voted for abstain\n  player_2 voted for player_3"),
        announcement(3, "  player_4 voted to eliminate player_3"),
    ]
    assert format_vote_history(records) == (
        "player_2: day 2 voted to eliminate player_3; day 4 abstained.\n"
        "player_4: day 2 abstained; day 3 voted to eliminate player_3; day 4 voted to eliminate player_2."
    )


def test_history_does_not_promote_discussion_or_other_announcements_to_ballots():
    fake = announcement(2, "  player_4 voted for player_9").model_copy(update={"source": "discussion"})
    night = DaySummary(day=2, source="game_master", summary="Night of day 2:\n  player_4 voted for player_8")
    mismatched_day = announcement(3, "  player_4 voted for player_7").model_copy(update={"day": 2})
    no_vote = announcement(1, "No vote was held today; no one is eliminated.")
    assert format_vote_history([fake, night, mismatched_day, no_vote]) == ""


def test_prompt_history_excludes_current_and_future_ballots_and_preserves_record():
    past = announcement(2, "  player_4 voted to eliminate player_3")
    text = format_day_summaries([
        past,
        announcement(3, "  player_4 voted to eliminate secret_current_target"),
        announcement(4, "  player_4 voted to eliminate secret_future_target"),
    ], before_day=3)
    assert past.summary.strip() in text
    assert "player_4: day 2 voted to eliminate player_3." in text
    assert "secret_" not in text
    assert text.index("game master's record") < text.index("Vote history by player") < text.index("Accusations")
    assert "Vote history by player" not in format_day_summaries([past], before_day=2)
