# Description: Research assistant class that handles the research process for a given question.

# libraries
import asyncio
import json
import uuid

from actions.web_search import web_search
from actions.web_scrape import async_browse
from processing.text import \
    write_to_file, \
    create_message, \
    create_chat_completion, \
    read_txt_files, \
    write_md_to_pdf
from config import Config
from agent import prompts
import os
import string


CFG = Config()


class ResearchAgent:
    def __init__(self, question, agent, agent_role_prompt, num_query, num_urls):
        """ Initializes the research assistant with the given question.
        Args: question (str): The question to research
        Returns: None
        """

        self.question = question
        self.agent = agent
        self.agent_role_prompt = agent_role_prompt if agent_role_prompt else prompts.generate_agent_role_prompt(agent)
        self.visited_urls = set()
        self.research_summary = ""
        self.directory_name = uuid.uuid4()
        self.dir_path = os.path.dirname(f"D:\\Upwork\\Akinloye\\GPT-Research\\gpt-research\\outputs\\{self.directory_name}\\")
        self.num_query = num_query
        self.num_urls = num_urls


    async def summarize(self, text, topic):
        """ Summarizes the given text for the given topic.
        Args: text (str): The text to summarize
                topic (str): The topic to summarize the text for
        Returns: str: The summarized text
        """

        messages = [create_message(text, topic)]
        print(f"📝 Summarizing text for query: {text}")

        return create_chat_completion(
            model=CFG.fast_llm_model,
            messages=messages,
        )

    async def get_new_urls(self, url_set_input):
        """ Gets the new urls from the given url set.
        Args: url_set_input (set[str]): The url set to get the new urls from
        Returns: list[str]: The new urls from the given url set
        """

        new_urls = []
        for url in url_set_input:
            if url not in self.visited_urls:
                print(f"✅ Adding source url to research: {url}")
                self.visited_urls.add(url)
                new_urls.append(url)
        print('\n')

        return new_urls

    async def call_agent(self, action):
        messages = [{
            "role": "system",
            "content": self.agent_role_prompt
        }, {
            "role": "user",
            "content": action,
        }]
        answer = create_chat_completion(
            model=CFG.smart_llm_model,
            messages=messages
        )
        return answer

    async def create_search_queries(self):
        """ Creates the search queries for the given question.
        Args: None
        Returns: list[str]: The search queries for the given question
        """
        result = await self.call_agent(prompts.generate_search_queries_prompt(self.question, self.num_query))
        print(f"🧠 I will conduct my research based on the following queries: {result}\n...\n")
        # Split the result into lines and remove empty lines
        lines = result.split('\n')
        lines = [line.strip() for line in lines if line.strip()]

        # Create a JSON array from the cleaned lines
        json_array = ', '.join(lines)
        return json.loads(result)

    async def async_search(self, query):
        """ Runs the async search for the given query.
        Args: query (str): The query to run the async search for
        Returns: list[str]: The async search for the given query
        """
        search_results = json.loads(web_search(query, self.num_urls))
        new_search_urls = self.get_new_urls([url.get("href") for url in search_results])

        # print(f"🌐 Browsing the following sites for relevant information: {new_search_urls}...")

        # Create a list to hold the coroutine objects
        tasks = [async_browse(url, query) for url in await new_search_urls]

        # Gather the results as they become available
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        return responses

    async def run_search_summary(self, query):
        """ Runs the search summary for the given query.
        Args: query (str): The query to run the search summary for
        Returns: str: The search summary for the given query
        """

        print(f"🔎 Running research for '{query}'\n...\n")

        responses = await self.async_search(query)

        result = "\n".join(responses)
        os.makedirs(os.path.dirname(f"D:\\Upwork\\Akinloye\\GPT-Research\\gpt-research\\outputs\\{self.directory_name}\\research-{query}.txt"), exist_ok=True)
        write_to_file(f"D:\\Upwork\\Akinloye\\GPT-Research\\gpt-research\\outputs\\{self.directory_name}\\research-{query}.txt", result)
        return result

    async def conduct_research(self):
        """ Conducts the research for the given question.
        Args: None
        Returns: str: The research for the given question
        """

        self.research_summary = read_txt_files(self.dir_path) if os.path.isdir(self.dir_path) else ""

        if not self.research_summary:
            search_queries = await self.create_search_queries()
            for query in search_queries:
                research_result = await self.run_search_summary(query)
                self.research_summary += f"{research_result}\n\n"
                print('------------------------------------------------------------------\n')

        print(f"Total research words: {len(self.research_summary.split(' '))}")

        return self.research_summary


    async def create_concepts(self):
        """ Creates the concepts for the given question.
        Args: None
        Returns: list[str]: The concepts for the given question
        """
        result = self.call_agent(prompts.generate_concepts_prompt(self.question, self.research_summary))

        print(f"I will research based on the following concepts: {result}\n")
        return json.loads(result)

    async def write_report(self, report_type):
        """ Writes the report for the given question.
        Args: None
        Returns: str: The report for the given question
        """
        report_type_func = prompts.get_report_by_type(report_type)
        print(f"✍️ Writing {report_type} for research task: {self.question}\n...\n")
        answer = await self.call_agent(report_type_func(self.question, self.research_summary))

        path = await write_md_to_pdf(report_type, self.directory_name, answer)

        return answer, path

    async def write_lessons(self):
        """ Writes lessons on essential concepts of the research.
        Args: None
        Returns: None
        """
        concepts = await self.create_concepts()
        for concept in concepts:
            answer = await self.call_agent(prompts.generate_lesson_prompt(concept))
            write_md_to_pdf("Lesson", self.directory_name, answer)
