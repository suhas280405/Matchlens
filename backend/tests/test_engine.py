import pytest
from backend.app.engine.models import DeliveryEvent
from backend.app.engine.state_tracker import MatchStateTracker
from backend.app.engine.similarity import MatchTwinEngine
from backend.app.data.db import DuckDBService
from backend.app.engine.replay_feed import ReplayMatchFeed


def test_state_tracker_basic():
    info = {
        "match_id": "test_1",
        "teams": ["Chennai Super Kings", "Gujarat Titans"],
        "venue": "Narendra Modi Stadium",
        "toss_winner": "Chennai Super Kings",
        "toss_decision": "field"
    }
    tracker = MatchStateTracker(info)
    assert tracker.batting_team == "Gujarat Titans"
    assert tracker.bowling_team == "Chennai Super Kings"
    assert tracker.runs == 0
    assert tracker.wickets == 0

    # Deliver 6 balls in over 0
    for b in range(1, 7):
        deliv = DeliveryEvent(
            match_id="test_1",
            innings=1,
            over=0,
            ball=b,
            legal_ball_num=b,
            batter="Shubman Gill",
            bowler="Deepak Chahar",
            non_striker="Wriddhiman Saha",
            runs_batter=1 if b % 2 != 0 else 4,
            runs_extras=0,
            runs_total=1 if b % 2 != 0 else 4,
            is_wicket=False,
        )
        tracker.process_delivery(deliv)

    state = tracker.get_match_state()
    assert state.runs == 15  # 1 + 4 + 1 + 4 + 1 + 4 = 15
    assert state.wickets == 0
    assert state.overs_completed == 1.0
    assert state.crr == 15.0
    assert len(state.momentum_events) == 1
    assert state.momentum_events[0].swing_type == "batting_surge"


def test_similarity_match_twin():
    engine = MatchTwinEngine()
    result = engine.find_similar_situations(
        balls_remaining=30,
        wickets_lost=4,
        runs_needed=50,
        rrr=10.0,
        limit=3
    )
    assert result.total_historical_matches > 0
    assert len(result.similar_matches) <= 3
    assert 0.0 <= result.win_percentage <= 100.0
    top = result.similar_matches[0]
    assert top.target_runs > 0
    assert top.balls_remaining > 0


def test_duckdb_head_to_head():
    db = DuckDBService()
    # Check famous matchup: V Kohli vs JJ Bumrah
    h2h = db.get_head_to_head("V Kohli", "JJ Bumrah")
    assert h2h is not None
    assert h2h.balls_faced > 0
    assert h2h.runs_scored > 0


def test_replay_feed_stepping():
    feed = ReplayMatchFeed()
    assert len(feed.deliveries) > 0
    initial_idx = feed.current_index
    deliv = feed.step_next()
    assert deliv is not None
    assert feed.current_index == initial_idx + 1
    state = feed.get_current_state()
    assert state.runs >= 0
