from indico import IndicoClient, IndicoConfig
from indico.errors import IndicoAuthenticationFailed
from indico_toolkit.errors import ToolkitAuthError

def create_client(
    host: str,
    api_token_path: str = None,
    api_token_string: str = None,
    verify_ssl: bool = True,
    **kwargs,
) -> IndicoClient:
    """
    Instantiate your Indico API client. 
    Specify either the path to your token or the token string itself.
    """
    config = IndicoConfig(
        host=host,
        api_token_path=api_token_path,
        api_token=api_token_string,
        verify_ssl=verify_ssl,
        **kwargs,
    )
    try:
        return IndicoClient(config)
    except IndicoAuthenticationFailed as e:
        raise ToolkitAuthError(
            f"{e}\n\n Ensure that you are using your most recently downloaded token with the correct host URL"
        )
