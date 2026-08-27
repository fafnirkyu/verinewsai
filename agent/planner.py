import logging
from typing import List
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from agent.planner_schema import ResearchPlan
from serpapi_tools.multi_engine_search import MultiEngineSearchTool

load_dotenv()
logger = logging.getLogger("VeriNewsPlanner")


class ResearchPlanner:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        # Temperature set to 0.0 for deterministic, ultra-fast structural parsing
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.0
        )
        self.structured_llm = self.llm.with_structured_output(ResearchPlan)
        self.search_tool = MultiEngineSearchTool()

    def create_plan(self, user_input: str) -> ResearchPlan:
        """Analyzes input and outputs a streamlined, deduplicated research plan."""
        system_prompt = (
            "You are an elite, low-latency verification strategist.\n\n"
            "RULES:\n"
            "1. Identify the core assertion in the input text.\n"
            "2. Formulate 3 to 4 non-redundant sub-queries (3-6 words maximum per query).\n"
            "3. Do NOT invent unrelated claims or search loops.\n"
            "4. Match search engines accurately:\n"
            "   - 'google_news': Recent news events & press updates.\n"
            "   - 'google_search': General legal, web, or factual corroboration.\n"
            "   - 'google_scholar': Medical, scientific, or academic papers.\n"
            "   - 'google_patents': Physical inventions, filings, or technical designs.\n\n"
            "Return structured JSON matching the schema."
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "INPUT TO AUDIT:\n{user_input}")
        ])

        chain = prompt | self.structured_llm
        
        try:
            plan = chain.invoke({"user_input": user_input[:4000]})  # Truncate input to avoid context overflow
            
            # Post-processing: Deduplicate queries
            seen_queries = set()
            unique_sub_queries = []
            for sub in plan.sub_queries:
                q_key = f"{sub.engine.value}:{sub.query.lower().strip()}"
                if q_key not in seen_queries:
                    seen_queries.add(q_key)
                    unique_sub_queries.append(sub)

            plan.sub_queries = unique_sub_queries
            return plan

        except Exception as e:
            logger.error(f"Planning failed: {e}. Executing fallback plan.")
            # Fallback Plan matching schema requirements
            return ResearchPlan(
                objective="Fallback execution due to planning failure.",
                sub_queries=[]
            )

    def execute_plan(self, plan: ResearchPlan) -> List[dict]:
        """Executes search calls safely, continuing even if individual queries fail."""
        results = []
        if not plan.sub_queries:
            logger.warning("Empty sub-queries plan provided. Returning empty dataset.")
            return results

        for index, sub in enumerate(plan.sub_queries, start=1):
            logger.info(f"[{index}/{len(plan.sub_queries)}] Querying {sub.engine.value}: '{sub.query}'")
            res = self.search_tool.search(query=sub.query, engine=sub.engine.value)
            results.append(res)
            
        return results