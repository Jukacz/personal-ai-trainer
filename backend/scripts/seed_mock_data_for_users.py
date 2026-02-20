#!/usr/bin/env python3
"""CLI for seeding mock training and tracking data."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.services.mock_data_seed_service import MockDataSeedService, MockSeedConfig  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed mock training and tracking data for users")
    parser.add_argument("--execute", action="store_true", help="Write changes to MongoDB")
    parser.add_argument("--user-id", type=str, default=None, help="Optional single user_id to seed")
    parser.add_argument("--plans-per-user", type=int, default=12, help="Plans to create per user")
    parser.add_argument("--min-days-per-plan", type=int, default=3, help="Minimum days per plan")
    parser.add_argument("--max-days-per-plan", type=int, default=5, help="Maximum days per plan")
    parser.add_argument("--exercises-per-day", type=int, default=6, help="Exercises per training day")
    parser.add_argument("--not-completed-rate", type=float, default=0.2, help="Chance of not completed status")
    parser.add_argument("--opinion-rate", type=float, default=0.55, help="Chance of generating opinion")
    parser.add_argument("--start-days-ago", type=int, default=120, help="How far back generated history starts")
    parser.add_argument("--base-seed", type=int, default=20260220, help="Deterministic base seed")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = MockSeedConfig(
        plans_per_user=args.plans_per_user,
        min_days_per_plan=args.min_days_per_plan,
        max_days_per_plan=args.max_days_per_plan,
        exercises_per_day=args.exercises_per_day,
        not_completed_rate=args.not_completed_rate,
        opinion_rate=args.opinion_rate,
        start_days_ago=args.start_days_ago,
        base_seed=args.base_seed,
    )
    service = MockDataSeedService(config=config)

    if args.user_id:
        summary = service.seed_for_user(user_id=args.user_id, execute=args.execute, config=config)
    else:
        summary = service.seed_for_all_users(execute=args.execute, config=config)
    print(summary)


if __name__ == "__main__":
    main()
