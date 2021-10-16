#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 19 18:07:17 2021

@author: franz
"""
import logging
import re
from typing import List, Final, Pattern
import sys
from languageSpecificCorrectors.arabic_corrector import ArabicCorrector
from languageSpecificCorrectors.english_corrector import EnglishCorrector
from languageSpecificCorrectors.french_corrector import FrenchCorrector
from languageSpecificCorrectors.german_corrector import GermanCorrector
from languageSpecificCorrectors.spanish_corrector import SpanishCorrector


class Corrector:
    """
    Takes in a page to correct and offers functions to fix language specific and language nonspecific typos
    """

    __slots__ = ['__fixed_content', '__LANGUAGE']

    def __init__(self, content_to_be_fixed: List[str], language: str) -> None:
        self.__fixed_content: List[str] = content_to_be_fixed
        self.__LANGUAGE: Final[str] = language

    @staticmethod
    def __fix_capitalization(text_to_correct: str) -> str:
        """
        Fix wrong capitalization at the beginning of a sentence or after a colon

        Args:
            text_to_correct (str): Text to be fixed

        Returns:
            str: String where the letter following a .!?;: is capitalized
        """
        # TODO: Quotation marks are not yet covered - double check if necessary
        FIND_WRONG_CAPITALIZATION: Final[Pattern[str]] = re.compile(r'[.!?:;]\s*([a-z])')
        matches = re.finditer(FIND_WRONG_CAPITALIZATION, text_to_correct)
        fixed_text: str = text_to_correct
        for match in reversed(list(matches)):
            fixed_text = fixed_text[:match.end() - 1] + match.group(1).upper() + fixed_text[match.end():]
        fixed_text = fixed_text[0].upper() + fixed_text[1:]
        return fixed_text

    @staticmethod
    def __fix_misplaced_spaces(text_to_correct: str) -> str:
        """
        Reduce redundant spaces to one
        Insert missing spaces between punctuation and chars
        Erase redundant spaces before punctuation

        Args:
            text_to_correct (str): Text to be fixed

        Returns:
           str: String with correct amount of spaces
        """
        fixed_section: str
        check_multiple_spaces = re.compile(r'( ){2,}')
        check_missing_spaces = re.compile(r'([.!?;,])(\w)')
        check_wrong_spaces = re.compile(r'\s+([.!?;,])')
        fixed_section = re.sub(check_multiple_spaces, r' ', text_to_correct)
        fixed_section = re.sub(check_missing_spaces, r'\1 \2', fixed_section)
        fixed_section = re.sub(check_wrong_spaces, r'\1', fixed_section)
        return fixed_section

    def fix_language_independent_typos(self) -> None:
        """
        Fixes typos in page translation-sections independent of language:
            * Reduce redundant spaces to one
            * Insert missing spaces between punctuation and chars
            * Erase redundant spaces before punctuation
            * Fix wrong capitalization at the beginning of a sentence or after a colon
        """
        for counter, content in enumerate(self.__fixed_content):
            content = self.__fix_misplaced_spaces(content)
            content = self.__fix_capitalization(content)
            self.__fixed_content[counter] = content

    @staticmethod
    def unify_document_file_name(file_name: str) -> str:
        """
        Unifies document file names (.doc, .odg, .odt, .pdf) and ignores others
        - limit unification to document files with the following extensions: '.doc', '.odg', '.odt', and '.pdf'
        - replace spaces with single underscore
        - replace multiple consecutive underscores with single underscore
        - have file ending in lower case
        """
        if not file_name.lower().endswith(('.doc', '.odg', '.odt',  '.pdf')):
            logging.info(f"input parameter does not look to be a file: {file_name}")
            return file_name

        file_name = re.sub(r"( )+", r'_', file_name)
        file_name = re.sub(r"_+", r'_', file_name)
        name: str = file_name[:-4]
        extension: str = file_name[-4:].lower()
        return name + extension

    def fix_language_specific_typos(self) -> None:
        """
        Fixes language specific typos - use function to dispatch the language
        """
        for paragraph_counter in range(len(self.__fixed_content)):
            paragraph: str = self.__fixed_content[paragraph_counter]

            if self.__LANGUAGE == "en":
                self.__fixed_content[paragraph_counter] = EnglishCorrector(paragraph).run()
            elif self.__LANGUAGE == "de":
                self.__fixed_content[paragraph_counter] = GermanCorrector(paragraph).run()
            elif self.__LANGUAGE == "fr":
                self.__fixed_content[paragraph_counter] = FrenchCorrector(paragraph).run()
            elif self.__LANGUAGE == "es":
                self.__fixed_content[paragraph_counter] = SpanishCorrector(paragraph).run()
            elif self.__LANGUAGE == "ar":
                self.__fixed_content[paragraph_counter] = ArabicCorrector(paragraph).run()
            else:
                logging.fatal("Unknown language")
                sys.exit(1)

    @staticmethod
    def fix_right_to_left_title(text_to_correct: str) -> str:
        """ when title ends with closing parenthesis, add a RTL mark at the end
        Only use this for the "page display title" translation unit!
        TODO: Move this into a separate class that individual language classes like Arabic can inherit from
        """
        return re.sub(r'\)$', ')\u200f', text_to_correct)

    @staticmethod
    def fix_right_to_left_filename(text_to_correct: str) -> str:
        """ when file name has a closing parenthesis right before the file ending,
        make sure we have a RTL mark in there!
        TODO: Move this into a separate class that individual language classes like Arabic can inherit from
        """
        file_extensions: List[str] = ['.pdf', '.odt', '.doc', '.odg']
        if not text_to_correct.endswith(tuple(file_extensions)):
            # TODO logger.info(f"Translation unit doesn't seem to be a file name: {text_to_correct}")
            return text_to_correct
        re.sub(r'\)\.([a-z][a-z][a-z])$', ')\u200f.\\1', text_to_correct)
        return text_to_correct

    @property
    def get_corrected_paragraphs(self) -> List[str]:
        """
        Getter for fixed reduced page

        Returns:
            ReducedPage: reduced page with fixed content
        """
        return self.__fixed_content
