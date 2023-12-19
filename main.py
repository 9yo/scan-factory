import os
import re
import sqlite3
from typing import List, Tuple, Dict

DB_PATH = os.environ.get('DB_PATH', 'db.sqlite3')
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


def get_data_from_db(project_id: int) -> List[Tuple[int, str]]:
    # Better implement offset and limit for big tables
    cursor.execute(f"SELECT project_id, name FROM domains WHERE project_id = '{str(project_id)}'")
    return cursor.fetchall()


def insert_regexp(project_id: int, regexp: str):
    cursor.execute(f"INSERT OR REPLACE INTO rules (project_id, regexp) VALUES ('{str(project_id)}', '{regexp}')")
    conn.commit()


def create_regex_for_position(position_data):
    regex_parts = []

    average_count = sum(position_data.values()) / len(position_data.values())

    for domain_part, count in position_data.items():
        if count >= average_count + 1:
            regex_parts.append(re.escape(domain_part))

    if not regex_parts:
        return None

    return '(?:' + '|'.join(regex_parts) + ')'


def regexp_for_bad_domains(project_domains: List[Tuple[int, str]]) -> str:
    patterns: Dict[int, Dict[str, int]] = {}

    # Separate domains into parts and count them for each position
    # patterns[position][domain_body] = domain_body on that position across all domains records
    for project_id, domain in project_domains:
        parts: List[str] = domain.split('.')

        for domain_position, domain_part in enumerate(parts):
            patterns.setdefault(domain_position, {}).setdefault(domain_part, 0)
            patterns[domain_position][domain_part] += 1

    regexp_parts = []

    for pos_data in patterns.values():
        regexp_part = create_regex_for_position(pos_data)
        if regexp_part:
            regexp_parts.append(regexp_part)

    return r'\.'.join(regexp_parts)


def run():
    first_project_id: int = 1234
    second_project_id: int = 5678

    first_project_domains: List[Tuple[int, str]] = get_data_from_db(first_project_id)
    second_project_domains: List[Tuple[int, str]] = get_data_from_db(second_project_id)

    first_project_regexp: str = regexp_for_bad_domains(first_project_domains)
    second_project_regexp: str = regexp_for_bad_domains(second_project_domains)

    insert_regexp(first_project_id, first_project_regexp)
    insert_regexp(second_project_id, second_project_regexp)

    print(f"Domains from first project: {first_project_id} , apply regexp: \'{first_project_regexp}\'")
    for _, domain in first_project_domains:
        if not re.search(first_project_regexp, domain):
            print(f'\t{domain}')

    print(f"\nDomains from second project: {second_project_id} , apply regexp: \'{second_project_regexp}\'")
    for _, domain in second_project_domains:
        if not re.search(second_project_regexp, domain):
            print(f'\t{domain}')


if __name__ == '__main__':
    run()
