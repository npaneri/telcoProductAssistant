#Added to fix error on streamlit
import sys
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
########

import os
from dotenv import load_dotenv
import json
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool

# Load environment variables
load_dotenv()

# Initialize LLM
llm = LLM(
    provider="google",
    model="gemini/gemini-2.0-flash-lite",
    api_key=os.getenv("GOOGLE_API_KEY")
)

# Initialize tool
serper_tool = SerperDevTool(num_results=1)

# Define agents
input_validator_agent = Agent(
    role="Input Validator",
    goal="Ensure user prompts are clear, complete, and relevant to telecom product design.",
    backstory=(
        "You analyze user requests for topic relevance and parameter validity (e.g., country, currency), "
        "guiding users to refine incomplete or off-topic inputs."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm
)

market_research_analyst = Agent(
    role="Concise Telecom Market Analyst",
    goal="Identify one primary competitor mobile plan and its key details.",
    backstory=(
        "You efficiently research competitor offerings in telecom, swiftly pinpointing the most prominent "
        "plan's core pricing and features in a given country."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[serper_tool],
    llm=llm
)

product_innovation_strategist = Agent(
    role="Agile Telecom Strategist",
    goal="Propose one concise product idea or a clear pricing recommendation.",
    backstory=(
        "You synthesize market data to generate a single, impactful product concept or a well-justified pricing "
        "strategy, focusing on actionable recommendations."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# Define tasks
class TelecomProductTasks:
    def validate_and_clarify_input(self, agent: Agent, user_prompt: str) -> Task:
        return Task(
            description=(
                f"Analyze: '{user_prompt}'.\n\n"
                "1. **Relevance:** If NOT telecom product related, output 'RESPONSE_OFF_TOPIC: Rephrase query.'\n"
                "2. **Extract:** Identify `country` (MUST be present), `price_point` (with currency), `features`, `customer_segment`.\n"
                "3. **Validate:** If `country` missing, output 'RESPONSE_INCOMPLETE: Specify country.' "
                "**Crucially, use your knowledge to determine if the currency (if given) is valid for the country.** "
                "If not valid, output 'RESPONSE_INVALID_CURRENCY: Correct currency/country.' "
                "If too vague for analysis, output 'RESPONSE_INCOMPLETE: Provide specifics.'\n"
                "4. **Output:** Valid JSON with `status: 'valid'`, extracted params (null if missing), and `original_prompt`."
            ),
            expected_output="JSON object or specific error string.",
            agent=agent
        )

    def competitor_market_research(self, agent: Agent, research_params: dict) -> Task:
        search_query = f"telecom mobile plans {research_params.get('country')} {research_params.get('price_point', '')} " \
                       f"{research_params.get('features', '')} {research_params.get('customer_segment', 'general')}".strip()
        return Task(
            description=(
                f"Research telecom plans in {research_params.get('country')} for: '{research_params.get('price_point')}' / "
                f"'{research_params.get('features')}' ({research_params.get('customer_segment', 'general')}). "
                f"Original Prompt: '{research_params.get('original_prompt')}'\n\n"
                f"1. Use `serper_tool` with query: {search_query}.\n"
                "2. From the *single most relevant result*, extract: Operator, Plan Name, Price (with currency), Key Features, Source URL.\n"
                "3. Present as a *very brief, concise summary paragraph* (max 3 sentences). State 'N/A' for missing data."
            ),
            expected_output="Concise summary of one competitor plan.",
            agent=agent,
            tools=[serper_tool]
        )

    def product_ideation_and_pricing(self, agent: Agent, research_data: str, user_prompt: str) -> Task:
        return Task(
            description=(
                f"Analyze brief market data: '{research_data}'. Original Prompt: '{user_prompt}'.\n\n"
                "1. **Intent:** Determine if user wants 'product ideas', 'right price analysis', or 'list competition'.\n"
                "2. **Generate:**\n"
                "   - If 'product ideas': Propose **one** idea: Name, Key Features, Price.\n"
                "   - If 'right price analysis': Propose 'right price' with **brief** justification.\n"
                "   - If 'list competition': Summarize `research_data` in one short sentence.\n"
                "3. **Format:** Concise paragraph or bullet point."
            ),
            expected_output="Concise product idea or pricing insight.",
            agent=agent
        )

telecom_tasks = TelecomProductTasks()

def run_telecom_product_crew(user_input_prompt: str) -> str:
    validation_crew = Crew(
        agents=[input_validator_agent],
        tasks=[telecom_tasks.validate_and_clarify_input(input_validator_agent, user_input_prompt)],
        process=Process.sequential,
        verbose=True
    )

    validation_output = validation_crew.kickoff(inputs={'user_prompt': user_input_prompt}).raw
    if validation_output.startswith("```json"):
        validation_output = validation_output.strip("```json").strip("```").strip()

    if validation_output.startswith("RESPONSE_OFF_TOPIC:") or \
       validation_output.startswith("RESPONSE_INCOMPLETE:") or \
       validation_output.startswith("RESPONSE_INVALID_CURRENCY:"):
        return validation_output

    try:
        result = json.loads(validation_output)
        validated_params = {
            "country": result.get("country"),
            "price_point": result.get("price_point"),
            "features": result.get("features"),
            "customer_segment": result.get("customer_segment"),
            "original_prompt": result.get("original_prompt")
        }

        research_crew = Crew(
            agents=[market_research_analyst],
            tasks=[telecom_tasks.competitor_market_research(market_research_analyst, validated_params)],
            process=Process.sequential,
            verbose=True
        )
        competitor_data = research_crew.kickoff(inputs={'research_params': validated_params}).raw

        ideation_crew = Crew(
            agents=[product_innovation_strategist],
            tasks=[telecom_tasks.product_ideation_and_pricing(product_innovation_strategist, competitor_data, validated_params["original_prompt"])],
            process=Process.sequential,
            verbose=True
        )
        final_output = ideation_crew.kickoff(inputs={
            'research_data': competitor_data,
            'user_prompt': validated_params["original_prompt"]
        }).raw

        return final_output

    except json.JSONDecodeError:
        return "Error: Unable to parse validation output as JSON."
