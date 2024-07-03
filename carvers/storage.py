from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from cassandra.query import dict_factory


CASSANDRA_IP = '172.18.0.22'
KEYSPACE = 'newsSpace'
TABLE = 'newsTable'
ELASTICSEARCH_IP = '172.18.0.23'


class cassandraClient():
    def __init__(self) -> None:
        self._is_connected = False
        self.session = None

    # Function to connect to Cassandra
    def connect_cassandra(self):
        self.cluster = Cluster([CASSANDRA_IP])
        session = self.cluster.connect()
        # self.session.set_keyspace(KEYSPACE)
        # self.session.row_factory = dict_factory
        self._is_connected = True
        return self.session

    def close(self):
        if self._is_connected:
            self.session = None
            self.cluster.shutdown()

    # Function to create keyspace
    def create_keyspace(self):
        self.session.execute(f"""
            CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
            WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': '1'}}
        """)

    # Function to create table
    def create_table(self):
        self.session.set_keyspace(KEYSPACE)
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                url TEXT PRIMARY KEY,
                publish_date TEXT,
                authors LIST<TEXT>,
                text TEXT,
                top_image TEXT,
                movies LIST<TEXT>,
                title TEXT,
                summary TEXT
            )
        """)

    def article_statement(self):
        if self.session:
            return self.session.prepare("""
                INSERT INTO articles (url, publish_date, authors, text, top_image, movies, title, summary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """)
    
    def insert_article(self, article_data):
        if self.session:
            article_statement = self.article_statement()
            self.session.execute(article_statement, (
            article_data['url'],
            article_data['publish_date'],
            article_data['authors'],
            article_data['text'],
            article_data['top_image'],
            article_data['movies'],
            article_data['title'],
            article_data['summary']
        ))

