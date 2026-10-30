# Evaluation Report — Predixion AI Research Agent

## 1. Evaluation Overview

The research agent was evaluated using functional research queries and automated tests to assess its planning, tool execution, source retrieval, evidence evaluation, answer synthesis, and failure handling.

The evaluation focuses on:
- Research relevance and answer quality.
- Tool execution and source retrieval.
- Evidence quality and confidence reporting.
- Handling of failed webpage retrieval.
- Structured response generation.

## 2. Research Test Cases

### Test Case 1: Enterprise AI Applications

**Query:**

What are the main applications of AI agents in enterprise software?

**Expected Behaviour:**
- Generate a research plan.
- Retrieve relevant web sources.
- Extract webpage content.
- Generate key findings with sources.
- Report confidence and limitations.

**Observed Result:**
- Retrieved 5 search results.
- Selected 3 unique sources.
- Successfully fetched 1 webpage.
- 2 webpage retrieval attempts failed and used search snippets as fallback.
- Source quality was rated moderate.
- Gemini generated a structured research response.

**Result:** Successful, with partial webpage retrieval.

**What Worked:**
- Search and synthesis completed successfully.
- Failed webpage retrieval was handled.
- Execution trace displayed successful and failed operations.

**What Did Not:**
- Some sources were available only as search snippets.

### Test Case 2: PostgreSQL vs MongoDB

**Query:**

Compare PostgreSQL and MongoDB for modern enterprise applications. Explain their architecture, scalability, performance, advantages, limitations, and suitable use cases.

**Expected Behaviour:**
- Retrieve evidence about both databases.
- Compare their architectures and capabilities.
- Identify strengths, limitations, and use cases.
- Report evidence gaps.

**Observed Result:**
- Retrieved 5 search results.
- Selected 3 unique sources.
- Successfully fetched 2 webpages.
- 1 webpage retrieval failed and used a search snippet.
- Source quality was rated moderate (score: 0.69).
- Generated a structured comparison with assumptions and limitations.

**Result:** Successful, with incomplete source coverage.

**What Worked:**
- The agent generated a relevant comparison.
- Source retrieval failures were handled.
- The response disclosed limited PostgreSQL evidence.

**What Did Not:**
- Most retrieved evidence focused on MongoDB.
- Direct PostgreSQL architectural evidence was limited.

### Test Case 3: Source Retrieval Failure

**Scenario:**

Some websites do not allow automated webpage retrieval.

**Expected Behaviour:**
- Record failed retrieval attempts.
- Use available search snippets as fallback evidence.
- Continue the research workflow.
- Disclose the limitation.

**Observed Result:**
- Some webpage requests failed.
- Search snippets were used as fallback evidence.
- The workflow continued through source evaluation and synthesis.

**Result:** Successful failure handling.

### Test Case 4: Missing API Configuration

**Scenario:**

Run the web search tool without a configured Tavily API key.

**Expected Behaviour:**
- Detect missing API configuration.
- Return a controlled error.
- Avoid crashing the application.

**Observed Result:**
- Automated test `test_web_search_handles_missing_api_key` passed.

**Result:** Passed automated test.

### Test Case 5: Webpage Timeout

**Scenario:**

Simulate a webpage request timeout.

**Expected Behaviour:**
- Retry the request.
- Return a controlled failure if retries are unsuccessful.
- Allow the workflow to handle the failed retrieval.

**Observed Result:**
- Automated test `test_fetch_webpage_handles_timeout` passed.
- The test verified two retrieval attempts and controlled failure handling.

**Result:** Passed automated test.

## 3. Automated Testing

The project includes automated tests covering:

- URL validation and rejection of unsafe destinations.
- Missing API key handling.
- Webpage retrieval failures and timeouts.
- Source-quality evaluation.
- Duplicate and malformed evidence handling.
- Synthesis output validation.
- Prompt-injection-aware prompt construction.
- Structured response evaluation.
- LangGraph workflow execution and search failure handling.

**Latest confirmed test baseline:** 26 tests passed before the final evaluator check-name correction. Rerun the complete suite and update this result with the latest confirmed count before submission.

## 4. Evaluation Summary

| Evaluation Area | Observation |
|---|---|
| Research planning | Working |
| Web search | Working |
| Source filtering | Working |
| Webpage retrieval | Working with some failures |
| Snippet fallback | Working |
| Source-quality evaluation | Working |
| Structured synthesis | Working |
| Confidence and limitations | Working |
| Failure handling | Covered by automated tests |
| Source coverage | Needs improvement |

## 5. Key Findings

The agent successfully completes its research workflow and generates structured answers using retrieved evidence.

The main observed limitation is inconsistent webpage accessibility and uneven source coverage. The system handles these cases by using search snippets where available and reporting limitations rather than silently treating all evidence as complete.

Further improvements could include stronger source diversity, claim-level citation verification, and more extensive research evaluation datasets.