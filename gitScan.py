import os
from typing import NamedTuple, Union, List, Optional


import requests
from pprint import pprint
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache
from cachecontrol.heuristics import ExpiresAfter
from requests import Session

PROJECT_BASE = "https://api.github.com/orgs/GSS-Cogs/projects"
ALL_BASE = "https://api.github.com/projects"

# Cache 23 hours for now as we're aiming to snapshot once a day
session = CacheControl(Session(), cache=FileCache('.cache'), heuristic=ExpiresAfter(hours=23))
session.auth = (os.environ["GIT_USER_NAME"], os.environ["GIT_TOKEN"])


class CardObj(NamedTuple):
    id: int
    node_id: str
    note: str
    project_url: str
    updated_at: str
    url: str
    column_url: str
    created_at: str

# Cards can also be issues, we'll use "Article" to tie this together
class ArticleObj(NamedTuple):
    card: CardObj

class ColumnObj(NamedTuple):
    id: int
    name: str
    created_at: str
    updated_at: str
    cards_url: str
    url: str
    node_id: str
    project_url: str
    articles: List[ArticleObj]

class BoardObj(NamedTuple):
    id: int
    number: int
    name: str
    columns_url: str
    columns: List[ColumnObj]

class Structure(NamedTuple):
    boards: Optional[List[BoardObj]]


class GitService:

    def __init__(self):
        # Github headers required by the preview api
        self.gith = {"Accept": "application/vnd.github.inertia-preview+json"}

        # Keep objects as we build them
        self.structure = None
        self.init()

    def getf(self, url):
        """
        Get using full url
        """
        r = session.get(url, headers=self.gith)
        if r.status_code != 200:
            raise Exception('Url "{}" failed with status code "{}".'.format(url, r.status_code))
        return r.json()

    def getd(self, end_point):
        """
        get-Dynamic url:

        Simple http get to the given end point on the project root
        if end_point None is passed the base project end point is requested for all project info
        """
        if end_point is not None:
            url = "{}/{}".format(ALL_BASE, end_point)
        else:
            url = PROJECT_BASE

        return self.getf(url)

    def get_issues_from_card(self, card_url):
        """
        Cards that are also issues dont have a note. Instead we're going to take
        the title of the issue.
        """
        content_url = self.getf(card_url)["content_url"]
        content_title = self.getf(content_url)["title"]

        #pprint(self.getf(content_url))
        #import sys
        #sys.exit(1)
        return content_title

    def populate_boards(self):
        """
        Create a list of populated Board class tuples
        Store in self.objects so we don't end up repeating ourselves
        """

        if self.structure is not None:
            return self.structure.boards

        boards = []
        jsonBoards = self.getd(None)
        for board in jsonBoards:
            boards.append(
                BoardObj(
                    number=board["number"],
                    name=board["name"],
                    id=board["id"],
                    columns_url = board["columns_url"],
                    columns=[] # populated later
                )
            )
        self.structure = Structure(boards=boards)
        return self

    def populate_columns_from_boards(self):
        """
        Create a list of populated Columns class tuples per Board class tuple
        Store in self.objects so we don't end up repeating ourselves
        """

        for boardObj in self.structure.boards:

            for columnJson in self.getf(boardObj.columns_url):
                columnObj = ColumnObj(
                    id=columnJson["id"],
                    name=columnJson["name"],
                    created_at=columnJson["created_at"],
                    updated_at=columnJson["updated_at"],
                    url=columnJson["url"],
                    node_id=columnJson["node_id"],
                    project_url=columnJson["project_url"],
                    cards_url=columnJson["cards_url"],
                    articles=[] # populated later
                )
                boardObj.columns.append(columnObj)

    def populate_cards_from_columns(self):

        for boardObj in self.structure.boards:
            for columnObj in boardObj.columns:

                cardsJson = self.getf(columnObj.cards_url)
                for cardJson in cardsJson:
                    
                    card = CardObj(
                            id=cardJson["id"],
                            node_id=cardJson["node_id"],
                            note=cardJson["note"] if cardJson["note"] != None else self.get_issues_from_card(cardJson["url"]),
                            project_url=cardJson["project_url"],
                            updated_at=cardJson["updated_at"],
                            url=cardJson["url"],
                            column_url=cardJson["column_url"],
                            created_at=cardJson["created_at"]
                        )
                    columnObj.articles.append(ArticleObj(card=card))
        return 
        
    def summarise(self):
        """
        Create a numerical summary of what we've gotten off the api
        """
        for article in self.structure.boards[0].columns[0].articles:
            print(article.card)
            print()


    def init(self):
        """
        Pull all the information we need from all the apis
        """
        self.populate_boards()
        self.populate_columns_from_boards()
        self.populate_cards_from_columns()


gs = GitService()
gs.summarise()
