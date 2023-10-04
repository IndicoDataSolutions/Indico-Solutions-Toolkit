from indico_toolkit import create_client
from indico_toolkit.auto_populate import AutoPopulator

"""
Create an Indico Classification Workflow without any labeling 
using an organized directory/folder structure. Each folder/directory should contain only one file 
type.

For example, you would target '/base_directory/' if you had your files organized like:

/base_directory/
/base_directory/invoices/ -> contains only invoice files
/base_directory/disclosures/ -> contains only disclosure files
"""

HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"

DIRECTORY_FILE_PATH = "./base_directory/"

client = create_client(HOST, API_TOKEN_PATH)
auto_populator = AutoPopulator(client)
new_workflow = auto_populator.create_auto_classification_workflow(
    DIRECTORY_FILE_PATH,
    "My dataset",
    "My workflow",
    "My teach task",
)