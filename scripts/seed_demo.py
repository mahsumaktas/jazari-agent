"""Seed demo user memory for impressive hackathon demo.

Usage:
    python scripts/seed_demo.py [user_id]

Creates a demo user with pre-populated memory showing Jazari's capabilities:
- Remembers name and profession
- Tracks fitness and career goals
- Has past conversation history
- Shows proactive follow-up potential
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from memory.store import MemoryStore


DEMO_MEMORIES = [
    {
        "content": "User's name is Mehmet. He is a software engineer at a startup in Istanbul.",
        "memory_type": "fact",
    },
    {
        "content": "Mehmet's goal is to become a Tech Lead within the next year. He wants to improve his system design and leadership skills.",
        "memory_type": "goal",
    },
    {
        "content": "Mehmet started a habit of running 3 times per week. He completed his first 5K run last week.",
        "memory_type": "habit",
    },
    {
        "content": "Mehmet wants to save 20% of his monthly salary. He tends to overspend on eating out.",
        "memory_type": "goal",
    },
    {
        "content": "Session summary: Mehmet discussed his career frustrations — feeling stuck in his current role. We set a 3-month plan: study system design (month 1), lead a project (month 2), apply for lead roles (month 3). Key points: career growth, system design, leadership.",
        "memory_type": "insight",
    },
    {
        "content": "Mehmet prefers direct, no-nonsense coaching. He doesn't like sugarcoating.",
        "memory_type": "preference",
    },
    {
        "content": "Mehmet mentioned he sleeps only 5-6 hours. He wants to improve this to 7-8 hours.",
        "memory_type": "habit",
    },
    {
        "content": "Mehmet is learning Rust on the side to expand his skills beyond TypeScript and Python.",
        "memory_type": "fact",
    },
]


async def seed(user_id: str):
    store = MemoryStore()
    print(f"Seeding {len(DEMO_MEMORIES)} memories for user: {user_id}")

    for i, mem in enumerate(DEMO_MEMORIES):
        result = await store.store(
            user_id=user_id,
            content=mem["content"],
            memory_type=mem["memory_type"],
        )
        status = "ok" if "memory_id" in result else "error"
        print(f"  [{i+1}/{len(DEMO_MEMORIES)}] {status}: {mem['memory_type']} — {mem['content'][:60]}...")

    print(f"\nDone. Start the server and chat as userId={user_id}")
    print(f"The agent will greet Mehmet by name and follow up on his goals.")


if __name__ == "__main__":
    user_id = sys.argv[1] if len(sys.argv) > 1 else "demo-user"
    asyncio.run(seed(user_id))
