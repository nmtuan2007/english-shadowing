#!/usr/bin/env python3
"""
English Shadowing - Main Application

Usage:
    python app.py generate-sources              Generate sources.json
    python app.py generate-lessons              Generate all lessons
    python app.py generate-lessons --category business
    python app.py generate-lessons --category business --lesson how_to_speak
    python app.py list-categories               List all categories
    python app.py list-lessons --category business
"""

import argparse
import json
import sys
from pathlib import Path

from config import (
    SOURCES_FILE,
    LESSONS_DIR,
    CATEGORIES,
    MIN_DURATION,
    MAX_DURATION,
    VIDEOS_PER_CATEGORY
)


def cmd_generate_sources(args):
    """Generate sources.json from YouTube channels."""
    print("🚀 Generating sources.json...")
    print(f"   Duration filter: {MIN_DURATION}s - {MAX_DURATION}s")
    print(f"   Videos per category: {VIDEOS_PER_CATEGORY}")
    print()

    from scripts.generate_sources import generate_sources, save_sources
    sources = generate_sources()
    save_sources(sources)


def cmd_generate_lessons(args):
    """Generate shadowing lessons."""
    from scripts.run_lessons import (
        load_sources,
        run_all,
        run_category,
        run_single_lesson
    )

    sources = load_sources()

    if args.lesson and not args.category:
        print("❌ Error: --lesson requires --category")
        sys.exit(1)

    if args.lesson:
        # Generate specific lesson
        print(f"🚀 Generating lesson: {args.category}/{args.lesson}")
        run_single_lesson(args.category, args.lesson, sources)
    elif args.category:
        # Generate all lessons in category
        print(f"🚀 Generating category: {args.category}")
        run_category(args.category, sources)
    else:
        # Generate all
        print("🚀 Generating all lessons...")
        run_all(sources)


def cmd_list_categories(args):
    """List all available categories."""
    print("\n📁 Available Categories:")
    print("=" * 40)

    for name, config in CATEGORIES.items():
        level = config["level"]
        source_count = len(config["sources"])
        print(f"  {name}")
        print(f"      Level: {level}")
        print(f"      Sources: {source_count} channel(s)")
        print()


def cmd_list_lessons(args):
    """List all lessons in a category."""
    if not SOURCES_FILE.exists():
        print("❌ sources.json not found. Run 'generate-sources' first.")
        sys.exit(1)

    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        sources = json.load(f)

    if args.category:
        categories = [args.category]
    else:
        categories = list(sources.keys())

    for category in categories:
        if category not in sources:
            print(f"❌ Category not found: {category}")
            continue

        lessons = sources[category]
        print(f"\n📁 {category.upper()} ({len(lessons)} lessons)")
        print("=" * 50)

        for lesson in lessons:
            lesson_id = lesson["lesson"]
            title = lesson["title"]
            duration = lesson.get("duration", 0)
            level = lesson.get("level", "")

            # Check if completed
            shadowing_path = LESSONS_DIR / category / lesson_id / "shadowing.md"
            status = "✅" if shadowing_path.exists() else "⬜"

            duration_min = duration // 60
            duration_sec = duration % 60

            print(f"  {status} {lesson_id}")
            print(f"       {title}")
            print(f"       [{level}] {duration_min}:{duration_sec:02d}")
            print()


def cmd_status(args):
    """Show overall progress status."""
    if not SOURCES_FILE.exists():
        print("❌ sources.json not found. Run 'generate-sources' first.")
        sys.exit(1)

    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        sources = json.load(f)

    print("\n📊 Progress Status")
    print("=" * 50)

    total_lessons = 0
    total_completed = 0

    for category, lessons in sources.items():
        completed = 0
        for lesson in lessons:
            lesson_id = lesson["lesson"]
            shadowing_path = LESSONS_DIR / category / lesson_id / "shadowing.md"
            if shadowing_path.exists():
                completed += 1

        total_lessons += len(lessons)
        total_completed += completed

        pct = (completed / len(lessons) * 100) if lessons else 0
        bar_filled = int(pct / 5)
        bar_empty = 20 - bar_filled
        bar = "█" * bar_filled + "░" * bar_empty

        print(f"  {category}")
        print(f"      [{bar}] {completed}/{len(lessons)} ({pct:.0f}%)")
        print()

    # Total
    total_pct = (total_completed / total_lessons * 100) if total_lessons else 0
    print("=" * 50)
    print(f"  TOTAL: {total_completed}/{total_lessons} ({total_pct:.0f}%)")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="English Shadowing - Learn English through shadowing practice",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python app.py generate-sources
    python app.py generate-lessons
    python app.py generate-lessons --category business
    python app.py generate-lessons --category business --lesson how_to_speak
    python app.py list-categories
    python app.py list-lessons --category science
    python app.py status
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # generate-sources
    parser_sources = subparsers.add_parser(
        "generate-sources",
        help="Generate sources.json from YouTube channels"
    )
    parser_sources.set_defaults(func=cmd_generate_sources)

    # generate-lessons
    parser_lessons = subparsers.add_parser(
        "generate-lessons",
        help="Generate shadowing lessons"
    )
    parser_lessons.add_argument(
        "--category", "-c",
        help="Specific category to generate"
    )
    parser_lessons.add_argument(
        "--lesson", "-l",
        help="Specific lesson to generate (requires --category)"
    )
    parser_lessons.set_defaults(func=cmd_generate_lessons)

    # list-categories
    parser_list_cat = subparsers.add_parser(
        "list-categories",
        help="List all available categories"
    )
    parser_list_cat.set_defaults(func=cmd_list_categories)

    # list-lessons
    parser_list_lessons = subparsers.add_parser(
        "list-lessons",
        help="List lessons in a category"
    )
    parser_list_lessons.add_argument(
        "--category", "-c",
        help="Category to list (or all if not specified)"
    )
    parser_list_lessons.set_defaults(func=cmd_list_lessons)

    # status
    parser_status = subparsers.add_parser(
        "status",
        help="Show overall progress status"
    )
    parser_status.set_defaults(func=cmd_status)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()
