import asyncio
import datetime

from typing import List, Dict
from config import check_openai_api_key
from agent.research_agent import ResearchAgent
import logging


async def run_agent(task, report_type, agent, agent_role_prompt, num_queries, num_urls):
    check_openai_api_key()

    start_time = datetime.datetime.now()

    assistant = ResearchAgent(task, agent, agent_role_prompt, num_queries, num_urls)
    await assistant.conduct_research()

    research_flag = input('Do you want to write a report? [Y/N] = ')
    if research_flag.lower() == 'y':
        report, path = await assistant.write_report(report_type)
        print(f"report saved at path: {path}")
    else:
        print('\n\n-------Printing research----------\n')
        print(assistant.research_summary)

    end_time = datetime.datetime.now()


# QUESTION TO RESEARCH ON
question = "What are the new features in iphone 15"
# TYPE OF AGENT
agent = "Smartphone Technology Research Agent"
# ROLE OF THE AGENT
agent_prompt = "Get a survey of the new features that apple provides in iphone 15. Provide an indepth explanation of the advantages of the new features and compare it to other flagship smartphones in the market"
# TYPE OF REPORT TO GENERATE
# 'research_report','resource_report','outline_report'
report_type = 'research_report'

num_query = 2
num_urls = 2

asyncio.run(run_agent(question, report_type, agent, agent_prompt, num_query, num_urls))