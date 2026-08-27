from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from agent.verifier_schema import VeritabilityReport

load_dotenv()

class VeriNewsVerifier:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.0
        )
        self.structured_llm = self.llm.with_structured_output(VeritabilityReport)

    def verify_news(self, user_headline: str, evidence_data: dict) -> VeritabilityReport:
        """Analyzes atomic claims against live SerpApi context and produces a multi-dimensional VeritabilityReport."""
        system_prompt = (
            "You are an elite investigative fact-checker and real-time news auditor.\n"
            "Evaluate the provided news headline against retrieved LIVE search evidence.\n\n"
            "CRITICAL AUDIT RULES:\n"
            "1. Ground every judgment STRICTLY in the provided evidence context.\n"
            "2. If search evidence directly supports a claim with credible sources, mark status as 'VERIFIED'.\n"
            "3. If evidence is missing or ambiguous, mark as 'UNVERIFIED'.\n"
            "4. If search evidence explicitly refutes the claim, mark as 'CONTRADICTED'.\n\n"
            "ADVANCED ANALYSIS RULES:\n"
            "5. SOURCE TIERING:\n"
            "   - Tier 1: Peer-reviewed journals, health authorities (WHO, CDC, FDA, PubMed), academic papers, patents.\n"
            "   - Tier 2: Mainstream news outlets (Reuters, AP, BBC, NYT, Reuters, WSJ).\n"
            "   - Tier 3: Unverified web pages, blogs, social media posts, discussion boards.\n"
            "   Categorize retrieved sources across these tiers and summarize the alignment in spectrum_analysis.\n\n"
            "6. CLAIM TIMELINE:\n"
            "   Build a chronological sequence (3-5 key milestones) tracking the origin, viral evolution, or scientific refutation of the claim based on search snippets and dates."
        )

        context_str = evidence_data.get("context_text", "")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "HEADLINE TO AUDIT: {user_headline}\n\nLIVE SEARCH EVIDENCE:\n{evidence_context}")
        ])

        chain = prompt | self.structured_llm
        return chain.invoke({
            "user_headline": user_headline,
            "evidence_context": context_str
        })
    def verify_without_search(self, user_headline: str) -> str:
        """Evaluates the headline using base LLM parametric knowledge only."""
        prompt = f"Fact-check this recent headline or claim based strictly on your internal training data: '{user_headline}'. State whether it is true or false and cite any specific sources if you know them."
        return self.llm.invoke(prompt).content