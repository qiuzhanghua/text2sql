from sqlalchemy import (
    create_engine,
    MetaData,
    text,
    inspect,
)

from sqlalchemy.schema import CreateTable
from sqlalchemy.orm import sessionmaker

from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.models.ollama import OllamaModel

from typing import List, Optional
from pydantic import BaseModel

import os


class PgColumn(BaseModel):
    column_name: str
    data_type: str
    column_comment: Optional[str]
    fk_description: Optional[str]


class PgTable(BaseModel):
    table_name: str
    table_comment: Optional[str]
    primary_key: List[str]
    columns: List[PgColumn]


# PostgreSQL 数据库连接信息
username = "app"
password = "app"
host = "localhost"
database = "app"
port = 5432

# 创建连接字符串
connection_str = f"postgresql://{username}:{password}@{host}:{port}/{database}"

engine = create_engine(connection_str)
metadata = MetaData()
metadata.reflect(bind=engine)
inspector = inspect(engine)


def get_foreign_key_description(table_name: str, column_name: str) -> Optional[str]:
    """
    Get the foreign key description for a specific column in a table.
    """
    foreign_keys = inspector.get_foreign_keys(table_name)
    for fk in foreign_keys:
        if column_name in fk["constrained_columns"]:
            return f"{fk['referred_table']}.{fk['referred_columns'][0]}"
    return None


def get_tables(engine):
    metadata_obj = MetaData()
    metadata_obj.reflect(bind=engine)
    tables = metadata_obj.sorted_tables
    return list(map(lambda x: x.name, tables))


def get_all_tables_info() -> List[PgTable]:
    tables_info = []

    # Get all table names
    table_names = get_tables(engine)

    for table_name in table_names:
        # Get table comment
        table_comment = inspector.get_table_comment(table_name).get("text")

        # Get columns info
        columns = []
        for column in inspector.get_columns(table_name):
            column_info = PgColumn(
                column_name=column["name"],
                data_type=column["type"].__visit_name__,  # Get the data type
                column_comment=column.get("comment"),
                fk_description=get_foreign_key_description(table_name, column["name"]),
            )
            columns.append(column_info)

        # Get primary key info
        primary_key = inspector.get_pk_constraint(table_name)["constrained_columns"]

        # Create PgTable object
        table_info = PgTable(
            table_name=table_name,
            table_comment=table_comment,
            columns=columns,
            primary_key=primary_key,
        )
        tables_info.append(table_info)

    return tables_info


def pgtable_to_custom_format(pg_table: PgTable) -> str:
    # Table name and comment
    result = f"table: {pg_table.table_name}, {pg_table.table_comment or ''}\n"

    # Primary key
    primary_keys = ", ".join(pg_table.primary_key)
    result += f"Primary Key: {primary_keys}\n"

    if pg_table.columns:
        result += "Columns: \n"
    # Columns
    for column in pg_table.columns:
        column_info = f" - {column.column_name}, {column.data_type}"
        if column.column_comment:
            column_info += f", {column.column_comment}"
        if column.fk_description:
            column_info += f", {column.fk_description}"
        result += column_info + "\n"

    return result


def create_db():
    content = Path("tpcc-sqlite.sql").read_text()
    ddls = content.split(";")
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    session = Session()
    for ddl in ddls:
        session.execute(text(ddl))
    session.commit()
    return engine


def get_ddl(engine):
    metadata_obj = MetaData()
    metadata_obj.reflect(bind=engine)
    tables = metadata_obj.sorted_tables
    return list(map(lambda x: str(CreateTable(x).compile(engine)).rstrip(), tables))


def remove_sql_tag(md):
    md = md.strip()
    idx = md.find("```sql")
    if idx >= 0:
        md = md[idx + 6 :].lstrip()
    index = md.find("```")
    if index > 0:
        md = md[:index].lstrip()
    return md.strip()


# Please remove ```sql tags also.


def system_prompt(ddls, DB_TYPE="sqlite"):
    a = f"""\
Given the following {DB_TYPE} tables of records, write SQL query that suits the user's request.
Return only SQL text, avoiding any additional explanations or interpretations.
Remove any ```sql tags.

Database schema:
"""
    b = "\n\n".join(ddls)
    return a + b

def main():
    all_tables_info = get_all_tables_info()
    ddls = [pgtable_to_custom_format(table_info) for table_info in all_tables_info]
    # prompt = "\n\n".join(ddls)
    # print(prompt)

    sp = system_prompt(ddls, DB_TYPE="postgresql")
    print(sp)

    model_name = os.getenv("TEXT_TO_SQL_MODEL")
    if model_name is None:
        model_name = "qwen2.5-coder:14b"

    print(f"Using Ollama with {model_name} ...")

    model = OllamaModel(model_name)
    agent = Agent(model=model, system_prompt=sp)

    result = agent.run_sync('查询名字为"打印机"的库存数量')
    print(result.data)
    print("======")
    print(remove_sql_tag(result.data))


if __name__ == "__main__":
    main()
