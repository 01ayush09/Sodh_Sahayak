from langgraph.graph import END, START, StateGraph

from scoping_nodes import clarify_with_user, write_draft_report, write_research_brief
from state import AgentInputState, AgentState

scope_builder = StateGraph(AgentState, input_schema=AgentInputState)

scope_builder.add_node("clarify_with_user", clarify_with_user)
scope_builder.add_node("write_research_brief", write_research_brief)
scope_builder.add_node("write_draft_report", write_draft_report)

scope_builder.add_edge(START, "clarify_with_user")
scope_builder.add_edge("write_research_brief", "write_draft_report")
scope_builder.add_edge("write_draft_report", END)

scope_research = scope_builder.compile()
