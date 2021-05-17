from typing import Dict, List, Callable


REQUIRED_CONF_ARGS = ["function"]


class ReviewConfiguration:
    def __init__(
        self, field_config: List[dict], custom_functions: Dict[str, Callable] = {}
    ):
        """
        Args:
        field_config (List[dict]): list of function config dictionaries. Available functions defined in auto_review_functions.py
        function config:
        {
            "function": "reject_by_confidence",
            "kwargs": {
                "labels": ["Check Amount", "Name"],
                "conf_threshold": 0.98
            },
        }
        custom_functions (Dict[str, Callable]): Dictionary with custom functions to
                                                use in auto-review
        """
        self.custom_functions = custom_functions
        self.field_config = self.validate_field_config(field_config)

    @staticmethod
    def validate_field_config(field_config):
        for function_config in field_config:
            if not isinstance(function_config, dict):
                raise TypeError(f"{function_config} value is not type dict")
            config_keys = function_config.keys()
            for key in REQUIRED_CONF_ARGS:
                if key not in config_keys:
                    raise KeyError(f"{key} key missing from {function_config} config")
        return field_config
