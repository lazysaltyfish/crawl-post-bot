import logging
import json
import sqlite3
import requests
import re
import random
import urllib
import time
import argparse
import importlib

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


_parser = argparse.ArgumentParser(description='Pull artical links and push to Telegram channel.')
_parser.add_argument('--token', type=str, required=True, help='Telegram bot token.')
_parser.add_argument('--chat_id', type=str, required=True, help='Chat id.')
_parser.add_argument('--config', type=str, required=False, default='config.json', help='config file in JSON format.')
_parser.add_argument('--db', type=str, required=False, default='data.db', help='Database path, default is ')
_parser.add_argument('--dryrun', type=bool, required=False, default=False, help='Dry run.')
_args = _parser.parse_args()

TOKEN = _args.token
CHAT_ID = _args.chat_id
CONFIG_PATH = _args.config
DB_PATH= _args.db
IS_DRYRUN = _args.dryrun

def push_to_chat(conn: sqlite3.Connection, site_config: dict, chat_id: str, only_new=True):

    def send_message(text: str, chat_id: str) -> bool:
        URL = "https://api.telegram.org/bot" + TOKEN + "/sendMessage?parse_mode=MarkdownV2&text={text}&chat_id={id}".format(text=urllib.parse.quote(text), id=chat_id)
        r = requests.get(URL)
        if r.status_code != 200:
            logging.warning("When push " + text + "\n" + "Got response " + r.text)
            res_object = json.loads(r.text)
            if res_object["error_code"] == 429:
                parameters = res_object["parameters"]
                retry_time = parameters["retry_after"]
                logging.warning("Wait " + str(retry_time) + " for next round")
                time.sleep(retry_time)
            
        return r.status_code == 200

    def conv_str_to_tg(s: str) -> str:
        return s.replace("-", r"\-").replace("#", r"\#").replace(".", r"\.")

    def compose_text(url, desc, title, date, tag):
        result = conv_str_to_tg(tag) + "\n\n" + "[" + conv_str_to_tg(title) + "](" + url + ")\n" + conv_str_to_tg(desc) + "\n" + conv_str_to_tg(date)
        return result
    
    
    QUERY_SQL = "SELECT * From {table}"
    MARK_DONE_SQL = "UPDATE {table} SET done=TRUE WHERE url=\"{url}\""
    cur = conn.cursor()

    if only_new:
        QUERY_SQL += " WHERE done is NULL"

    site_tag = site_config["site_tag"]
    for sub_site in site_config["sub_sites"]:
        table_name = site_tag + sub_site["subsite_tag"]
        cur.execute(QUERY_SQL.format(table=table_name))
        data = cur.fetchall()
        for item in data:
            url, desc, title, date, tag, done = item
            if IS_DRYRUN:
                logging.info("Dryrun: push info in " + url + " ---> " + title)
                continue
            logging.info("Push " + title)
            if send_message(compose_text(url, desc, title, date, tag), chat_id):
                cur.execute(MARK_DONE_SQL.format(table=table_name, url=url))
                conn.commit()
            else:
                logging.error("Error on push " + title)
        

def config_syntax_check(config: dict) -> bool:
    if "site_url" not in config:
        logging.error("Need site url")
        return False
    if "sub_sites" not in config:
        logging.error("Need subsite info")
        return False
    return True

def create_table(conn: sqlite3.Connection, config: dict):
    SQL_TEMPLATE = "create table if not exists {site_tag} (url TEXT primary key, desc TEXT, title TEXT, date TEXT, tag TEXT, done NUMERIC)"
    cursor = conn.cursor()
    tag_prefix = config["site_tag"]
    for subsite in config["sub_sites"]:
        tag = tag_prefix + subsite["subsite_tag"]
        cursor.execute(SQL_TEMPLATE.format(site_tag=tag))
        conn.commit()
    cursor.close()

def parse_url(url: str, parser_func) -> dict:

    AGENT_HEAD = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.92 Safari/537.36"
    headers = {'user-agent': AGENT_HEAD}
    
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return {'code': r.status_code}
    logging.debug("Get {} length response from website".format(len(r.text)))
    
    parse_result = parser_func(r.text)
    return {"code": r.status_code, "content": parse_result}


def update_database(conn: sqlite3.Connection, tag: str, data: list, tag_in_data: str):
    cur = conn.cursor()
    SQL = 'INSERT OR IGNORE INTO {tag} ({columns}, tag, done) VALUES ({placeholder}, \"{tag_in_data}\", NULL)'
    for item in data:
        cur.execute(SQL.format(tag=tag, columns=", ".join(item.keys()), placeholder=":"+", :".join(item.keys()), tag_in_data=tag_in_data), item)

    conn.commit()
    cur.close()

def spy(conn: sqlite3.Connection, config: dict):

    def spy_subsite(conn: sqlite3.Connection, config: dict):
        if "subsite_tag" not in config:
            logging.error("Subsite config error")
        logging.info("comes to " + config["subsite_push_tag"])

        parser_module = importlib.import_module(config["subsite_parser_module"])
        result = parse_url(config["subsite_url"], parser_module.parser_func)
        final_tag = "#" + site_push_tag + " #" + config["subsite_push_tag"]
        if result["code"] != 200:
            logging.warn("spy error on " + config["subsite_name"])
        else:
            update_database(conn, site_tag + config["subsite_tag"], result["content"], final_tag)

    site_name = config["site_name"]
    site_tag = config["site_tag"]
    site_push_tag = config["site_push_tag"]
    logging.info("Working on " + site_name)

    for subsite in config["sub_sites"]:
        spy_subsite(conn, subsite)

def spider_main(push_update=False):

    with open(CONFIG_PATH, "r", encoding='utf-8') as file_config:
        site_config = json.load(file_config)
    
    if config_syntax_check(site_config):
        logging.info("Pass config syntax check")

    conn = sqlite3.connect(DB_PATH)
    create_table(conn, site_config)
    spy(conn, site_config)

    if push_update:
        push_to_chat(conn, site_config=site_config, only_new=True, chat_id=CHAT_ID)

    conn.close()

if __name__ == "__main__":
    spider_main(push_update=True)