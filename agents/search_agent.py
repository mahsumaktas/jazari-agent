"""Search Agent — Google Search grounding for factual claims."""

from google.adk.agents import Agent
from google.adk.tools import google_search

search_agent = Agent(
    name="search_agent",
    model="gemini-2.5-flash",
    description="Search the web for factual information. Use for nutrition data, exercise guidelines, health facts, current events, or anything that needs verified information.",
    instruction="""You are the Search Agent for Jazari, a life coaching system.
Your role is to find accurate, factual information from the web.

When to search:
- Nutrition facts (calories, macros, vitamins)
- Exercise guidelines (reps, form, safety)
- Health information (sleep recommendations, hydration)
- Current events the user asks about
- Any factual claim that needs verification

Always cite your sources. Return concise, actionable information.
Never give medical advice — say "consult a professional" for medical questions.""",
    tools=[google_search],
)
