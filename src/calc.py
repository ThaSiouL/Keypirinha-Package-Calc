# Keypirinha | A semantic launcher for Windows | http://keypirinha.com

import ast
import math
import random
from itertools import chain

import keypirinha as kp
import keypirinha_util as kpu

from .lib import simpleeval


class Calc(kp.Plugin):
    """
    Inline calculator.

    Evaluates a mathematical expression and shows its result.
    """

    DEFAULT_KEYWORD = "="
    DEFAULT_ALWAYS_EVALUATE = True
    DEFAULT_DECIMAL_SIGN = "."
    MAX_ROUNDING_PRECISION = 16
    DEFAULT_ROUNDING_PRECISION = 8

    MATH_CONSTANTS = {
        'pi': math.pi,
        'e': math.e,
        'inf': math.inf,
        'nan': math.nan,
    }

    MATH_FUNCTIONS = {
        'abs': abs,
        'bool': bool,
        'chr': chr,
        'divmod': divmod,
        'float': float,
        'hex': hex,
        'bin': bin,
        'int': int,
        'len': len,
        'min': min,
        'max': max,
        'oct': oct,
        'ord': ord,
        'pow': pow,
        'round': round,
        'str': str,

        'rand': simpleeval.random_int,
        'rand1': random.random,  # returns [0.0, 1.0)
        'randf': random.uniform,
        # random.uniform(a, b): Return a random floating point number N such that a <= N <= b for a <= b and b <= N <= a for b < a
        'randi': random.randint,  # returns N where: a <= N <= b

        'acos': math.acos,
        'acosh': math.acosh,
        'asin': math.asin,
        'asinh': math.asinh,
        'atan': math.atan,
        'atan2': math.atan2,
        'atanh': math.atanh,
        'ceil': math.ceil,
        'cos': math.cos,
        'cosh': math.cosh,
        'deg': math.degrees,
        'exp': math.exp,
        'factor': math.factorial,
        'floor': math.floor,
        'gcd': math.gcd,
        'hypot': math.hypot,
        'log': math.log,
        'rad': math.radians,
        'sin': math.sin,
        'sinh': math.sinh,
        'sqrt': math.sqrt,
        'tan': math.tan,
        'tanh': math.tanh,
    }

    ADDITIONAL_MATH_OPERATORS = {
        ast.BitXor: simpleeval.safe_power
    }

    always_evaluate = DEFAULT_ALWAYS_EVALUATE
    decimal_sign = DEFAULT_DECIMAL_SIGN
    keyword = DEFAULT_KEYWORD
    trans = ''
    operators = dict(chain(simpleeval.DEFAULT_OPERATORS.items(), ADDITIONAL_MATH_OPERATORS.items()))

    def __init__(self):
        super().__init__()

    def on_start(self):
        self._read_config()

    def on_catalog(self):
        self._read_config()
        self.set_catalog([self.create_item(
            category=kp.ItemCategory.KEYWORD,
            label=self.keyword,
            short_desc="Evaluate a mathematical expression",
            target=self.keyword,
            args_hint=kp.ItemArgsHint.REQUIRED,
            hit_hint=kp.ItemHitHint.NOARGS)])

    def on_suggest(self, user_input, items_chain):
        if len(user_input) == 0:
            return
        if not items_chain and not self.always_evaluate:
            return
        if items_chain and (
                        items_chain[0].category() != kp.ItemCategory.KEYWORD or
                        items_chain[0].target() != self.keyword):
            return

        suggestions = []
        try:
            result = simpleeval.simple_eval(user_input.translate(self.trans),
                                            operators=self.operators,
                                            functions=self.MATH_FUNCTIONS,
                                            names=self.MATH_CONSTANTS)
            result_str = "{number:.{digits}g}".format(number=result, digits=self.rounding_precision).translate(
                self.trans)
            suggestions.append(self.create_item(
                category=kp.ItemCategory.EXPRESSION,
                label=user_input,
                short_desc="= {number} (Press Enter to copy the result)".format(number=result_str),
                target=user_input,
                args_hint=kp.ItemArgsHint.FORBIDDEN,
                hit_hint=kp.ItemHitHint.IGNORE,
                data_bag=result_str))
        except Exception as e:
            if not items_chain:
                return  # stay quiet if an item hasn't been selected yet
            result_str = str(e)
            suggestions.append(self.create_error_item(
                label=user_input,
                short_desc="Error: " + str(e)))

        if user_input != result_str:  # Input String
            self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    def on_execute(self, item, action):
        if item and item.category() == kp.ItemCategory.EXPRESSION:
            kpu.set_clipboard(item.data_bag())

    def on_events(self, flags):
        if flags & kp.Events.PACKCONFIG:
            # repopulating the catalog entry in case the keyword was changed
            self.on_catalog()

    def _read_config(self):
        settings = self.load_settings()
        self.always_evaluate = settings.get_bool(
            "always_evaluate", "main", self.DEFAULT_ALWAYS_EVALUATE)
        self.decimal_sign = settings.get_stripped(
            "decimal_sign", "main", self.DEFAULT_DECIMAL_SIGN)
        self.keyword = settings.get_stripped(
            "keyword", "main", self.DEFAULT_KEYWORD)
        self.rounding_precision = settings.get_int(
            "rounding_precision", "main", self.DEFAULT_ROUNDING_PRECISION)
        self.validate_config_values()

    def validate_config_values(self):
        if len(self.decimal_sign) != 1:
            self.decimal_sign = self.DEFAULT_DECIMAL_SIGN
        if self.rounding_precision not in range(self.MAX_ROUNDING_PRECISION):
            self.rounding_precision = self.DEFAULT_ROUNDING_PRECISION
        self.trans = str.maketrans(self.DEFAULT_DECIMAL_SIGN + self.decimal_sign,
                                   self.decimal_sign + self.DEFAULT_DECIMAL_SIGN)
