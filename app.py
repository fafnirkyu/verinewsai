import os
import streamlit as st
from agent.planner import ResearchPlanner
from agent.context_manager import HybridContextEngine
from agent.verifier import VeriNewsVerifier
from agent.url_extractor import is_url, extract_article_from_url
from dotenv import load_dotenv
load_dotenv()

for key, value in st.secrets.items():
    os.environ[key] = value

st.set_page_config(
    page_title="VeriNews AI | Institutional Fact Verification",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Interface Styling
st.markdown("""
<style>
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .timeline-node {
        border-left: 3px solid #3b82f6;
        padding-left: 16px;
        margin-bottom: 20px;
    }
    .card-box {
        background-color: #0f172a;
        padding: 16px;
        border-radius: 6px;
        border: 1px solid #1e293b;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar System Configuration
with st.sidebar:
    st.title("VeriNews Engine")
    st.caption("Autonomous Real-Time Fact Audit Platform")
    st.markdown("---")
    st.markdown("**Supported Input Types:**")
    st.markdown("- Single Assertions / Headlines")
    st.markdown("- Full Web Article URLs")
    st.markdown("---")
    st.markdown("**Active Search Indices:**")
    st.markdown("- Google News: Media consensus tracking")
    st.markdown("- Google Search: Web verification")
    st.markdown("- Google Scholar: Academic literature")
    st.markdown("- Google Patents: Intellectual property filings")

# Main Interface Header
st.title("VeriNews AI — Real-Time Veritability Platform")
st.markdown(
    "Submit a headline, statement, or full article URL to audit claims against live multi-engine web evidence."
)

st.subheader("Input Selection")
col_p1, col_p2, col_p3 = st.columns(3)

preset_input = ""
if col_p1.button("Sample 1: BBC Article URL"):
    preset_input = "https://www.bbc.com/news/articles/cwyz9gjw9n9o"
if col_p2.button("Sample 2: Solid-State Battery Claim"):
    preset_input = "Tesla announced immediate full production of solid-state battery electric vehicles in 2026."
if col_p3.button("Sample 3: Health Assertion"):
    preset_input = "Sunscreen causes skin cancer and blocks all essential vitamin absorption."

user_input = st.text_area(
    "Article URL, Headline, or Claim:",
    value=preset_input if preset_input else "",
    placeholder="Enter URL (https://...) or raw text claim...",
    height=90
)

audit_button = st.button("Run Veritability Audit", type="primary", use_container_width=True)

if audit_button and user_input.strip():
    status_box = st.status("Initializing Fact Audit Sequence...", expanded=True)

    try:
        audit_text = user_input.strip()
        article_meta = None

        if is_url(audit_text):
            status_box.update(label=f"Extracting content from URL: {audit_text}...")
            article_meta = extract_article_from_url(audit_text)

            if not article_meta["success"]:
                status_box.update(label="URL Extraction Failed", state="error")
                st.error(f"Could not scrape target URL: {article_meta['error']}")
                st.stop()

            st.markdown("### Extracted Article Context")
            st.markdown(f"**Title:** {article_meta['title']}")
            with st.expander("View Scraped Body Text Preview"):
                st.write(article_meta["content"][:1500] + ("..." if len(article_meta["content"]) > 1500 else ""))

            audit_text = f"TITLE: {article_meta['title']}\n\nARTICLE BODY:\n{article_meta['content']}"

        # Step 1: Planning
        status_box.update(label="Decomposing Content & Formulating Search Plan...")
        planner = ResearchPlanner()
        plan = planner.create_plan(audit_text)

        st.markdown("### Formulated Sub-Queries")
        for sq in plan.sub_queries:
            st.write(f"- **[{sq.engine.value.upper()}]** `{sq.query}` *(Rationale: {sq.rationale})*")

        # Step 2: Search Execution
        status_box.update(label="Executing Multi-Engine Searches...")
        raw_results = planner.execute_plan(plan)

        # Step 3: Context Routing
        status_box.update(label="Aggregating & Structuring Search Evidence...")
        context_engine = HybridContextEngine()
        evidence = context_engine.prepare_evidence(raw_results)

        # Step 3b: Vector Retrieval (only triggers when evidence volume required FAISS indexing)
        if evidence.get("mode") == "faiss_rag":
            status_box.update(label="Retrieving Most Relevant Evidence via Vector Search...")
            retrieval_query = article_meta['title'] if article_meta else user_input.strip()
            evidence["context_text"] = context_engine.get_context_text(
                evidence["vector_store"], retrieval_query
            )

        # Step 4: Verification & Synthesis
        status_box.update(label="Analyzing Source Credibility & Synthesizing Audit Report...")
        verifier = VeriNewsVerifier()
        headline_for_report = article_meta['title'] if article_meta else user_input.strip()
        report = verifier.verify_news(headline_for_report, evidence)

        status_box.update(label="Veritability Audit Complete", state="complete", expanded=False)

        # ------------------- TABBED AUDIT PRESENTATION -------------------
        st.markdown("---")
        tab_audit, tab_halftruth, tab_social, tab_evidence = st.tabs([
            "Full Audit Report",
            "Half-Truth & Omission Analysis",
            "Social Debunking Kit",
            "Live Context & Baseline Comparison"
        ])

        # TAB 1: COMPREHENSIVE AUDIT REPORT
        with tab_audit:
            res_col1, res_col2 = st.columns([1, 2])

            with res_col1:
                score = report.overall_truth_score
                if score >= 70:
                    st.metric("Overall Truth Index", f"{score} / 100", delta="High Credibility", delta_color="normal")
                    st.success("Verdict: Verified")
                elif score >= 40:
                    st.metric("Overall Truth Index", f"{score} / 100", delta="Mixed Credibility", delta_color="off")
                    st.warning("Verdict: Partially Verified / Ambiguous")
                else:
                    st.metric("Overall Truth Index", f"{score} / 100", delta="Low Credibility", delta_color="inverse")
                    st.error("Verdict: Unverified / Contradicted")

            with res_col2:
                st.subheader("Summary Verdict")
                st.write(report.verdict_summary)

            st.markdown("---")
            st.subheader("Source Credibility Spectrum")
            spec = report.source_spectrum
            tier_col1, tier_col2, tier_col3 = st.columns(3)
            with tier_col1:
                st.metric("Tier 1: Academic & Official", f"{spec.tier_1_count} sources")
            with tier_col2:
                st.metric("Tier 2: Mainstream News", f"{spec.tier_2_count} sources")
            with tier_col3:
                st.metric("Tier 3: Unverified Web", f"{spec.tier_3_count} sources")

            st.info(f"**Consensus Analysis:** {spec.spectrum_analysis}")

            if report.timeline:
                st.markdown("---")
                st.subheader("Claim Origin & Evolution Timeline")
                for t_item in report.timeline:
                    st.markdown(
                        f"<div class='timeline-node'>"
                        f"<strong>{t_item.time_frame} — {t_item.event_title}</strong><br/>"
                        f"{t_item.description}"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                    if t_item.source_url:
                        st.markdown(f"Reference: [{t_item.source_url}]({t_item.source_url})")

            st.markdown("---")
            st.subheader("Atomic Claim Breakdown")
            for idx, claim in enumerate(report.atomic_claims, 1):
                status = claim.status.upper()
                status_label = f"[{status}]"
                with st.expander(f"Claim {idx}: {status_label} — {claim.claim_text}"):
                    st.markdown(f"**Confidence Score:** {claim.confidence_score}%")
                    st.markdown(f"**Reasoning:** {claim.reasoning}")
                    if claim.citation_links:
                        st.markdown("**Evidence Citations:**")
                        for link in claim.citation_links:
                            st.markdown(f"- [{link}]({link})")

        # TAB 2: HALF-TRUTH & OMISSION ANALYSIS
        with tab_halftruth:
            st.subheader("Deconstruction of Nuanced Assertions")
            st.caption("Isolates partial truths, context manipulation, and selective framing.")

            for idx, claim in enumerate(report.atomic_claims, 1):
                st.markdown(f"#### Sub-Claim {idx}: {claim.claim_text}")
                
                # Check for half-truth schema attributes if extended, or render analytical breakdown
                literal_accuracy = getattr(claim, 'literal_truth', True if claim.status == 'VERIFIED' else False)
                misleading_spin = getattr(claim, 'misleading_spin', claim.reasoning)
                omitted_context = getattr(claim, 'omitted_context', "Contextual details evaluated against search findings.")

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
                    st.markdown("**Literal Factuality Status**")
                    st.write("Factually Accurate Core" if literal_accuracy else "Factually Inaccurate / Unverified")
                    st.markdown("</div>", unsafe_allow_html=True)

                with col_b:
                    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
                    st.markdown("**Framing & Narrative Analysis**")
                    st.write(misleading_spin)
                    st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("<div class='card-box'>", unsafe_allow_html=True)
                st.markdown("**Omitted Critical Context**")
                st.write(omitted_context)
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("---")

        # TAB 3: SOCIAL DEBUNKING KIT
        with tab_social:
            st.subheader("Exportable Counter-Narratives & Public Fact Notes")
            st.caption("Structured text blocks formatted for public disclosure and platform moderation systems.")

            st.markdown("### X (Twitter) Community Notes Draft")
            primary_claim = report.atomic_claims[0].claim_text if report.atomic_claims else "Audited Assertion"
            primary_reason = report.atomic_claims[0].reasoning if report.atomic_claims else report.verdict_summary
            sources_list = ", ".join(report.key_sources[:3]) if report.key_sources else "Verified Search Indices"

            community_note = (
                f"CONTEXT NEEDED:\n"
                f"{report.verdict_summary}\n\n"
                f"KEY EVIDENCE:\n"
                f"Claim assertion '{primary_claim}' evaluated as {report.atomic_claims[0].status if report.atomic_claims else 'UNVERIFIED'}. "
                f"{primary_reason}\n\n"
                f"PRIMARY SOURCES:\n"
                f"{sources_list}"
            )
            st.code(community_note, language="text")

            st.markdown("### Press & Media Fact Briefing")
            thread_text = f"FACT CHECK AUDIT: {report.headline_under_test}\n\n"
            thread_text += f"Truth Score: {report.overall_truth_score}/100\n"
            thread_text += f"Summary Verdict: {report.verdict_summary}\n\n"
            thread_text += "Sub-Claim Verification Breakdown:\n"
            for idx, claim in enumerate(report.atomic_claims, 1):
                thread_text += f"{idx}. {claim.claim_text}\n   Status: {claim.status}\n   Details: {claim.reasoning}\n\n"
            thread_text += f"Source Tier Alignment: Tier 1 ({spec.tier_1_count}), Tier 2 ({spec.tier_2_count}), Tier 3 ({spec.tier_3_count})"

            st.text_area("Formated Media Briefing", value=thread_text, height=220)

        # TAB 4: LIVE CONTEXT & BASELINE COMPARISON
        with tab_evidence:
            st.subheader("Evidence Retrieval Log & System Comparison")
            
            col_comp1, col_comp2 = st.columns(2)
            with col_comp1:
                st.markdown("#### VeriNews Multi-Engine Real-Time Audit")
                st.markdown(f"**Score:** {report.overall_truth_score} / 100")
                st.write(report.verdict_summary)

            with col_comp2:
                st.markdown("#### Parametric Baseline (Unassisted Model)")
                st.markdown("**Score:** N/A (Static Knowledge)")
                st.write("Parametric memory lacks real-time awareness of breaking events, precise publication timestamps, and recent legal or scientific retractions.")

            st.markdown("---")
            st.subheader("Aggregated Search Context")
            st.text_area("Live Context Stream", value=evidence.get("context_text", ""), height=300)

    except Exception as e:
        status_box.update(label="Audit Execution Failed", state="error")
        st.error(f"Error executing verification sequence: {str(e)}")