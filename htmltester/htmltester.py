import datetime
import json
import operator
import re
from enum import Enum
from typing import List

import bs4
import requests


class Page:
    def __init__(self, soup):
        self.soup = soup


class Field:
    def __init__(self, css_selector):
        self.css_selector = css_selector


class TextInput(Field):
    def __get__(self, instance, owner):
        element = instance.soup.select_one(self.css_selector)
        return element.text.strip()


class DateInput(TextInput):
    def __get__(self, instance, owner):
        value = super().__get__(instance, owner)
        return datetime.datetime.strptime(value, "%d/%m/%Y").date()


class Types(str, Enum):
    TEXT = "text"
    DATE = "date"


TypesToClasses = {
    Types.TEXT: TextInput,
    Types.DATE: DateInput,
}

ClassesToTypes = {v: k for k, v in TypesToClasses.items()}

Operators = {
    '==': operator.eq,
    '>=': operator.ge,
    'regex': lambda l, r: re.match(l, r),
    # ...
}


def test_runner(self, *, tests: List):
    for index, test in enumerate(tests):
        name = test.get('name', f'test {index:04}')
        field = test['field']
        op = Operators[test['operator']]
        expected_value = test['expected_value']

        try:
            assert op(getattr(self, field), expected_value), (
                f'{getattr(self, field)} {test["operator"]} {expected_value}'
            )
        except AssertionError as err:
            print(f'Test {name} fails: {err}')
        else:
            print(f'Test "{name}" passes!')


def init_page(self, *, url: str):
    response = requests.get(url)
    content = response.content
    soup = bs4.BeautifulSoup(content, 'html.parser')
    self.soup = soup  # dirty! Should call super (and go through metaclasses instead)


def build_page_class(*, name: str, definition: List, ) -> type:
    extra = {
        field['name']: TypesToClasses[Types(field['type'])](field['selector']) for field in definition
    }
    extra['test_runner'] = test_runner
    extra['__init__'] = init_page
    return type(
        f'{name}Page',
        (Page,),
        extra
    )


def main():
    with open('htmltester_conf.json') as conf:
        data_conf = json.load(conf)

    if data_conf:
        for index, page in enumerate(data_conf.get('pages')):
            PageClass = build_page_class(
                name=page.get('name', f'Test{index:04}'),
                definition=page.get('definition', []),
            )
            url = page['url']
            tests = page.get('tests', [])
            page_obj = PageClass(url=url)

            page_obj.test_runner(tests=tests)


if __name__ == '__main__':
    main()
