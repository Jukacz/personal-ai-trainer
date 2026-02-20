#!/usr/bin/env python3
"""One-time migration from legacy trainings to v2 training_plans/training_days schema."""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bson import ObjectId
from pymongo import MongoClient

DATABASE_NAME = "personal_trainer"
LEGACY_TRAININGS_COLLECTION = "trainings"
TRAINING_PLANS_COLLECTION = "training_plans"
TRAINING_DAYS_COLLECTION = "training_days"
TRAINING_TASKS_COLLECTION = "training_tasks"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate legacy trainings to v2 schema")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Analyze without writing changes")
    mode.add_argument("--execute", action="store_true", help="Perform migration changes")
    parser.add_argument("--batch-size", type=int, default=200, help="Mongo cursor batch size")
    parser.add_argument("--resume-from", type=str, default=None, help="Legacy training _id to resume from")
    parser.add_argument("--report-dir", type=str, default=".", help="Output directory for reports")
    return parser.parse_args()


def get_client() -> MongoClient:
    uri = os.getenv("MONGODB_URI", "mongodb://admin:password123@localhost:27017/?authSource=admin")
    return MongoClient(uri)


def is_valid_training_doc(doc: dict[str, Any]) -> tuple[bool, str]:
    if not doc.get("user_id"):
        return False, "missing_user_id"
    trainings = doc.get("trainings")
    if not isinstance(trainings, list) or not trainings:
        return False, "missing_or_empty_trainings"
    for idx, day in enumerate(trainings):
        if not isinstance(day, dict):
            return False, f"invalid_training_day_type_{idx}"
        if not day.get("day"):
            return False, f"missing_day_field_{idx}"
        if not day.get("name"):
            return False, f"missing_name_field_{idx}"
        if day.get("timeRequired") is None:
            return False, f"missing_timeRequired_{idx}"
        if not isinstance(day.get("exercises", []), list):
            return False, f"invalid_exercises_type_{idx}"
    return True, ""


def migrate(args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "mode": "dry-run" if args.dry_run else "execute",
        "processed": 0,
        "migrated": 0,
        "skipped": 0,
        "tasks_updated": 0,
        "tasks_without_mapped_plan": 0,
        "errors": 0,
        "skipped_items": [],
        "warnings": [],
    }

    client = get_client()
    try:
        db = client[DATABASE_NAME]
        legacy = db[LEGACY_TRAININGS_COLLECTION]
        plans = db[TRAINING_PLANS_COLLECTION]
        days = db[TRAINING_DAYS_COLLECTION]
        tasks = db[TRAINING_TASKS_COLLECTION]

        query: dict[str, Any] = {}
        if args.resume_from:
            query["_id"] = {"$gt": ObjectId(args.resume_from)}

        cursor = legacy.find(query).sort("_id", 1).batch_size(args.batch_size)

        old_to_new: dict[str, str] = {}

        for doc in cursor:
            report["processed"] += 1
            old_id = str(doc["_id"])

            valid, reason = is_valid_training_doc(doc)
            if not valid:
                report["skipped"] += 1
                report["skipped_items"].append({"legacy_id": old_id, "reason": reason})
                continue

            existing = plans.find_one({"legacy_training_id": old_id}, {"_id": 1})
            if existing:
                new_plan_id = existing["_id"]
            elif args.dry_run:
                new_plan_id = ObjectId()
            else:
                now = datetime.now(timezone.utc)
                plan_doc = {
                    "user_id": doc["user_id"],
                    "difficulty": doc.get("difficulty"),
                    "created_at": doc.get("createdAt", now),
                    "updated_at": now,
                    "source_version": 2,
                    "legacy_training_id": old_id,
                }
                new_plan_id = plans.insert_one(plan_doc).inserted_id

            old_to_new[old_id] = str(new_plan_id)

            if args.execute:
                days.delete_many({"plan_id": new_plan_id})
                now = datetime.now(timezone.utc)
                day_docs = []
                for training_day in doc["trainings"]:
                    day_docs.append(
                        {
                            "plan_id": new_plan_id,
                            "user_id": doc["user_id"],
                            "day": training_day["day"],
                            "name": training_day["name"],
                            "time_required": training_day["timeRequired"],
                            "exercises": training_day.get("exercises", []),
                            "created_at": now,
                            "updated_at": now,
                        }
                    )
                if day_docs:
                    days.insert_many(day_docs)

            report["migrated"] += 1

        task_query = {"result.training_id": {"$exists": True, "$ne": None}}
        task_cursor = tasks.find(task_query).batch_size(args.batch_size)
        for task_doc in task_cursor:
            legacy_training_id = str(task_doc.get("result", {}).get("training_id"))
            mapped_plan_id = old_to_new.get(legacy_training_id)
            if not mapped_plan_id:
                report["tasks_without_mapped_plan"] += 1
                report["warnings"].append(
                    {
                        "task_id": str(task_doc.get("_id")),
                        "warning": "task_without_mapped_plan",
                        "legacy_training_id": legacy_training_id,
                    }
                )
                continue

            if args.execute:
                tasks.update_one(
                    {"_id": task_doc["_id"]},
                    {
                        "$set": {
                            "result.training_id": mapped_plan_id,
                            "result.schema_version": 2,
                        },
                        "$unset": {
                            "result.trainings": "",
                        },
                    },
                )
            report["tasks_updated"] += 1

    except Exception as exc:  # pragma: no cover - runtime guard
        report["errors"] += 1
        report["warnings"].append({"error": str(exc)})
    finally:
        client.close()

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    return report


def write_reports(report: dict[str, Any], report_dir: str) -> None:
    output_dir = Path(report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / "migration_report.json"
    skipped_path = output_dir / "migration_skipped.csv"

    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)

    with skipped_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["legacy_id", "reason"])
        writer.writeheader()
        for item in report.get("skipped_items", []):
            writer.writerow(item)


if __name__ == "__main__":
    arguments = parse_args()
    migration_report = migrate(arguments)
    write_reports(migration_report, arguments.report_dir)
    print(json.dumps(migration_report, ensure_ascii=False, indent=2))
