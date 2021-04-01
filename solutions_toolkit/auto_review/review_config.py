from typing import Dict, List, Callable


REQUIRED_CONF_ARGS = ["kwargs", "function"]


class ReviewConfiguration():
    def __init__(self, field_config: List[dict], custom_functions: Dict[str, Callable]):
        """
        field_config is list of function configs
        function config:
        {
            "function": "reject_by_confidence",
            "kwargs": {
                "label": "Check Amount",
                "conf_threshold": 0.98
            },
        }
        """
        self.custom_functions = custom_functions
        self.field_config = validate_field_config(field_config)

    def validate_field_config(field_config):
        for function_config in field_config:
            if not isinstance(function_config, dict):
                raise TypeError(f"{function_config} value is not type dict")
            config_keys = function_config.keys()
            for key in REQUIRED_CONF_ARGS:
                if key not in config_keys:
                    raise KeyError(f"{key} key missing from {function_config} config")
        return field_config