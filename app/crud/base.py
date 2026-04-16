from connection import ServerConnect


class BaseCrud:
    def __init__(self, connector: ServerConnect) -> None:
        self.connector = connector

    def query(self, sql: str, params: tuple = ()) -> list[tuple]:
        conn = self.connector.getConnection()
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()

    def execute(self, sql: str, params: tuple = ()) -> None:
        conn = self.connector.getConnection()
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
        self.connector.commit()
